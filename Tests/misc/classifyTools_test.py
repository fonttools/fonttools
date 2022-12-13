from fontTools.misc.classifyTools import classify


def test_classify():
    assert classify([]) == ([], {})
    assert classify([[]]) == ([], {})
    assert classify([[], []]) == ([], {})
    assert classify([[1]]) == ([{1}], {1: {1}})
    assert classify([[1, 2]]) == ([{1, 2}], {1: {1, 2}, 2: {1, 2}})
    assert classify([[1], [2]]) == ([{1}, {2}], {1: {1}, 2: {2}})
    assert classify([[1, 2], [2]]) == ([{1}, {2}], {1: {1}, 2: {2}})
    assert classify([[1, 2], [2, 4]]) == ([{1}, {2}, {4}], {1: {1}, 2: {2}, 4: {4}})
    assert classify([[1, 2], [2, 4, 5]]) == (
        [{4, 5}, {1}, {2}],
        {1: {1}, 2: {2}, 4: {4, 5}, 5: {4, 5}},
    )
    assert classify([[1, 2], [2, 4, 5]], sort=False) == (
        [{1}, {4, 5}, {2}],
        {1: {1}, 2: {2}, 4: {4, 5}, 5: {4, 5}},
    )
    assert classify([[1, 2, 9], [2, 4, 5]], sort=False) == (
        [{1, 9}, {4, 5}, {2}],
        {1: {1, 9}, 2: {2}, 4: {4, 5}, 5: {4, 5}, 9: {1, 9}},
    )
    assert classify([[1, 2, 9, 15], [2, 4, 5]], sort=False) == (
        [{1, 9, 15}, {4, 5}, {2}],
        {1: {1, 9, 15}, 2: {2}, 4: {4, 5}, 5: {4, 5}, 9: {1, 9, 15}, 15: {1, 9, 15}},
    )
    classes, mapping = classify([[1, 2, 9, 15], [2, 4, 5], [15, 5]], sort=False)
    assert set([frozenset(c) for c in classes]) == set(
        [frozenset(s) for s in ({1, 9}, {4}, {2}, {5}, {15})]
    )
    assert mapping == {1: {1, 9}, 2: {2}, 4: {4}, 5: {5}, 9: {1, 9}, 15: {15}}
