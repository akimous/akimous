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


@register('rename')
async def rename(msg, send, context):
    old_path = Path(msg['path'])
    new_path = old_path.with_name(msg['newName'])
    
    print(old_path, new_path)
    result = {
        'oldPath': str(old_path),
        'newPath': str(new_path),
        'newName': msg['newName']
    }
    if new_path.exists():
        result.update(cmd='rename-failed', reason='existed')
    else:
        try:
            old_path.rename(new_path)
            result.update(cmd='rename-ok')
        except IOError as e:
            result.update(cmd='rename-failed', reason=repr(e))
    await send(result)
        

