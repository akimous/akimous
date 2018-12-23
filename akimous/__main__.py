from boltons.gcutils import toggle_gc_postcollect
from logging import DEBUG, INFO
from .utils import Timer
import logzero

with Timer('initialization'):
    with toggle_gc_postcollect:
        import argparse

        parser = argparse.ArgumentParser(description='Start Akimous server')
        parser.add_argument('--host', type=str, nargs=1, default='127.0.0.1',
                            help='The IP address Akimous server will listen on. (default=127.0.0.1)')
        parser.add_argument('--port', type=int, nargs=1, default=3179,
                            help='The port Akimous server will listen on. (default=3179)')
        parser.add_argument('--no-browser', action='store_true', default=False,
                            help='Do not open the IDE in a browser after startup.')
        parser.add_argument('--verbose', action='store_true', default=False,
                            help='Print extra debug messages.')
        args = parser.parse_args()

        logzero.loglevel(DEBUG if args.verbose else INFO)

        from .websocket import start_server
        from .file_tree import * # 11ms, 4M memory
        from .editor import *  # 800ms, 80M memory


def start():
    start_server(**args.__dict__)


if __name__ == '__main__':
    start()
