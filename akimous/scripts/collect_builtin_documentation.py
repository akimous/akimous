import os
import re
import sqlite3
from pathlib import Path
from subprocess import call

import docutils.core
from docutils.writers.html5_polyglot import Writer

# call(['git', 'clone', 'https://github.com/python/cpython.git'])


writer = Writer()


def define_roles(paragraph):
    role_set = set(i[1:-2] if i.startswith(':') else i[:-2] for i in re.findall('\w*:\w+:`', paragraph))
    role_definitions = [f'.. role:: {i}(literal)' for i in role_set]
    return '\n'.join(role_definitions) + '\n\n' + paragraph


indentation = re.compile('^\s+')


def dedent_lines(lines):
    if not lines:
        return lines
    indent = indentation.match(lines[0])
    if not indent:
        return lines
    amount = indent.end()
    result = []
    for i, line in enumerate(lines):
        indent = indentation.match(line)
        indent = indent.end() if indent else 0
        if line.strip() == '':
            result.append(line)
        elif indent < amount:
            break
        else:
            result.append(line[amount:])
    return result


def convert_to_html(rst):
    rst = rst
    return docutils.core.publish_parts(writer_name='html5_polyglot', source=rst)['html_body']


def process_file(path):
    with open(path, 'r') as f:
        paragraphs = {}
        lines = f.readlines()
        module_name = None
        first_line = lines[0]
        if first_line.startswith(':mod:`'):
            module_name = first_line[6:first_line.find('`', 6)]
        print('module name:', module_name)

        start_line = 0

        pattern = re.compile('^\.\. .*:: ')
        blank_line = re.compile('^\s*$')
        for i, line in enumerate(lines):
            if pattern.match(line):
                signature_line = lines[start_line]
                if 'index:: ' not in signature_line and '::' in signature_line:
                    if start_line == 0:
                        start_line = i
                        continue

                    entry_name = signature_line[pattern.match(signature_line).end():]
                    if '(' in entry_name:
                        entry_name = entry_name[:entry_name.find('(')]

                    start_line += 1
                    while blank_line.match(lines[start_line]):
                        start_line += 1
                    for xxx in lines[start_line:i]:
                        if '::' in xxx:
                            print(xxx)
                    paragraph_lines = [
                        line for line in lines[start_line:i]
                        # if '::' not in line
                    ]
                    paragraph_lines = dedent_lines(paragraph_lines)
                    paragraph = ''.join(paragraph_lines)
                    # print(define_roles(paragraph))
                    paragraphs[entry_name] = define_roles(paragraph)





                    # if entry_name == 'AbstractEventLoop.call_soon':
                    if True:
                        # print(lines[start_line:i], flush=True)
                        print(paragraph, flush=True)
                        html = convert_to_html(define_roles(paragraph))
                        print('TITLE', entry_name, flush=True)
                        print(html, flush=True)

                start_line = i
        # for k, v in paragraphs.items():
            # print('>>>', k)
            # print(v)
            # print(convert_to_html(v))
            # convert_to_html(v)


# process_file('cpython/Doc/library/array.rst')
for dirpath, dirnames, filenames in os.walk('cpython/Doc/library'):
    for file in filenames:
        path = Path('cpython/Doc/library') / Path(file)
        if not file.endswith('.rst'):
            continue
        print(path)
        process_file(path)
        break
    break
