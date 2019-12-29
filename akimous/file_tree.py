import os
import platform
from asyncio import sleep
from contextlib import suppress
from functools import partial
from pathlib import Path
from shutil import rmtree
from subprocess import Popen

from logzero import logger
from send2trash import send2trash
from send2trash.exceptions import TrashPermissionError
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .project import save_state
from .websocket import register_handler


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.root = context.shared.project_root

    def on_created(self, event):
        logger.info('on create %s', repr(event))
        # do not rely on event.is_directory, it might be wrong on Windows
        is_directory = Path(event.src_path).is_dir()
        self.send = self.context.main_thread_send(
            'DirCreated' if is_directory else 'FileCreated', {
                'path': Path(event.src_path).relative_to(self.root).parts,
            })

    def on_deleted(self, event):
        logger.info('on delete %s', repr(event))
        self.context.main_thread_send(
            'DirDeleted' if event.is_directory else 'FileDeleted', {
                'path': Path(event.src_path).relative_to(self.root).parts,
            })
        for k in tuple(self.context.observed_watches.keys()):
            if k.startswith(event.src_path):
                stop_monitor(k, self.context)

    def on_modified(self, event):
        logger.info('on modified %s', repr(event))

    def on_moved(self, event):
        logger.info('on moved %s', repr(event))
        print(event.event_type, event.src_path, event.dest_path)
        # do not rely on event.is_directory, it might be wrong on Windows
        is_directory = Path(event.dest_path).is_dir()
        self.context.main_thread_send(
            'DirRenamed' if is_directory else 'FileRenamed', {
                'path': Path(event.src_path).relative_to(self.root).parts,
                'newName': Path(event.dest_path).name
            })
        for k in tuple(self.context.observed_watches.keys()):
            if k.startswith(event.src_path + '/'):
                stop_monitor(k, self.context)
                start_monitor(
                    k.replace(event.src_path + '/', event.dest_path + '/'),
                    self.context)


handles = partial(register_handler, 'fileTree')


def start_monitor(path, context):
    path = str(path)
    logger.debug('start monitoring %s', path)
    change_handler = ChangeHandler(context)
    context.observed_watches[path] = context.observer.schedule(
        change_handler, path)


def stop_monitor(path, context):
    path = str(path)
    logger.debug('stop monitoring %s', path)
    watch = context.observed_watches.get(path, None)
    if watch is None:
        logger.error('stopping nonexistent watch of path %s', path)
        return
    context.observer.unschedule(watch)
    del context.observed_watches[path]


@handles('_connected')
async def connected(msg, send, context):
    context.observed_watches = {}
    context.observer = Observer()
    context.observer.start()


@handles('_disconnected')
async def disconnected(context):
    with suppress(ValueError, SystemError):
        # may raise ValueError: PyCapsule_GetPointer called with invalid PyCapsule object
        context.observer.stop()


@handles('OpenDir')
async def open_dir(msg, send, context):
    path = Path(context.shared.project_root, *msg['path'])
    root, dirs, files = next(os.walk(path))
    result = {
        'path': path.relative_to(context.shared.project_root).parts,
        'dirs': dirs,
        'files': [file for file in files if file != '.DS_Store']
    }
    start_monitor(path, context)
    await send('DirOpened', result)

    # store opened folders
    opened_folders = context.shared.project_config['openedFolders']
    pointer = opened_folders
    dirty = False
    for part in path.relative_to(context.shared.project_root).parts:
        next_pointer = pointer.get(part)
        if not next_pointer:
            pointer[part] = {}
            next_pointer = pointer[part]
            dirty = True
        pointer = next_pointer
    if dirty:
        save_state(context)

    # restore opened folders when project root is opened
    if not msg['path']:
        await restore_opened_folders([], opened_folders, send, context)


async def restore_opened_folders(path, pointer, send, context):
    for k, v in pointer.items():
        await sleep(0)
        await open_dir({'path': path + [k]}, send, context)
        await restore_opened_folders(path + [k], v, send, context)


@handles('CloseDir')
async def close_dir(msg, send, context):
    path = Path(context.shared.project_root, *msg['path'])
    stop_monitor(path, context)

    # remove from opened folders
    parts = path.relative_to(context.shared.project_root).parts
    pointer = context.shared.project_config['openedFolders']
    for part in parts[:-1]:
        next_pointer = pointer.get(part)
        if not next_pointer:
            return
        pointer = next_pointer
    del pointer[parts[-1]]
    save_state(context)


@handles('Rename')
async def rename(msg, send, context):
    old_path = Path(context.shared.project_root, *msg['path'])
    new_name = msg['newName']
    new_path = old_path.with_name(new_name)
    logger.info('renaming %s to %s', old_path, new_path)
    try:
        old_path.rename(new_path)
        await send('Done',
                   f'"<b>{old_path.name}</b>" renamed to "<b>{new_name}</b>"')
        if str(old_path) in context.observed_watches:
            stop_monitor(old_path, context)
            start_monitor(new_path, context)
    except OSError as e:
        await send(
            'Failed',
            f'Failed to rename "<b>{old_path.name}</b>". {e.strerror}.')


@handles('CreateFile')
async def create_file(msg, send, context):
    path = Path(context.shared.project_root, *msg['path'])
    file_name = msg['path'][-1]
    if path.exists():
        await send(
            'Failed',
            f'Failed to create file "<b>{file_name}</b>". File already exists.'
        )
    else:
        try:
            with path.open('w'):
                pass
            await send('Done', f'New file "<b>{file_name}</b>" created.')
        except OSError as e:
            await send(
                'Failed',
                f'Failed to create file "<b>{file_name}</b>". {e.strerror}')


@handles('CreateDir')
async def create_dir(msg, send, context):
    path = Path(context.shared.project_root, *msg['path'])
    dir_name = msg['path'][-1]
    if path.exists():
        await send(
            'Failed',
            f'Failed to create folder "<b>{dir_name}</b>". Folder already exists.'
        )
    else:
        try:
            path.mkdir(parents=True, exist_ok=False)
            await send('Done', f'New folder "<b>{dir_name}</b>" created.')
        except OSError as e:
            await send(
                'Failed',
                f'Failed to create folder "<b>{dir_name}</b>". {e.strerror}')


@handles('Delete')
async def delete(msg, send, context):
    path = Path(context.shared.project_root, *msg['path']).resolve()
    name = msg['path'][-1]
    try:
        try:
            send2trash(str(path))
            await send('Done', f'"<b>{name}</b>" moved to trash.')
        except TrashPermissionError:
            if path.is_dir():
                rmtree(str(path))
            else:
                path.unlink()
            await send('Done', f'"<b>{name}</b>" deleted.')
    except OSError as e:
        await send('Failed', f'Failed to delete "<b>{name}</b>". {e.strerror}')


@handles('OpenInFileManager')
async def open_in_file_manager(msg, send, context):
    path = Path(context.shared.project_root, *msg['path']).resolve()
    if platform.system() == 'Windows':
        Popen(['explorer', '/select,', str(path)])
    elif platform.system() == 'Darwin':
        path = str(path.parent) if path.is_file() else str(path)
        Popen(['open', path])
    else:
        path = str(path.parent) if path.is_file() else str(path)
        Popen(['xdg-open', path])
