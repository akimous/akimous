import json
import os
from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from time import perf_counter

from appdirs import user_config_dir
from logzero import logger

# ~/Library/Application Support/akimous
config_directory = Path(user_config_dir('akimous'))
psutil = None


def set_verbosity(verbose):
    global psutil
    if verbose:
        try:
            import psutil
        except ImportError:
            pass


def get_project_config(context, file_name):
    return context.shared.project_config_path / file_name


def merge_dict(primary, secondary):
    """ Merge secondary into primary (maximum depth = 2).
    If a key exists in secondary, overwrite the value of the same key in primary with the value in secondary.
    :param primary: dictionary
    :param secondary: dictionary
    :return: None
    """
    for k, v in secondary.items():
        section = primary.get(k, None)
        if section is None or not isinstance(v, dict):
            primary[k] = v
        else:
            for key, value in v.items():
                section[key] = value
    return primary


def get_merged_config(user_file, default_file):
    with resources.open_text('akimous.resources', default_file) as f:
        config = json.load(f)
    if user_file.exists():
        with open(user_file) as f:
            user_config = json.loads(f.read())
            return merge_dict(config, user_config)
    else:
        user_file.parent.mkdir(parents=True, exist_ok=True)
        with open(user_file, 'w') as f:
            json.dump(config, f, indent=4, sort_keys=True)
        return config


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


async def nop(*args, **kwargs):
    pass


@contextmanager
def log_exception():
    try:
        yield
    except Exception as e:
        logger.exception(e)


class Timer:
    def __init__(self, description):
        self.description = description

    def __enter__(self):
        if not psutil:
            return self
        logger.debug(
            f'Starting {self.description}; memory = {get_memory_usage()}')
        self.start = perf_counter()
        return self

    def __exit__(self, *args):
        if not psutil:
            return
        self.end = perf_counter()
        logger.debug(
            f'{self.description} took {(self.end - self.start) * 1000: .3f} ms;'
            f' memory = {get_memory_usage()}')
