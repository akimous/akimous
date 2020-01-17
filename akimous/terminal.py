import asyncio
import shlex
from asyncio.subprocess import PIPE, STDOUT
from functools import partial
from pathlib import Path

from logzero import logger

from .utils import nop
from .websocket import register_handler

IS_PTY = False
try:
    from ptyprocess import PtyProcessUnicode
    IS_PTY = True
except ModuleNotFoundError:
    logger.warning('ptyprocess is not available, '
                   'terminal function will behave differently')

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
        except asyncio.CancelledError:
            return


async def async_reader(pty, send):
    logger.info('reader started')
    source = pty.stdout
    while True:
        try:
            message = await source.read(65536)
            if message:
                await send('Stdout', message)
            else:
                await asyncio.sleep(.01)
            if source.at_eof():
                return
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.exception(e)


async def wait_until_finish(pty, send):
    try:
        await pty.wait()
        await asyncio.sleep(.01)
        await send('Stdout',
                   f'(Process finished with exit code {pty.returncode})')
    except Exception:
        logger.exception(e)


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

    if IS_PTY:
        pty = PtyProcessUnicode.spawn(command,
                                      cwd=cwd,
                                      dimensions=(msg['rows'], msg['cols']))
        await send('Started', None)
        context.pty = pty
        loop = asyncio.get_event_loop()
        context.reader = asyncio.ensure_future(
            loop.run_in_executor(
                None, partial(reader, pty, context.main_thread_send, context)))
    else:
        pty = await asyncio.create_subprocess_shell(shlex.join(command),
                                                    stdin=PIPE,
                                                    stdout=PIPE,
                                                    stderr=STDOUT,
                                                    cwd=cwd,
                                                    bufsize=0)
        await send('Started', None)
        context.pty = pty
        context.reader = asyncio.create_task(async_reader(pty, send))
        context.reader = asyncio.create_task(wait_until_finish(pty, send))


@handles('Stdin')
async def stdin(msg: str, send, context):
    pty = context.pty
    logger.warning('%r, %r', pty, IS_PTY)
    if pty:
        if IS_PTY:
            pty.write(msg)
        else:
            if msg == '\r':
                msg = '\n'
            pty.stdin.write(msg.encode('utf-8'))
            await pty.stdin.drain()
            await send('Stdout', msg)


@handles('Stop')
async def stop(msg, send, context):
    pty = context.pty
    if pty:
        if context.reader:
            context.reader.cancel()
        if IS_PTY:
            pty.terminate(force=True)
        elif pty.returncode is None:
            pty.kill()
        await send('Stdout', '\n(Process terminated.)')
