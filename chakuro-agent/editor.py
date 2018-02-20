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


@register('saveFile')
async def save_file(msg, send, context):
    with open(msg['filePath'], 'w') as f:
        f.write(msg['content'])
    await send({
        'cmd': 'saveFile-ok'
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
