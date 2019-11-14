import asyncio
import shlex
from functools import partial
from pathlib import Path

from logzero import logger

from .utils import nop
from .websocket import register_handler

try:
    from ptyprocess import PtyProcessUnicode
except ModuleNotFoundError:
    logger.warning('ptyprocess does not support Windows, '
                   'terminal function will be disabled')

handles = partial(register_handler, 'terminal')


def reader(pty, send, context):
    while True:
        try:
            message = pty.read(65536)
            send('Stdout', message)
        except EOFError:
            pty.wait()
            exit_code = pty.exitstatus
            if exit_code is not None:
                send('Stdout',
                     f'(Process finished with exit code {exit_code})')
            return


@handles('_connected')
async def connected(msg, send, context):
    context.pty = None
    context.reader = None


@handles('_disconnected')
async def disconnected(context):
    await stop({}, nop, context)


@handles('RunInTerminal')
async def run_in_terminal(msg, send, context):
    root = context.shared.project_root
    mode = msg['mode']
    path = Path(root, *msg.get('filePath', [])).resolve()
    args = shlex.split(msg.get('args', ''))

    await stop(msg, send, context)
    if mode == 'script':
        command = ['python', shlex.quote(str(path))] + args
    elif mode == 'module':
        module = '.'.join(path.relative_to(root).parts[:-1] + (path.stem, ))
        command = ['python', '-m', module] + args
    elif mode == 'shell':
        command = shlex.split(msg['command'])
    else:
        raise ValueError('unsupported mode')

    cwd = msg.get('cwd', None)
    if not cwd:
        cwd = str(root)
    cwd = shlex.quote(cwd)
    pty = PtyProcessUnicode.spawn(command,
                                  cwd=cwd,
                                  dimensions=(msg['rows'], msg['cols']))
    await send('Started', None)

    context.pty = pty
    loop = asyncio.get_event_loop()
    context.reader = asyncio.ensure_future(
        loop.run_in_executor(
            None, partial(reader, pty, context.main_thread_send, context)))


@handles('Stdin')
async def stdin(msg, send, context):
    if context.pty:
        context.pty.write(msg)


@handles('Stop')
async def stop(msg, send, context):
    pty = context.pty
    if pty:
        if context.reader:
            context.reader.cancel()
        pty.terminate(force=True)
    await send('Stdout', '\n(Process terminated.)')
