from utils import Timer
from boltons.gcutils import toggle_gc_postcollect

with Timer('Initialization'):
    with toggle_gc_postcollect:
        from ws import WS
        import file_tree
        import editor

WS.start_server()

