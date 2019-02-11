from functools import partial
import json
import os

from .spell_checker import SpellChecker
from .websocket import register_handler
from .file_finder import find_in_directory, replace_all_in_directory
from .utils import config_directory
from importlib import resources
from pathlib import Path
from appdirs import user_config_dir

handles = partial(register_handler, '')

# load defaults
with resources.open_text('akimous.resources', 'default_config.json') as f:
    config = json.load(f)


def merge_dict(primary, secondary):
    for k, v in secondary.items():
        section = primary.get(k, None)
        if section is None:
            primary[k] = v
        else:
            for key, value in v.items():
                section[key] = value


if not config_directory.exists():
    config_directory.mkdir(parents=True, exist_ok=True)

# load user config
config_file = config_directory / 'akimous.json'
if config_file.exists():
    with open(config_file) as f:
        user_config = json.loads(f.read())
        merge_dict(config, user_config)


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


@handles('OpenProject')
async def open_project(msg, send, context):
    shared_context = context.shared_context
    shared_context.project_root = Path(*msg['path']).resolve()
    await send('ProjectOpened', {
        'root': shared_context.project_root.parts
    })
    SpellChecker(shared_context)


handles('FindInDirectory')(find_in_directory)
handles('ReplaceAllInDirectory')(replace_all_in_directory)
