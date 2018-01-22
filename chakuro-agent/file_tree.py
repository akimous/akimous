import os
from functools import partial
from pathlib import Path

from ws import WS

register = partial(WS.register, 'fileTree')

@register('openFolder')
async def open_folder(msg, send, context):
    path = Path(msg['path'])
    root, dirs, files = next(os.walk(Path(path)))
    result = {
        'cmd': 'openFolder',
        'folderName': path.name,
        'path': str(path),
        'dirs': [dict(name=d, path=str(path / d)) for d in dirs],
        'files': [dict(name=f, path=str(path / f)) for f in files]
    }
    await send(result)
