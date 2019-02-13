import asyncio
import shlex
from functools import partial
from pathlib import Path

from logzero import logger
from ptyprocess import PtyProcessUnicode

from .websocket import register_handler

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
                send('Stdout', f'(Process finished with exit code {exit_code})')
            return


@handles('_connected')
async def connected(client_id, send, context):
    context.pty = None
    context.reader = None


@handles('RunScript')
async def run_script(msg, send, context):
    root = context.shared_context.project_root
    path = Path(root, *msg['filePath']).resolve()
    mode = msg['mode']

    if context.pty:
        if context.reader:
            context.reader.cancel()
        context.pty.terminate(force=True)

    if mode == 'script':
        command = ['python', shlex.quote(str(path))]
    elif mode == 'module':
        module = '.'.join(path.relative_to(root).parts[:-1] + (path.stem, ))
        command = ['python', '-m', module]
    else:
        raise ValueError('unsupported mode')

    pty = PtyProcessUnicode.spawn(command,
                                  cwd=shlex.quote(str(root)),
                                  dimensions=(msg['rows'], msg['cols']))
    await send('Started', None)

    context.pty = pty
    loop = asyncio.get_event_loop()
    context.reader = asyncio.ensure_future(loop.run_in_executor(
            None, partial(reader, pty, context.main_thread_send, context)))


@handles('Stdin')
async def stdin(msg, send, context):
    if context.pty:
        context.pty.write(msg)
