import re
import os
from pathlib import Path
from collections import namedtuple
from pathspec import PathSpec
from cachetools import cached, TTLCache


Match = namedtuple('Match', ('line', 'start', 'end', 'text'))


def get_gitignore_file(path):
    path = path.resolve()
    for _ in range(5):
        file = path / '.gitignore'
        if file.is_file():
            return file
        if path.parent == path:
            return
        path = path.parent
    return


_pathspec_cache = {}
_null_spec = PathSpec.from_lines('gitwildmatch', ('', ))


@cached(cache=TTLCache(maxsize=16, ttl=30))
def get_pathspec(directory):
    ignore_file = get_gitignore_file(directory)
    if not ignore_file:
        return _null_spec
    with open(ignore_file) as f:
        spec = PathSpec.from_lines('gitwildmatch', f.readlines())
    return spec


def search(file, regex):
    matches = []
    with open(file, errors='ignore') as f:
        for line, line_content in enumerate(f):
            matches.extend(Match(line, m.start(), m.end(), line_content)
                           for m in regex.finditer(line_content))
    return matches


async def find_in_directory(msg, send, context):
    regex = re.compile(msg['query'])
    limit = msg['limit']
    project_root = context.shared_context.project_root
    directory = Path(project_root, *msg['path'])
    pathspec = get_pathspec(project_root)
    results = []
    file_count = 0
    match_count = 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            path = Path(root) / file
            relative_path = str(path.relative_to(project_root))
            if pathspec.match_file(relative_path):
                continue
            matches = search(path, regex)
            if not matches:
                continue
            results.append((relative_path, matches))
            file_count += 1
            match_count += len(matches)
            if match_count > limit:
                break
        if match_count > limit:
            break

    await send('FoundInDirectory',
               dict(result=results, overflow=match_count > limit, nFiles=file_count))
