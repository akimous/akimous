import json
import shlex
import sys
from asyncio import (CancelledError, create_subprocess_shell, create_task,
                     subprocess)
from collections import namedtuple
from functools import partial
from importlib import resources
from pathlib import Path

import jedi
import pyflakes.api
import wordsegment
from logzero import logger

from .completion_utilities import is_parameter_of_def
from .config import config
from .doc_generator import DocGenerator  # 165ms, 13M memory
from .jedi_preloader import preload_modules
from .modeling.feature.feature_definition import tokenize
from .online_feature_extractor import \
    OnlineFeatureExtractor  # 90ms, 10M memory
from .project import persistent_state, save_state
from .pyflakes_reporter import PyflakesReporter
from .utils import Timer, detect_doc_type, log_exception, nop
from .websocket import register_handler
from .word_completer import search_prefix

# prevent pandas being imported by xgboost (save ~500ms)
_pandas = sys.modules.get('pandas', None)
if _pandas:
    from xgboost.core import Booster, DMatrix
else:
    sys.modules['pandas'] = None
    from xgboost.core import Booster, DMatrix
    del sys.modules['pandas']

DEBUG = False
MODEL_NAME = 'v12.xgb'
PredictionRow = namedtuple('PredictionRow', ('c', 't', 's', 'p'))

handles = partial(register_handler, 'editor')
doc_generator = DocGenerator()

with resources.path('akimous.resources', MODEL_NAME) as _path:
    model = Booster(model_file=str(_path))  # 3 ms
    model.set_param('nthread', 1)
logger.info('Model %s loaded.', MODEL_NAME)


def get_relative_path(context):
    try:
        return tuple(
            context.path.relative_to(context.shared.project_root).parts)
    except ValueError:
        # the file does not belong to the project folder
        return tuple(context.path.parts)


async def run_pylint(context, send):
    if not config['linter']['pylint']:
        return
    if context.path.suffix != '.py':
        return
    try:
        with Timer('Linting'):
            absolute_path = context.path.absolute()
            context.linter_process = await create_subprocess_shell(
                f'cd {shlex.quote(str(absolute_path.parent))} && '
                f'pylint {shlex.quote(str(absolute_path))} --output-format=json',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            stdout, stderr = await context.linter_process.communicate()
            if stderr:
                logger.error(stderr)
            context.linter_output = json.loads(stdout)
        await send('OfflineLints', {
            'result': context.linter_output,
        })
    except (CancelledError, AttributeError):
        # may raise AttributeError after the editor is closed
        return
    except Exception as e:
        logger.exception(e)


async def run_yapf(context):
    if not config['formatter']['yapf']:
        return
    if context.path.suffix != '.py':
        return
    with log_exception():
        with Timer('YAPF'):
            absolute_path = context.path.absolute()
            context.yapf_process = await create_subprocess_shell(
                f'cd {shlex.quote(str(absolute_path.parent))} && '
                f'yapf {shlex.quote(str(absolute_path))} --in-place',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            stdout, stderr = await context.yapf_process.communicate()
            if stdout:
                logger.info(stdout)
            if stderr:
                logger.error(stderr)


async def run_isort(context):
    if not config['formatter']['isort']:
        return
    if context.path.suffix != '.py':
        return
    with log_exception():
        with Timer('Sorting'):
            absolute_path = context.path.absolute()
            context.isort_process = await create_subprocess_shell(
                f'cd {shlex.quote(str(absolute_path.parent))} && '
                f'isort {shlex.quote(str(absolute_path))} --atomic',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            stdout, stderr = await context.isort_process.communicate()
            if stdout:
                logger.info(stdout)
            if stderr:
                logger.error(stderr)


async def run_spell_checker(context, send):
    if not config['linter']['spellChecker']:
        return
    with Timer('Spelling check'):
        tokens = tokenize(context.content)
        await send('SpellingErrors', {
            'result':
            await context.shared.spell_checker.check_spelling(tokens)
        })


async def run_pyflakes(context, send):
    if not config['linter']['pyflakes']:
        return
    if context.path.suffix != '.py':
        return
    reporter = context.pyflakes_reporter
    reporter.clear()
    pyflakes.api.check(context.content, '', reporter)
    await send('RealTimeLints', dict(result=reporter.errors))


async def warm_up_jedi(context):
    # Avoid jedi error when the file is empty.
    if not context.doc:
        logger.debug('File is empty')
        return

    jedi.Script('\n'.join(context.doc), len(context.doc), 0,
                str(context.path)).completions()

    await jedi_preload_modules(context, 0, len(context.doc))


async def jedi_preload_modules(context, start_line, end_line):
    if end_line > 32:
        end_line = 32
    await preload_modules(context.doc[start_line:end_line])


async def post_content_change(context, send):
    with Timer('Post content change'):
        context.doc = context.content.splitlines()
        context.shared.doc = context.doc
        # initialize feature extractor
        context.feature_extractor = OnlineFeatureExtractor()
        for line, line_content in enumerate(context.doc):
            context.feature_extractor.fill_preprocessor_context(
                line_content, line, context.doc)
        create_task(warm_up_jedi(context))
        create_task(run_spell_checker(context, send))
        create_task(run_pyflakes(context, send))
        context.linter_task = create_task(run_pylint(context, send))


@handles('_connected')
async def connected(msg, send, context):
    context.warmed_up = False
    context.doc = []
    context.linter_task = create_task(nop())
    # open file
    context.path = Path(context.shared.project_root, *msg['filePath'])
    file_state = persistent_state.get_file_state(context.path)
    context.pos = file_state.get('pos', (0, 0))
    context.is_python = context.path.suffix in ('.py', '.pyx')
    context.pyflakes_reporter = PyflakesReporter()
    with open(context.path) as f:
        try:
            content = f.read()
        except UnicodeDecodeError:
            await send(
                'FailedToOpen',
                f'Failed to open file {context.path}. (only text files are supported)'
            )
            return
        context.content = content
    # somehow risky, but it should not wait until the extractor ready
    await send('FileOpened', {
        'mtime': context.path.stat().st_mtime,
        'content': content,
        **file_state,
    })
    # update opened files
    opened_files = context.shared.project_config['openedFiles']
    path_tuple = get_relative_path(context)
    if path_tuple not in opened_files:
        opened_files.append(path_tuple)
    await activate_editor(msg, send, context)
    # skip all completion, linting etc. if it is not a Python file
    if not context.is_python:
        return


async def warm_up(context, send):
    if context.warmed_up:
        return
    context.warmed_up = True
    await post_content_change(context, send)


@handles('_disconnected')
async def disconnected(context):
    context.linter_task.cancel()
    persistent_state.set_file_state(context.path, {'pos': context.pos})


@handles('Close')
async def close(msg, send, context):
    """
    Called when the editor is explicitly closed, not when it is disconnected
    """
    opened_files = context.shared.project_config['openedFiles']
    opened_files.remove(get_relative_path(context))
    context.pos = msg['pos']
    save_state(context)


@handles('Blur')
async def blur(msg, send, context):
    context.pos = msg['pos']


@handles('Reload')
async def reload(msg, send, context):
    with open(context.path) as f:
        content = f.read()
        context.content = content
    await send('Reloaded', {'content': content})
    await post_content_change(context, send)


@handles('ActivateEditor')
async def activate_editor(msg, send, context):
    context.shared.doc = context.doc
    # When the editor is activated by user (not when initializing)
    if not msg:
        await warm_up(context, send)
        context.shared.project_config['activePanels'][
            'middle'] = get_relative_path(context)
        save_state(context)


@handles('Mtime')
async def modification_time(msg, send, context):
    new_path = msg.get('newPath', None)
    if new_path is not None:
        logger.info('path modified from %s to %s', context.path, new_path)
        context.path = Path(*new_path)
    try:
        await send('Mtime', {'mtime': context.path.stat().st_mtime})
    except FileNotFoundError:
        await send('FileDeleted', {})


@handles('SaveFile')
async def save_file(msg, send, context):
    content = msg['content']
    context.content = content
    with open(context.path, 'w') as f:
        f.write(content)
    mtime_before_formatting = context.path.stat().st_mtime
    result = {'mtime': mtime_before_formatting}
    if not context.is_python:
        await send('FileSaved', result)
        return

    await run_isort(context)
    await run_yapf(context)

    mtime_after_formatting = context.path.stat().st_mtime
    if mtime_after_formatting != mtime_before_formatting:
        with open(context.path) as f:
            content = f.read()
            context.content = content
        result['mtime'] = mtime_after_formatting
        result['content'] = content
    await send('FileSaved', result)
    await post_content_change(context, send)


@handles('SyncRange')
async def sync_range(msg, send, context):
    from_line, to_line, lint, *lines = msg  # to_line is exclusive
    doc = context.doc
    doc[from_line:to_line] = lines
    context.content = '\n'.join(doc)

    # for whatever reason the document in the browser is not in sync with the one here
    if to_line > len(doc):
        logger.warning('Request doc synchronization')
        await send('RequestFullSync', None)
        return

    # If total number of lines changed, update from_line and below; otherwise, update changed range.
    for i in range(from_line,
                   to_line if to_line - from_line == len(lines) else len(doc)):
        context.feature_extractor.fill_preprocessor_context(doc[i], i, doc)

    if to_line < 32:
        await jedi_preload_modules(context, from_line, to_line)

    if lint:
        await run_spell_checker(context, send)
        await run_pyflakes(context, send)


@handles('Predict')
async def predict(msg, send, context):
    line_number, ch, line_content = msg
    while len(context.doc) <= line_number:
        context.doc.append('')
    context.doc[line_number] = line_content
    doc = '\n'.join(context.doc)
    context.content = doc

    if is_parameter_of_def(context.doc, line_number, ch):
        # don't make prediction if it is defining function parameters
        await send(
            'Prediction', {
                'line': line_number,
                'ch': ch,
                'result': [],
                'parameterDefinition': True
            })
        return
    try:
        with Timer(f'Prediction ({line_number}, {ch})'):
            j = jedi.Script(doc, line_number + 1, ch, str(context.path))
            completions = j.completions()

        offset = 0
        with Timer(f'Rest ({line_number}, {ch})'):
            if completions:
                context.currentCompletions = {
                    completion.name: completion
                    for completion in completions
                }

                completion = completions[0]
                offset = len(completion.complete) - len(completion.name)

                feature_extractor = context.feature_extractor
                feature_extractor.extract_online(completions, line_content,
                                                 line_number, ch, context.doc,
                                                 j.call_signatures())
                # scores = model.predict_proba(feature_extractor.X)[:, 1] * 1000
                d_test = DMatrix(feature_extractor.X)
                scores = model.predict(
                    d_test, output_margin=True, validate_features=False) * 1000
                # c.name_with_symbol is not reliable
                # e.g. def something(path): len(p|)
                # will return "path="
                result = [
                    PredictionRow(c=c.name,
                                  t=c.type,
                                  s=int(s),
                                  p=c.name_with_symbols[len(c.name):])
                    for c, s in zip(completions, scores)
                ]
            else:
                result = []

        await send('Prediction', {
            'line': line_number,
            'ch': ch,
            'offset': offset,
            'result': result,
        })
        context.pos = (line_number, ch)
    except Exception as e:
        logger.exception(e)
        await send('RequestFullSync', None)


@handles('PredictExtra')
async def predict_extra(msg, send, context):
    """
    Prediction from tokens, words and snake-cases from word segments
    """
    line_number, ch, text = msg
    results = {}  # used as an ordered set

    # 1. words from dictionary
    if len(results) < 6:
        words = search_prefix(text)
        for i, word in enumerate(words):
            if word not in results:
                results[word] = PredictionRow(c=word,
                                              t='word',
                                              s=990 - i,
                                              p='')

    # 2. existing tokens
    tokens = context.feature_extractor.context.t0map.query_prefix(
        text, line_number)
    for i, token in enumerate(tokens):
        if token not in results:
            results[token] = PredictionRow(c=token, t='token', s=980 - i, p='')

    # 3. segmented words
    if len(results) < 6:
        parts = text.split('_')  # handle private variables starting with _
        words = []
        for part in parts:
            if not part:
                words.append(part)
            else:
                words.extend(wordsegment.segment(part))
        snake = '_'.join(words)
        if snake and snake not in results:
            results[snake] = PredictionRow(c=snake,
                                           t='word-segment',
                                           s=1,
                                           p='')

    await send('ExtraPrediction', {
        'line': line_number,
        'ch': ch,
        'result': list(results.values())
    })


@handles('GetCompletionDocstring')
async def get_completion_docstring(msg, send, context):
    # get docstring
    completion = context.currentCompletions.get(msg['text'], None)
    if not completion:
        return
    docstring = completion.docstring(fast=False)
    definition = None

    # try to follow definition if it fails to get docstring
    if not docstring:
        try:
            definition = completion.infer()
        except (NotImplementedError, AttributeError):
            return
        if not definition:
            return
        docstring = definition[0].docstring()
        if not docstring:
            return

    if definition and hasattr(definition, 'params'):
        parameters = definition.params
    elif hasattr(completion, 'params'):
        parameters = completion.params
    else:
        parameters = []

    # render doc
    doc_type = detect_doc_type(docstring)
    html = None
    if doc_type != 'text':
        with log_exception():
            html = doc_generator.make_html(docstring)
    await send(
        'CompletionDocstring', {
            'doc': html if html else docstring,
            'type': 'html' if html else 'text',
            'parameters': bool(parameters),
        })


@handles('GetFunctionDocumentation')
async def get_function_documentation(msg, send, context):
    line_number = msg['line']
    ch = msg['ch']
    content = context.content

    j = jedi.Script(content, line_number + 1, ch, str(context.path))
    call_signatures = j.call_signatures()
    if not call_signatures:
        logger.debug('call signature is empty while obtaining docstring')
        return
    signature = call_signatures[0]
    docstring = signature.docstring()
    if not docstring:
        return
    doc_type = detect_doc_type(docstring)
    html = None
    if doc_type != 'text':
        with log_exception():
            html = doc_generator.make_html(docstring)

    await send(
        'FunctionDocumentation', {
            'doc': html if html else docstring,
            'fullName': signature.full_name,
            'type': 'html' if html else 'text'
        })


@handles('FindAssignments')
async def find_assignments(msg, send, context):
    content = context.content
    j = jedi.Script(content, msg['line'] + 1, msg['ch'], str(context.path))
    definitions = j.goto_assignments(follow_imports=True)
    results = [{
        'path': d.module_path,
        'module': d.module_name,
        'builtin': d.in_builtin_module(),
        'definition': d.is_definition(),
        'line': d.line,
        'ch': d.column,
        'code': d.get_line_code().strip()
    } for d in definitions]
    await send('AssignmentsFound', results)


@handles('FindUsages')
async def find_usage(msg, send, context):
    content = context.content
    j = jedi.Script(content, msg['line'] + 1, msg['ch'], str(context.path))
    usages = j.usages()
    results = [{
        'path': u.module_path,
        'module': u.module_name,
        'definition': u.is_definition(),
        'line': u.line,
        'ch': u.column,
        'code': u.get_line_code().strip()
    } for u in usages]
    await send('UsagesFound', results)


def definition_to_dict(d, project_root):
    # use relative path if possible
    # otherwise, the GUI will open two editors, one with relative path and one with absolute path
    path = Path(d.module_path)
    if project_root in path.parents:
        path = path.relative_to(project_root)

    return {
        'path': path.parts,
        'module': d.module_name,
        'builtin': d.in_builtin_module(),
        'definition': d.is_definition(),
        'line': d.line - 1,
        'from': d.column,
        'to': d.column + len(d.name),
        'code': d.get_line_code()
    }


@handles('FindReferences')
async def find_references(msg, send, context):
    definitions = []
    assignments = []
    usages = []
    mode = msg['type']
    j = jedi.Script(context.content, msg['line'] + 1, msg['ch'],
                    str(context.path))
    if 'assignments' in mode:
        references = j.goto_assignments(follow_imports=True)
        if 'usages' not in mode:
            definitions.extend(r for r in references if r.is_definition())
        assignments.extend(r for r in references if not r.is_definition())
    if 'usages' in mode:
        references = j.usages()
        definitions.extend(r for r in references if r.is_definition())
        usages.extend(r for r in references if not r.is_definition())

    project_root = context.shared.project_root
    await send(
        'ReferencesFound', {
            'definitions':
            [definition_to_dict(x, project_root) for x in definitions],
            'assignments':
            [definition_to_dict(x, project_root) for x in assignments],
            'usages': [definition_to_dict(x, project_root) for x in usages]
        })
