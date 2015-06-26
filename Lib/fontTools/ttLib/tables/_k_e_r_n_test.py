from __future__ import print_function, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttLib
import unittest
from ._k_e_r_n import KernTable_format_0

class MockFont(object):

        def getGlyphOrder(self):
                return ["glyph00000", "glyph00001", "glyph00002", "glyph00003"]

        def getGlyphName(self, glyphID):
                return "glyph%.5d" % glyphID

class KernTable_format_0_Test(unittest.TestCase):

        def test_decompileBadGlyphId(self):
                subtable = KernTable_format_0()
                subtable.apple = False
                subtable.decompile(  b'\x00' * 6
                                   + b'\x00' + b'\x02' + b'\x00' * 6
                                   + b'\x00' + b'\x01' + b'\x00' + b'\x03' + b'\x00' + b'\x01'
                                   + b'\x00' + b'\x01' + b'\xFF' + b'\xFF' + b'\x00' + b'\x02',
                                   MockFont())
                self.assertEqual(subtable[("glyph00001", "glyph00003")], 1)
                self.assertEqual(subtable[("glyph00001", "glyph65535")], 2)

if __name__ == "__main__":
        unittest.main()
