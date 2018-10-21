from time import perf_counter
from logzero import logger as log
import os
import psutil


def get_memory_usage():
    process = psutil.Process(os.getpid())
    return f'{process.memory_info().rss / 1024 / 1024:.3f} M'


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
        log.debug(f'Starting {self.description}; memory = {get_memory_usage()}')
        self.start = perf_counter()
        return self

    def __exit__(self, *args):
        self.end = perf_counter()
        log.debug(f'{self.description} took {(self.end - self.start) * 1000: .3f} ms;'
                  f' memory = {get_memory_usage()}')
