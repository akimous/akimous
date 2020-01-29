from akimous.modeling.completion_engine import (AttributeInferenceEngine,
                                                CompletionEngine)


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


def test_learning():
    engine = AttributeInferenceEngine()
    engine.learn('a = b.c.d(e)')
    assert engine.infer('b') == {'c'}
    assert engine.infer('c') == {'d('}

    engine.learn('zero = self.one.two()')
    assert engine.infer('self') == {'one'}
    assert engine.infer('one') == {'two()'}

    engine.learn('zero = three.four')
    assert engine.infer('three') == {'four'}

    engine.learn('alpha[3 + 4].beta')
    assert engine.infer('alpha[]') == {'beta'}

    engine.learn('gamma(1, 2).delta')
    assert engine.infer('gamma()') == {'delta'}


def test_prediction():
    engine = AttributeInferenceEngine()
    engine.learn('    print(x.attribute)')
    assert engine.predict(2, 'x.')[0].name == 'attribute'


def test_completion_engine():
    engine = CompletionEngine('')
    engine.update(1, 'a="";a.')
    assert engine.complete(1, 7, 'a="";a.')[0].name == 'capitalize'

    engine.update(1, 'def f(x):')
    engine.update(2, '    print(x.attribute)')
    assert engine.complete(3, 6, '    x.')[0].name == 'attribute'

    assert engine.complete(4, 7, 'nothing') == []
