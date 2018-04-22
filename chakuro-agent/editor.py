import os
import time
from ws import WS
from functools import partial
from pathlib import Path
import jedi
from online_feature_extractor import OnlineFeatureExtractor
from sklearn.externals import joblib
from logzero import logger as log


DEBUG = False
feature_extractor = OnlineFeatureExtractor()

register = partial(WS.register, 'editor')
# MODEL_PATH = '/Users/ray/Code/Working/train10.model'
MODEL_PATH = './resources/v1.model'
model = joblib.load(Path(MODEL_PATH))
model.n_jobs = 1
log.info(f'Model {MODEL_PATH} loaded, n_jobs={model.n_jobs}')


@register('openFile')
async def open_file(msg, send, context):
    context.path = Path(*msg['filePath'])
    with open(context.path) as f:
        content = f.read()
    context.doc = content.splitlines()
    await send({
        'cmd': 'openFile',
        'mtime': str(context.path.stat().st_mtime),
        'content': content
    })


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
    with open(context.path, 'w') as f:
        f.write(msg['content'])
    await send({
        'cmd': 'saveFile-ok',
        'mtime': str(context.path.stat().st_mtime)
    })


@register('sync')
async def sync(msg, send, context):
    context.doc = msg['doc'].splitlines()


@register('predict')
async def predict(msg, send, context):
    line_content = msg['text']
    line_number = msg['line']
    ch = msg['ch']

    while len(context.doc) <= line_number:
        context.doc.append('')
    context.doc[line_number] = line_content
    doc = '\n'.join(context.doc)
    j = jedi.Script(doc, line_number + 1, ch, context.path)
    completions = j.completions()

    if DEBUG:
        log.info(doc)
        log.info(completions)
        
    if completions:
        context.currentCompletions = {
            completion.name: completion for completion in completions
        }
        feature_extractor.extract_online(completions, line_content, line_number, ch, doc, j.call_signatures())
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

    await send({
        'cmd': 'predict-result',
        'line': line_number,
        'ch': ch,
        'result': result
    })


@register('getCompletionDocstring')
async def get_completion_docstring(msg, send, context):
    result = context.currentCompletions.get(msg['name'], None)
    if result:
        result = result.docstring(fast=False)
    await send({
        'cmd': 'getCompletionDocstring-result',
        'docstring': result
    })


@register('findUsages')
async def find_usage(msg, send, context):
    print(msg)
    doc = '\n'.join(context.doc)
    j = jedi.Script(doc, msg['line'] + 1, msg['ch'], context.path)
    usages = j.usages()
    print(usages)
    await send({
        'cmd': 'findUsages-ok',
        'pos': [
            (i.line - 1, i.column + 1) for i in usages
        ],
        'token': msg['token']
    })
