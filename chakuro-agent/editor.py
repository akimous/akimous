from ws import WS
from functools import partial
from pathlib import Path
import jedi
from online_feature_extractor import OnlineFeatureExtractor
from sklearn.externals import joblib
from logzero import logger as log
from doc_generator import DocGenerator
from utils import detect_doc_type
from contextlib import suppress

DEBUG = False
feature_extractor = OnlineFeatureExtractor()
doc_generator = DocGenerator()

register = partial(WS.register, 'editor')
MODEL_PATH = './resources/v2.model'
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
    j = jedi.Script(doc, line_number + 1, ch, context.path)
    completions = j.completions()

    if DEBUG:
        print('completions:', completions)

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
