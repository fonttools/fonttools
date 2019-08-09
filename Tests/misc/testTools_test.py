# -*- coding: utf-8 -*-
from fontTools.misc.py23 import *
import fontTools.misc.testTools as testTools
import unittest


class TestToolsTest(unittest.TestCase):

    def test_parseXML_str(self):
        self.assertEqual(testTools.parseXML(
            '<Foo n="1"/>'
            '<Foo n="2">'
            '    some ünıcòðe text'
            '    <Bar color="red"/>'
            '    some more text'
            '</Foo>'
            '<Foo n="3"/>'), [
                ("Foo", {"n": "1"}, []),
                ("Foo", {"n": "2"}, [
                    "    some ünıcòðe text    ",
                    ("Bar", {"color": "red"}, []),
                    "    some more text",
                ]),
                ("Foo", {"n": "3"}, [])
            ])

    def test_parseXML_bytes(self):
        self.assertEqual(testTools.parseXML(
            b'<Foo n="1"/>'
            b'<Foo n="2">'
            b'    some \xc3\xbcn\xc4\xb1c\xc3\xb2\xc3\xb0e text'
            b'    <Bar color="red"/>'
            b'    some more text'
            b'</Foo>'
            b'<Foo n="3"/>'), [
                ("Foo", {"n": "1"}, []),
                ("Foo", {"n": "2"}, [
                    "    some ünıcòðe text    ",
                    ("Bar", {"color": "red"}, []),
                    "    some more text",
                ]),
                ("Foo", {"n": "3"}, [])
            ])

    def test_parseXML_str_list(self):
        self.assertEqual(testTools.parseXML(
            ['<Foo n="1"/>'
             '<Foo n="2"/>']), [
                ("Foo", {"n": "1"}, []),
                ("Foo", {"n": "2"}, [])
            ])

    def test_parseXML_bytes_list(self):
        self.assertEqual(testTools.parseXML(
            [b'<Foo n="1"/>'
             b'<Foo n="2"/>']), [
                ("Foo", {"n": "1"}, []),
                ("Foo", {"n": "2"}, [])
            ])

    def test_getXML(self):
        def toXML(writer, ttFont):
            writer.simpletag("simple")
            writer.newline()
            writer.begintag("tag", attr='value')
            writer.newline()
            writer.write("hello world")
            writer.newline()
            writer.endtag("tag")
            writer.newline()  # toXML always ends with a newline

        self.assertEqual(testTools.getXML(toXML),
                         ['<simple/>',
                          '<tag attr="value">',
                          '  hello world',
                          '</tag>'])


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
