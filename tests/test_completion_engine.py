from akimous.modeling.completion_engine import AttributeInferenceEngine


def test_digesting():
    engine = AttributeInferenceEngine()
    engine.digest('t1', 'a1')
    assert engine.infer('t1') == {'a1'}

    engine.digest('t2', 'a2')
    assert engine.infer('t2') == {'a2'}

    engine.digest('t2', 'a2')  # duplication should be ignored
    engine.digest('t2', 'a1')
    assert engine.infer('t2') == {'a1', 'a2'}

    engine.digest('t3', 'a2')
    assert engine.infer('t3') == {'a1', 'a2'}

    engine.digest('t3', 'a3')
    assert engine.infer('t3') == {'a1', 'a2', 'a3'}
    assert engine.infer('t2') == {'a1', 'a2', 'a3'}
    assert engine.infer('t1') == {'a1'}

    engine.digest('arr', 'shape')  # arr is np.ndarray
    assert 'ndim' in engine.infer('arr')

    engine.digest('arr', 'a3')
    assert engine.infer('arr') == {'a3'}

    engine.digest('lst', 'append')
    assert 'pop' in engine.infer('lst')
