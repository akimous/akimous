import lzma
from types import SimpleNamespace
from collections import OrderedDict
from tokenize import generate_tokens, TokenError
from io import StringIO

import msgpack

from modeling.token_map import TokenMap, DirtyMap
from modeling.utility import p, to_key_value_columns, working_dir

NOT_APPLICABLE = -99999
MAX = 99999
SIGMA_SCALING_FACTOR = 1000
UNIT_SCALING_FACTOR = 10000
EPSILON = .001
MAX_SCAN_LINES = 20
_EMPTY = tuple()


def _load_token_statistics(file_name):
    with lzma.open(working_dir / file_name, 'rb') as f:
        return msgpack.unpack(f, use_list=False, raw=False)


class FeatureDefinition:
    context_features = OrderedDict()
    preprocessors = []
    context_names_required_by_preprocessors = OrderedDict()
    token_features = OrderedDict()
    token_frequency = _load_token_statistics('token.msgpack.lzma')
    bigram_frequency = _load_token_statistics('bigram.msgpack.lzma')
    trigram_frequency = _load_token_statistics('trigram.msgpack.lzma')

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
            FeatureDefinition.context_names_required_by_preprocessors = OrderedDict(
                **FeatureDefinition.context_names_required_by_preprocessors,
                **context_names
            )
            return f

        return inner

    def __init__(self):
        self.context = SimpleNamespace()
        self.n_context_features = len(FeatureDefinition.context_features)
        self.n_token_features = len(FeatureDefinition.token_features)
        self.n_features = self.n_context_features + self.n_token_features

        self.name_to_feature_index = OrderedDict()
        self.normalization_source_feature_indice = []
        self.normalization_target_feature_indice = []
        for i, k in enumerate(FeatureDefinition.token_features.keys()):
            self.name_to_feature_index[k] = i
        for i, k in enumerate(FeatureDefinition.context_features.keys()):
            self.name_to_feature_index[k] = i + self.n_token_features
        p(to_key_value_columns(self.name_to_feature_index.keys(), self.name_to_feature_index.values()))

        for name in self.name_to_feature_index.keys():
            if 'normalized' in name:
                self.normalization_source_feature_indice.append(self.name_to_feature_index[name[:-len('_normalized')]])
                self.normalization_target_feature_indice.append(self.name_to_feature_index[name])
        p('Need normalization:', self.normalization_source_feature_indice, '=>',
          self.normalization_target_feature_indice)
        for k, v in FeatureDefinition.context_names_required_by_preprocessors.items():
            setattr(self.context, k, v)

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


@FeatureDefinition.register_context_preprocessor_for_token_features(
    doc_lines_to_lower_case={}
)
def f(doc, line, context, **_):
    context.doc_lines_to_lower_case = {}
    for l in range(0, min(line, MAX_SCAN_LINES)):
        context.doc_lines_to_lower_case[line - l] = doc[line - l].lower()


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
    line_to_tokens={},
    dirty_map=DirtyMap(),
    t1map=TokenMap(),
    t2map=TokenMap(),
    t3map=TokenMap(),
    trigram_map=TokenMap(),
)
def f(doc, context, line, ch, **_):
    dirty_map = context.dirty_map
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
        t1map.remove_line(line_number)
        t2map.remove_line(line_number)
        t3map.remove_line(line_number)
        trigram_map.remove_line(line_number)
        dirty_map.set_clear(line_number, line_content)

        tokens0 = line_to_tokens.get(line_number, _EMPTY)
        tokens1 = line_to_tokens.get(line_number - 1, _EMPTY)
        t1, t2, t3 = '', '', ''
        if tokens1:
            t2 = tokens1[-1]
            if len(tokens1) > 1:
                t3 = tokens1[-2]
        for token in tokens0:
            t0 = token.string
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
