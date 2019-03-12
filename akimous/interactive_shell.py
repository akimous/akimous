import asyncio
import token
from collections import defaultdict
from threading import Thread, Event
from functools import partial
import re
from contextlib import suppress
from tokenize import generate_tokens

from jupyter_client import KernelManager

from .websocket import register_handler
from .utils import nop, Timer
from logzero import logger

handles = partial(register_handler, 'jupyter')

IDLE = 'IDLE'
RESTARTING = 'RESTARTING'
A_RUNNING = 'A_RUNNING'
B_RUNNING = 'B_RUNNING'


def set_state(context, new_state):
    context.evaluation_state = new_state
    if new_state is A_RUNNING:
        context.a_queued = False
    elif new_state is B_RUNNING:
        context.b_queued = False
    logger.debug('state: %s; a_queued: %s; b_queued: %s', new_state, context.a_queued, context.b_queued)


def iopub_listener(context):
    client = context.jupyter_client
    send = context.main_thread_send
    kernel_stopped = context.kernel_stopped
    while True:
        message = client.get_iopub_msg()
        if kernel_stopped.is_set():
            logger.info('IOPub listener terminated')
            return
        # logger.debug('full message: %s', message)
        content = message['content']

        execution_state = content.get('execution_state', None)

        if execution_state is not RESTARTING:
            if context.iopub_buffer is not None:
                logger.debug('buffered %s', content)
                context.iopub_buffer.append(content)
            else:
                logger.debug('unbuffered %s', content)
                send('IOPub', content)

        if execution_state == 'idle':
            evaluation_state = context.evaluation_state
            if evaluation_state is RESTARTING:
                with suppress(Exception):
                    parent_header = message['parent_header']
                    msg_type = parent_header['msg_type']
                    msg_id = parent_header['msg_id']
                    if msg_type == 'is_complete_request' and msg_id == context.kernel_restart_completion_id:
                        run_job_a(context)
            elif evaluation_state is A_RUNNING:
                if context.b_queued:
                    run_job_b(context)
                else:
                    set_state(context, IDLE)
            elif evaluation_state is B_RUNNING:
                context.main_thread_create_task(reset_kernel(context))


@handles('_connected')
async def connected(client_id, send, context):
    context.kernel_manager = KernelManager()
    context.iopub_listener_thread = Thread()
    context.part_a_end_line = 0
    context.iopub_buffer = None
    context.a_queued = False
    context.b_queued = False
    set_state(context, RESTARTING)


@handles('_disconnected')
async def disconnected(context):
    logger.info('stopping kernel')
    await stop_kernel({}, nop, context)


@handles('StartKernel')
async def start_kernel(msg, send, context):
    set_state(context, RESTARTING)
    await stop_kernel(msg, send, context)
    context.kernel_manager.start_kernel()
    context.jupyter_client = context.kernel_manager.client()
    context.kernel_stopped = Event()
    context.iopub_listener_thread = Thread(target=iopub_listener, args=(context, ))
    context.iopub_listener_thread.start()
    await wait_until_kernel_ready(context)
    await send('KernelStarted', None)


async def wait_until_kernel_ready(context):
    while context.evaluation_state is RESTARTING:
        context.kernel_restart_completion_id = context.jupyter_client.is_complete('')
        logger.debug('sleeping')
        await asyncio.sleep(.1)


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
    context.jupyter_client.execute(msg['code'], store_history=False)


indented = re.compile('(^\\s+)|(^@)')
continued = re.compile('\\\\\\s*$')


async def restart_kernel(context):
    # TODO: Use this function instead of reset_kernel if configured so.
    with Timer('restarting kernel'):
        set_state(context, RESTARTING)
        context.kernel_manager.restart_kernel(now=True)
        context.iopub_buffer = []
        await wait_until_kernel_ready(context)


async def reset_kernel(context):
    with Timer('resetting kernel'):
        set_state(context, RESTARTING)
        context.kernel_manager.interrupt_kernel()  # interrupt the kernel if it is busy
        context.jupyter_client.execute('%reset -f')
        context.iopub_buffer = []
        context.kernel_restart_completion_id = context.jupyter_client.is_complete('')


def run_job_a(context):
    set_state(context, A_RUNNING)
    context.a_queued = False
    context.main_thread_create_task(job_a(context))


def run_job_b(context):
    set_state(context, B_RUNNING)
    context.b_queued = False
    context.main_thread_create_task(job_b(context))


def cell_boundary_generator(code_lines):
    tokens = list(generate_tokens(StringIO('\n'.join(code_lines)).readline))
    line_to_tokens = defaultdict(list)
    for t in tokens:
        max_line = t.start[0]
        line_to_tokens[max_line].append(t)

    last_token_type = token.NEWLINE
    last_cell_end_line = 0
    for i, t in enumerate(tokens):

        if t.end[0] < last_cell_end_line:
            continue

        if last_token_type == token.NEWLINE and t.type == token.NL:
            current_line = t.end[0]

            last_non_nl_token = None
            for line in range(current_line, max_line + 1):
                tokens_ = line_to_tokens[line]
                if not tokens:
                    continue
                t_ = tokens_[0]
                if t_.type == token.NL:
                    continue
                last_non_nl_token = t_
                break

            if not last_non_nl_token or last_non_nl_token.start[1] != 0:
                last_token_type = t.type
                continue

            yield slice(last_cell_end_line, current_line)
            last_cell_end_line = current_line
        last_token_type = t.type

    yield slice(last_cell_end_line, None)


async def job_a(context):
    doc = context.shared_context.doc
    line = context.part_a_end_line
    context.iopub_buffer = []
    context.jupyter_client.execute('\n'.join(doc[:line]))


async def send_buffer(send, buffer):
    if not buffer:
        return
    last_execution_state = None
    for message in buffer:
        if message.get('execution_state', None):
            last_execution_state = message['execution_state']
        else:
            send('IOPub', message)
    if last_execution_state:
        send('IOPub', last_execution_state)


async def job_b(context):
    doc = context.shared_context.doc
    from_line = context.part_a_end_line
    send = context.main_thread_send
    send('Clear', None)
    await send_buffer(send, context.iopub_buffer)
    context.iopub_buffer = None
    logger.info('\n'.join(doc[from_line:]))

    context.busy = True
    context.jupyter_client.execute('\n'.join(doc[from_line:]))


@handles('EvaluatePartA')
async def evaluate_part_a(msg, send, context):
    doc = context.shared_context.doc
    line = 0
    for line in range(msg, -1, -1):
        if (line == len(doc) or not indented.match(doc[line])) \
                and (line > 0 and not continued.match(doc[line - 1])):
            break
    if line == context.part_a_end_line:
        logger.warn('Skipped A as line number is the same')
        return
    context.part_a_end_line = line

    context.a_queued = True
    if context.evaluation_state in (IDLE, A_RUNNING):
        await reset_kernel(context)
    # NOP for RESTARTING, B_RUNNING


@handles('EvaluatePartB')
async def evaluate_part_b(msg, send, context):
    context.b_queued = True
    line = msg['line']
    line_content = msg['line_content']
    doc = context.shared_context.doc
    doc[line] = line_content

    state = context.evaluation_state
    if state is IDLE:
        run_job_b(context)
    elif state is B_RUNNING:
        context.a_queued = True
        await reset_kernel(context)
    # NOP for RESTARTING, A_RUNNING


