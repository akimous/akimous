from pathlib import Path

from modeling import extract_features
from modeling.offline_feature_extractor import OfflineFeatureExtractor

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

