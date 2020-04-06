import logging

import logzero

from akimous.modeling import extract_features
from akimous.modeling.offline_feature_extractor import OfflineFeatureExtractor

logzero.loglevel(logging.WARNING)
feature_extractor = OfflineFeatureExtractor()


def test_extract_feature():
    global df
    file = './tests/fixture/test1.py'
    extract_features.run_file(file, feature_extractor, silent=True, zero_length_prediction=True)
    feature_extractor.finalize()
    df = feature_extractor.dataframe()
    print(df.shape)


def get_index_range_at_token(line, ch, name):
    start_index = None
    start_position = None
    for i, token in enumerate(feature_extractor.tokens):
        if start_index is not None and token.start != start_position:
            return start_index, i
        if start_index is None and token.end > (line, ch):
            start_index = i
            start_position = token.start
            assert token.string == name


def get_completion(line, ch, name, completion=None):
    if completion is None:
        completion = name
    start, end = get_index_range_at_token(line, ch, name)
    view = df[start:end]
    for i, completion_name in enumerate(view['c']):
        if completion_name == completion:
            break
    return view.iloc[i]


def test_get_completion():
    assert get_completion(1, 1, 'def')['c'] == 'def'
    assert get_completion(2, 7, 'pass')['c'] == 'pass'


def test_completion_types():
    assert get_completion(5, 3, 'weights').function == 1


def test_completion_data_type():
    assert get_completion(7, 16, 'integer_1').int == 1


def test_is_upper_case():
    assert get_completion(7, 16, 'integer_1').is_upper_case == 0
    assert get_completion(9, 4, 'UPPER').is_upper_case == 1
    assert get_completion(16, 8, 'Dog').is_upper_case == 0


def test_is_lower_case():
    assert get_completion(7, 16, 'integer_1').is_lower_case == 1
    assert get_completion(9, 4, 'UPPER').is_lower_case == 0
    assert get_completion(16, 8, 'Dog').is_lower_case == 0


def test_is_initial_upper_case():
    assert get_completion(16, 8, 'Dog').is_initial_upper_case == 1
    assert get_completion(7, 16, 'integer_1').is_initial_upper_case == 0


def test_contains__():
    assert get_completion(5, 0, 'weights').contains__ == 0
    assert get_completion(7, 6, 'integer_1').contains__ == 1


def test_regex():
    assert get_completion(21, 4, 'is_good').regex_is == 1
    assert get_completion(21, 4, 'is_good').regex_has == 0

    assert get_completion(21, 16, 'have_fun').regex_has == 1
    assert get_completion(21, 16, 'have_fun').regex_is == 0

    assert get_completion(24, 15, 'ValueError').regex_error == 1
    assert get_completion(21, 16, 'have_fun').regex_error == 0

    assert get_completion(22, 5, '_underscore').regex_starts_with__ == 1
    assert get_completion(21, 4, 'is_good').regex_starts_with__ == 0

    assert get_completion(22, 5, '_underscore').regex_starts_with___ == 0
    assert get_completion(22, 20, '__dunder').regex_starts_with___ == 1


def test_keywords():
    assert get_completion(2, 7, 'pass').kw_pass == 1
    assert get_completion(2, 7, 'pass').kw_def == 0
    assert get_completion(19, 0, 'def').kw_pass == 0
    assert get_completion(19, 0, 'def').kw_def == 1
    assert get_completion(21, 4, 'is_good').kw_def == 0


def test_is_keywords():
    assert get_completion(2, 7, 'pass').is_keyword == 1
    assert get_completion(21, 4, 'is_good').is_keyword == 0


def test_in_builtin_module():
    assert get_completion(2, 7, 'pass').in_builtin_module == 1
    assert get_completion(24, 15, 'ValueError').in_builtin_module == 1
    assert get_completion(21, 4, 'is_good').in_builtin_module == 0


def test_blank_line_before():
    assert get_completion(19, 0, 'def').blank_line_before == 2


def test_line_number():
    assert get_completion(19, 0, 'def').line_number == 18


def test_indent():
    assert get_completion(19, 0, 'def').indent == 0
    assert get_completion(2, 7, 'pass').indent == 4
    assert get_completion(24, 15, 'ValueError').indent == 8


def test_indent_delta():
    assert get_completion(19, 0, 'def').indent_delta == 0
    assert get_completion(21, 4, 'is_good').indent_delta == 0
    assert get_completion(21, 16, 'have_fun').indent_delta == 0
    assert get_completion(24, 15, 'ValueError').indent_delta == 4
    assert get_completion(16, 7, 'Dog').indent_delta == -4


def test_at_line_start():
    assert get_completion(19, 0, 'def').at_line_start == 1
    assert get_completion(21, 4, 'is_good').at_line_start == 1
    assert get_completion(21, 16, 'have_fun').at_line_start == 0
    assert get_completion(24, 9, 'raise').at_line_start == 1


def test_left_char_is():
    assert get_completion(26, 9, 'integer_1')['left_char_is_('] == 1
    assert get_completion(26, 9, 'integer_1')['left_char_is_['] == 0
    assert get_completion(21, 16, 'have_fun')['left_char_is_='] == 1
    assert get_completion(26, 20, 'integer_2')['left_char_is_,'] == 1


def test_in_builtin_function():
    assert get_completion(27, 6, 'integer_2').in_function_bool == 1
    assert get_completion(27, 6, 'integer_2').in_function_len == 0


def test_match_current_line():
    assert get_completion(23, 12, 'True')['if'] == 1
    assert get_completion(22, 5, '_underscore')['if'] == 0
    assert get_completion(23, 4, 'if')['if'] == 0
    assert get_completion(23, 12, 'True')['not'] == 1
    assert get_completion(22, 5, '_underscore')['not'] == 0


def test_contains_in_nth_line():
    assert get_completion(26, 9, 'integer_1').contains_in_nth_line == 19
    assert get_completion(27, 6, 'integer_2').contains_in_nth_line == 1
    assert get_completion(12, 1, 'class').contains_in_nth_line == 99999
    assert get_completion(47, 62, 'kernel_regularizer').contains_in_nth_line == 0


def test_contains_in_nth_line_lower():
    assert get_completion(26, 9, 'integer_1').contains_in_nth_line_lower == 19
    assert get_completion(27, 6, 'integer_2').contains_in_nth_line_lower == 1
    assert get_completion(12, 1, 'class').contains_in_nth_line_lower == 99999
    assert get_completion(16, 7, 'Dog').contains_in_nth_line_lower == 0


def test_t1_match():
    assert get_completion(30, 27, 'integer_2').t1_match == 4
    assert get_completion(27, 6, 'integer_2').t1_match == 99999


def test_t2_match():
    assert get_completion(29, 13, 'integer_1').t2_match == 22
    assert get_completion(29, 1, 'integer_2').t2_match == 99999


def test_t3_match():
    assert get_completion(29, 13, 'integer_1').t3_match == 99999
    assert get_completion(29, 1, 'integer_2').t3_match == 99999
    assert get_completion(31, 26, 'integer_2').t3_match == 1


def test_trigram_match():
    assert get_completion(30, 27, 'integer_2').trigram_match == 4
    assert get_completion(31, 26, 'integer_2').trigram_match == 1


def test_last_line_ends_with():
    assert get_completion(35, 5, 'def')['last_line_ends_with_:'] == 1
    assert get_completion(9, 4, 'UPPER')['last_line_ends_with_:'] == 0


def test_first_token_ratio():
    assert get_completion(22, 20, '__dunder').first_token_ratio == 63
    assert get_completion(35, 5, 'def').first_token_ratio == -2


def test_first_token_partial_ratio():
    assert get_completion(22, 20, '__dunder').first_token_partial_ratio == 75
    assert get_completion(35, 5, 'def').first_token_partial_ratio == -2
    assert get_completion(45, 15, 'Placeholder').first_token_partial_ratio == 100
    assert get_completion(47, 27, 'regularizers').first_token_partial_ratio == 92


def test_last_line_first_token_ratio():
    assert get_completion(21, 4, 'is_good').last_line_first_token_ratio == 100
    assert get_completion(1, 1, 'def').last_line_first_token_ratio == -1
    assert get_completion(47, 27, 'regularizers').last_line_first_token_ratio == 0


def test_last_line_first_token_partial_ratio():
    assert get_completion(21, 4, 'is_good').last_line_first_token_partial_ratio == 100
    assert get_completion(1, 1, 'def').last_line_first_token_partial_ratio == -1
    assert get_completion(47, 27, 'regularizers').last_line_first_token_partial_ratio == 0
    assert get_completion(45, 15, 'Placeholder').last_line_first_token_partial_ratio == 36


def test_last_n_lines_first_token_partial_ratio():
    assert get_completion(47, 27, 'regularizers').last_n_lines_first_token_partial_ratio == 100


def test_all_token_ratio():
    assert get_completion(48, 47, 'kernel_regularizer').all_token_ratio == 73


def test_last_line_all_token_ratio():
    assert get_completion(48, 12, 'regularizers').last_line_all_token_ratio == 100
    assert get_completion(22, 20, '__dunder').last_line_all_token_ratio == 38


def test_token_frequency():
    def_freq = get_completion(35, 5, 'def').token_frequency
    class_freq = get_completion(12, 1, 'class').token_frequency
    dog_freq = get_completion(16, 7, 'Dog').token_frequency
    assert def_freq > class_freq
    assert def_freq > dog_freq


def test_bigram_frequency():
    def_init = get_completion(40, 9, '__init__').bigram_frequency
    if_not = get_completion(23, 8, 'not').bigram_frequency
    raise_value_error = get_completion(24, 15, 'ValueError').bigram_frequency
    assert if_not > def_init
    assert if_not > raise_value_error


def test_trigram_frequency():
    # TODO: add test
    pass


def test_signature_parameter_matching():
    assert get_completion(56, 39, 'regularizers').signature_parameter_ratio == 91
    assert get_completion(56, 53, 'placeholder').signature_parameter_ratio == 53
    assert get_completion(56, 39, 'regularizers').signature_parameter_partial_ratio == 100
    assert get_completion(56, 53, 'placeholder').signature_parameter_partial_ratio == 100


def test_function_ratio():
    assert get_completion(60, 11, 'string').function_ratio == 67
    assert get_completion(60, 11, 'string').function_partial_ratio == 100
