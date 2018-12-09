from functools import partial
import json

from spell_checker import SpellChecker
from websocket import register_handler
from importlib import resources
from pathlib import Path

handles = partial(register_handler, '')

# load defaults
with resources.open_text('resources', 'default_config.json') as f:
    config = json.load(f)


def merge_dict(primary, secondary):
    for k, v in secondary.items():
        section = primary.get(k, None)
        if section is None:
            primary[k] = v
        else:
            for key, value in v.items():
                section[key] = value


# load user config
config_path = Path.home() / '.akimous.json'
if config_path.exists():
    with open(config_path) as f:
        user_config = json.loads(f.read())
        merge_dict(config, user_config)


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
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4, sort_keys=True)


@handles('OpenProject')
async def open_project(msg, send, context):
    shared_context = context.shared_context
    shared_context.project_root = Path(msg['path']).resolve()
    SpellChecker(shared_context)

