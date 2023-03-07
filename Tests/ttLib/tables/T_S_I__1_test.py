from fontTools.misc.loggingTools import CapturingLogHandler
from fontTools.misc.textTools import tobytes
from fontTools.ttLib import TTFont, TTLibError
from fontTools.ttLib.tables.T_S_I__0 import table_T_S_I__0
from fontTools.ttLib.tables.T_S_I__1 import table_T_S_I__1
import pytest


TSI1_DATA = b"""abcdefghijklmnopqrstuvxywz0123456789"""
TSI1_UTF8_DATA = b"""abcd\xc3\xa9ghijklmnopqrstuvxywz0123456789"""


@pytest.fixture
def indextable():
    table = table_T_S_I__0()
    table.set(
        [
            (0, 1, 0),  # gid 0, length=1, offset=0, text='a'
            (1, 5, 1),  # gid 1, length=5, offset=1, text='bcdef'
            (2, 0, 1),  # gid 2, length=0, offset=1, text=''
            (3, 0, 1),  # gid 3, length=0, offset=1, text=''
            (4, 8, 6),
        ],  # gid 4, length=8, offset=6, text='ghijklmn'
        [
            (0xFFFA, 2, 14),  # 'ppgm', length=2, offset=14, text='op'
            (0xFFFB, 4, 16),  # 'cvt', length=4, offset=16, text='qrst'
            (0xFFFC, 6, 20),  # 'reserved', length=6, offset=20, text='uvxywz'
            (0xFFFD, 10, 26),
        ],  # 'fpgm', length=10, offset=26, text='0123456789'
    )
    return table


@pytest.fixture
def font(indextable):
    font = TTFont()
    # ['a', 'b', 'c', ...]
    ch = 0x61
    n = len(indextable.indices)
    font.glyphOrder = [chr(i) for i in range(ch, ch + n)]
    font["TSI0"] = indextable
    return font


@pytest.fixture
def empty_font():
    font = TTFont()
    font.glyphOrder = []
    indextable = table_T_S_I__0()
    indextable.set([], [(0xFFFA, 0, 0), (0xFFFB, 0, 0), (0xFFFC, 0, 0), (0xFFFD, 0, 0)])
    font["TSI0"] = indextable
    return font


def test_decompile(font):
    table = table_T_S_I__1()
    table.decompile(TSI1_DATA, font)

    assert table.glyphPrograms == {
        "a": "a",
        "b": "bcdef",
        # 'c': '',  # zero-length entries are skipped
        # 'd': '',
        "e": "ghijklmn",
    }
    assert table.extraPrograms == {
        "ppgm": "op",
        "cvt": "qrst",
        "reserved": "uvxywz",
        "fpgm": "0123456789",
    }


def test_decompile_utf8(font):
    table = table_T_S_I__1()
    table.decompile(TSI1_UTF8_DATA, font)

    assert table.glyphPrograms == {
        "a": "a",
        "b": "bcd\u00e9",
        # 'c': '',  # zero-length entries are skipped
        # 'd': '',
        "e": "ghijklmn",
    }
    assert table.extraPrograms == {
        "ppgm": "op",
        "cvt": "qrst",
        "reserved": "uvxywz",
        "fpgm": "0123456789",
    }


def test_decompile_empty(empty_font):
    table = table_T_S_I__1()
    table.decompile(b"", empty_font)

    assert table.glyphPrograms == {}
    assert table.extraPrograms == {}


def test_decompile_invalid_length(empty_font):
    empty_font.glyphOrder = ["a"]
    empty_font["TSI0"].indices = [(0, 0x8000 + 1, 0)]

    table = table_T_S_I__1()
    with pytest.raises(TTLibError) as excinfo:
        table.decompile(b"", empty_font)
    assert excinfo.match("textLength .* must not be > 32768")


def test_decompile_offset_past_end(empty_font):
    empty_font.glyphOrder = ["foo", "bar"]
    content = "baz"
    data = tobytes(content)
    empty_font["TSI0"].indices = [(0, len(data), 0), (1, 1, len(data) + 1)]

    table = table_T_S_I__1()
    with CapturingLogHandler(table.log, "WARNING") as captor:
        table.decompile(data, empty_font)

    # the 'bar' program is skipped because its offset > len(data)
    assert table.glyphPrograms == {"foo": "baz"}
    assert any("textOffset > totalLength" in r.msg for r in captor.records)


def test_decompile_magic_length_last_extra(empty_font):
    indextable = empty_font["TSI0"]
    indextable.extra_indices[-1] = (0xFFFD, 0x8000, 0)
    content = "0" * (0x8000 + 1)
    data = tobytes(content)

    table = table_T_S_I__1()
    table.decompile(data, empty_font)

    assert table.extraPrograms["fpgm"] == content


def test_decompile_magic_length_last_glyph(empty_font):
    empty_font.glyphOrder = ["foo", "bar"]
    indextable = empty_font["TSI0"]
    indextable.indices = [
        (0, 3, 0),
        (1, 0x8000, 3),
    ]  # the actual length of 'bar' program is
    indextable.extra_indices = [  # the difference between the first extra's
        (0xFFFA, 0, 0x8004),  # offset and 'bar' offset: 0x8004 - 3
        (0xFFFB, 0, 0x8004),
        (0xFFFC, 0, 0x8004),
        (0xFFFD, 0, 0x8004),
    ]
    foo_content = "0" * 3
    bar_content = "1" * (0x8000 + 1)
    data = tobytes(foo_content + bar_content)

    table = table_T_S_I__1()
    table.decompile(data, empty_font)

    assert table.glyphPrograms["foo"] == foo_content
    assert table.glyphPrograms["bar"] == bar_content


def test_decompile_magic_length_non_last(empty_font):
    indextable = empty_font["TSI0"]
    indextable.extra_indices = [
        (0xFFFA, 3, 0),
        (0xFFFB, 0x8000, 3),  # the actual length of 'cvt' program is:
        (0xFFFC, 0, 0x8004),  # nextTextOffset - textOffset: 0x8004 - 3
        (0xFFFD, 0, 0x8004),
    ]
    ppgm_content = "0" * 3
    cvt_content = "1" * (0x8000 + 1)
    data = tobytes(ppgm_content + cvt_content)

    table = table_T_S_I__1()
    table.decompile(data, empty_font)

    assert table.extraPrograms["ppgm"] == ppgm_content
    assert table.extraPrograms["cvt"] == cvt_content

    table = table_T_S_I__1()
    with CapturingLogHandler(table.log, "WARNING") as captor:
        table.decompile(data[:-1], empty_font)  # last entry is truncated
    captor.assertRegex("nextTextOffset > totalLength")
    assert table.extraPrograms["cvt"] == cvt_content[:-1]


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(sys.argv))
