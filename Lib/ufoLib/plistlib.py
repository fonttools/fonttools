from __future__ import absolute_import, unicode_literals
import re
from io import BytesIO
from datetime import datetime
from base64 import b64encode, b64decode
from numbers import Integral

try:
    from functools import singledispatch
except ImportError:
    try:
        from singledispatch import singledispatch
    except ImportError:
        singledispatch = None

from ufoLib import etree

from fontTools.misc.py23 import (
    unicode,
    basestring,
    tounicode,
    tobytes,
    SimpleNamespace,
    range,
)


# we use a custom XML declaration for backward compatibility with older
# ufoLib versions which would write it using double quotes.
# https://github.com/unified-font-object/ufoLib/issues/158
XML_DECLARATION = b"""<?xml version="1.0" encoding="UTF-8"?>"""

PLIST_DOCTYPE = (
    b'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
    b'"http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
)

# Date should conform to a subset of ISO 8601:
# YYYY '-' MM '-' DD 'T' HH ':' MM ':' SS 'Z'
_date_parser = re.compile(
    r"(?P<year>\d\d\d\d)"
    r"(?:-(?P<month>\d\d)"
    r"(?:-(?P<day>\d\d)"
    r"(?:T(?P<hour>\d\d)"
    r"(?::(?P<minute>\d\d)"
    r"(?::(?P<second>\d\d))"
    r"?)?)?)?)?Z",
    getattr(re, "ASCII", 0),  # py3-only
)


def _date_from_string(s):
    order = ("year", "month", "day", "hour", "minute", "second")
    gd = _date_parser.match(s).groupdict()
    lst = []
    for key in order:
        val = gd[key]
        if val is None:
            break
        lst.append(int(val))
    return datetime(*lst)


def _date_to_string(d):
    return "%04d-%02d-%02dT%02d:%02d:%02dZ" % (
        d.year,
        d.month,
        d.day,
        d.hour,
        d.minute,
        d.second,
    )


class PlistTarget(object):
    """ Event handler using the ElementTree Target API that can be
    passed to a XMLParser to produce property list objects from XML.
    It is based on the CPython plistlib module's _PlistParser class,
    but does not use the expat parser.

    >>> from ufoLib import etree
    >>> parser = etree.XMLParser(target=PlistTarget())
    >>> result = etree.XML(
    ...     "<dict>"
    ...     "    <key>something</key>"
    ...     "    <string>blah</string>"
    ...     "</dict>",
    ...     parser=parser)
    >>> result == {"something": "blah"}
    True

    Links:
    https://github.com/python/cpython/blob/master/Lib/plistlib.py
    http://lxml.de/parsing.html#the-target-parser-interface
    """

    def __init__(self, dict_type=dict):
        self.stack = []
        self.current_key = None
        self.root = None
        self._dict_type = dict_type

    def start(self, tag, attrib):
        self._data = []
        handler = _TARGET_START_HANDLERS.get(tag)
        if handler is not None:
            handler(self)

    def end(self, tag):
        handler = _TARGET_END_HANDLERS.get(tag)
        if handler is not None:
            handler(self)

    def data(self, data):
        self._data.append(data)

    def close(self):
        return self.root

    # helpers

    def add_object(self, value):
        if self.current_key is not None:
            if not isinstance(self.stack[-1], type({})):
                raise ValueError("unexpected element: %r" % self.stack[-1])
            self.stack[-1][self.current_key] = value
            self.current_key = None
        elif not self.stack:
            # this is the root object
            self.root = value
        else:
            if not isinstance(self.stack[-1], type([])):
                raise ValueError("unexpected element: %r" % self.stack[-1])
            self.stack[-1].append(value)

    def get_data(self):
        data = "".join(self._data)
        self._data = []
        return data


# event handlers


def start_dict(self):
    d = self._dict_type()
    self.add_object(d)
    self.stack.append(d)


def end_dict(self):
    if self.current_key:
        raise ValueError("missing value for key '%s'" % self.current_key)
    self.stack.pop()


def end_key(self):
    if self.current_key or not isinstance(self.stack[-1], type({})):
        raise ValueError("unexpected key")
    self.current_key = self.get_data()


def start_array(self):
    a = []
    self.add_object(a)
    self.stack.append(a)


def end_array(self):
    self.stack.pop()


def end_true(self):
    self.add_object(True)


def end_false(self):
    self.add_object(False)


def end_integer(self):
    self.add_object(int(self.get_data()))


def end_real(self):
    self.add_object(float(self.get_data()))


def end_string(self):
    self.add_object(self.get_data())


def end_data(self):
    self.add_object(b64decode(self.get_data()))


def end_date(self):
    self.add_object(_date_from_string(self.get_data()))


_TARGET_START_HANDLERS = {"dict": start_dict, "array": start_array}

_TARGET_END_HANDLERS = {
    "dict": end_dict,
    "array": end_array,
    "key": end_key,
    "true": end_true,
    "false": end_false,
    "integer": end_integer,
    "real": end_real,
    "string": end_string,
    "data": end_data,
    "date": end_date,
}


# functions to build element tree from plist data


def _unicode_element(value, ctx):
    el = etree.Element("string")
    el.text = value
    return el


def _bool_element(value, ctx):
    if value:
        return etree.Element("true")
    else:
        return etree.Element("false")


def _integer_element(value, ctx):
    if -1 << 63 <= value < 1 << 64:
        el = etree.Element("integer")
        el.text = "%d" % value
        return el
    else:
        raise OverflowError(value)


def _float_element(value, ctx):
    el = etree.Element("real")
    el.text = repr(value)
    return el


def _dict_element(d, ctx):
    el = etree.Element("dict")
    items = d.items()
    if ctx.sort_keys:
        items = sorted(items)
    ctx.indent_level += 1
    for key, value in items:
        if not isinstance(key, basestring):
            if ctx.skipkeys:
                continue
            raise TypeError("keys must be strings")
        k = etree.SubElement(el, "key")
        k.text = tounicode(key, "utf-8")
        el.append(_make_element(value, ctx))
    ctx.indent_level -= 1
    return el


def _array_element(array, ctx):
    el = etree.Element("array")
    if len(array) == 0:
        return el
    ctx.indent_level += 1
    for value in array:
        el.append(_make_element(value, ctx))
    ctx.indent_level -= 1
    return el


def _date_element(date, ctx):
    el = etree.Element("date")
    el.text = _date_to_string(date)
    return el


def _data_element(data, ctx):
    data = b64encode(data)
    if data and ctx.pretty_print:
        # split into multiple lines right-justified to max 76 chars
        indent = b"\n" + b"  " * ctx.indent_level
        max_length = max(16, 76 - len(indent))
        chunks = []
        for i in range(0, len(data), max_length):
            chunks.append(indent)
            chunks.append(data[i : i + max_length])
        chunks.append(indent)
        data = b"".join(chunks)
    el = etree.Element("data")
    el.text = data
    return el


# if singledispatch is available, we use a generic '_make_element' function
# and register overloaded implementations that are run based on the type of
# the first argument

if singledispatch is not None:

    @singledispatch
    def _make_element(value, ctx):
        raise TypeError("unsupported type: %s" % type(value))

    _make_element.register(unicode)(_unicode_element)
    _make_element.register(bool)(_bool_element)
    _make_element.register(Integral)(_integer_element)
    _make_element.register(float)(_float_element)
    _make_element.register(dict)(_dict_element)
    _make_element.register(list)(_array_element)
    _make_element.register(tuple)(_array_element)
    _make_element.register(datetime)(_date_element)
    _make_element.register(bytes)(_data_element)
    _make_element.register(bytearray)(_data_element)

else:
    # otherwise we use a long switch-like if statement

    def _make_element(value, ctx):
        if isinstance(value, unicode):
            return _unicode_element(value, ctx)
        elif isinstance(value, bool):
            return _bool_element(value, ctx)
        elif isinstance(value, Integral):
            return _integer_element(value, ctx)
        elif isinstance(value, float):
            return _float_element(value, ctx)
        elif isinstance(value, dict):
            return _dict_element(value, ctx)
        elif isinstance(value, (list, tuple)):
            return _array_element(value, ctx)
        elif isinstance(value, datetime):
            return _date_element(value, ctx)
        elif isinstance(value, (bytes, bytearray)):
            return _data_element(value, ctx)


# Public functions to create element tree from plist-compatible python
# data structures and viceversa, for use when (de)serializing GLIF xml.


def totree(
    value, sort_keys=True, skipkeys=False, pretty_print=True, indent_level=1
):
    context = SimpleNamespace(
        sort_keys=sort_keys,
        skipkeys=skipkeys,
        pretty_print=pretty_print,
        indent_level=indent_level,
    )
    return _make_element(value, context)


def fromtree(tree, dict_type=dict):
    target = PlistTarget(dict_type=dict_type)
    for action, element in etree.iterwalk(tree, events=("start", "end")):
        if action == "start":
            target.start(element.tag, element.attrib)
        elif action == "end":
            # if there are no children, parse the leaf's data
            if not len(element):
                # always pass str, not None
                target.data(element.text or "")
            target.end(element.tag)
    return target.close()


# python3 plistlib API


def load(fp, dict_type=dict):
    if not hasattr(fp, "read"):
        raise AttributeError(
            "'%s' object has no attribute 'read'" % type(fp).__name__
        )
    target = PlistTarget(dict_type=dict_type)
    parser = etree.XMLParser(target=target)
    result = etree.parse(fp, parser=parser)
    # lxml returns the target object directly, while ElementTree wraps
    # it as the root of an ElementTree object
    try:
        return result.getroot()
    except AttributeError:
        return result


def loads(value, dict_type=dict):
    fp = BytesIO(value)
    return load(fp, dict_type=dict_type)


def dump(value, fp, sort_keys=True, skipkeys=False, pretty_print=True):
    if not hasattr(fp, "write"):
        raise AttributeError(
            "'%s' object has no attribute 'write'" % type(fp).__name__
        )
    root = etree.Element("plist", version="1.0")
    el = totree(
        value,
        sort_keys=sort_keys,
        skipkeys=skipkeys,
        pretty_print=pretty_print,
    )
    root.append(el)
    tree = etree.ElementTree(root)
    # we write the doctype ourselves instead of using the 'doctype' argument
    # of 'write' method, becuse lxml will force adding a '\n' even when
    # pretty_print is False.
    if pretty_print:
        header = b"\n".join((XML_DECLARATION, PLIST_DOCTYPE, b""))
    else:
        header = XML_DECLARATION + PLIST_DOCTYPE
    fp.write(header)
    tree.write(
        fp, encoding="utf-8", pretty_print=pretty_print, xml_declaration=False
    )


def dumps(value, sort_keys=True, skipkeys=False, pretty_print=True):
    fp = BytesIO()
    dump(
        value,
        fp,
        sort_keys=sort_keys,
        skipkeys=skipkeys,
        pretty_print=pretty_print,
    )
    return fp.getvalue()


# The following functions were part of the old py2-like ufoLib.plistlib API.
# They are kept only for backward compatiblity.
from .utils import deprecated


@deprecated("Use 'load' instead")
def readPlist(path_or_file):
    did_open = False
    if isinstance(path_or_file, basestring):
        path_or_file = open(path_or_file, "rb")
        did_open = True
    try:
        return load(path_or_file)
    finally:
        if did_open:
            path_or_file.close()


@deprecated("Use 'dump' instead")
def writePlist(value, path_or_file):
    did_open = False
    if isinstance(path_or_file, basestring):
        path_or_file = open(path_or_file, "wb")
        did_open = True
    try:
        dump(value, path_or_file)
    finally:
        if did_open:
            path_or_file.close()


@deprecated("Use 'loads' instead")
def readPlistFromString(data):
    return loads(tobytes(data, encoding="utf-8"))


@deprecated("Use 'dumps' instead")
def writePlistToString(value):
    return dumps(value)
