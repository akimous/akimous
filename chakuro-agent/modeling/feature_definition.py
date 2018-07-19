import numpy as np
import pandas as pd
import re
import Levenshtein
from contextlib import suppress
from fuzzywuzzy import fuzz
from tokenize import generate_tokens, TokenError
from io import StringIO
from token_map import TokenMap

NOT_APPLICABLE = -99999
MAX = 99999
SIGMA_SCALING_FACTOR = 1000
UNIT_SCALING_FACTOR = 10000
EPSILON = .001
MAX_SCAN_LINES = 20


class FeatureDefinition:
    context_features = {}
    preprocessors = []
    context_names_required_by_preprocessors = {}
    token_features = {}

    @staticmethod
    def register_feature_generator(feature_name, is_context_feature=False):
        def inner(f):
            if is_context_feature:
                FeatureDefinition.context_features[feature_name] = f
            else:
                FeatureDefinition.token_features[feature_name] = f
            return f

        return inner

    @staticmethod
    def register_context_preprocessor_for_token_features(**context_names):
        def inner(f):
            FeatureDefinition.preprocessors.append(f)
            FeatureDefinition.context_names_required_by_preprocessors = {
                **FeatureDefinition.context_names_required_by_preprocessors,
                **context_names
            }
            return f

        return inner

    def __init__(self):
        self.n_context_features = len(FeatureDefinition.context_features)
        self.n_token_features = len(FeatureDefinition.token_features)
        self.n_features = self.n_context_features + self.n_token_features
        # self.stack_context_info = self.get_stack_context_info(None)

        self.name_to_feature_index = {}
        self.normalization_source_feature_indice = []
        self.normalization_target_feature_indice = []
        for i, k in enumerate(FeatureDefinition.token_features.keys()):
            self.name_to_feature_index[k] = i
        for i, k in enumerate(FeatureDefinition.context_features.keys()):
            self.name_to_feature_index[k] = i + self.n_token_features
        print(self.name_to_feature_index)

        for name in self.name_to_feature_index.keys():
            if 'normalized' in name:
                self.normalization_source_feature_indice.append(self.name_to_feature_index[name[:-len('_normalized')]])
                self.normalization_target_feature_indice.append(self.name_to_feature_index[name])
        print('Need normalization:', self.normalization_source_feature_indice, '=>',
              self.normalization_target_feature_indice)

    # def get_stack_context_info(self, completion):
    #     '''
    #     Example:
    #     Code: ```def aaa(): pass
    #     def func(bbb='ccc'):
    #         ddd = aaa(bbb)
    #         eee = func(bbb=
    #     ```
    #     Stack:
    #     [<Name: eee@1,0>,  # top_name
    #      <Operator: =>,
    #      <Name: func@1,6>, # func_name
    #      <Operator: (>,
    #      <Name: bbb@1,11>, # bottom_name
    #      <Operator: =>]
    #     '''
    #
    #     result = {
    #         'top_name': None,
    #         'func_name': None,
    #         'bottom_name': None,
    #         'is_bottom_equal_sign': False,
    #         # 'top==func': True,
    #         # 'func==bottom': True
    #     }
    #     if not completion or not completion._stack:
    #         return result
    #     completion._stack
    #     stack = list(completion._stack.get_nodes())
    #     if not stack:
    #         return result
    #
    #     for node in stack:
    #         with suppress(AttributeError):
    #             if node.type == 'name':
    #                 result['top_name'] = node.value
    #                 break
    #
    #     for i in range(len(stack) - 1):
    #         with suppress(AttributeError):
    #             if stack[i + 1].value == '(' and stack[i].type == 'name':
    #                 result['func_name'] = stack[i].value
    #                 break
    #
    #     for node in reversed(stack):
    #         with suppress(AttributeError):
    #             if node.type == 'name':
    #                 result['bottom_name'] = node.value
    #                 break
    #
    #     with suppress(AttributeError):
    #         if stack[-1].value == '=':
    #             result['is_bottom_equal_sign'] = True
    #
    #     return result

    def normalize_feature(self):
        data = self.X[self.current_completion_start_index:self.n_samples,
               self.normalization_source_feature_indice]
        for i in range(data.shape[1]):
            column = data[:, i]
            mask = column > NOT_APPLICABLE
            if mask.sum() == 0: continue
            masked_values = column[mask]
            std = masked_values.std()
            if std < EPSILON: continue
            data[mask, i] = (masked_values - masked_values.mean()) / masked_values.std() * SIGMA_SCALING_FACTOR

        self.X[self.current_completion_start_index:self.n_samples,
        self.normalization_target_feature_indice] = data


# ch: 0-based
# line: 0-based


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
    return 1 if completion.name.isupper() else 0


@FeatureDefinition.register_feature_generator('is_lower_case')
def f(completion, **_):
    return 1 if completion.name.islower() else 0


@FeatureDefinition.register_feature_generator('is_initial_upper_case')
def f(completion, **_):
    return 1 if completion.name[0].isupper() else 0


CONTAINS_STRING = ['_']
for s in CONTAINS_STRING:
    @FeatureDefinition.register_feature_generator('contains_' + s)
    def f(completion, s=s, **_):
        return 1 if s in completion.name else 0

REGEX = {
    'is': re.compile(r'^(is|are|IS|ARE).*'),
    'has': re.compile(r'^(has|have|HAS|HAVE).*'),
    'error': re.compile(r'.*Error$')
}
for name, regex in REGEX.items():
    @FeatureDefinition.register_feature_generator(name)
    def f(completion, regex=regex, **_):
        return 1 if regex.fullmatch(completion.name) else 0


KEYWORDS = (
    'not', 'None', 'self', 'super', 'if', 'else', 'elif', 'return',
    'del', 'def', 'raise', 'import', 'from', 'as', 'break', 'continue'
)
for keyword in KEYWORDS:
    @FeatureDefinition.register_feature_generator('is_' + keyword)
    def f(completion, keyword=keyword, **_):
        return int(completion.name == keyword)


@FeatureDefinition.register_feature_generator('in_builtin_module')
def f(completion, **_):
    return int(completion.in_builtin_module())


@FeatureDefinition.register_feature_generator('is_keyword')
def f(completion, **_):
    return int(completion.is_keyword)


@FeatureDefinition.register_feature_generator('blank_line_before', True)
def f(line, doc, **_):
    count = 0
    for i in range(line - 1, 0, -1):
        if not doc[line - 1].lstrip():
            count += 1
        else:
            return count
    return count


# @FeatureDefinition.register_feature_generator('indent_level', True)
# def f(line_content, **_):
#     return (len(line_content) - len(line_content.lstrip())) // 4


@FeatureDefinition.register_feature_generator('at_line_start', True)
def f(line_content, ch, **_):
    head = line_content[:ch].lstrip()
    return 0 if head else 1


LEFT_CHAR = ['(', '[', '{']
for c in LEFT_CHAR:
    @FeatureDefinition.register_feature_generator('left_char_is_' + c, True)
    def f(line_content, ch, c=c, **_):
        return int(line_content[ch - len(c):ch] == c)

# TODO: add popular build-in functions
IN_FUNCTION_SIGNATURE = ['range', 'isinstance', 'len', 'type']
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


@FeatureDefinition.register_feature_generator('contains_in_nth_line')
def f(completion, doc, line, **_):
    completion = completion.name
    for l in range(0, min(line, MAX_SCAN_LINES)):
        if completion in doc[line - l]:
            return l
    return MAX


@FeatureDefinition.register_context_preprocessor_for_token_features(
    doc_lines_to_lower_case={}
)
def f(doc, line, context, **_):
    context.doc_lines_to_lower_case = {}
    for l in range(0, min(line, MAX_SCAN_LINES)):
        context.doc_lines_to_lower_case[line - l] = doc[line - l].lower()


@FeatureDefinition.register_feature_generator('contains_in_nth_line_lower')
def f(completion, line, context, **_):
    completion = completion.name.lower()
    doc = context.doc_lines_to_lower_case
    for l in range(0, min(line, MAX_SCAN_LINES)):
        if completion in doc[line - l]:
            return l
    return MAX


@FeatureDefinition.register_context_preprocessor_for_token_features(bigram=TokenMap())
def f(doc, context, line, ch, **_):
    context.line_tokens = []
    context.t1 = ''
    bigram = context.bigram
    line_tokens = context.line_tokens

    for line_number, line_content in enumerate(doc):
        if bigram.dirty(line_number, line_content):
            bigram.remove_line(line_number)
            # tokens = tokenize(BytesIO(line_content.encode('utf-8')).readline)
            tokens = generate_tokens(StringIO(line_content).readline)
            try:
                last_token = ''
                for token in tokens:
                    if token.start == token.end:
                        continue
                    t = token.string
                    bigram.add(line_number, line_content, (last_token, t))
                    last_token = t

                    if line == line_number:
                        line_tokens.append(token)
            except (StopIteration, TokenError):
                pass
    try:
        # for token in tokenize(BytesIO(doc[line].encode('utf-8')).readline):
        for token in generate_tokens(StringIO(doc[line]).readline):
            if token.start == token.end:
                continue
            line_tokens.append(token)
    except (StopIteration, TokenError):
        pass
    if line_tokens:
        current_token_index = 0
        for current_token_index, token in enumerate(context.line_tokens):
            if token.end[1] == ch + 1:
                break
        if current_token_index > 0:
            context.t1 = context.line_tokens[current_token_index - 1].string


@FeatureDefinition.register_feature_generator('bigram_distance')
def f(context, line, completion, **_):
    completed_bigram = (context.t1, completion.name)
    matched_line_numbers = context.bigram.query(completed_bigram)
    if not matched_line_numbers:
        return MAX
    result = min(abs(l-line) for l in matched_line_numbers)
    # print(line_content, completed_bigram, result)
    return result

# @FeatureDefinition.register_feature_generator('contains_in_line')
# def f(completion, line_content, **_):
#     completion = completion.name
#     if completion in line_content:
#         return 1
#     return 0
#
#
# @FeatureDefinition.register_feature_generator('contains_in_line_lower')
# def f(completion, line_content, **_):
#     completion = completion.name.lower()
#     if completion in line_content.lower():
#         return 1
#     return 0

# for comparison_target in ['top_name', 'func_name', 'bottom_name']:
#     for distance_name in ['Leven', 'Jaro']:
#         @FeatureDefinition.register_feature_generator(f'{comparison_target}_{distance_name}')
#         def f(completion, stack_context_info, comparison_target=comparison_target,
#               distance_name=distance_name, **_):
#             target = stack_context_info[comparison_target]
#             if not target:
#                 return NOT_APPLICABLE
#             if distance_name == 'Leven':
#                 return -Levenshtein.distance(completion.name, target)
#             if distance_name == 'Jaro':
#                 return int(Levenshtein.jaro(completion.name, target) * UNIT_SCALING_FACTOR)
#
#
#         @FeatureDefinition.register_feature_generator(f'{comparison_target}_{distance_name}_normalized')
#         def f(**_):
#             return NOT_APPLICABLE
