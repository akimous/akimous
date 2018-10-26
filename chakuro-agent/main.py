from utils import Timer
from boltons.gcutils import toggle_gc_postcollect

with Timer('initialization'):
    with toggle_gc_postcollect:
        from ws import WS  # 44 ms, 6M memory
        import file_tree  # 11ms, 4M memory
        import editor  # 800ms, 80M memory

WS.start_server()

