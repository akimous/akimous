import asyncio
import json
import shlex
from asyncio import create_subprocess_shell, subprocess
from collections import namedtuple
from functools import partial
from importlib.resources import open_binary
from pathlib import Path

import jedi
import pyflakes.api
import wordsegment
from boltons.gcutils import toggle_gc_postcollect
from logzero import logger as log
from sklearn.externals import joblib

from doc_generator import DocGenerator  # 165ms, 13M memory
from online_feature_extractor import OnlineFeatureExtractor  # 90ms, 10M memory
from pyflakes_reporter import PyflakesReporter
from utils import Timer, detect_doc_type
from websocket import register_handler
from word_completer import search_prefix

handles = partial(register_handler, 'editor')
DEBUG = False
doc_generator = DocGenerator()
MODEL_NAME = 'v10.model'
model = joblib.load(open_binary('resources', MODEL_NAME))  # 300 ms
model.n_jobs = 1
log.info(f'Model {MODEL_NAME} loaded, n_jobs={model.n_jobs}')

PredictionRow = namedtuple('PredictionRow', ('c', 't', 's'))


async def lint_offline(context, send):
    try:
        with Timer('Linting'):
            absolute_path = context.path.absolute()
            context.linter_process = await create_subprocess_shell(
                f'cd {shlex.quote(str(absolute_path.parent))} && '
                f'pylint {shlex.quote(str(absolute_path))} --output-format=json',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await context.linter_process.communicate()
            if stderr:
                log.error(stderr)
            context.linter_output = json.loads(stdout)
        await send('OfflineLints', {
            'result': context.linter_output,
        })
    except Exception as e:
        log.error(e)


async def yapf(context, send):
    try:
        with Timer('YAPF'):
            absolute_path = context.path.absolute()
            context.yapf_process = await create_subprocess_shell(
                f'cd {shlex.quote(str(absolute_path.parent))} && '
                f'yapf {shlex.quote(str(absolute_path))} --in-place',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await context.yapf_process.communicate()
            if stdout:
                log.info(stdout)
            if stderr:
                log.error(stderr)
    except Exception as e:
        log.error(e)


async def isort(context, send):
    try:
        with Timer('Sorting'):
            absolute_path = context.path.absolute()
            context.isort_process = await create_subprocess_shell(
                f'cd {shlex.quote(str(absolute_path.parent))} && '
                f'isort {shlex.quote(str(absolute_path))} --atomic',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await context.isort_process.communicate()
            if stdout:
                log.info(stdout)
            if stderr:
                log.error(stderr)
    except Exception as e:
        log.error(e)


@handles('OpenFile')
async def open_file(msg, send, context):
    context.path = Path(*msg['filePath'])
    context.is_python = context.path.suffix in ('.py', '.pyx')
    context.pyflakes_reporter = PyflakesReporter()
    with open(context.path) as f:
        content = f.read()
    # somehow risky, but it should not wait until the extractor ready
    await send('FileOpened', {
        'mtime': context.path.stat().st_mtime,
        'content': content
    })
    # skip all completion, linting etc. if it is not a Python file
    if not context.is_python:
        return

    with Timer('Initializing extractor'):
        with toggle_gc_postcollect:
            context.doc = content.splitlines()
            # initialize feature extractor
            context.feature_extractor = OnlineFeatureExtractor()
            for line, line_content in enumerate(context.doc):
                context.feature_extractor.fill_preprocessor_context(line_content, line, context.doc)
            # warm up Jedi
            j = jedi.Script('\n'.join(context.doc), len(context.doc), 0, context.path)
            j.completions()

    context.linter_task = asyncio.create_task(lint_offline(context, send))
    with Timer('pyflakes'):
        pyflakes.api.check(content, '', context.pyflakes_reporter)
        await send('RealTimeLints', dict(result=context.pyflakes_reporter.errors))


@handles('Reload')
async def reload(msg, send, context):
    with open(context.path) as f:
        content = f.read()
    context.doc = content.splitlines()
    await send('Reloaded', {
        'content': content
    })


@handles('Mtime')
async def modification_time(msg, send, context):
    new_path = msg.get('newPath', None)
    if new_path is not None:
        print('path modified', context.path, new_path)
        context.path = Path(*new_path)
    try:
        await send('Mtime', {
            'mtime': context.path.stat().st_mtime
        })
    except FileNotFoundError:
        await send('FileDeleted', {})


@handles('SaveFile')
async def save_file(msg, send, context):
    # with atomic_save(str(context.path)) as f:
    #     f.write(msg['content'].encode('utf-8'))
    with open(context.path, 'w') as f:
        f.write(msg['content'])
    mtime_before_formatting = context.path.stat().st_mtime
    result = {
            'mtime': mtime_before_formatting
        }
    if not context.is_python:
        await send('FileSaved', result)
        return

    await yapf(context, send)
    await isort(context, send)
    mtime_after_formatting = context.path.stat().st_mtime
    if mtime_after_formatting != mtime_before_formatting:
        with open(context.path) as f:
            content = f.read()
        result['mtime'] = mtime_after_formatting
        result['content'] = content
    await send('FileSaved', result)
    context.linter_task = asyncio.create_task(lint_offline(context, send))


@handles('Sync')
async def sync(msg, send, context):
    context.doc = msg['doc'].splitlines()
    for line, line_content in enumerate(context.doc):
        context.feature_extractor.fill_preprocessor_context(line_content, line, context.doc)


@handles('SyncLine')
async def sync_line(msg, send, context):
    line_content = msg['text']
    line = msg['line']
    set_line(context, line, line_content)
    context.feature_extractor.fill_preprocessor_context(line_content, line, context.doc)


def set_line(context, line_number, line_content):
    while len(context.doc) <= line_number:
        context.doc.append('')
    context.doc[line_number] = line_content


@handles('Predict')
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
            feature_extractor.extract_online(completions, line_content, line_number, ch, context.doc,
                                             j.call_signatures())
            scores = model.predict_proba(feature_extractor.X)[:, 1] * 1000
            result = [
                PredictionRow(c=c.name_with_symbols, t=c.type, s=int(s))
                for c, s in zip(completions, scores)
            ]
        else:
            result = []

    await send('Prediction', {
        'line': line_number,
        'ch': ch,
        'result': result,
    })


@handles('PredictExtra')
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
        result.append(PredictionRow(c=token, t='token', s=990 - i))
        result_set.add(token)

    # 2. words from dictionary
    if len(result) < 6:
        words = search_prefix(text)
        for i, word in enumerate(words):
            if word in result_set:
                continue
            result.append(PredictionRow(c=word, t='word', s=980 - i))
            result_set.add(word)

    # 3. segmented words
    if len(result) < 6:
        segmented_words = wordsegment.segment(text)
        if segmented_words:
            snake = '_'.join(segmented_words)
            if snake not in result_set:
                result.append(PredictionRow(c=snake, t='word-segment', s=1))

    await send('ExtraPrediction', {
        'line': line_number,
        'ch': ch,
        'result': result
    })


@handles('GetCompletionDocstring')
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
    await send('CompletionDocstring', {
        'doc': html if html else docstring,
        'type': 'html' if html else 'text'
    })


@handles('GetFunctionDocumentation')
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

    await send('FunctionDocumentation', {
        'doc': html if html else docstring,
        'fullName': signature.full_name,
        'type': 'html' if html else 'text'
    })


@handles('FindUsages')
async def find_usage(msg, send, context):
    doc = '\n'.join(context.doc)
    j = jedi.Script(doc, msg['line'] + 1, msg['ch'], context.path)
    usages = j.usages()
    await send('UsageFound', {
        'pos': [
            (i.line - 1, i.column + 1) for i in usages
        ],
        'token': msg['token']
    })
