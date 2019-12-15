from akimous.modeling.token_map import DirtyMap, PrefixTokenMap, TokenMap


def test_dirty_map():
    d = DirtyMap()
    d.set_clear(1, 'a')
    d.set_clear(2, 'b')
    assert not d.is_dirty(1, 'a')
    assert d.is_dirty(1, 'b')
    assert d.is_dirty(3, 'a')
    assert d.get_dirty_lines(['', 'a', 'c']) == [2]

    d.set_clear(2, 'c')
    assert not d.is_dirty(2, 'c')
    assert not d.get_dirty_lines(['', 'a', 'c'])


def test_token_map():
    t = TokenMap()
    t.add(1, 'a')
    t.add(1, 'b')
    t.add(2, 'c')
    t.add(3, 'a')
    assert t.query('a') == {1, 3}
    assert t.query('c') == {2}
    assert t.query('not found') is None
    t.remove_line(1)
    assert t.query('a') == {3}


def test_prefix_token_map():
    p = PrefixTokenMap()
    p.add_many(1, ['ape', 'appear', 'apple'])
    p.add(2, 'apple')
    p.add(3, 'apple')
    p.add(4, 'banana')
    assert p.query_min('apple') == 1
    assert p.query_max('apple') == 3
    assert p.query_min_max('apple') == (1, 3)
    assert 'apple' in p.query_prefix('app', 1)
    assert 'appear' in p.query_prefix('app', 1)

    p.remove_line(1)
    assert p.query_min('apple') == 2
    p.remove_line(2)
    assert p.query_min('apple') == 3
    p = None
