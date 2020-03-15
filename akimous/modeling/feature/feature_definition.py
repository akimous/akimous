import lzma
from collections import OrderedDict
from importlib.resources import open_binary
from io import StringIO
from token import NAME
from tokenize import TokenError, generate_tokens
from types import SimpleNamespace

import msgpack
import numpy as np

from ..token_map import DirtyMap, PrefixTokenMap, TokenMap
from ..utility import p, to_key_value_columns

NOT_APPLICABLE = -99999
MAX = 99999
UNIT_SCALING_FACTOR = 10000
EPSILON = .001
MAX_SCAN_LINES = 20
_EMPTY = tuple()


def _load_token_statistics(file_name):
    with open_binary('akimous.resources', file_name) as f1:
        with lzma.open(f1, 'rb') as f2:
            return msgpack.unpack(f2, use_list=False, raw=False, strict_map_key=False)


class FeatureDefinition:
    preprocessors = []
    context_features = OrderedDict()
    completion_features = OrderedDict()
    completion_feature_indices_require_normalization = []
    context_names_required_by_preprocessors = OrderedDict()

    token_frequency = _load_token_statistics('token.xz')
    bigram_frequency = _load_token_statistics('bigram.xz')
    trigram_frequency = _load_token_statistics('trigram.xz')

    @staticmethod
    def register_feature_generator(feature_name,
                                   is_context_feature=False,
                                   normalized=False):
        def inner(f):
            if is_context_feature:
                FeatureDefinition.context_features[feature_name] = f
                if normalized:
                    raise NotImplementedError
            else:
                FeatureDefinition.completion_features[feature_name] = f
                if normalized:
                    FeatureDefinition.completion_feature_indices_require_normalization.append(
                        len(FeatureDefinition.completion_features) - 1)
            return f

        return inner

    @staticmethod
    def register_context_preprocessor_for_token_features(**context_names):
        def inner(f):
            FeatureDefinition.preprocessors.append(f)
            FeatureDefinition.context_names_required_by_preprocessors = OrderedDict(
                **FeatureDefinition.context_names_required_by_preprocessors,
                **context_names)
            return f

        return inner

    def __init__(self):
        self.context = SimpleNamespace()
        self.n_context_features = len(FeatureDefinition.context_features)
        self.n_token_features = len(FeatureDefinition.completion_features)
        self.n_features = self.n_context_features + self.n_token_features
        self.normalized_features = np.array(
            FeatureDefinition.completion_feature_indices_require_normalization
        ) + self.n_context_features

        self.current_completion_start_index = 0
        self.n_samples = 0
        self.name_to_feature_index = OrderedDict()

        for i, k in enumerate(FeatureDefinition.completion_features.keys()):
            self.name_to_feature_index[k] = i
        for i, k in enumerate(FeatureDefinition.context_features.keys()):
            self.name_to_feature_index[k] = i + self.n_token_features
        p(
            to_key_value_columns(self.name_to_feature_index.keys(),
                                 self.name_to_feature_index.values()))

        for k, v in FeatureDefinition.context_names_required_by_preprocessors.items(
        ):
            setattr(self.context, k, v())

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
        if len(self.normalized_features) == 0:
            return
        data = self.X[self.current_completion_start_index:self.n_samples, self
                      .normalized_features]
        for i in range(data.shape[1]):
            column = data[:, i]
            minimum = column.min()
            maximum = column.max()
            if maximum - minimum < EPSILON:
                continue
            data[:, i] = UNIT_SCALING_FACTOR * (column - minimum) / (maximum -
                                                                     minimum)
        self.X[self.current_completion_start_index:self.n_samples, self
               .normalized_features] = data


# ch: 0-based
# line: 0-based


@FeatureDefinition.register_context_preprocessor_for_token_features(
    casefolded_doc_lines=dict)
def f(doc, line, context, **_):
    context.casefolded_doc_lines = {}
    for l in range(0, min(line, MAX_SCAN_LINES)):
        context.casefolded_doc_lines[line - l] = doc[line - l].casefold()


def tokenize(string):
    result = []
    try:
        for token in generate_tokens(StringIO(string).readline):
            if token.start == token.end:
                continue
            result.append(token)
    except (StopIteration, TokenError):
        pass
    return result


@FeatureDefinition.register_context_preprocessor_for_token_features(
    line_to_tokens=dict,
    dirty_map=DirtyMap,
    t0map=PrefixTokenMap,
    t1map=TokenMap,
    t2map=TokenMap,
    t3map=TokenMap,
    trigram_map=TokenMap,
)
def f(doc, context, line, ch, **_):
    dirty_map = context.dirty_map
    t0map = context.t0map
    t1map = context.t1map
    t2map = context.t2map
    t3map = context.t3map
    trigram_map = context.trigram_map
    line_to_tokens = context.line_to_tokens

    # tokenize dirty lines
    dirty_lines = dirty_map.get_dirty_lines(doc)
    for line_number in dirty_lines:
        line_to_tokens[line_number] = tokenize(doc[line_number])

    for line_number in dirty_lines:
        line_content = doc[line_number]
        for i in (t0map, t1map, t2map, t3map, trigram_map):
            i.remove_line(line_number)
        dirty_map.set_clear(line_number, line_content)

        tokens0 = line_to_tokens.get(line_number, _EMPTY)
        tokens1 = line_to_tokens.get(line_number - 1, _EMPTY)
        t1, t2, t3 = '', '', ''
        if tokens1:
            t2 = tokens1[-1].string.strip()
            if len(tokens1) > 1:
                t3 = tokens1[-2].string.strip()
        # leave t1 alone to indicate a line break
        for token in tokens0:
            t0 = token.string.strip()
            if token.type == NAME and len(t0) > 3:
                t0map.add(line_number, t0)
            t1map.add(line_number, (t1, t0))
            t2map.add(line_number, (t2, t0))
            t3map.add(line_number, (t3, t0))
            trigram_map.add(line_number, (t2, t1, t0))
            t3, t2, t1 = t2, t1, t0

    # get t1, t2
    tokens0 = line_to_tokens.get(line, _EMPTY)
    tokens1 = line_to_tokens.get(line - 1, _EMPTY)
    context.t1 = ''
    context.t2 = ''
    context.t3 = ''
    current_token_index = 0
    # t1
    if tokens0:
        for current_token_index, token in enumerate(tokens0):
            if token.end[1] >= ch + 1:
                break
        if current_token_index > 0:
            context.t1 = tokens0[current_token_index - 1].string
    # t2
    if current_token_index >= 2:
        context.t2 = tokens0[current_token_index - 2].string
    elif tokens1:
        context.t2 = tokens1[-1].string
    # t3
    if current_token_index >= 3:
        context.t3 = tokens0[current_token_index - 3].string
    elif len(tokens1) > 1:
        context.t3 = tokens1[-2].string
