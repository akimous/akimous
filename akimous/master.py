from functools import partial
import json

from .spell_checker import SpellChecker
from .websocket import register_handler
from importlib import resources
from pathlib import Path

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


config_directory = Path.home() / '.akimous'
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
if not macro_file.exists():
    template = resources.read_text('akimous.resources', 'macro.js')
    with open(macro_file, 'w') as f:
        f.write(template)


@handles('_connected')
async def connected(client_id, send, context):
    await send('Connected', {
        'clientId': client_id,
        'config': config
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
    shared_context.project_root = Path(msg['path']).resolve()
    SpellChecker(shared_context)

