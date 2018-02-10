import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
import asyncio
import websockets
import json
from pathlib import Path
import os

observer = Observer()
observer.start()


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
async def test():
    path = '/Users/ray/Code/chakuro/chakuro-agent'
    event_handler = LoggingEventHandler()

    # observer.schedule(event_handler, path, recursive=False)
# try:
#     while True:
#         time.sleep(1)
# except KeyboardInterrupt:
#     observer.stop()
# observer.join()


async def socket_handler(ws: websockets.WebSocketServerProtocol, path: str):
    while True:
        msg = await ws.recv()
        msg = json.loads(msg)
        print(msg)
        if msg['cmd'] == 'openFolder':
            path = Path(msg['path'])
            observer.schedule(LoggingEventHandler(), str(path.absolute()))
            root, dirs, files = next(os.walk(Path(path)))
            result = {
                'cmd': 'openFolder',
                'folderName': path.name,
                'path': str(path),
                'dirs': [dict(name=d, path=str(path / d)) for d in dirs],
                'files': [dict(name=f, path=str(path / f)) for f in files]
            }
            print('result', result)
            await ws.send(json.dumps(result))
            print('done')

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    server = websockets.serve(socket_handler, host='0.0.0.0', port=3179)
    loop.run_until_complete(server)
    loop.run_until_complete(test())
    loop.run_forever()
