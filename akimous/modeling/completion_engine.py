import re
from collections import defaultdict

import jedi
import numpy as np


class DummyCompletion:
    __slots__ = 'name', 'complete', 'type', 'is_keyword'

    def __init__(self, name, prefix_length):
        self.name = name
        self.complete = name[prefix_length:]
        self.type = 'guessed'
        self.is_keyword = False

    def in_builtin_module(self):
        return False


class CompletionEngine:
    def __init__(self, file_path, content=''):
        self.file_path = file_path
        self.lines = content.splitlines()
        self.string = content
        self.jedi = jedi.Script(content, path=file_path)
        self.engine = AttributeInferenceEngine()

    def complete(self, line, ch, line_content):
        # line starts from 1
        self.update(line, line_content)
        self.string = '\n'.join(self.lines[1:])
        self.jedi = jedi.Script(self.string, line, ch, self.file_path)
        completions = self.jedi.completions()  # TODO: update after Jedi 0.16.0
        if completions:
            return completions
        return self.engine.predict(ch, line_content)

    def update(self, line, line_content):
        while len(self.lines) <= line:
            self.lines.append('')
        self.lines[line] = line_content
        self.engine.learn(line_content)


BUILTIN_TYPES = {
    '!bytearray',
    '!bytes',
    '!dict',
    '!float',
    '!int',
    '!list',
    '!set',
    '!str',
    '!tuple',
}

ATTRIBUTE_TO_BUILTIN_TYPES = defaultdict(set)
BUILTIN_TYPE_TO_ATTRIBUTES = {}
# populate common built-in types
for t in BUILTIN_TYPES:
    obj = __builtins__[t[1:]]()
    attributes = set(a for a in dir(obj) if not a.startswith('__'))
    for a in attributes:
        ATTRIBUTE_TO_BUILTIN_TYPES[a].add(t)
    BUILTIN_TYPE_TO_ATTRIBUTES[t] = attributes

# populate numpy ndarray
obj = np.zeros(1)
t = '!ndarray'
attributes = set(a for a in dir(obj) if not a.startswith('__'))
for a in attributes:
    ATTRIBUTE_TO_BUILTIN_TYPES[a].add(t)
BUILTIN_TYPE_TO_ATTRIBUTES[t] = attributes

# matches
# a.b
# a(b, c).d
# a[b + c].d
RE_ATTRIBUTE = re.compile(r'(\w[\w\d]*)(?:(\[.+\])|(\(.+\)))?\.(\w[\w\d]*)')
# groups                     ^---1----     ^--2--   ^--3--      ^---4----

RE_ATTRIBUTE_PREDICTION = re.compile(
    r'(\w[\w\d]*)(?:(\[.+\])|(\(.+\)))?\.(\w[\w\d]*)?$')
#      ^---1----     ^--2--   ^--3--      ^---4----


class AttributeInferenceEngine:
    def __init__(self):
        self.name_to_guessed_types = {}
        self.attibute_to_guessed_types = defaultdict(set)
        self.attibute_to_guessed_types.update(ATTRIBUTE_TO_BUILTIN_TYPES)
        self.type_to_attributes = BUILTIN_TYPE_TO_ATTRIBUTES.copy()
        # Types can be in one of the following formats:
        # * something
        # * something[]
        # * something()
        # Attributes can be in one of the following formats:
        # * attribute
        # * method_with_parameter(
        # * method_without_parameter()

    def _get_name_attribute_pair(self, line, match):
        start, end = match.span()
        name = match.group(1)
        if match.group(2):
            name += '[]'
        elif match.group(3):
            name += '()'
        attribute = match.group(4)
        if line[end:end + 1] == '(':
            if line[end + 1:end + 2] == ')':
                attribute += '()'
            else:
                attribute += '('
        return name, attribute

    def learn(self, line):
        match = RE_ATTRIBUTE.search(line)
        while match:
            name, attribute = self._get_name_attribute_pair(line, match)
            self.digest(name, attribute)
            match = RE_ATTRIBUTE.search(line, match.start(match.lastindex))

    def digest(self, name, attribute):
        guessed_types = self.name_to_guessed_types.get(name, None)
        if guessed_types:
            for t in guessed_types:
                if attribute in self.type_to_attributes[t]:
                    return  # type <=> attribute mapping exists

            # add attribute to all guessed types (except for built-in types)
            added = False
            for t in guessed_types:
                if t.startswith('!'):
                    continue
                self.type_to_attributes[t].add(attribute)
                self.attibute_to_guessed_types[attribute].add(t)
                added = True

            # create new type if all guessed types are built-in
            if not added:
                self._add_new_type(name, attribute)
        else:
            guessed_types = self.attibute_to_guessed_types[attribute]
            if guessed_types:
                self.name_to_guessed_types[name] = guessed_types
            else:
                self._add_new_type(name, attribute)

    def _add_new_type(self, name, attribute):
        # use the first encountered object name as type name,
        # because we don't know the actual type name
        self.name_to_guessed_types[name] = set((name, ))
        self.attibute_to_guessed_types[attribute].add(name)
        self.type_to_attributes[name] = set((attribute, ))

    def predict(self, column, line_content):
        match = RE_ATTRIBUTE_PREDICTION.search(line_content, 0, column)
        if not match:
            return []
        name, attribute_prefix = self._get_name_attribute_pair(
            line_content, match)
        guesses = self.infer(name)
        prefix_length = 0
        if attribute_prefix:
            guesses = set(i for i in guesses if i.startswith(attribute_prefix))
            prefix_length = len(attribute_prefix)
        return [DummyCompletion(i, prefix_length) for i in guesses]

    def infer(self, name):
        guessed_types = self.name_to_guessed_types.get(name, set())
        result = set()
        for t in guessed_types:
            result.update(self.type_to_attributes[t])
        return result
