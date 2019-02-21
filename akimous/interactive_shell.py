from threading import Thread
from functools import partial

from jupyter_client import KernelManager

from akimous.websocket import register_handler
from logzero import logger

handles = partial(register_handler, 'jupyter')


def iopub_listener(client):
    while True:
        message = client.get_iopub_msg()
        if not message:
            logger.info('IOPub listener terminated')
            return
        logger.debug(message['content'])


@handles('_connected')
async def connected(client_id, send, context):
    context.kernel_manager = KernelManager()
    context.iopub_listener_thread = Thread()


@handles('StartKernel')
async def start_kernel(msg, send, context):
    await stop_kernel(msg, send, context)
    context.kernel_manager.start_kernel()
    context.jupyter_client = context.kernel_manager.client()
    context.iopub_listener_thread = Thread(target=iopub_listener, args=(context.jupyter_client, ))
    context.iopub_listener_thread.start()
    await send('KernelStarted', None)


@handles('StopKernel')
async def stop_kernel(msg, send, context):
    if not context.kernel_manager.is_alive():
        return
    context.kernel_manager.shutdown_kernel()
    await send('KernelStopped', None)


@handles('Run')
async def run(msg, send, context):
    logger.debug('Running code %s', msg['code'])
    context.jupyter_client.execute(msg['code'])