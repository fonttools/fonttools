from __future__ import absolute_import, unicode_literals
import sys
import os
import datetime
import codecs
import collections
from io import BytesIO
from numbers import Integral
from fontTools.misc.py23 import tounicode, unicode
from fontTools.misc import etree
from fontTools.misc import plistlib
from fontTools.ufoLib.plistlib import (
    readPlist, readPlistFromString, writePlist, writePlistToString,
)
import pytest

try:
    from collections.abc import Mapping # python >= 3.3
except ImportError:
    from collections import Mapping

PY2 = sys.version_info < (3,)
if PY2:
    # This is a ResourceWarning that only happens on py27 at interpreter
    # finalization, and only when coverage is enabled. We can ignore it.
    # https://github.com/numpy/numpy/issues/3778#issuecomment-24885336
    pytestmark = pytest.mark.filterwarnings(
        "ignore:tp_compare didn't return -1 or -2 for exception"
    )

# The testdata is generated using https://github.com/python/cpython/...
# Mac/Tools/plistlib_generate_testdata.py
# which uses PyObjC to control the Cocoa classes for generating plists
datadir = os.path.join(os.path.dirname(__file__), "testdata")
with open(os.path.join(datadir, "test.plist"), "rb") as fp:
    TESTDATA = fp.read()


def _test_pl(use_builtin_types):
    DataClass = bytes if use_builtin_types else plistlib.Data
    pl = dict(
        aString="Doodah",
        aList=["A", "B", 12, 32.5, [1, 2, 3]],
        aFloat=0.5,
        anInt=728,
        aBigInt=2 ** 63 - 44,
        aBigInt2=2 ** 63 + 44,
        aNegativeInt=-5,
        aNegativeBigInt=-80000000000,
        aDict=dict(
            anotherString="<hello & 'hi' there!>",
            aUnicodeValue="M\xe4ssig, Ma\xdf",
            aTrueValue=True,
            aFalseValue=False,
            deeperDict=dict(a=17, b=32.5, c=[1, 2, "text"]),
        ),
        someData=DataClass(b"<binary gunk>"),
        someMoreData=DataClass(b"<lots of binary gunk>\0\1\2\3" * 10),
        nestedData=[DataClass(b"<lots of binary gunk>\0\1\2\3" * 10)],
        aDate=datetime.datetime(2004, 10, 26, 10, 33, 33),
        anEmptyDict=dict(),
        anEmptyList=list(),
    )
    pl["\xc5benraa"] = "That was a unicode key."
    return pl


@pytest.fixture
def pl():
    return _test_pl(use_builtin_types=True)


@pytest.fixture
def pl_no_builtin_types():
    return _test_pl(use_builtin_types=False)


@pytest.fixture(
    params=[True, False],
    ids=["builtin=True", "builtin=False"],
)
def use_builtin_types(request):
    return request.param


@pytest.fixture
def parametrized_pl(use_builtin_types):
    return _test_pl(use_builtin_types), use_builtin_types


def test__test_pl():
    # sanity test that checks that the two values are equivalent
    # (plistlib.Data implements __eq__ against bytes values)
    pl = _test_pl(use_builtin_types=False)
    pl2 = _test_pl(use_builtin_types=True)
    assert pl == pl2


def test_io(tmpdir, parametrized_pl):
    pl, use_builtin_types = parametrized_pl
    testpath = tmpdir / "test.plist"
    with testpath.open("wb") as fp:
        plistlib.dump(pl, fp, use_builtin_types=use_builtin_types)

    with testpath.open("rb") as fp:
        pl2 = plistlib.load(fp, use_builtin_types=use_builtin_types)

    assert pl == pl2

    with pytest.raises(AttributeError):
        plistlib.dump(pl, "filename")

    with pytest.raises(AttributeError):
        plistlib.load("filename")


def test_invalid_type():
    pl = [object()]

    with pytest.raises(TypeError):
        plistlib.dumps(pl)


@pytest.mark.parametrize(
    "pl",
    [
        0,
        2 ** 8 - 1,
        2 ** 8,
        2 ** 16 - 1,
        2 ** 16,
        2 ** 32 - 1,
        2 ** 32,
        2 ** 63 - 1,
        2 ** 64 - 1,
        1,
        -2 ** 63,
    ],
)
def test_int(pl):
    data = plistlib.dumps(pl)
    pl2 = plistlib.loads(data)
    assert isinstance(pl2, Integral)
    assert pl == pl2
    data2 = plistlib.dumps(pl2)
    assert data == data2


@pytest.mark.parametrize(
    "pl", [2 ** 64 + 1, 2 ** 127 - 1, -2 ** 64, -2 ** 127]
)
def test_int_overflow(pl):
    with pytest.raises(OverflowError):
        plistlib.dumps(pl)


def test_bytearray(use_builtin_types):
    DataClass = bytes if use_builtin_types else plistlib.Data
    pl = DataClass(b"<binary gunk\0\1\2\3>")
    array = bytearray(pl) if use_builtin_types else bytearray(pl.data)
    data = plistlib.dumps(array)
    pl2 = plistlib.loads(data, use_builtin_types=use_builtin_types)
    assert isinstance(pl2, DataClass)
    assert pl2 == pl
    data2 = plistlib.dumps(pl2, use_builtin_types=use_builtin_types)
    assert data == data2


@pytest.mark.parametrize(
    "DataClass, use_builtin_types",
    [(bytes, True), (plistlib.Data, True), (plistlib.Data, False)],
    ids=[
        "bytes|builtin_types=True",
        "Data|builtin_types=True",
        "Data|builtin_types=False",
    ],
)
def test_bytes_data(DataClass, use_builtin_types):
    pl = DataClass(b"<binary gunk\0\1\2\3>")
    data = plistlib.dumps(pl, use_builtin_types=use_builtin_types)
    pl2 = plistlib.loads(data, use_builtin_types=use_builtin_types)
    assert isinstance(pl2, bytes if use_builtin_types else plistlib.Data)
    assert pl2 == pl
    data2 = plistlib.dumps(pl2, use_builtin_types=use_builtin_types)
    assert data == data2


def test_bytes_string(use_builtin_types):
    pl = b"some ASCII bytes"
    data = plistlib.dumps(pl, use_builtin_types=False)
    pl2 = plistlib.loads(data, use_builtin_types=use_builtin_types)
    assert isinstance(pl2, unicode)  # it's always a <string>
    assert pl2 == pl.decode()


def test_indentation_array():
    data = [[[[[[[[{"test": "aaaaaa"}]]]]]]]]
    assert plistlib.loads(plistlib.dumps(data)) == data


def test_indentation_dict():
    data = {
        "1": {"2": {"3": {"4": {"5": {"6": {"7": {"8": {"9": "aaaaaa"}}}}}}}}
    }
    assert plistlib.loads(plistlib.dumps(data)) == data


def test_indentation_dict_mix():
    data = {"1": {"2": [{"3": [[[[[{"test": "aaaaaa"}]]]]]}]}}
    assert plistlib.loads(plistlib.dumps(data)) == data


@pytest.mark.xfail(reason="we use two spaces, Apple uses tabs")
def test_apple_formatting(parametrized_pl):
    # we also split base64 data into multiple lines differently:
    # both right-justify data to 76 chars, but Apple's treats tabs
    # as 8 spaces, whereas we use 2 spaces
    pl, use_builtin_types = parametrized_pl
    pl = plistlib.loads(TESTDATA, use_builtin_types=use_builtin_types)
    data = plistlib.dumps(pl, use_builtin_types=use_builtin_types)
    assert data == TESTDATA


def test_apple_formatting_fromliteral(parametrized_pl):
    pl, use_builtin_types = parametrized_pl
    pl2 = plistlib.loads(TESTDATA, use_builtin_types=use_builtin_types)
    assert pl == pl2


def test_apple_roundtrips(use_builtin_types):
    pl = plistlib.loads(TESTDATA, use_builtin_types=use_builtin_types)
    data = plistlib.dumps(pl, use_builtin_types=use_builtin_types)
    pl2 = plistlib.loads(data, use_builtin_types=use_builtin_types)
    data2 = plistlib.dumps(pl2, use_builtin_types=use_builtin_types)
    assert data == data2


def test_bytesio(parametrized_pl):
    pl, use_builtin_types = parametrized_pl
    b = BytesIO()
    plistlib.dump(pl, b, use_builtin_types=use_builtin_types)
    pl2 = plistlib.load(
        BytesIO(b.getvalue()), use_builtin_types=use_builtin_types
    )
    assert pl == pl2


@pytest.mark.parametrize("sort_keys", [False, True])
def test_keysort_bytesio(sort_keys):
    pl = collections.OrderedDict()
    pl["b"] = 1
    pl["a"] = 2
    pl["c"] = 3

    b = BytesIO()

    plistlib.dump(pl, b, sort_keys=sort_keys)
    pl2 = plistlib.load(
        BytesIO(b.getvalue()), dict_type=collections.OrderedDict
    )

    assert dict(pl) == dict(pl2)
    if sort_keys:
        assert list(pl2.keys()) == ["a", "b", "c"]
    else:
        assert list(pl2.keys()) == ["b", "a", "c"]


@pytest.mark.parametrize("sort_keys", [False, True])
def test_keysort(sort_keys):
    pl = collections.OrderedDict()
    pl["b"] = 1
    pl["a"] = 2
    pl["c"] = 3

    data = plistlib.dumps(pl, sort_keys=sort_keys)
    pl2 = plistlib.loads(data, dict_type=collections.OrderedDict)

    assert dict(pl) == dict(pl2)
    if sort_keys:
        assert list(pl2.keys()) == ["a", "b", "c"]
    else:
        assert list(pl2.keys()) == ["b", "a", "c"]


def test_keys_no_string():
    pl = {42: "aNumber"}

    with pytest.raises(TypeError):
        plistlib.dumps(pl)

    b = BytesIO()
    with pytest.raises(TypeError):
        plistlib.dump(pl, b)


def test_skipkeys():
    pl = {42: "aNumber", "snake": "aWord"}

    data = plistlib.dumps(pl, skipkeys=True, sort_keys=False)

    pl2 = plistlib.loads(data)
    assert pl2 == {"snake": "aWord"}

    fp = BytesIO()
    plistlib.dump(pl, fp, skipkeys=True, sort_keys=False)
    data = fp.getvalue()
    pl2 = plistlib.loads(fp.getvalue())
    assert pl2 == {"snake": "aWord"}


def test_tuple_members():
    pl = {"first": (1, 2), "second": (1, 2), "third": (3, 4)}

    data = plistlib.dumps(pl)
    pl2 = plistlib.loads(data)
    assert pl2 == {"first": [1, 2], "second": [1, 2], "third": [3, 4]}
    assert pl2["first"] is not pl2["second"]


def test_list_members():
    pl = {"first": [1, 2], "second": [1, 2], "third": [3, 4]}

    data = plistlib.dumps(pl)
    pl2 = plistlib.loads(data)
    assert pl2 == {"first": [1, 2], "second": [1, 2], "third": [3, 4]}
    assert pl2["first"] is not pl2["second"]


def test_dict_members():
    pl = {"first": {"a": 1}, "second": {"a": 1}, "third": {"b": 2}}

    data = plistlib.dumps(pl)
    pl2 = plistlib.loads(data)
    assert pl2 == {"first": {"a": 1}, "second": {"a": 1}, "third": {"b": 2}}
    assert pl2["first"] is not pl2["second"]


def test_controlcharacters():
    for i in range(128):
        c = chr(i)
        testString = "string containing %s" % c
        if i >= 32 or c in "\r\n\t":
            # \r, \n and \t are the only legal control chars in XML
            data = plistlib.dumps(testString)
            # the stdlib's plistlib writer, as well as the elementtree
            # parser, always replace \r with \n inside string values;
            # lxml doesn't (the ctrl character is escaped), so it roundtrips
            if c != "\r" or etree._have_lxml:
                assert plistlib.loads(data) == testString
        else:
            with pytest.raises(ValueError):
                plistlib.dumps(testString)


def test_non_bmp_characters():
    pl = {"python": "\U0001f40d"}
    data = plistlib.dumps(pl)
    assert plistlib.loads(data) == pl


def test_nondictroot():
    test1 = "abc"
    test2 = [1, 2, 3, "abc"]
    result1 = plistlib.loads(plistlib.dumps(test1))
    result2 = plistlib.loads(plistlib.dumps(test2))
    assert test1 == result1
    assert test2 == result2


def test_invalidarray():
    for i in [
        "<key>key inside an array</key>",
        "<key>key inside an array2</key><real>3</real>",
        "<true/><key>key inside an array3</key>",
    ]:
        with pytest.raises(ValueError):
            plistlib.loads(
                ("<plist><array>%s</array></plist>" % i).encode("utf-8")
            )


def test_invaliddict():
    for i in [
        "<key><true/>k</key><string>compound key</string>",
        "<key>single key</key>",
        "<string>missing key</string>",
        "<key>k1</key><string>v1</string><real>5.3</real>"
        "<key>k1</key><key>k2</key><string>double key</string>",
    ]:
        with pytest.raises(ValueError):
            plistlib.loads(("<plist><dict>%s</dict></plist>" % i).encode())
        with pytest.raises(ValueError):
            plistlib.loads(
                ("<plist><array><dict>%s</dict></array></plist>" % i).encode()
            )


def test_invalidinteger():
    with pytest.raises(ValueError):
        plistlib.loads(b"<plist><integer>not integer</integer></plist>")


def test_invalidreal():
    with pytest.raises(ValueError):
        plistlib.loads(b"<plist><integer>not real</integer></plist>")


@pytest.mark.parametrize(
    "xml_encoding, encoding, bom",
    [
        (b"utf-8", "utf-8", codecs.BOM_UTF8),
        (b"utf-16", "utf-16-le", codecs.BOM_UTF16_LE),
        (b"utf-16", "utf-16-be", codecs.BOM_UTF16_BE),
        # expat parser (used by ElementTree) does't support UTF-32
        # (b"utf-32", "utf-32-le", codecs.BOM_UTF32_LE),
        # (b"utf-32", "utf-32-be", codecs.BOM_UTF32_BE),
    ],
)
def test_xml_encodings(parametrized_pl, xml_encoding, encoding, bom):
    pl, use_builtin_types = parametrized_pl
    data = TESTDATA.replace(b"UTF-8", xml_encoding)
    data = bom + data.decode("utf-8").encode(encoding)
    pl2 = plistlib.loads(data, use_builtin_types=use_builtin_types)
    assert pl == pl2


def test_fromtree(parametrized_pl):
    pl, use_builtin_types = parametrized_pl
    tree = etree.fromstring(TESTDATA)
    pl2 = plistlib.fromtree(tree, use_builtin_types=use_builtin_types)
    assert pl == pl2


def _strip(txt):
    return (
        "".join(l.strip() for l in tounicode(txt, "utf-8").splitlines())
        if txt is not None
        else ""
    )


def test_totree(parametrized_pl):
    pl, use_builtin_types = parametrized_pl
    tree = etree.fromstring(TESTDATA)[0]  # ignore root 'plist' element
    tree2 = plistlib.totree(pl, use_builtin_types=use_builtin_types)
    assert tree.tag == tree2.tag == "dict"
    for (_, e1), (_, e2) in zip(etree.iterwalk(tree), etree.iterwalk(tree2)):
        assert e1.tag == e2.tag
        assert e1.attrib == e2.attrib
        assert len(e1) == len(e2)
        # ignore whitespace
        assert _strip(e1.text) == _strip(e2.text)


def test_no_pretty_print(use_builtin_types):
    data = plistlib.dumps(
        {"data": b"hello" if use_builtin_types else plistlib.Data(b"hello")},
        pretty_print=False,
        use_builtin_types=use_builtin_types,
    )
    assert data == (
        plistlib.XML_DECLARATION
        + plistlib.PLIST_DOCTYPE
        + b'<plist version="1.0">'
        b"<dict>"
        b"<key>data</key>"
        b"<data>aGVsbG8=</data>"
        b"</dict>"
        b"</plist>"
    )


def test_readPlist_from_path(pl):
    path = os.path.join(datadir, "test.plist")
    pl2 = readPlist(path)
    assert isinstance(pl2["someData"], plistlib.Data)
    assert pl2 == pl


def test_readPlist_from_file(pl):
    with open(os.path.join(datadir, "test.plist"), "rb") as f:
        pl2 = readPlist(f)
        assert isinstance(pl2["someData"], plistlib.Data)
        assert pl2 == pl
        assert not f.closed


def test_readPlistFromString(pl):
    pl2 = readPlistFromString(TESTDATA)
    assert isinstance(pl2["someData"], plistlib.Data)
    assert pl2 == pl


def test_writePlist_to_path(tmpdir, pl_no_builtin_types):
    testpath = tmpdir / "test.plist"
    writePlist(pl_no_builtin_types, str(testpath))
    with testpath.open("rb") as fp:
        pl2 = plistlib.load(fp, use_builtin_types=False)
    assert pl2 == pl_no_builtin_types


def test_writePlist_to_file(tmpdir, pl_no_builtin_types):
    testpath = tmpdir / "test.plist"
    with testpath.open("wb") as fp:
        writePlist(pl_no_builtin_types, fp)
    with testpath.open("rb") as fp:
        pl2 = plistlib.load(fp, use_builtin_types=False)
    assert pl2 == pl_no_builtin_types


def test_writePlistToString(pl_no_builtin_types):
    data = writePlistToString(pl_no_builtin_types)
    pl2 = plistlib.loads(data)
    assert pl2 == pl_no_builtin_types


def test_load_use_builtin_types_default():
    pl = plistlib.loads(TESTDATA)
    expected = plistlib.Data if PY2 else bytes
    assert isinstance(pl["someData"], expected)


def test_dump_use_builtin_types_default(pl_no_builtin_types):
    data = plistlib.dumps(pl_no_builtin_types)
    pl2 = plistlib.loads(data)
    expected = plistlib.Data if PY2 else bytes
    assert isinstance(pl2["someData"], expected)
    assert pl2 == pl_no_builtin_types


def test_non_ascii_bytes():
    with pytest.raises(ValueError, match="invalid non-ASCII bytes"):
        plistlib.dumps("\U0001f40d".encode("utf-8"), use_builtin_types=False)


class CustomMapping(Mapping):
    a = {"a": 1, "b": 2}

    def __getitem__(self, key):
        return self.a[key]

    def __iter__(self):
        return iter(self.a)

    def __len__(self):
        return len(self.a)


def test_custom_mapping():
    test_mapping = CustomMapping()
    data = plistlib.dumps(test_mapping)
    assert plistlib.loads(data) == {"a": 1, "b": 2}


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(sys.argv))
