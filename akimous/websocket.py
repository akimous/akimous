import webbrowser
from asyncio import Queue, ensure_future, CancelledError, create_task, get_event_loop
from collections import defaultdict, namedtuple
from types import SimpleNamespace
from websockets.exceptions import ConnectionClosed
import msgpack
import websockets
from logzero import logger

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
                          ws: websockets.WebSocketServerProtocol, shared_context: SimpleNamespace):
    session_handlers = handlers.get(endpoint)
    disconnected_callback = session_handlers.get('_disconnected', None)

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
        context.event_loop.call_soon_threadsafe(ensure_future, send(event, obj))

    def main_thread_create_task(task):
        context.event_loop.call_soon_threadsafe(ensure_future, task)

    context = SimpleNamespace(
        linter_task=None,  # TODO: remove
        observer=None,
        observed_watches={},
        event_loop=get_event_loop(),
        main_thread_send=main_thread_send,
        main_thread_create_task=main_thread_create_task,
        shared=shared_context,
    )

    connected_callback = session_handlers.get('_connected', None)
    if connected_callback:
        try:
            await connected_callback(send, context)
        except Exception as e:
            logger.exception(e)

    while 1:
        try:
            event, obj = await queue.get()
            event_handler = session_handlers.get(event, None)
            if not event_handler:
                logger.warning('Unhandled command %s/%s.', endpoint, event)
                continue
            try:
                await event_handler(obj, send, context)
            except Exception as e:
                logger.exception(e)
            queue.task_done()
        except CancelledError:
            logger.warning('Session %s closed.', endpoint)
            break
    if disconnected_callback:
        await disconnected_callback(context)


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
            logger.debug('Received message from %s/%s: %s', session_id, event, obj)

            if session_id == 0 and event == 'OpenSession':  # new session
                endpoint = obj['endpoint']
                session_id = obj['sessionId']
                queue = Queue()
                session_loop = create_task(session_handler(session_id, endpoint, queue, ws, shared_context))
                session = Session(session_loop, queue)
                client_sessions[session_id] = session
                logger.info('Session %s of endpoint %s opened.', session_id, endpoint)
            else:
                session: Session = client_sessions.get(session_id, None)
                if not session:
                    logger.error('Unknown session ID %d', session_id)
                    continue
                await session.queue.put((event, obj))

    except ConnectionClosed:
        logger.info('Connection %s closed.', path)
        for session in client_sessions.values():
            session.loop.cancel()
        del sessions[client_id]


def start_server(host, port, no_browser, verbose):
    loop = get_event_loop()
    loop.set_debug(True)
    loop.slow_callback_duration = .1 if verbose else 1.

    http_handler = HTTPHandler()
    websocket_server = websockets.serve(
        socket_handler, host=host, port=port, process_request=http_handler.process_request)
    loop.run_until_complete(websocket_server)
    initialize_word_completer(loop)
    logger.info('Starting server, listening on %s:%d.', host, port)

    if not no_browser and not webbrowser.open(f'http://{host}:{port}'):
        logger.warning(f'No browsers available. Please open http://{host}:{port} manually.')
    logger.info('Press Control-C to stop.')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('Terminating')
        # for paths in clients.values():
        #     for path in paths.values():
        #         for socket in path:
        #             socket.close()
        loop.stop()
        logger.info('Terminated')
