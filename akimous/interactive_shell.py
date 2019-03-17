import asyncio
import re
import token
from collections import defaultdict
from functools import partial
from io import StringIO
from threading import Event, Thread
from tokenize import generate_tokens

from jupyter_client import KernelManager
from logzero import logger

from .utils import Timer, nop
from .websocket import register_handler

handles = partial(register_handler, 'jupyter')

IDLE = 'IDLE'
RESTARTING = 'RESTARTING'
A_RUNNING = 'A_RUNNING'
B_RUNNING = 'B_RUNNING'


@handles('_connected')
async def connected(client_id, send, context):
    context.kernel_manager = KernelManager()
    context.iopub_listener_thread = Thread()
    context.part_a_end_line = 0
    context.iopub_buffer = None
    context.a_queued = False
    context.b_queued = False
    context.realtime_evaluation_mode = False
    context.pending_messages = set()
    set_state(context, RESTARTING)


@handles('_disconnected')
async def disconnected(context):
    logger.info('stopping kernel')
    await stop_kernel({}, nop, context)


def set_state(context, new_state):
    context.evaluation_state = new_state
    if new_state is A_RUNNING:
        context.a_queued = False
    elif new_state is B_RUNNING:
        context.b_queued = False
    logger.warn('state: %s; a_queued: %s; b_queued: %s', new_state,
                context.a_queued, context.b_queued)


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
            parent_header = message['parent_header']
            msg_id = parent_header['msg_id']
            context.pending_messages.discard(msg_id)
            logger.info('removing message id %s; %s', msg_id,
                        context.pending_messages)

            if not context.pending_messages:  # only change state when there's no pending messages waiting response
                evaluation_state = context.evaluation_state
                if (evaluation_state is RESTARTING
                        and context.realtime_evaluation_mode):
                    if context.realtime_evaluation_mode:
                        run_job_a(context)
                    else:
                        set_state(context, IDLE)
                elif evaluation_state is A_RUNNING:
                    if context.b_queued:
                        run_job_b(context)
                    else:
                        set_state(context, IDLE)
                elif evaluation_state is B_RUNNING:
                    context.main_thread_create_task(reset_kernel(context))


async def execute_lines(context, lines):
    message_id = context.jupyter_client.execute(
        '\n'.join(lines), store_history=False)
    context.pending_messages.add(message_id)
    logger.info('executing lines\n%s', '\n'.join(lines))
    logger.info('adding message id %s; %s', message_id,
                context.pending_messages)


@handles('StartKernel')
async def start_kernel(msg, send, context):
    logger.warn(msg)
    context.realtime_evaluation_mode = msg['realtimeEvaluation']
    set_state(context, RESTARTING)
    await stop_kernel(msg, send, context)
    context.a_queued = context.b_queued = context.realtime_evaluation_mode
    context.kernel_manager.start_kernel()
    context.jupyter_client = context.kernel_manager.client()
    context.kernel_stopped = Event()
    context.iopub_listener_thread = Thread(
        target=iopub_listener, args=(context, ))
    context.iopub_listener_thread.start()
    await wait_until_kernel_ready(context)
    await send('KernelStarted', None)


async def wait_until_kernel_ready(context):
    while context.evaluation_state is RESTARTING:
        context.kernel_restart_completion_id = context.jupyter_client.is_complete(
            '')
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
    await execute_lines(context, msg['code'])


indented = re.compile('(^\\s+)|(^@)')
continued = re.compile('\\\\\\s*$')


async def restart_kernel(context):
    # TODO: Use this function instead of reset_kernel if configured so.
    with Timer('restarting kernel'):
        set_state(context, RESTARTING)
        context.kernel_manager.restart_kernel(now=True)
        context.iopub_buffer = []
        await wait_until_kernel_ready(context)


async def reset_kernel(context, interrupt=False):
    with Timer('resetting kernel'):
        set_state(context, RESTARTING)
        if interrupt:
            # interrupt the kernel if it is busy
            context.kernel_manager.interrupt_kernel()
            context.pending_messages.clear()
        await execute_lines(context, ('%reset -f', ))
        context.iopub_buffer = []
        context.kernel_restart_completion_id = context.jupyter_client.is_complete(
            '')


def cell_boundary_generator(code_lines, start_line=0, end_line=999999):
    tokens = list(generate_tokens(StringIO('\n'.join(code_lines)).readline))
    line_to_tokens = defaultdict(list)
    max_line = 0
    for t in tokens:
        max_line = t.start[0]
        line_to_tokens[max_line].append(t)

    last_token_type = token.NEWLINE
    last_cell_end_line = start_line
    for i, t in enumerate(tokens):
        line = t.end[0]
        if line < last_cell_end_line:
            continue
        if line > end_line:
            return

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


def run_job_a(context):
    set_state(context, A_RUNNING)
    context.a_queued = False
    context.main_thread_create_task(job_a(context))


async def job_a(context):
    doc = context.shared_context.doc
    line = context.part_a_end_line
    context.iopub_buffer = []
    part_a_is_empty = True
    for boundary in cell_boundary_generator(doc, end_line=line):
        # logger.info('Running A: \n%s', '\n'.join(doc[boundary]))
        logger.info('Running A %s', boundary)
        part_a_is_empty = False
        await execute_lines(context, doc[boundary])
    # make sure iopub_listener will go to next state if nothing to run
    if part_a_is_empty:
        context.jupyter_client.is_complete('')


def run_job_b(context):
    set_state(context, B_RUNNING)
    context.b_queued = False
    context.main_thread_create_task(job_b(context))


async def job_b(context):
    doc = context.shared_context.doc
    from_line = context.part_a_end_line
    send = context.main_thread_send
    send('Clear', None)
    await send_buffer(send, context.iopub_buffer)
    context.iopub_buffer = None
    for boundary in cell_boundary_generator(doc, start_line=from_line):
        await execute_lines(context, doc[boundary])


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
        await reset_kernel(context, interrupt=True)
    # NOP for RESTARTING, A_RUNNING
