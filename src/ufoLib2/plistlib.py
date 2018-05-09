from __future__ import absolute_import, unicode_literals
import re
from io import BytesIO
from datetime import datetime
from base64 import b64encode, b64decode
from numbers import Integral
from lxml import etree
from fontTools.misc.py23 import unicode, basestring, tounicode


PLIST_DOCTYPE = ('<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                 '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">')

# Date should conform to a subset of ISO 8601:
# YYYY '-' MM '-' DD 'T' HH ':' MM ':' SS 'Z'
_date_parser = re.compile(r"(?P<year>\d\d\d\d)"
                          r"(?:-(?P<month>\d\d)"
                          r"(?:-(?P<day>\d\d)"
                          r"(?:T(?P<hour>\d\d)"
                          r"(?::(?P<minute>\d\d)"
                          r"(?::(?P<second>\d\d))"
                          r"?)?)?)?)?Z", getattr(re, "ASCII", 0))  # py3-only


def _date_from_string(s):
    order = ('year', 'month', 'day', 'hour', 'minute', 'second')
    gd = _date_parser.match(s).groupdict()
    lst = []
    for key in order:
        val = gd[key]
        if val is None:
            break
        lst.append(int(val))
    return datetime(*lst)


def _date_to_string(d):
    return '%04d-%02d-%02dT%02d:%02d:%02dZ' % (d.year, d.month, d.day, d.hour,
                                               d.minute, d.second)


class PlistTarget(object):
    """ Event handler using the ElementTree Target API that can be
    passed to a XMLParser to produce property list objects from XML.
    It is based on the CPython plistlib module's _PlistParser class,
    but does not use the expat parser.

    >>> from lxml import etree
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
        handler = getattr(self, "start_" + tag, None)
        if handler is not None:
            handler(attrib)

    def end(self, tag):
        handler = getattr(self, "end_" + tag, None)
        if handler is not None:
            handler()

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
        data = ''.join(self._data)
        self._data = []
        return data

    # event handlers

    def start_dict(self, attrs):
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

    def start_array(self, attrs):
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


class PlistTreeBuilder(object):

    def __init__(self, sort_keys=True, skipkeys=False):
        self._sort_keys = sort_keys
        self._skipkeys = skipkeys

    def build(self, value):
        if isinstance(value, unicode):
            return self.simple_element("string", value)
        elif isinstance(value, bool):
            if value:
                return etree.Element("true")
            else:
                return etree.Element("false")
        elif isinstance(value, Integral):
            if -1 << 63 <= value < 1 << 64:
                return self.simple_element("integer", "%d" % value)
            else:
                raise OverflowError(value)
        elif isinstance(value, float):
            return self.simple_element("real", repr(value))
        elif isinstance(value, dict):
            return self.dict_element(value)
        elif isinstance(value, (tuple, list)):
            return self.array_element(value)
        elif isinstance(value, datetime):
            return self.simple_element("date", _date_to_string(value))
        elif isinstance(value, (bytes, bytearray)):
            return self.simple_element("data", b64encode(value))
        else:
            raise TypeError("unsupported type: %s" % type(value))

    @staticmethod
    def simple_element(tag, value):
        el = etree.Element(tag)
        el.text = tounicode(value, "utf-8")
        return el

    def array_element(self, array):
        el = etree.Element("array")
        if len(array) == 0:
            return el
        for value in array:
            el.append(self.build(value))
        return el

    def dict_element(self, d):
        el = etree.Element("dict")
        items = d.items()
        if self._sort_keys:
            items = sorted(items)
        for key, value in items:
            if not isinstance(key, basestring):
                if self._skipkeys:
                    continue
                TypeError("keys must be strings")
            k = etree.SubElement(el, "key")
            k.text = tounicode(key, "utf-8")
            el.append(self.build(value))
        return el


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


def totree(value, sort_keys=True, skipkeys=False):
    builder = PlistTreeBuilder(sort_keys=sort_keys, skipkeys=skipkeys)
    return builder.build(value)


# python3 plistlib API


def load(fp, dict_type=dict):
    target = PlistTarget(dict_type=dict_type)
    parser = etree.XMLParser(target=target)
    return etree.parse(fp, parser=parser)


def loads(value, dict_type=dict):
    fp = BytesIO(value)
    return load(fp, dict_type=dict_type)


def dump(value, fp, sort_keys=True, skipkeys=False, _pretty_print=True):
    root = etree.Element("plist", version="1.0")
    root.append(totree(value, sort_keys=sort_keys, skipkeys=skipkeys))
    tree = etree.ElementTree(root)
    tree.write(
        fp,
        encoding="utf-8",
        pretty_print=_pretty_print,
        xml_declaration=True,
        doctype=PLIST_DOCTYPE)


def dumps(value, sort_keys=True, skipkeys=False, _pretty_print=True):
    fp = BytesIO()
    dump(
        value,
        fp,
        sort_keys=sort_keys,
        skipkeys=skipkeys,
        _pretty_print=_pretty_print)
    return fp.getvalue()
