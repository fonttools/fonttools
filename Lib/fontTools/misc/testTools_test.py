from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
import fontTools.misc.testTools as testTools
import os
import unittest


class TestToolsTest(unittest.TestCase):
    def test_parseXML(self):
        self.assertEqual(testTools.parseXML(
            '<Foo n="1"/>'
            '<Foo n="2">'
            '    some text'
            '    <Bar color="red"/>'
            '    some more text'
            '</Foo>'
            '<Foo n="3"/>'), [
                ("Foo", {"n": "1"}, []),
                ("Foo", {"n": "2"}, [
                    "    some text    ",
                    ("Bar", {"color": "red"}, []),
                    "    some more text",
                ]),
                ("Foo", {"n": "3"}, [])
            ])


if __name__ == "__main__":
    unittest.main()
