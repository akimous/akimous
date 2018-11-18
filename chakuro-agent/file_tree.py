import os
from functools import partial
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from websocket import register_handler
from logzero import logger as log


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, context):
        super().__init__()
        self.context = context

    def on_created(self, event):
        log.info('on create %s', repr(event))
        # do not rely on event.is_directory, it might be wrong on Windows
        is_directory = Path(event.src_path).is_dir()
        self.context.main_thread_send('DirCreated' if is_directory else 'FileCreated', {
            'path': Path(event.src_path).relative_to(self.context.fileRoot).parts,
        })

    def on_deleted(self, event):
        log.info('on delete %s', repr(event))
        self.context.main_thread_send('DirDeleted' if event.is_directory else 'FileDeleted',{
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
        # do not rely on event.is_directory, it might be wrong on Windows
        is_directory = Path(event.dest_path).is_dir()
        self.context.main_thread_send('DirRenamed' if is_directory else 'FileRenamed', {
            'path': Path(event.src_path).relative_to(self.context.fileRoot).parts,
            'newName': Path(event.dest_path).name
        })
        for k in tuple(self.context.observed_watches.keys()):
            if k.startswith(event.src_path + '/'):
                stop_monitor(k, self.context)
                start_monitor(k.replace(event.src_path + '/', event.dest_path + '/'), self.context)


handles = partial(register_handler, 'fileTree')


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


@handles('OpenDir')
async def open_dir(msg, send, context):
    is_root = msg.get('isRoot', False)
    if is_root:
        path = Path(msg['path']).resolve()
        context.fileRoot = path
    else:
        path = Path(context.fileRoot, *msg['path'])
    root, dirs, files = next(os.walk(path))
    result = {
        'path': path.relative_to(context.fileRoot).parts,
        'dirs': dirs,
        'files': files
    }
    start_monitor(path, context)
    await send('DirOpened', result)


@handles('CloseDir')
async def close_dir(msg, send, context):
    stop_monitor(Path(context.fileRoot, *msg['path']), context)


@handles('Rename')
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


@handles('CreateFile')
async def create_file(msg, send, context):
    path = Path(context.fileRoot, *msg['path'])
    result = {
        'path': msg['path'],
        'fileName': msg['path'][-1]
    }
    if path.exists():
        result.update(cmd='newFile-failed', reason='File already exists')
    else:
        try:
            with path.open('w'):
                pass
            result.update(cmd='FileCreated')
        except OSError as e:
            result.update(cmd='newFile-failed', reason=e.strerror)
    await send(result)


@handles('CreateDir')
async def create_dir(msg, send, context):
    path = Path(context.fileRoot, *msg['path'])
    dir_name = msg['path'][-1]
    if path.exists():
        await send('Failed', f'Failed to create folder "<b>{dir_name}</b>". Folder already exists.')
    else:
        try:
            path.mkdir(parents=True, exist_ok=False)
            await send('Done', f'New folder "<b>{dir_name}</b>" created.')
        except OSError as e:
            await send('Failed', f'Failed to create folder "<b>{dir_name}</b>". {e.strerror}')
