import asyncio
import json
import re
import token
from collections import defaultdict
from contextlib import suppress
from functools import partial
from io import StringIO
from tokenize import generate_tokens

from logzero import logger
from zmq.asyncio import Context, Socket

from .utils import Timer, nop
from .websocket import register_handler

handles = partial(register_handler, 'jupyter')
_jupyter_imported = False

indented = re.compile('(^\\s+)|(^@)')
continued = re.compile('\\\\\\s*$')

IDLE = 'IDLE'
RESTARTING = 'RESTARTING'
A_RUNNING = 'A_RUNNING'
B_RUNNING = 'B_RUNNING'
"""Realtime Evaluation State Transition
| Current State \\ Event Received | IDLE  | EvaluatePartA | EvaluatePartB |
| ------------------------------- | ----- | ------------- | ------------- |
| IDLE                            |       | reset         | job B         |
| RESTARTING                      | job A |               |               |
| RUNNING_A                       | job B | reset         |               |
| RUNNING_B                       | reset |               | reset         |
"""


def set_state(context, new_state):
    context.evaluation_state = new_state
    if new_state is A_RUNNING:
        context.a_queued = False
    elif new_state is B_RUNNING:
        context.b_queued = False
    logger.info('state: %s; a_queued: %s; b_queued: %s', new_state,
                context.a_queued, context.b_queued)


@handles('_connected')
async def connected(msg, send, context):
    logger.info('shell connected')
    # Lazy import to reduce memory consumption
    if not _jupyter_imported:
        from jupyter_client import KernelManager
        _jupyter_imported = True
    context.kernel_manager = KernelManager()
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
    context.kernel_manager.cleanup()
    context.kernel_manager = None
    logger.debug('shell disconnected')


async def iopub_listener(send, context):
    client = context.jupyter_client
    socket = Socket(context=Context(),
                    socket_type=client.iopub_channel.socket.socket_type)
    try:
        with open(client.connection_file) as f:
            connection_info = json.load(f)

        socket.connect(
            f'{connection_info["transport"]}://{connection_info["ip"]}:{connection_info["iopub_port"]}'
        )
        socket.subscribe(b'')
        while True:
            message = await socket.recv_multipart()
            _, _, _, _, parent_header, _, content, *_ = message
            parent_header = json.loads(parent_header)
            content = json.loads(content)

            execution_state = content.get('execution_state', None)

            if context.evaluation_state is not RESTARTING:
                if context.iopub_buffer is not None:
                    logger.debug('buffered %s', content)
                    context.iopub_buffer.append(content)
                else:
                    logger.debug('unbuffered %s', content)
                    await send('IOPub', content)

            if execution_state == 'idle':
                msg_id = parent_header['msg_id']
                context.pending_messages.discard(msg_id)
                logger.info('removing message id %s; %s', msg_id,
                            context.pending_messages)

                if context.kernel_restart_completion_id == msg_id:
                    if context.realtime_evaluation_mode:
                        context.job_a = asyncio.create_task(job_a(context))
                    else:
                        set_state(context, IDLE)

                elif not context.pending_messages:
                    # only change state when there's no pending messages waiting response
                    evaluation_state = context.evaluation_state
                    if evaluation_state is A_RUNNING:
                        if context.b_queued:
                            context.job_b = asyncio.create_task(
                                job_b(send, context))
                        else:
                            set_state(context, IDLE)
                    elif evaluation_state is B_RUNNING:
                        asyncio.create_task(reset_kernel(context))

    except asyncio.CancelledError:
        socket.close()
        logger.info('iopub socket closed')


@handles('StartKernel')
async def start_kernel(msg, send, context):
    logger.info('start_kernel')
    logger.warn(msg)
    context.realtime_evaluation_mode = msg['realtimeEvaluation']
    set_state(context, RESTARTING)
    await stop_kernel(msg, send, context)
    context.a_queued = context.b_queued = context.realtime_evaluation_mode
    context.kernel_manager.start_kernel()
    context.jupyter_client = context.kernel_manager.client()
    context.iopub_listener = asyncio.create_task(iopub_listener(send, context))
    asyncio.create_task(wait_until_kernel_ready(send, context))


async def wait_until_kernel_ready(send, context):
    with Timer('waiting kernel'):
        await asyncio.sleep(.1)
        while context.evaluation_state is RESTARTING:
            context.kernel_restart_completion_id = context.jupyter_client.is_complete(
                '')
            logger.debug('sleeping')
            await asyncio.sleep(.1)
    await send('KernelStarted', None)


async def reset_kernel(context, interrupt=False):
    set_state(context, RESTARTING)
    logger.warning('pending_messages %s', context.pending_messages)
    if interrupt:
        # interrupt the kernel if it is busy
        context.kernel_manager.interrupt_kernel()
        context.pending_messages.clear()
    await execute_lines(context, ('%reset -f', ))
    context.iopub_buffer = []
    context.kernel_restart_completion_id = context.jupyter_client.is_complete(
        '')


@handles('InterruptKernel')
async def interrupt_kernel(msg, send, context):
    with suppress(Exception):
        context.job_a.cancel()
        context.job_b.cancel()
    context.kernel_manager.interrupt_kernel()


@handles('StopKernel')
async def stop_kernel(msg, send, context):
    with suppress(Exception):
        context.job_a.cancel()
        context.job_b.cancel()
    if not context.kernel_manager.is_alive():
        return
    context.kernel_manager.shutdown_kernel()
    context.iopub_listener.cancel()
    await send('KernelStopped', None)


async def execute_lines(context, lines):
    message_id = context.jupyter_client.execute('\n'.join(lines),
                                                store_history=False)
    context.pending_messages.add(message_id)
    logger.info('executing lines\n%s', '\n'.join(lines))
    logger.info('adding message id %s; %s', message_id,
                context.pending_messages)
    await asyncio.sleep(0)  # allow other tasks to run


@handles('Run')
async def run(msg, send, context):
    logger.debug('Running code %s', msg['code'])
    await execute_lines(context, msg['code'].splitlines())


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


async def job_a(context):
    set_state(context, A_RUNNING)
    context.a_queued = False
    doc = context.shared.doc
    line = context.part_a_end_line
    context.iopub_buffer = []
    part_a_is_empty = True
    for boundary in cell_boundary_generator(doc, end_line=line):
        logger.info('Running A %s', boundary)
        part_a_is_empty = False
        await execute_lines(context, doc[boundary])
    # make sure iopub_listener will go to next state if nothing to run
    if part_a_is_empty:
        context.jupyter_client.is_complete('')


async def job_b(send, context):
    set_state(context, B_RUNNING)
    context.b_queued = False
    doc = context.shared.doc
    from_line = context.part_a_end_line
    await send('Clear', None)
    await send_buffer(send, context.iopub_buffer)
    context.iopub_buffer = None
    for boundary in cell_boundary_generator(doc, start_line=from_line):
        await execute_lines(context, doc[boundary])


async def send_buffer(send, buffer):
    if not buffer:
        return
    last_execution_state = None
    # remove duplicated/bouncing execution states
    for message in buffer:
        if message.get('execution_state', None):
            last_execution_state = message['execution_state']
        else:
            await send('IOPub', message)
    if last_execution_state:
        await send('IOPub', last_execution_state)


@handles('EvaluatePartA')
async def evaluate_part_a(msg, send, context):
    logger.info('EvaluatePartA %s', msg)
    doc = context.shared.doc
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
    logger.info('EvaluatePartB %s', msg)
    context.b_queued = True
    line = msg['line']
    line_content = msg['line_content']
    doc = context.shared.doc
    doc[line] = line_content

    state = context.evaluation_state
    if state is IDLE:
        context.job_b = asyncio.create_task(job_b(send, context))
    elif state is B_RUNNING:
        context.a_queued = True
        await reset_kernel(context, interrupt=True)
    # NOP for RESTARTING, A_RUNNING
