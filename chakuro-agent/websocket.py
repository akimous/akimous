import asyncio
import traceback
import webbrowser
from collections import defaultdict
from contextlib import suppress
from multiprocessing import Process
from types import SimpleNamespace

import msgpack
import websockets
from logzero import logger as log

from static_server import serve_http
from word_completer import initialize as initialize_word_completer

_handlers = defaultdict(dict)  # [path][event] -> coroutine
_clients = defaultdict(set)  # [path]{} -> websocket


def register_handler(path, command):
    path = f'/{path}'
    assert command not in _handlers[path]

    def decorator(coroutine):
        _handlers[path][command] = coroutine
        return coroutine

    return decorator


async def socket_handler(ws: websockets.WebSocketServerProtocol, path: str):
    def main_thread_send(event, obj):
        context.event_loop.call_soon_threadsafe(asyncio.ensure_future, send(event, obj))

    context = SimpleNamespace(
        linter_task=None,
        observer=None,
        observed_watches={},
        event_loop=asyncio.get_event_loop(),
        main_thread_send=main_thread_send)
    try:
        path_handler = _handlers.get(path, None)
        if path_handler is None:
            log.error('No handlers associated with path %s', path)
            ws.close()
            return
        _clients[path].add(ws)

        async def send(event, obj):
            # log.warn('sending event %s: %s', event, repr(obj))
            await ws.send(msgpack.packb([event, obj]))

        log.info('Connection %s established.', path)

        while 1:
            msg = await ws.recv()
            msg = msgpack.unpackb(msg, raw=False)
            event, obj = msg
            # log.debug('Received message from %s/%s: %s', path, event, obj)
            event_handler = path_handler.get(event, None)
            if not event_handler:
                log.warn('Unhandled command %s/%s.', path, event)
                continue
            try:
                await path_handler[event](obj, send, context)
            except Exception:
                traceback.print_exc()

    except websockets.exceptions.ConnectionClosed:
        log.info('Connection %s closed.', path)
        _clients[path].remove(ws)
        if context.linter_task:
            context.linter_task.cancel()
        if context.observer:
            with suppress(Exception):
                context.observer.stop()


def start_server(host, port, ws_port, no_browser):
    # serve static content
    process = Process(target=serve_http, name='http_process', kwargs={'host': host, 'port': port})
    process.start()

    # serve websocket
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.slow_callback_duration = 0.1
    websocket_server = websockets.serve(socket_handler, host=host, port=ws_port)
    loop.run_until_complete(websocket_server)
    initialize_word_completer(loop)
    log.info('Starting websocket server, listening on %s:%d', host, ws_port)

    if not no_browser and not webbrowser.open(f'http://{host}:{port}'):
        log.warn(f'No browsers available. Please open http://{host}:{port} manually.')

    try:
        loop.run_forever()
        process.join()
    except KeyboardInterrupt:
        for clients in _clients.values():
            for socket in clients:
                socket.close()
        loop.stop()
        exit(0)
