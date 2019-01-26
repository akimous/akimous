import re
import os
from pathlib import Path
from collections import namedtuple


Match = namedtuple('Match', ('line', 'start', 'end', 'text'))


def search(file, regex):
    matches = []
    with open(file, errors='ignore') as f:
        for line, line_content in enumerate(f):
            matches.extend(Match(line, m.start(), m.end(), line_content)
                           for m in regex.finditer(line_content))
    return matches


async def find_in_directory(msg, send, context):
    regex = re.compile(msg['query'])
    directory = Path(context.shared_context.project_root, *msg['path'])
    results = []
    file_count = 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            path = Path(root) / file
            matches = search(path, regex)
            file_count += 1
            if not matches:
                continue
            results.append(
                (str(path.relative_to(context.shared_context.project_root)), matches))

    await send('FoundInDirectory', dict(result=results))
