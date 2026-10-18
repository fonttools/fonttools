from fontTools.misc.textTools import Tag, pad
import pytest


@pytest.mark.parametrize(
    "content, other, equal",
    [
        ("head", "head", True),
        ("head", b"head", True),
        ("head", Tag("head"), True),
        ("head", "name", False),
        ("head", b"name", False),
        ("head", Tag("name"), False),
        ("h\xe9ad", b"h\xe9ad", True),
        ("h\xe9ad", b"head", False),
    ],
)
def test_tag_comparison(content, other, equal):
    tag = Tag(content)
    assert (tag == other) is equal
    assert (other == tag) is equal
    assert (tag != other) is not equal
    assert (other != tag) is not equal


@pytest.mark.parametrize("other", [None, 0, object()])
def test_tag_unsupported_comparison(other):
    tag = Tag("head")
    assert tag.__eq__(other) is NotImplemented
    assert tag.__ne__(other) is NotImplemented
    assert (tag == other) is False
    assert (other == tag) is False
    assert (tag != other) is True
    assert (other != tag) is True


@pytest.mark.parametrize("equal", [False, True])
def test_tag_reflected_comparison(equal):
    class Comparable:
        def __eq__(self, other):
            return equal

        def __ne__(self, other):
            return not equal

    tag = Tag("head")
    other = Comparable()
    assert (tag == other) is equal
    assert (other == tag) is equal
    assert (tag != other) is not equal
    assert (other != tag) is not equal


def test_pad():
    assert len(pad(b"abcd", 4)) == 4
    assert len(pad(b"abcde", 2)) == 6
    assert len(pad(b"abcde", 4)) == 8
    assert pad(b"abcdef", 4) == b"abcdef\x00\x00"
    assert pad(b"abcdef", 1) == b"abcdef"
