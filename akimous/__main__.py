from logging import DEBUG, INFO

import logzero
from boltons.gcutils import toggle_gc

from .utils import Timer


log_format = '%(color)s[%(levelname)1.1s %(asctime)s.%(msecs)03d %(module)s:%(lineno)d]%(end_color)s %(message)s'
formatter = logzero.LogFormatter(fmt=log_format)
logzero.setup_default_logger(formatter=formatter)


with Timer('initialization'), toggle_gc:
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
    from . import project
    from . import file_tree  # 11ms, 4M memory
    from . import editor  # 900ms, 80M memory
    from . import terminal
    from . import interactive_shell # 30ms, 3M memory


def start():
    start_server(**args.__dict__)


if __name__ == '__main__':
    start()

    # clean up to avoid ResourceWarning
    editor.doc_generator.temp_dir.cleanup()
