"""Helpers for writing unit tests."""

from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
import collections
from fontTools.misc.py23 import *
from fontTools.misc.xmlWriter import XMLWriter


def parseXML(xmlSnippet):
    """Parses a snippet of XML.

    Input can be either a single string (unicode or UTF-8 bytes), or a
    a sequence of strings.

    The result is in the same format that would be returned by
    XMLReader, but the parser imposes no constraints on the root
    element so it can be called on small snippets of TTX files.
    """
    # To support snippets with multiple elements, we add a fake root.
    reader = TestXMLReader_()
    xml = b"<root>"
    if isinstance(xmlSnippet, bytes):
        xml += xmlSnippet
    elif isinstance(xmlSnippet, unicode):
        xml += tobytes(xmlSnippet, 'utf-8')
    elif isinstance(xmlSnippet, collections.Iterable):
        xml += b"".join(tobytes(s, 'utf-8') for s in xmlSnippet)
    else:
        raise TypeError("expected string or sequence of strings; found %r"
                        % type(xmlSnippet).__name__)
    xml += b"</root>"
    reader.parser.Parse(xml, 0)
    return reader.root[2]


class FakeFont:
    def __init__(self, glyphs):
        self.glyphOrder_ = glyphs
        self.lazy = False

    def getGlyphID(self, name):
        return self.glyphOrder_.index(name)

    def getGlyphName(self, glyphID):
        if glyphID < len(self.glyphOrder_):
            return self.glyphOrder_[glyphID]
        else:
            return "glyph%.5d" % glyphID

    def getGlyphOrder(self):
        return self.glyphOrder_


class TestXMLReader_(object):
    def __init__(self):
        from xml.parsers.expat import ParserCreate
        self.parser = ParserCreate()
        self.parser.StartElementHandler = self.startElement_
        self.parser.EndElementHandler = self.endElement_
        self.parser.CharacterDataHandler = self.addCharacterData_
        self.root = None
        self.stack = []

    def startElement_(self, name, attrs):
        element = (name, attrs, [])
        if self.stack:
            self.stack[-1][2].append(element)
        else:
            self.root = element
        self.stack.append(element)

    def endElement_(self, name):
        self.stack.pop()

    def addCharacterData_(self, data):
        self.stack[-1][2].append(data)


def makeXMLWriter(newlinestr='\n'):
    # don't write OS-specific new lines
    writer = XMLWriter(BytesIO(), newlinestr=newlinestr)
    # erase XML declaration
    writer.file.seek(0)
    writer.file.truncate()
    return writer


def getXML(func, ttFont=None):
    """Call the passed toXML function and return the written content as a
    list of lines (unicode strings).
    Result is stripped of XML declaration and OS-specific newline characters.
    """
    writer = makeXMLWriter()
    func(writer, ttFont)
    xml = writer.file.getvalue().decode("utf-8")
    # toXML methods must always end with a writer.newline()
    assert xml.endswith("\n")
    return xml.splitlines()
