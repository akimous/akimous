import json
import os
from functools import partial
from importlib import resources
from logzero import logger

from .utils import (config_directory, get_merged_config, merge_dict)
from .websocket import register_handler

handles = partial(register_handler, 'config')

logger.info('Reading configuration from %s', config_directory)
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
async def connected(msg, send, context):
    await send('Connected', {'config': config, 'pathSeparator': os.sep})


@handles('SetConfig')
async def set_config(msg, send, context):
    global config
    merge_dict(config, msg)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4, sort_keys=True)
