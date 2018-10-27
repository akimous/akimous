import asyncio
import websockets
import json
import traceback
import webbrowser
from types import SimpleNamespace
from logzero import logger as log
from contextlib import suppress
from static_server import serve_http
from multiprocessing import Process
from word_completer import initialize as initialize_word_completer


class WS:
    handlers = {}  # [path][command] -> coroutine
    clients = {}  # [path]{} -> websocket

    @staticmethod
    def register(path, command):
        path = '/' + path
        if path not in WS.handlers:
            WS.handlers[path] = {}
        if path not in WS.clients:
            WS.clients[path] = set()
        if command in WS.handlers[path]:
            raise AttributeError('Command already registered')

        def decorator(coroutine):
            WS.handlers[path][command] = coroutine
            return coroutine
        return decorator

    @staticmethod
    async def socket_handler(ws: websockets.WebSocketServerProtocol, path: str):
        try:
            path_handler = WS.handlers.get(path, None)
            if path_handler is None:
                log.error('No handlers associated with path %s', path)
                ws.close()
                return
            WS.clients[path].add(ws)

            async def send(obj):
                await ws.send(json.dumps(obj))
            log.info('Connection %s established.', path)

            def main_thread_send(message):
                context.event_loop.call_soon_threadsafe(asyncio.ensure_future, send(message))

            context = SimpleNamespace(observer=None,
                                      observed_watches={},
                                      event_loop=asyncio.get_event_loop(),
                                      main_thread_send=main_thread_send)

            while 1:
                msg = await ws.recv()
#                log.debug('Received message from %s: %s', path, msg)
                msg = json.loads(msg)
                cmd = msg['cmd']
                command_handler = path_handler.get(cmd, None)
                if command_handler is None:
                    log.warn('Unhandled command %s/%s.', path, cmd)
                else:
                    try:
                        await command_handler(msg, send, context)
                    except Exception:
                        traceback.print_exc()

        except websockets.exceptions.ConnectionClosed:
            log.info('Connection %s closed.', path)
            WS.clients[path].remove(ws)
            if context.observer:
                with suppress(Exception):
                    context.observer.stop()

    @staticmethod
    def start_server(host, port, ws_port, no_browser):
        # serve static content
        process = Process(target=serve_http, name='http_process', kwargs={
            'host': host,
            'port': port
        })
        process.start()

        # serve websocket
        loop = asyncio.get_event_loop()
        loop.set_debug(True)
        loop.slow_callback_duration = 0.1
        websocket_server = websockets.serve(WS.socket_handler, host=host, port=ws_port)
        loop.run_until_complete(websocket_server)
        initialize_word_completer(loop)
        log.info('Starting websocket server, listening on %s:%d', host, ws_port)

        if not no_browser and not webbrowser.open(f'http://{host}:{port}'):
            log.warn(f'No browsers available. Please open http://{host}:{port} manually.')

        try:
            loop.run_forever()
            process.join()
        except KeyboardInterrupt:
            for clients in WS.clients.values():
                for ws in clients:
                    ws.close()
            loop.stop()
            return
