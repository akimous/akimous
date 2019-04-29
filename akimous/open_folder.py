from functools import partial
from pathlib import Path

from .websocket import register_handler

handles = partial(register_handler, 'openFolder')


async def list_folders(path, send):
    content = sorted(i.name for i in path.iterdir() if not i.is_file() and not i.name.startswith('.'))
    await send('Listed', {
        'currentPath': str(path),
        'list': content
    })


@handles('Ls')
async def ls(msg, send, context):
    await list_folders(Path(*msg).resolve(), send)


@handles('Home')
async def ls(msg, send, context):
    await list_folders(Path.home(), send)