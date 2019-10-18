import re

from .feature_definition import FeatureDefinition


@FeatureDefinition.register_feature_generator('blank_line_before', True)
def f(line, doc, **_):
    count = 0
    for i in range(line - 1, 0, -1):
        if not doc[i].lstrip():
            count += 1
        else:
            break
    return count


@FeatureDefinition.register_feature_generator('line_number', True)
def f(line, **_):
    return line


@FeatureDefinition.register_feature_generator('indent', True)
def f(line_content, **_):
    return len(line_content) - len(line_content.lstrip())


@FeatureDefinition.register_feature_generator('indent_delta', True)
def f(line_content, line, doc, **_):
    last_non_empty_line = ''
    for i in range(line - 1, -1, -1):
        if doc[i]:
            last_non_empty_line = doc[i]
            break
    last_indent = len(line_content) - len(line_content.lstrip())
    current_indent = len(last_non_empty_line) - len(last_non_empty_line.lstrip())
    result = last_indent - current_indent
    return result


@FeatureDefinition.register_feature_generator('at_line_start', True)
def f(line_content, ch, **_):
    head = line_content[:ch].lstrip()
    return 0 if head else 1


LEFT_CHAR = ['(', '[', '{', '=', ',', '@', ':', '.']
for c in LEFT_CHAR:
    @FeatureDefinition.register_feature_generator(f'left_char_is_{c}', True)
    def f(line_content, ch, c=c, **_):
        for i in reversed(line_content[:ch]):
            if i.isspace():
                continue
            if i == c:
                return 1
        return 0


ENDING = ['(', '[', '{', '}', ']', ')', ',', ':']
for c in ENDING:
    @FeatureDefinition.register_feature_generator(f'last_line_ends_with_{c}', True)
    def f(doc, line, c=c, **_):
        if line < 1:
            return 0
        last_line = doc[line - 1]
        if last_line:
            return last_line[-1] == c
        return 0


IN_FUNCTION_SIGNATURE = [
    'abs',
    # 'delattr',     # removed on 20180929 for 0 importance
    # 'hash',        # removed on 20180929 for 0 importance
    # 'memoryview',  # removed on 20180929 for 0 importance
    'set',
    # 'all',         # removed on 20180929 for improved accuracy
    'dict',
    # 'help',        # removed on 20180929 for 0 importance
    # 'min',         # removed on 20180929 for improved accuracy
    'setattr',
    # 'any',         # removed on 20180930 for improved accuracy
    # 'dir',         # removed on 20180929 for 0 importance
    # 'hex',         # removed on 20180929 for 0 importance
    # 'next',        # removed on 20180929 for 0 importance
    'slice',
    # 'ascii',       # removed on 20180929 for 0 importance
    # 'divmod',      # removed on 20180929 for 0 importance
    # 'id',          # removed on 20180929 for improved accuracy
    # 'object',      # removed on 20180929 for 0 importance
    'sorted',
    # 'bin',         # removed on 20180929 for 0 importance
    'enumerate',
    # 'input',       # removed on 20180929 for 0 importance
    # 'oct',         # removed on 20180929 for 0 importance
    # 'staticmethod',# removed on 20180929 for 0 importance
    'bool',
    # 'eval',        # removed on 20180929 for 0 importance
    'int',
    'open',
    'str',
    # 'breakpoint',  # removed on 20180929 for 0 importance
    # 'exec',        # removed on 20180929 for 0 importance
    'isinstance',
    # 'ord',         # removed on 20180929 for 0 importance
    'sum',
    # 'bytearray',   # removed on 20180929 for 0 importance
    # 'filter',      # removed on 20180929 for 0 importance
    # 'issubclass',  # removed on 20180929 for 0 importance
    # 'pow',         # removed on 20180929 for 0.0003% importance
    'super',
    # 'bytes',       # removed on 20180929 for 0 importance
    # 'float',       # removed on 20180929 for 0.0009% importance
    # 'iter',        # removed on 20180929 for 0 importance
    'print',
    'tuple',
    # 'callable',    # removed on 20180929 for improved accuracy
    'format',
    'len',
    # 'property',    # removed on 20180929 for 0 importance
    # 'type',        # removed on 20180929 for improved accuracy
    'chr',
    # 'frozenset',   # removed on 20180929 for 0 importance
    'list',
    'range',
    # 'vars',        # removed on 20180929 for 0 importance
    # 'classmethod', # removed on 20180929 for 0 importance
    'getattr',
    # 'locals',      # removed on 20180929 for 0 importance
    # 'repr',        # removed on 20180929 for improved accuracy
    'zip',
    # 'compile',     # removed on 20180929 for 0.0009% importance
    # 'globals',     # removed on 20180929 for 0 importance
    'map',
    # 'reversed',    # removed on 20180929 for 0 importance
    # '__import__',  # removed on 20180929 for 0 importance
    # 'complex',     # removed on 20180929 for 0 importance
    'hasattr',
    # 'max',         # removed on 20180929 for 0 importance
    # 'round'        # removed on 20180929 for improved accuracy
]
for i in IN_FUNCTION_SIGNATURE:
    @FeatureDefinition.register_feature_generator('in_function_' + i, True)
    def f(call_signatures, i=i, **_):
        if not call_signatures:
            return 0
        return int(call_signatures[0].name == i)

# TODO: use stack instead
MATCH_CURRENT_LINE = {
    'for': re.compile(r'^\s*for\s.*'),
    'while': re.compile(r'^\s*while\s.*'),
    'with': re.compile(r'^\s*with\s.*'),
    'if': re.compile(r'^\s*(if|elif)\s.*'),
    # 'try': re.compile(r'^\s*try\s.*'), # removed on 20180929 for 0 importance
    'except': re.compile(r'^\s*except\s.*'),
    'not': re.compile(r'.*\snot\s.*'),
}
for name, regex in MATCH_CURRENT_LINE.items():
    @FeatureDefinition.register_feature_generator(name, True)
    def f(line_content, regex=regex, **_):
        return 1 if regex.fullmatch(line_content) else 0
