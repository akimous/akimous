from boltons.gcutils import toggle_gc_postcollect

from utils import Timer

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
        args = parser.parse_args()

        from websocket import start_server
        import file_tree  # 11ms, 4M memory
        import editor  # 800ms, 80M memory


if __name__ == '__main__':
    host = args.host
    start_server(**args.__dict__)
