import jedi
import re
from asyncio import sleep
from .utils import Timer

IMPORT_REGEX = re.compile(r'^\s*(from|import)\s')
BRACES_REGEX = re.compile(r'(\(|\))')
_loaded_modules = set()


def preload(module):
    if module in _loaded_modules:
        return
    _loaded_modules.add(module)
    with Timer(f'preloading module {module}'):
        # pass
        jedi.api.preload_module(module)


async def preload_modules(source_lines):
    for line in source_lines:
        if not IMPORT_REGEX.match(line):
            continue
        # get the `from ...` part
        prefix_start = line.find('from ') + 5
        if prefix_start >= 5:
            prefix_end = line.find('import ', prefix_start)
            prefix = line[prefix_start:prefix_end].strip()
        else:
            prefix_end = 0
            prefix = ''

        # get the `as ...` part
        postfix_start = line.find(' as ', prefix_end)
        if postfix_start < 0:
            postfix_start = None

        # get the import part
        in_between = line[prefix_end + 7:postfix_start]
        in_between = BRACES_REGEX.sub('', in_between)
        modules = in_between.split(',')

        if prefix:
            prefix = prefix + '.'
            if prefix.startswith('.'):  # bypass relative imports
                continue
        for module in modules:
            if module.startswith('.'):  # bypass relative imports
                continue
            await sleep(0)
            preload(prefix + module)
