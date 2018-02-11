import asyncio
import websockets
import json
import traceback
from types import SimpleNamespace
from logzero import logger as log
from contextlib import suppress


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
            context = SimpleNamespace(observer=None, observed_watches={})

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
    def start_server(host='127.0.0.1', port=3179):
        log.info('Server started, listening on %s:%d', host, port)
        loop = asyncio.get_event_loop()
        loop.set_debug(True)
        # loop.slow_callback_duration = 0.016
        server = websockets.serve(WS.socket_handler, host=host, port=port)
        loop.run_until_complete(server)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            for clients in WS.clients.values():
                for ws in clients:
                    ws.close()
            loop.stop()
            return
