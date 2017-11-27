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
    "8002 0018 "      #  4: tupleVariationCount=2|TUPLES_SHARE_POINT_NUMBERS offsetToData=24
    "0004 "           #  8: tvHeader[0].variationDataSize=4
    "8000 "           # 10: tvHeader[0].tupleIndex=EMBEDDED_PEAK
    "4000 0000 "      # 12: tvHeader[0].peakTuple=[1.0, 0.0]
    "0004 "           # 16: tvHeader[1].variationDataSize=4
    "8000 "           # 18: tvHeader[1].tupleIndex=EMBEDDED_PEAK
    "C000 3333 "      # 20: tvHeader[1].peakTuple=[-1.0, 0.8]
    "03 02 02 01 01"  # 24: shared_pointCount=03, run_count=2 cvt=[2, 3, 4]
    "02 03 01 04 "    # 25: deltas=[3, 1, 4]
    "02 09 07 08")    # 29: deltas=[9, 7, 8]

CVAR_PRIVATE_POINT_DATA = deHexStr(
    "0001 0000 "                    #  0: majorVersion=1 minorVersion=0
    "0002 0018 "                    #  4: tupleVariationCount=2 offsetToData=24
    "0009 "                         #  8: tvHeader[0].variationDataSize=9
    "A000 "                         # 10: tvHeader[0].tupleIndex=EMBEDDED_PEAK|PRIVATE_POINT_NUMBERS
    "4000 0000 "                    # 12: tvHeader[0].peakTuple=[1.0, 0.0]
    "0009 "                         # 16: tvHeader[1].variationDataSize=9
    "A000 "                         # 18: tvHeader[1].tupleIndex=EMBEDDED_PEAK|PRIVATE_POINT_NUMBERS
    "C000 3333 "                    # 20: tvHeader[1].peakTuple=[-1.0, 0.8]
    "03 02 02 01 01 02 03 01 04 "   # 24: pointCount=3 run_count=2 cvt=2 1 1 run_count=2 deltas=[3, 1, 4]
    "03 02 02 01 01 02 09 07 08 ")  # 33: pointCount=3 run_count=2 cvt=2 1 1 run_count=2 deltas=[9, 7, 8]

CVAR_XML = [
    '<version major="1" minor="0"/>',
    '<tuple>',
    '  <coord axis="wght" value="1.0"/>',
    '  <delta cvt="2" value="3"/>',
    '  <delta cvt="3" value="1"/>',
    '  <delta cvt="4" value="4"/>',
    '</tuple>',
    '<tuple>',
    '  <coord axis="wght" value="-1.0"/>',
    '  <coord axis="wdth" value="0.8"/>',
    '  <delta cvt="2" value="9"/>',
    '  <delta cvt="3" value="7"/>',
    '  <delta cvt="4" value="8"/>',
    '</tuple>',
]

CVAR_VARIATIONS = [
    TupleVariation({"wght": (0.0, 1.0, 1.0)}, [None, None, 3, 1, 4]),
    TupleVariation({"wght": (-1, -1.0, 0.0), "wdth": (0.0, 0.8, 0.8)},
                   [None, None, 9, 7, 8]),
]


class CVARTableTest(unittest.TestCase):
    def makeFont(self):
        cvt, cvar, fvar = newTable("cvt "), newTable("cvar"), newTable("fvar")
        font = {"cvt ": cvt, "cvar": cvar, "fvar": fvar}
        cvt.values = [0, 0, 0, 1000, -2000]
        Axis = getTableModule("fvar").Axis
        fvar.axes = [Axis(), Axis()]
        fvar.axes[0].axisTag, fvar.axes[1].axisTag = "wght", "wdth"
        return font, cvar

    def test_compile(self):
        font, cvar = self.makeFont()
        cvar.variations = CVAR_VARIATIONS
        self.assertEqual(hexStr(cvar.compile(font)), hexStr(CVAR_PRIVATE_POINT_DATA))

    def test_compile_shared_points(self):
        font, cvar = self.makeFont()
        cvar.variations = CVAR_VARIATIONS
        self.assertEqual(hexStr(cvar.compile(font, useSharedPoints=True)), hexStr(CVAR_DATA))

    def test_decompile(self):
        font, cvar = self.makeFont()
        cvar.decompile(CVAR_PRIVATE_POINT_DATA, font)
        self.assertEqual(cvar.majorVersion, 1)
        self.assertEqual(cvar.minorVersion, 0)
        self.assertEqual(cvar.variations, CVAR_VARIATIONS)

    def test_decompile_shared_points(self):
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
