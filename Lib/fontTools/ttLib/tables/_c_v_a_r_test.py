from __future__ import \
    print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.testTools import getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import TTLibError, getTableModule, newTable
from fontTools.ttLib.tables.TupleVariation import TupleVariation

import unittest


CVAR_DATA = deHexStr(
    "0001 0000 "      #  0: majorVersion=1 minorVersion=0
    "0002 0018 "      #  4: tupleVariationCount=2 offsetToData=24
    "0005 "           #  8: tvHeader[0].variationDataSize=5
    "A000 "           # 10: tvHeader[0].tupleIndex=EMBEDDED_PEAK|PRIVATE_POINTS
    "4000 0000 "      # 12: tvHeader[0].peakTuple=[1.0, 0.0]
    "0005 "           # 16: tvHeader[1].variationDataSize=5
    "A000 "           # 18: tvHeader[1].tupleIndex=EMBEDDED_PEAK|PRIVATE_POINTS
    "C000 3333 "      # 20: tvHeader[1].peakTuple=[-1.0, 0.8]
    "00 02 03 01 04 " # 24: all values; deltas=[3, 1, 4]
    "00 02 09 07 08") # 29: all values; deltas=[9, 7, 8]

CVAR_XML = [
    '<version major="1" minor="0"/>',
    '<tuple>',
    '  <coord axis="wght" value="1.0"/>',
    '  <delta cvt="0" value="3"/>',
    '  <delta cvt="1" value="1"/>',
    '  <delta cvt="2" value="4"/>',
    '</tuple>',
    '<tuple>',
    '  <coord axis="wght" value="-1.0"/>',
    '  <coord axis="wdth" value="0.8"/>',
    '  <delta cvt="0" value="9"/>',
    '  <delta cvt="1" value="7"/>',
    '  <delta cvt="2" value="8"/>',
    '</tuple>',
]

CVAR_VARIATIONS = [
    TupleVariation({"wght": (0.0, 1.0, 1.0)}, [3, 1, 4]),
    TupleVariation({"wght": (-1, -1.0, 0.0), "wdth": (0.0, 0.8, 0.8)},
                   [9, 7, 8]),
]


class CVARTableTest(unittest.TestCase):
    def makeFont(self):
        cvt, cvar, fvar = newTable("cvt "), newTable("cvar"), newTable("fvar")
        font = {"cvt ": cvt, "cvar": cvar, "fvar": fvar}
        cvt.values = [0, 1000, -2000]
        Axis = getTableModule("fvar").Axis
        fvar.axes = [Axis(), Axis()]
        fvar.axes[0].axisTag, fvar.axes[1].axisTag = "wght", "wdth"
        return font, cvar

    def test_compile(self):
        font, cvar = self.makeFont()
        cvar.variations = CVAR_VARIATIONS
        self.assertEqual(hexStr(cvar.compile(font)), hexStr(CVAR_DATA))

    def test_decompile(self):
        font, cvar = self.makeFont()
        cvar.decompile(CVAR_DATA, font)
        self.assertEqual(cvar.majorVersion, 1)
        self.assertEqual(cvar.minorVersion, 0)
        self.assertEqual(cvar.variations, CVAR_VARIATIONS)

    def test_fromXML(self):
        font, cvar = self.makeFont()
        for name, attrs, content in parseXML(CVAR_XML):
            cvar.fromXML(name, attrs, content, ttFont=font)
        self.assertEqual(cvar.majorVersion, 1)
        self.assertEqual(cvar.minorVersion, 0)
        self.assertEqual(cvar.variations, CVAR_VARIATIONS)

    def test_toXML(self):
        font, cvar = self.makeFont()
        cvar.variations = CVAR_VARIATIONS
        self.assertEqual(getXML(cvar.toXML, font), CVAR_XML)


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
