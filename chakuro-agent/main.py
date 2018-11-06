from utils import Timer
from boltons.gcutils import toggle_gc_postcollect

with Timer('initialization'):
    with toggle_gc_postcollect:
        import argparse

        parser = argparse.ArgumentParser(description='Start Akimous server')
        parser.add_argument('--host', type=str, nargs=1, default='127.0.0.1',
                            help='The IP address Akimous server will listen on. (default=127.0.0.1)')
        parser.add_argument('--port', type=int, nargs=1, default=3178,
                            help='The port Akimous server will listen on for serving static contents. (default=3178)')
        parser.add_argument('--ws-port', type=int, nargs=1, default=3179,
                            help='The port Akimous server will listen on for communicating with websockets. '
                                 '(default=3179)')
        parser.add_argument('--no-browser', action='store_true', default=False,
                            help='Do not open the IDE in a browser after startup.')
        args = parser.parse_args()

        from ws import WS  # 44 ms, 6M memory
        import file_tree  # 11ms, 4M memory
        import editor  # 800ms, 80M memory


if __name__ == '__main__':
    host = args.host
    WS.start_server(**args.__dict__)
