from functools import partial
from pathlib import Path

from .websocket import register_handler
from .config import config

handles = partial(register_handler, 'openFolder')


async def list_folders(path, send):
    content = sorted(i.name for i in path.iterdir() if not i.is_file() and not i.name.startswith('.'))
    await send('Listed', {
        'path': str(path),
        'list': content
    })


@handles('Ls')
async def ls(msg, send, context):
    await list_folders(Path(*msg).resolve(), send)


@handles('Home')
async def home(msg, send, context):
    await list_folders(Path.home(), send)


@handles('Open')
async def open_dialogue(msg, send, context):
    last_opened_folder = config.get('lastOpenedFolder', None)
    if last_opened_folder and Path(last_opened_folder).is_dir():
        await list_folders(Path(last_opened_folder).parent, send)
    else:
        await list_folders(Path.home(), send)
