from functools import partial
import json
import os

from .spell_checker import SpellChecker
from .websocket import register_handler
from .file_finder import find_in_directory, replace_all_in_directory
from .utils import config_directory, get_project_config, get_merged_config, merge_dict
from importlib import resources
from pathlib import Path

handles = partial(register_handler, '')

config_file = config_directory / 'akimous.json'
config = get_merged_config(config_file, 'default_config.json')


# create user macro template if not exists
macro_file = config_directory / 'macro.js'
config['macro']['userMacroFile'] = macro_file.parts
if not macro_file.exists():
    template = resources.read_text('akimous.resources', 'macro.js')
    with open(macro_file, 'w') as f:
        f.write(template)


@handles('_connected')
async def connected(client_id, send, context):
    await send('Connected', {
        'clientId': client_id,
        'config': config,
        'sep': os.sep
    })


@handles('SetConfig')
async def set_config(msg, send, context):
    global config
    merge_dict(config, msg)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4, sort_keys=True)


@handles('SetProjectConfig')
async def set_project_config(msg, send, context):
    project_config = context.shared_context.project_config
    merge_dict(project_config, msg)
    with open(context.shared_context.project_config_file, 'w') as f:
        json.dump(project_config, f, indent=4, sort_keys=True)


def get_configuration_file(context):
    return get_project_config(context, 'config.json')


@handles('OpenProject')
async def open_project(msg, send, context):
    shared_context = context.shared_context
    shared_context.project_root = Path(*msg['path']).resolve()
    shared_context.project_config_file = shared_context.project_root / '.akimous' / 'config.json'
    shared_context.project_dictionary_file = shared_context.project_root / '.akimous' / 'dictionary.json'
    shared_context.project_config = get_merged_config(shared_context.project_config_file, 'default_project_config.json')
    await send('ProjectOpened', {
        'root': shared_context.project_root.parts,
        'projectConfig': shared_context.project_config
    })
    SpellChecker(context)


handles('FindInDirectory')(find_in_directory)
handles('ReplaceAllInDirectory')(replace_all_in_directory)
