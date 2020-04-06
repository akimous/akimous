import re
import token as token_

from fuzzywuzzy import fuzz

from .feature_definition import MAX, MAX_SCAN_LINES, FeatureDefinition

COMPLETION_TYPES = [
    'class',
    'function',
    'instance',
    'keyword',
    'module',
    'param',
    'statement'
]
for t in COMPLETION_TYPES:
    @FeatureDefinition.register_feature_generator(t)
    def f(completion, t=t, **_):
        return 1 if completion.type == t else 0

# TODO: type bi-gram, (name, type) and (type, name) bi-gram tuples
COMPLETION_DATA_TYPES = [
    'str', 'int', 'float', 'bool', 'bytes',
    'list', 'dict', 'tuple'
]
for t in COMPLETION_DATA_TYPES:
    @FeatureDefinition.register_feature_generator(t)
    def f(completion_data_type, t=t, **_):
        return int(completion_data_type == t)


@FeatureDefinition.register_feature_generator('is_upper_case')
def f(completion, **_):
    return int(completion.name.isupper())


@FeatureDefinition.register_feature_generator('is_lower_case')
def f(completion, **_):
    return int(completion.name.islower())


@FeatureDefinition.register_feature_generator('is_initial_upper_case')
def f(completion, **_):
    return int(completion.name[0].isupper())


CONTAINS_STRING = ['_']
for s in CONTAINS_STRING:
    @FeatureDefinition.register_feature_generator(f'contains_{s}')
    def f(completion, s=s, **_):
        return 1 if s in completion.name else 0

REGEX = {
    'is': re.compile(r'^(is|are|IS|ARE).*'),
    'has': re.compile(r'^(has|have|HAS|HAVE).*'),
    'error': re.compile(r'.*Error$'),
    'starts_with__': re.compile(r'^_.*'),
    'starts_with___': re.compile(r'^__.*'),
}
for name, regex in REGEX.items():
    @FeatureDefinition.register_feature_generator(f'regex_{name}')
    def f(completion, regex=regex, **_):
        return 1 if regex.fullmatch(completion.name) else 0

# from keyword.kwlist, total 33
KEYWORDS = (
    'False',
    'None',
    'True',
    'and',
    'as',
    'assert',
    'break',
    'class',
    'continue',
    'def',
    'del',
    'elif',
    'else',
    'except',
    # 'finally',  # removed on 20180930 for improved accuracy
    'for',
    'from',
    'global',
    'if',
    'import',
    'in',
    'is',
    'lambda',
    # 'nonlocal', # removed on 20180929 for improved accuracy
    'not',
    'or',
    'pass',
    'raise',
    'return',
    'try',
    'while',
    'with',
    # 'yield',    # removed on 20180929 for 0.0009% importance

    'abs',
    # 'hash',     # removed on 20180929 for improved accuracy
    'set',
    'all',
    'dict',
    'min',
    'setattr',
    # 'any',      # removed on 20180929 for improved accuracy
    # 'next',     # removed on 20180929 for improved accuracy
    'sorted',
    'enumerate',
    'bool',
    'int',
    'open',
    'str',
    'isinstance',
    'sum',
    'filter',
    'super',
    # 'iter',     # removed on 20180929 for 0.0007% importance
    'print',
    'tuple',
    # 'len',      # removed on 20180930 for improved accuracy
    'type',
    'list',
    'range',
    'getattr',    # removed on 20180930 for improved accuracy
    'zip',
    # 'map',      # removed on 20180929 for 0.0006% importance
    # 'reversed', # removed on 20180929 for improved accuracy
    'hasattr',
    'max',
    'round'
)
for keyword in KEYWORDS:
    @FeatureDefinition.register_feature_generator(f'kw_{keyword}')
    def f(completion, keyword=keyword, **_):
        return int(completion.name == keyword)


@FeatureDefinition.register_feature_generator('is_keyword')
def f(completion, **_):
    return int(completion.is_keyword)


@FeatureDefinition.register_feature_generator('in_builtin_module')
def f(completion, **_):
    return int(completion.in_builtin_module())


@FeatureDefinition.register_feature_generator('contains_in_nth_line')
def f(completion, doc, line, **_):
    completion = completion.name
    for l in range(0, min(line, MAX_SCAN_LINES)):
        if completion in doc[line - l]:
            return l
    return MAX


@FeatureDefinition.register_feature_generator('contains_in_nth_line_lower')
def f(completion, line, context, **_):
    completion = completion.name.casefold()
    doc = context.casefolded_doc_lines
    for l in range(0, min(line, MAX_SCAN_LINES)):
        if completion in doc[line - l]:
            return l
    return MAX


@FeatureDefinition.register_feature_generator('t1_match')
def f(context, line, completion, **_):
    bigram = (context.t1, completion.name)
    # min_line, max_line = context.t1map.query_min_max(bigram)
    # result = min(abs(min_line - line), abs(max_line - line))
    matched_line_numbers = context.t1map.query(bigram)
    if not matched_line_numbers:
        return MAX
    result = min(abs(l - line) for l in matched_line_numbers)
    return result


@FeatureDefinition.register_feature_generator('t2_match')
def f(context, line, completion, **_):
    if not context.t2:
        return MAX
    bigram = (context.t2, completion.name)
    matched_line_numbers = context.t2map.query(bigram)
    if not matched_line_numbers:
        return MAX
    result = min(abs(l - line) for l in matched_line_numbers)
    return result


@FeatureDefinition.register_feature_generator('t3_match')
def f(context, line, completion, **_):
    if not context.t3:
        return MAX
    bigram = (context.t3, completion.name)
    matched_line_numbers = context.t3map.query(bigram)
    if not matched_line_numbers:
        return MAX
    result = min(abs(l - line) for l in matched_line_numbers)
    return result


@FeatureDefinition.register_feature_generator('trigram_match')
def f(context, line, completion, **_):
    if not context.t2:
        return MAX
    trigram = (context.t2, context.t1, completion.name)
    matched_line_numbers = context.trigram_map.query(trigram)
    if not matched_line_numbers:
        return MAX
    result = min(abs(l - line) for l in matched_line_numbers)
    return result


@FeatureDefinition.register_feature_generator('first_token_ratio')
def f(context, line, ch, completion, **_):
    current_line_tokens = context.line_to_tokens[line]
    for token in current_line_tokens:
        if token.type in (token_.NAME, token_.STRING):
            first_token = token.string
            break
    else:
        return -1
    if ch < token.end[1]:
        return -2
    return fuzz.ratio(first_token, completion.name)


@FeatureDefinition.register_feature_generator('first_token_partial_ratio')
def f(context, line, ch, completion, **_):
    current_line_tokens = context.line_to_tokens[line]
    for token in current_line_tokens:
        if token.type in (token_.NAME, token_.STRING):
            first_token = token.string
            break
    else:
        return -1
    if ch < token.end[1]:
        return -2
    return fuzz.partial_ratio(first_token.casefold(), completion.name.casefold())


@FeatureDefinition.register_feature_generator('last_line_first_token_ratio')
def f(context, line, completion, **_):
    try:
        current_line_tokens = context.line_to_tokens[line - 1]
    except KeyError:
        return -1
    first_token = ''
    for token in current_line_tokens:
        if token.type in (token_.NAME, token_.STRING):
            first_token = token.string
            break
    return fuzz.ratio(first_token, completion.name)


@FeatureDefinition.register_feature_generator('last_line_first_token_partial_ratio')
def f(context, line, completion, **_):
    try:
        current_line_tokens = context.line_to_tokens[line - 1]
    except KeyError:
        return -1
    first_token = ''
    for token in current_line_tokens:
        if token.type in (token_.NAME, token_.STRING):
            first_token = token.string
            break
    return fuzz.partial_ratio(first_token.casefold(), completion.name.casefold())


@FeatureDefinition.register_feature_generator('last_n_lines_first_token_partial_ratio')
def f(context, line, completion, **_):
    result = -1
    for l in range(line - 2, max(-1, line - 7), -1):
        try:
            current_line_tokens = context.line_to_tokens[l]
        except KeyError:
            continue
        first_token = ''
        for token in current_line_tokens:
            if token.type == token_.NAME:
                first_token = token.string
                break
        result = max(result, fuzz.partial_ratio(first_token.casefold(), completion.name.casefold()))
    return result


@FeatureDefinition.register_feature_generator('all_token_ratio')
def f(context, line, ch, completion, **_):
    current_line_tokens = context.line_to_tokens[line]
    result = -1
    for token in current_line_tokens:
        if token.start[1] <= ch < token.end[1]:
            continue
        if token.type in (token_.NAME, token_.STRING):
            result = max(result, fuzz.ratio(token.string, completion.name))
    return result


@FeatureDefinition.register_feature_generator('last_line_all_token_ratio')
def f(context, line, completion, **_):
    try:
        current_line_tokens = context.line_to_tokens[line - 1]
    except KeyError:
        return -1
    result = -1
    for token in current_line_tokens:
        if token.type in (token_.NAME, token_.STRING):
            result = max(result, fuzz.ratio(token.string, completion.name))
    return result


_token_frequency = FeatureDefinition.token_frequency
_bigram_frequency = FeatureDefinition.bigram_frequency
_trigram_frequency = FeatureDefinition.trigram_frequency


@FeatureDefinition.register_feature_generator('token_frequency')
def f(completion, **_):
    return _token_frequency.get(completion.name, 0)


@FeatureDefinition.register_feature_generator('bigram_frequency')
def f(completion, context, **_):
    if not context.t1:
        return 0
    bigram = (context.t1, completion.name)
    return _bigram_frequency.get(bigram, 0)


@FeatureDefinition.register_feature_generator('trigram_frequency')
def f(completion, context, **_):
    if not context.t2 or not context.t1:
        return 0
    trigram = (context.t2, context.t1, completion.name)
    return _trigram_frequency.get(trigram, 0)


@FeatureDefinition.register_feature_generator('signature_parameter_ratio')
def f(completion, call_signatures, **_):
    if not call_signatures:
        return -1
    cs = call_signatures[0]
    index = cs.index
    if index is None:
        return -2
    parameter = cs.params[index].name
    return fuzz.ratio(completion.name, parameter)


@FeatureDefinition.register_feature_generator('signature_parameter_partial_ratio')
def f(completion, call_signatures, **_):
    if not call_signatures:
        return -1
    cs = call_signatures[0]
    index = cs.index
    if index is None:
        return -2
    parameter = cs.params[index].name
    return fuzz.partial_ratio(completion.name.casefold(), parameter.casefold())


@FeatureDefinition.register_feature_generator('function_ratio')
def f(completion, call_signatures, **_):
    if not call_signatures:
        return -1
    function_name = call_signatures[0].name
    return fuzz.ratio(completion.name, function_name)


@FeatureDefinition.register_feature_generator('function_partial_ratio')
def f(completion, call_signatures, **_):
    if not call_signatures:
        return -1
    function_name = call_signatures[0].name
    return fuzz.partial_ratio(completion.name, function_name)
