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
            send('Stdout', f'Process finished with exit code {pty.exitstatus}')
            return


@handles('_connected')
async def connected(client_id, send, context):
    context.pty = None
    context.reader = None


@handles('RunScript')
async def run_script(msg, send, context):
    root = context.shared_context.project_root
    path = Path(root, *msg['filePath']).resolve()

    if context.pty:
        if not context.reader:
            context.reader.cancel()
        context.pty.terminate(force=True)
        logger.info('terminated')

    pty = PtyProcessUnicode.spawn(['python', shlex.quote(str(path.name))],
                                  cwd=shlex.quote(str(path.parent)),
                                  dimensions=(msg['rows'], msg['cols']))
    await send('Started', None)

    context.pty = pty
    loop = asyncio.get_event_loop()
    context.reader = asyncio.ensure_future(loop.run_in_executor(
            None, partial(reader, pty, context.main_thread_send, context)))


