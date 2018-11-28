from functools import partial
import json
from websocket import register_handler
from importlib import resources
from pathlib import Path

handles = partial(register_handler, 'config')

# load defaults
with resources.open_text('resources', 'default_config.json') as f:
    config = json.loads(f.read())

# load user config
config_path = Path.home() / '.akimous.json'
if config_path.exists():
    with open(config_path) as f:
        user_config = json.loads(f.read())
        for k, v in user_config.items():
            section = config.get(k, {})
            for key, value in v.items():
                section[key] = value
        # config = {k: v for d in (config, user_config) for k, v in d.items()}


@handles('get')
async def get(msg, send, context):
    await send('Config', config)


@handles('set')
async def set(msg, send, context):
    global config
    config = {k: v for d in (config, msg) for k, v in d.items()}
    with open(config_path, 'w') as f:
        f.write(json.dumps(config))
