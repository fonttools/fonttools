import pytest

from fontTools.misc.dictTools import hashdict


@pytest.mark.parametrize(
    "update",
    [
        {"wght": (0, 1)},
        {"wdth": (-1, 1)},
        [("wght", (0, 1))],
    ],
)
def test_inplace_union_cannot_change_dictionary_key(update):
    original = {"wght": (-1, 1)}
    key = hashdict(original)
    cache = {key: "cached box"}

    with pytest.raises(TypeError, match="does not support item assignment"):
        key |= update

    assert key == original
    assert cache[key] == "cached box"


def test_nonmutating_merges_preserve_dictionary_key():
    original = {"wght": (-1, 1)}
    key = hashdict(original)
    cache = {key: "cached box"}
    update = {"wdth": (0, 1)}
    expected = {"wght": (-1, 1), "wdth": (0, 1)}

    assert key | update == expected
    added = key + update
    assert isinstance(added, hashdict)
    assert added == expected
    assert key == original
    assert cache[key] == "cached box"
