from time import perf_counter
from logzero import logger as log


def detect_doc_type(docstring):
    if '-----' in docstring:
        return 'NumPyDoc'
    if 'Args:' in docstring or 'Returns:' in docstring:
        return 'GoogleDoc'
    if ':param ' in docstring or ':returns:' in docstring:
        return 'rst'
    return 'text'


class Timer:
    def __init__(self, description):
        self.description = description

    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, *args):
        self.end = perf_counter()
        log.debug(f'{self.description} took {self.end - self.start} s')
