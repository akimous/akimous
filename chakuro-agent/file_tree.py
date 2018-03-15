import os
from functools import partial
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ws import WS
from logzero import logger as log


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, context):
        super().__init__()
        self.context = context

    def on_created(self, event):
        log.info('on create %s', repr(event))
        self.context.main_thread_send({
            'cmd': 'event-DirCreated' if event.is_directory else 'event-FileCreated',
            'path': Path(event.src_path).relative_to(self.context.fileRoot).parts,
        })

    def on_deleted(self, event):
        log.info('on delete %s', repr(event))
        self.context.main_thread_send({
            'cmd': 'event-DirDeleted' if event.is_directory else 'event-FileDeleted',
            'path': Path(event.src_path).relative_to(self.context.fileRoot).parts,
        })
        for k in tuple(self.context.observed_watches.keys()):
            if k.startswith(event.src_path):
                stop_monitor(k, self.context)

    def on_modified(self, event):
        log.info('on modified %s', repr(event))

    def on_moved(self, event):
        log.info('on moved %s', repr(event))
        print(event.event_type, event.src_path, event.dest_path)
        self.context.main_thread_send({
            'cmd': 'event-DirRenamed' if event.is_directory else 'event-FileRenamed',
            'path': Path(event.src_path).relative_to(self.context.fileRoot).parts,
            'newName': Path(event.dest_path).name
        })
        for k in tuple(self.context.observed_watches.keys()):
            if k.startswith(event.src_path + '/'):
                stop_monitor(k, self.context)
                start_monitor(k.replace(event.src_path + '/', event.dest_path + '/'), self.context)


register = partial(WS.register, 'fileTree')


def get_observer(context):
    observer = context.observer
    if observer is not None:
        return observer
    observer = Observer()
    observer.start()
    context.observer = observer
    return observer


def start_monitor(path, context):
    path = str(path)
    log.warn('starting monitor %s', path)
    change_handler = ChangeHandler(context)
    context.observed_watches[path] = get_observer(context).schedule(change_handler, path)


def stop_monitor(path, context):
    path = str(path)
    log.warn('stopping monitor %s', path)
    watch = context.observed_watches.get(path, None)
    if watch is None:
        log.error('stopping watch of path %s', path)
        log.error('==> %s', context.observed_watches)
        return
    get_observer(context).unschedule(watch)
    del context.observed_watches[path]


@register('openFolder')
async def open_folder(msg, send, context):
    is_root = msg.get('isRoot', False)
    if is_root:
        path = Path(msg['path']).resolve()
        context.fileRoot = path
    else:
        path = Path(context.fileRoot, *msg['path'])
    root, dirs, files = next(os.walk(path))
    result = {
        'cmd': 'openFolder-ok',
        'path': path.relative_to(context.fileRoot).parts,
        'dirs': dirs,
        'files': files
    }
    start_monitor(path, context)
    await send(result)


@register('closeFolder')
async def close_folder(msg, send, context):
    stop_monitor(Path(context.fileRoot, *msg['path']), context)


@register('rename')
async def rename(msg, send, context):
    old_path = Path(context.fileRoot, *msg['path'])
    new_path = old_path.with_name(msg['newName'])

    log.info('renaming %s to %s', str(old_path), str(new_path))
    result = {
        'oldPath': str(old_path),
        'newPath': str(new_path),
        'oldName': str(old_path.name),
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
                start_monitor(new_path, context)
        except OSError as e:
            result.update(cmd='rename-failed', reason=e.strerror)
    await send(result)


@register('newFile')
async def new_file(msg, send, context):
    path = Path(context.fileRoot, *msg['path'])
    result = {
        'path': msg['path'],
    }
    if path.exists():
        result.update(cmd='newFile-failed', reason='existed')
    else:
        try:
            with path.open('w'):
                pass
            result.update(cmd='newFile-ok')
        except OSError as e:
            result.update(cmd='newFile-failed', reason=e.strerror)
    await send(result)

