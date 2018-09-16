from .feature_definition import FeatureDefinition
import re


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
    # 'delattr',
    'hash',
    # 'memoryview',
    'set',
    'all',
    'dict',
    # 'help',
    'min',
    'setattr',
    'any',
    # 'dir',
    # 'hex',
    'next',
    'slice',
    # 'ascii',
    # 'divmod',
    # 'id',
    # 'object',
    'sorted',
    # 'bin',
    'enumerate',
    # 'input',
    # 'oct',
    # 'staticmethod',
    'bool',
    # 'eval',
    'int',
    'open',
    'str',
    # 'breakpoint',
    # 'exec',
    'isinstance',
    # 'ord',
    'sum',
    # 'bytearray',
    'filter',
    'issubclass',
    # 'pow',
    'super',
    # 'bytes',
    # 'float',
    'iter',
    'print',
    'tuple',
    # 'callable',
    # 'format',
    'len',
    # 'property',
    'type',
    # 'chr',
    # 'frozenset',
    'list',
    'range',
    # 'vars',
    # 'classmethod',
    'getattr',
    # 'locals',
    # 'repr',
    'zip',
    # 'compile',
    # 'globals',
    'map',
    'reversed',
    # '__import__',
    # 'complex',
    'hasattr',
    'max',
    'round'
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
    'try': re.compile(r'^\s*try\s.*'),
    'except': re.compile(r'^\s*except\s.*'),
    'not': re.compile(r'.*\snot\s.*'),
}
for name, regex in MATCH_CURRENT_LINE.items():
    @FeatureDefinition.register_feature_generator(name, True)
    def f(line_content, regex=regex, **_):
        return 1 if regex.fullmatch(line_content) else 0
