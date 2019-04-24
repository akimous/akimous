import json
from functools import partial
from pathlib import Path

from .file_finder import find_in_directory, replace_all_in_directory
from .spell_checker import SpellChecker
from .utils import get_merged_config, merge_dict
from .websocket import register_handler

handles = partial(register_handler, 'project')


@handles('OpenProject')
async def open_project(msg, send, context):
    shared_context = context.shared
    shared_context.project_root = Path(*msg['path']).resolve()
    shared_context.project_config_file = shared_context.project_root / '.akimous' / 'config.json'
    shared_context.project_dictionary_file = shared_context.project_root / '.akimous' / 'dictionary.json'
    shared_context.project_config = get_merged_config(shared_context.project_config_file,
                                                      'default_project_config.json')
    await send('ProjectOpened', {
        'root': shared_context.project_root.parts,
        'projectConfig': shared_context.project_config
    })
    SpellChecker(context)


@handles('SetProjectConfig')
async def set_project_config(msg, send, context):
    project_config = context.shared.project_config
    merge_dict(project_config, msg)
    with open(context.shared.project_config_file, 'w') as f:
        json.dump(project_config, f, indent=4, sort_keys=True)


handles('FindInDirectory')(find_in_directory)
handles('ReplaceAllInDirectory')(replace_all_in_directory)