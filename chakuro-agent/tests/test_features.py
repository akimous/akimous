from modeling import extract_features
from modeling.offline_feature_extractor import OfflineFeatureExtractor
import logzero
import logging

logzero.loglevel(logging.WARNING)
feature_extractor = OfflineFeatureExtractor()


def test_extract_feature():
    global df
    file = './tests/fixture/test1.py'
    extract_features.run_file(file, feature_extractor, silent=True, zero_length_prediction=True)
    feature_extractor.finalize()
    df = feature_extractor.dataframe()


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