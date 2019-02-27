import asyncio
from threading import Thread, Event
from functools import partial
import re

from jupyter_client import KernelManager

from .websocket import register_handler
from .utils import nop, Timer
from logzero import logger

handles = partial(register_handler, 'jupyter')


def iopub_listener(context):
    client = context.jupyter_client
    send = context.main_thread_send
    kernel_stopped = context.kernel_stopped
    while True:
        message = client.get_iopub_msg()
        if kernel_stopped.is_set():
            logger.info('IOPub listener terminated')
            return
        content = message['content']

        execution_state = content.get('execution_state', None)
        if execution_state in ('busy', 'starting'):
            context.busy = True
            logger.warn('busy = True')
        elif execution_state == 'idle':
            context.busy = False
            logger.warn('busy = False')

        if context.iopub_buffer is not None:
            logger.debug('buffered %s', content)
            context.iopub_buffer.append(content)
        else:
            logger.debug(content)
            send('IOPub', content)


def shell_listener(context):
    client = context.jupyter_client
    send = context.main_thread_send
    kernel_stopped = context.kernel_stopped
    while True:
        message = client.get_shell_msg()
        if kernel_stopped.is_set():
            logger.info('Shell listener terminated')
            return
        content = message['content']
        status = content.get('status', None)
        if status == 'complete':
            context.busy = False
            logger.warn('busy = False')
        logger.debug('Shell %s', repr(content))


@handles('_connected')
async def connected(client_id, send, context):
    context.kernel_manager = KernelManager()
    context.iopub_listener_thread = Thread()
    context.part_a_end_line = 0
    context.iopub_buffer = None
    context.busy = False


@handles('_disconnected')
async def disconnected(context):
    logger.info('stopping kernel')
    await stop_kernel({}, nop, context)


@handles('StartKernel')
async def start_kernel(msg, send, context):
    await stop_kernel(msg, send, context)
    context.busy = True
    context.kernel_manager.start_kernel()
    context.jupyter_client = context.kernel_manager.client()
    context.kernel_stopped = Event()
    context.iopub_listener_thread = Thread(target=iopub_listener, args=(context, ))
    context.iopub_listener_thread.start()
    context.shell_listener_thread = Thread(target=shell_listener, args=(context,))
    context.shell_listener_thread.start()
    logger.warn('is complete %s', repr(context.jupyter_client.is_complete('')))
    await send('KernelStarted', None)


@handles('StopKernel')
async def stop_kernel(msg, send, context):
    if not context.kernel_manager.is_alive():
        return
    context.kernel_stopped.set()
    context.kernel_manager.shutdown_kernel()
    await send('KernelStopped', None)


@handles('Run')
async def run(msg, send, context):
    logger.debug('Running code %s', msg['code'])
    context.jupyter_client.execute(msg['code'])


indented = re.compile('(^\\s+)|(^@)')
continued = re.compile('\\\\\\s*$')


@handles('EvaluatePartA')
async def evaluate_part_a(msg, send, context):
    logger.debug('EvaluateA %s', msg)
    doc = context.shared_context.doc
    line = 0
    for line in range(msg, -1, -1):
        if (line == len(doc) or not indented.match(doc[line]))\
                and (line > 0 and not continued.match(doc[line - 1])):
            break
    if line == context.part_a_end_line:
        logger.warn('Skipped A as line number is the same')
        return
    context.part_a_end_line = line
    logger.info('\n'.join(doc[:line]))

    with Timer('restarting kernel'):
        context.busy = True
        context.kernel_manager.restart_kernel(now=True)
        context.jupyter_client.is_complete('')
        context.iopub_buffer = []
    while context.busy:
        logger.warn('busy!')
        await asyncio.sleep(.1)
    context.jupyter_client.execute('\n'.join(doc[:line]))


@handles('EvaluatePartB')
async def evaluate_part_b(msg, send, context):
    logger.debug('EvaluateB %s', repr(msg))

    line = msg['line']
    line_content = msg['line_content']
    doc = context.shared_context.doc
    doc[line] = line_content
    from_line = context.part_a_end_line
    await send('Clear', None)
    for message in context.iopub_buffer:
        await send('IOPub', message)
    context.iopub_buffer = None
    logger.info('\n'.join(doc[from_line:]))

    context.busy = True
    context.jupyter_client.execute('\n'.join(doc[from_line:]))
    while context.busy:
        await asyncio.sleep(.1)
        logger.info('sleeping')
    context.part_a_end_line = -1
    await evaluate_part_a(line - 1, send, context)
