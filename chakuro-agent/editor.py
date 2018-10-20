from ws import WS
from online_feature_extractor import OnlineFeatureExtractor
from modeling.rule_based_predictor import RuleBasedPredictor
from doc_generator import DocGenerator
from word_completer import search_prefix
from utils import detect_doc_type, Timer
from importlib.resources import open_binary

from functools import partial
from pathlib import Path
from sklearn.externals import joblib
from logzero import logger as log
from boltons.fileutils import atomic_save
from boltons.gcutils import toggle_gc_postcollect

import jedi
import wordsegment
import numpy as np


DEBUG = False
doc_generator = DocGenerator()

register = partial(WS.register, 'editor')
MODEL_NAME = 'v10.model'
model = joblib.load(open_binary('resources', MODEL_NAME))
model.n_jobs = 1
log.info(f'Model {MODEL_NAME} loaded, n_jobs={model.n_jobs}')


@register('openFile')
async def open_file(msg, send, context):
    context.path = Path(*msg['filePath'])
    with open(context.path) as f:
        content = f.read()
    # somehow risky, but it should not wait until the extractor ready
    await send({
        'cmd': 'openFile',
        'mtime': str(context.path.stat().st_mtime),
        'content': content
    })
    with Timer('Initializing extractor'):
        with toggle_gc_postcollect:
            context.doc = content.splitlines()
            # initialize feature extractor
            context.feature_extractor = OnlineFeatureExtractor()
            for line, line_content in enumerate(context.doc):
                context.feature_extractor.fill_preprocessor_context(line_content, line, context.doc)
            context.rule_based_predictor = RuleBasedPredictor()
            # warm up Jedi
            j = jedi.Script('\n'.join(context.doc), len(context.doc), 1, context.path)
            j.completions()


@register('reload')
async def reload(msg, send, context):
    with open(context.path) as f:
        content = f.read()
    context.doc = content.splitlines()
    await send({
        'cmd': 'reload-ok',
        'content': content
    })


@register('mtime')
async def modification_time(msg, send, context):
    new_path = msg.get('newPath', None)
    if new_path is not None:
        print('path modified', context.path, new_path)
        context.path = Path(*new_path)
    try:
        await send({
            'cmd': 'mtime',
            'mtime': str(context.path.stat().st_mtime)
        })
    except FileNotFoundError:
        await send({
            'cmd': 'event-FileDeleted'
        })


@register('saveFile')
async def save_file(msg, send, context):
    with atomic_save(str(context.path)) as f:
        f.write(msg['content'].encode('utf-8'))
    await send({
        'cmd': 'saveFile-ok',
        'mtime': str(context.path.stat().st_mtime)
    })


@register('sync')
async def sync(msg, send, context):
    context.doc = msg['doc'].splitlines()
    for line, line_content in enumerate(context.doc):
        context.feature_extractor.fill_preprocessor_context(line_content, line, context.doc)


@register('syncLine')
async def sync(msg, send, context):
    line_content = msg['text']
    line = msg['line']
    set_line(context, line, line_content)
    context.feature_extractor.fill_preprocessor_context(line_content, line, context.doc)


def set_line(context, line_number, line_content):
    while len(context.doc) <= line_number:
        context.doc.append('')
    context.doc[line_number] = line_content


@register('predict')
async def predict(msg, send, context):
    line_content = msg['text']
    line_number = msg['line']
    ch = msg['ch']
    set_line(context, line_number, line_content)
    doc = '\n'.join(context.doc)
    with Timer(f'Prediction ({line_number}, {ch})'):
        j = jedi.Script(doc, line_number + 1, ch, context.path)
        completions = j.completions()

    if DEBUG:
        print('completions:', completions)

    with Timer(f'Rest ({line_number}, {ch})'):
        if completions:
            context.currentCompletions = {
                completion.name: completion for completion in completions
            }
            feature_extractor = context.feature_extractor
            feature_extractor.extract_online(completions, line_content, line_number, ch, context.doc, j.call_signatures())
            scores = model.predict_proba(feature_extractor.X)[:, 1] * 1000
            result = [
                {
                    'c': c.name,  # completion
                    't': c.type,  # type
                    's': int(s)  # score
                } for c, s in zip(completions, scores)
            ]
        else:
            result = []

    with Timer(f'Rule-based ({line_number}, {ch})'):
        top_completion = None
        if completions:
            top_completion = completions[np.argmax(scores)]

        rule_based_results = context.rule_based_predictor.predict(
            top_completion=top_completion,
            doc=context.doc,
            line=line_number,
            ch=ch
        )

    await send({
        'cmd': 'predict-result',
        'line': line_number,
        'ch': ch,
        'result': result,
        'rule_based_results': rule_based_results
    })


@register('predictExtra')
async def predict_extra(msg, send, context):
    text = msg['input']
    line_number = msg['line']
    ch = msg['ch']
    result = []
    result_set = set()
    # 
    # 1. existed tokens
    tokens = context.feature_extractor.context.t0map.query_prefix(text, line_number)
    for i, token in enumerate(tokens):
        if token in result_set:
            continue
        result.append(dict(c=token, t='token', s=990-i))
        result_set.add(token)

    # 2. words from dictionary
    if len(result) < 6:
        words = search_prefix(text)
        for i, word in enumerate(words):
            if word in result_set:
                continue
            result.append(dict(c=word + ' = ', t='word', s=980-i))
            result_set.add(word)

    # 3. segmented words
    if len(result) < 6:
        segmented_words = wordsegment.segment(text)
        if segmented_words:
            snake = '_'.join(segmented_words)
            if snake not in result_set:
                result.append(dict(c=snake + ' = ', t='word-segment', s=1))

    await send({
        'cmd': 'predictExtra-result',
        'line': line_number,
        'ch': ch,
        'result': result
    })


@register('getCompletionDocstring')
async def get_completion_docstring(msg, send, context):
    # get docstring
    completion = context.currentCompletions.get(msg['name'], None)
    if not completion:
        return
    docstring = completion.docstring(fast=False)

    # try to follow definition if it fails to get docstring
    if not docstring:
        try:
            definition = completion.follow_definition()
        except NotImplementedError:
            return
        if not definition:
            return
        docstring = definition[0].docstring()
        if not docstring:
            return

    # render doc
    doc_type = detect_doc_type(docstring)
    html = None
    if doc_type != 'text':
        try:
            html = doc_generator.make_html(docstring)
        except Exception as e:
            print(e)
    await send({
        'cmd': 'getCompletionDocstring-result',
        'doc': html if html else docstring,
        'type': 'html' if html else 'text'
    })


@register('getFunctionDocumentation')
async def get_function_documentation(msg, send, context):
    line_content = msg['text']
    line_number = msg['line']
    ch = msg['ch']

    set_line(context, line_number, line_content)
    doc = '\n'.join(context.doc)

    j = jedi.Script(doc, line_number + 1, ch, context.path)
    call_signatures = j.call_signatures()
    if not call_signatures:
        log.debug('call signature is empty while obtaining docstring')
        return
    signature = call_signatures[0]
    docstring = signature.docstring()
    if not docstring:
        return
    doc_type = detect_doc_type(docstring)
    html = None
    if doc_type != 'text':
        try:
            html = doc_generator.make_html(docstring)
        except Exception as e:
            print(e)

    await send({
        'cmd': 'getFunctionDocumentation-result',
        'doc': html if html else docstring,
        'fullName': signature.full_name,
        'type': 'html' if html else 'text'
    })


@register('findUsages')
async def find_usage(msg, send, context):
    doc = '\n'.join(context.doc)
    j = jedi.Script(doc, msg['line'] + 1, msg['ch'], context.path)
    usages = j.usages()
    await send({
        'cmd': 'findUsages-ok',
        'pos': [
            (i.line - 1, i.column + 1) for i in usages
        ],
        'token': msg['token']
    })
