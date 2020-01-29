import argparse
import gc
from logging import DEBUG, INFO
from pathlib import Path

import logzero

from .utils import Timer, set_verbosity

gc.disable()  # to improve startup performance

log_format = '%(color)s[%(levelname)1.1s %(asctime)s.%(msecs)03d %(module)s:%(lineno)d]%(end_color)s %(message)s'
formatter = logzero.LogFormatter(fmt=log_format)
logzero.setup_default_logger(formatter=formatter)

inside_docker = Path('/.dockerenv').exists()

parser = argparse.ArgumentParser(description='Start Akimous server')
parser.add_argument('--host', type=str, default='0.0.0.0' if inside_docker else '127.0.0.1',
                    help='The IP address Akimous server will listen on. '
                         '(default=0.0.0.0 if inside docker, otherwise 127.0.0.1)')
parser.add_argument('--port', type=int, default=3179,
                    help='The port Akimous server will listen on. (default=3179)')
parser.add_argument('--no-browser', action='store_true', default=False,
                    help='Do not open the IDE in a browser after startup.')
parser.add_argument('--verbose', action='store_true', default=False,
                    help='Print extra debug messages.')
args = parser.parse_args()

set_verbosity(args.verbose)
logzero.loglevel(DEBUG if args.verbose else INFO)

try:
    from importlib.metadata import version
    logzero.logger.info('Starting Akimous %s', version('akimous'))
except ModuleNotFoundError:
    pass

with Timer('initialization'):
    from .websocket import start_server
    from . import project
    from . import file_tree  # 11ms, 4M memory
    from . import editor  # 900ms, 80M memory
    from . import terminal
    from . import interactive_shell  # 30ms, 3M memory
    from . import open_folder


def start():
    start_server(clean_up_callback=stop, **args.__dict__)


def stop():
    project.persistent_state.close()
    editor.doc_generator.temp_dir.cleanup()  # avoid ResourceWarning


gc.enable()

if __name__ == '__main__':
    start()
