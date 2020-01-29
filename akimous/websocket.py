import errno
import sys
import webbrowser
from asyncio import (CancelledError, Queue, create_task, ensure_future,
                     get_event_loop, sleep, wait_for)
from collections import defaultdict, namedtuple
from types import SimpleNamespace

import msgpack
import websockets
from logzero import logger
from websockets.exceptions import (ConnectionClosed, ConnectionClosedError,
                                   ConnectionClosedOK)

from akimous.utils import log_exception, nop

from .static_server import HTTPHandler
from .word_completer import initialize as initialize_word_completer

Session = namedtuple('Session', ('loop', 'queue'))
handlers = defaultdict(dict)  # [endpoint][event] -> coroutine
sessions = defaultdict(dict)  # [client_id][session_id] -> Session
max_client_id = 0


def register_handler(endpoint, command):
    assert command not in handlers[endpoint]

    def decorator(coroutine):
        handlers[endpoint][command] = coroutine
        return coroutine

    return decorator


async def session_handler(session_id: int, endpoint: str, queue: Queue,
                          ws: websockets.WebSocketServerProtocol,
                          shared_context: SimpleNamespace, first_message):
    session_handlers = handlers.get(endpoint)

    if session_handlers is None:
        logger.error('No handlers associated with path %s', endpoint)
        return

    async def send(event, obj):
        logger.debug('Sending message to %s/%s: %s', session_id, event, obj)
        try:
            await ws.send(msgpack.packb([session_id, event, obj]))
        except ConnectionClosed:
            logger.warning('Sending to a socket that is already closed')

    def main_thread_send(event, obj):
        context.event_loop.call_soon_threadsafe(ensure_future,
                                                send(event, obj))

    def main_thread_create_task(task):
        context.event_loop.call_soon_threadsafe(ensure_future, task)

    context = SimpleNamespace(
        event_loop=get_event_loop(),
        main_thread_send=main_thread_send,
        main_thread_create_task=main_thread_create_task,
        shared=shared_context,
    )

    connected_callback = session_handlers.get('_connected', nop)
    disconnected_callback = session_handlers.get('_disconnected', nop)

    with log_exception():
        await connected_callback(first_message, send, context)

    while 1:
        try:
            event, obj = await queue.get()
            event_handler = session_handlers.get(event, None)
            if not event_handler:
                logger.warning('Unhandled command %s/%s.', endpoint, event)
                queue.task_done()
                continue
            try:
                await event_handler(obj, send, context)
            except Exception as e:
                logger.exception(e)
            queue.task_done()
        except CancelledError:
            break
    with log_exception():
        await disconnected_callback(context)
    logger.warning('Session %s closed.', endpoint)


async def socket_handler(ws: websockets.WebSocketServerProtocol, path: str):
    global max_client_id

    max_client_id += 1
    client_id = max_client_id
    client_sessions = sessions[client_id]

    try:
        shared_context = SimpleNamespace()
        shared_context.client_id = client_id
        logger.info('Connection %s established.', client_id)

        while 1:
            msg = await ws.recv()
            msg = msgpack.unpackb(msg, raw=False)
            session_id, event, obj = msg
            logger.debug('Received message from %s/%s: %s', session_id, event,
                         obj)

            if session_id == 0:  # master session
                if event == 'OpenSession':
                    endpoint = obj['endpoint']
                    session_id = obj['sessionId']
                    first_message = obj['firstMessage']
                    queue = Queue()
                    session_loop = create_task(
                        session_handler(session_id, endpoint, queue, ws,
                                        shared_context, first_message))
                    session = Session(session_loop, queue)
                    client_sessions[session_id] = session
                    logger.info('Session %s of endpoint %s opened.',
                                session_id, endpoint)
                elif event == 'CloseSession':
                    session_id = obj
                    session = client_sessions[session_id]
                    await wait_for(session.queue.join(), timeout=1)
                    session.loop.cancel()
                    del client_sessions[session_id]
            else:
                session: Session = client_sessions.get(session_id, None)
                if not session:
                    logger.error('Unknown session ID %d', session_id)
                    continue
                await session.queue.put((event, obj))

    except ConnectionClosedOK:
        logger.info('Connection %s closed.', path)
        for session in client_sessions.values():
            session.loop.cancel()
        del sessions[client_id]

    except (ConnectionClosed, ConnectionClosedError) as e:
        logger.warning(e)
        for session in client_sessions.values():
            session.loop.cancel()
        del sessions[client_id]


def start_server(host, port, no_browser, verbose, clean_up_callback):
    loop = get_event_loop()
    loop.set_debug(True)
    loop.slow_callback_duration = .1 if verbose else 1.

    http_handler = HTTPHandler()
    websocket_server = websockets.serve(
        socket_handler,
        host=host,
        port=port,
        extra_headers=[('Content-Security-Policy', "frame-ancestors: 'none'")],
        process_request=http_handler.process_request)
    try:
        loop.run_until_complete(websocket_server)
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            logger.error(
                '%s:%d is already in use. Please specify a new port using option --port.',
                host, port)
            sys.exit(1)
        raise e

    initialize_word_completer(loop)
    logger.info('Starting server, listening on %s:%d.', host, port)

    if not no_browser and not webbrowser.open(f'http://{host}:{port}'):
        logger.warning('No browsers available. ' +
                       f'Please open http://{host}:{port} manually.')
    logger.info('Press Control-C to stop.')

    try:
        loop.run_forever()
    except KeyboardInterrupt:

        async def stop_everything():
            for sessions_ in sessions.values():
                for session in sessions_.values():
                    session.loop.cancel()
            await sleep(.1)
            clean_up_callback()
            # give it some time to gracefully shutdown, or ResourceWarnings will pop up
            await sleep(.1)
            logger.info('Terminated')
            loop.stop()

        logger.info('Terminating')
        loop.run_until_complete(loop.create_task(stop_everything()))
