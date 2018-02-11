import os
import asyncio
from functools import partial
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ws import WS
from logzero import logger as log


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, send):
        super().__init__()
        self.send = send

    def on_created(self, event):
        log.info('on create %s', repr(event))
        self.send('456')

    def on_deleted(self, event):
        log.info('on delete %s', repr(event))

    def on_modified(self, event):
        log.info('on modified %s', repr(event))

    def on_moved(self, event):
        log.info('on moved %s', repr(event))
        print(event.event_type, event.src_path, event.dest_path)
        if event.is_directory:
            self.send({
                'cmd': 'event-DirRenamed',
                'srcPath': event.src_path,
                'destPath': event.dest_path,
                'newName': Path(event.dest_path).name
            })


register = partial(WS.register, 'fileTree')


def get_observer(context):
    observer = context.observer
    if observer is not None:
        return observer
    observer = Observer()
    observer.start()
    context.observer = observer
    return observer


def start_monitor(path, send, context):
    path = str(path)
    event_loop = asyncio.get_event_loop()

    def main_thread_send(message):
        event_loop.call_soon_threadsafe(asyncio.ensure_future, send(message))

    change_handler = ChangeHandler(main_thread_send)
    context.observed_watches[path] = get_observer(context).schedule(change_handler, path)


def stop_monitor(path, context):
    path = str(path)
    watch = context.observed_watches.get(path, None)
    if watch is None:
        log.error('stopping watch of path %s', path)
        log.error('==> %s', context.observed_watches)
        return
    get_observer(context).unschedule(watch)
    del context.observed_watches[path]


@register('openFolder')
async def open_folder(msg, send, context):
    path = Path(msg['path']).absolute()
    root, dirs, files = next(os.walk(Path(path)))
    result = {
        'cmd': 'openFolder-ok',
        'folderName': path.name,
        'path': str(path),
        'dirs': [dict(name=d, path=str(path / d)) for d in dirs],
        'files': [dict(name=f, path=str(path / f)) for f in files]
    }
    start_monitor(path, send, context)
    # event_loop = asyncio.get_event_loop()
    #
    # def main_thread_send(message):
    #     event_loop.call_soon_threadsafe(asyncio.ensure_future, send(message))
    #
    # change_handler = ChangeHandler(main_thread_send)
    # context.observed_watches[path] = get_observer(context).schedule(change_handler, str(path))
    await send(result)


@register('closeFolder')
async def close_folder(msg, send, context):
    stop_monitor(msg['path'], context)
    # path = Path(msg['path'])
    # get_observer(context).unschedule(context.observed_watches[path])
    # del context.observed_watches[path]


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
            if str(old_path) in context.observed_watches:
                stop_monitor(old_path, context)
                start_monitor(new_path, send, context)
        except IOError as e:
            result.update(cmd='rename-failed', reason=repr(e))
    await send(result)
