from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import TTLibError, getTableClass, getTableModule, newTable
import unittest
from fontTools.ttLib.tables.TupleVariation import TupleVariation


gvarClass = getTableClass("gvar")


GVAR_DATA = deHexStr(
    "0001 0000 "  #   0: majorVersion=1 minorVersion=0
    "0002 0000 "  #   4: axisCount=2 sharedTupleCount=0
    "0000001C "  #   8: offsetToSharedTuples=28
    "0003 0000 "  #  12: glyphCount=3 flags=0
    "0000001C "  #  16: offsetToGlyphVariationData=28
    "0000 0000 000C 002F "  #  20: offsets=[0,0,12,47], times 2: [0,0,24,94],
    #                 #           +offsetToGlyphVariationData: [28,28,52,122]
    #
    # 28: Glyph variation data for glyph #0, ".notdef"
    # ------------------------------------------------
    # (no variation data for this glyph)
    #
    # 28: Glyph variation data for glyph #1, "space"
    # ----------------------------------------------
    "8001 000C "  #  28: tupleVariationCount=1|TUPLES_SHARE_POINT_NUMBERS, offsetToData=12(+28=40)
    "000A "  #  32: tvHeader[0].variationDataSize=10
    "8000 "  #  34: tvHeader[0].tupleIndex=EMBEDDED_PEAK
    "0000 2CCD "  #  36: tvHeader[0].peakTuple={wght:0.0, wdth:0.7}
    "00 "  #  40: all points
    "03 01 02 03 04 "  #  41: deltaX=[1, 2, 3, 4]
    "03 0b 16 21 2C "  #  46: deltaY=[11, 22, 33, 44]
    "00 "  #  51: padding
    #
    # 52: Glyph variation data for glyph #2, "I"
    # ------------------------------------------
    "8002 001c "  #  52: tupleVariationCount=2|TUPLES_SHARE_POINT_NUMBERS, offsetToData=28(+52=80)
    "0012 "  #  56: tvHeader[0].variationDataSize=18
    "C000 "  #  58: tvHeader[0].tupleIndex=EMBEDDED_PEAK|INTERMEDIATE_REGION
    "2000 0000 "  #  60: tvHeader[0].peakTuple={wght:0.5, wdth:0.0}
    "0000 0000 "  #  64: tvHeader[0].intermediateStart={wght:0.0, wdth:0.0}
    "4000 0000 "  #  68: tvHeader[0].intermediateEnd={wght:1.0, wdth:0.0}
    "0016 "  #  72: tvHeader[1].variationDataSize=22
    "A000 "  #  74: tvHeader[1].tupleIndex=EMBEDDED_PEAK|PRIVATE_POINTS
    "C000 3333 "  #  76: tvHeader[1].peakTuple={wght:-1.0, wdth:0.8}
    "00 "  #  80: all points
    "07 03 01 04 01 "  #  81: deltaX.len=7, deltaX=[3, 1, 4, 1,
    "05 09 02 06 "  #  86:                       5, 9, 2, 6]
    "07 03 01 04 01 "  #  90: deltaY.len=7, deltaY=[3, 1, 4, 1,
    "05 09 02 06 "  #  95:                       5, 9, 2, 6]
    "06 "  #  99: 6 points
    "05 00 01 03 01 "  # 100: runLen=5(+1=6); delta-encoded run=[0, 1, 4, 5,
    "01 01 "  # 105:                                    6, 7]
    "05 f8 07 fc 03 fe 01 "  # 107: deltaX.len=5, deltaX=[-8,7,-4,3,-2,1]
    "05 a8 4d 2c 21 ea 0b "  # 114: deltaY.len=5, deltaY=[-88,77,44,33,-22,11]
    "00"  # 121: padding
)  # 122: <end>
assert len(GVAR_DATA) == 122


GVAR_VARIATIONS = {
    ".notdef": [],
    "space": [
        TupleVariation(
            {"wdth": (0.0, 0.7000122, 0.7000122)}, [(1, 11), (2, 22), (3, 33), (4, 44)]
        ),
    ],
    "I": [
        TupleVariation(
            {"wght": (0.0, 0.5, 1.0)},
            [(3, 3), (1, 1), (4, 4), (1, 1), (5, 5), (9, 9), (2, 2), (6, 6)],
        ),
        TupleVariation(
            {"wght": (-1.0, -1.0, 0.0), "wdth": (0.0, 0.7999878, 0.7999878)},
            [(-8, -88), (7, 77), None, None, (-4, 44), (3, 33), (-2, -22), (1, 11)],
        ),
    ],
}


GVAR_XML = [
    '<version value="1"/>',
    '<reserved value="0"/>',
    '<glyphVariations glyph="I">',
    "  <tuple>",
    '    <coord axis="wght" min="0.0" value="0.5" max="1.0"/>',
    '    <delta pt="0" x="3" y="3"/>',
    '    <delta pt="1" x="1" y="1"/>',
    '    <delta pt="2" x="4" y="4"/>',
    '    <delta pt="3" x="1" y="1"/>',
    '    <delta pt="4" x="5" y="5"/>',
    '    <delta pt="5" x="9" y="9"/>',
    '    <delta pt="6" x="2" y="2"/>',
    '    <delta pt="7" x="6" y="6"/>',
    "  </tuple>",
    "  <tuple>",
    '    <coord axis="wght" value="-1.0"/>',
    '    <coord axis="wdth" value="0.8"/>',
    '    <delta pt="0" x="-8" y="-88"/>',
    '    <delta pt="1" x="7" y="77"/>',
    '    <delta pt="4" x="-4" y="44"/>',
    '    <delta pt="5" x="3" y="33"/>',
    '    <delta pt="6" x="-2" y="-22"/>',
    '    <delta pt="7" x="1" y="11"/>',
    "  </tuple>",
    "</glyphVariations>",
    '<glyphVariations glyph="space">',
    "  <tuple>",
    '    <coord axis="wdth" value="0.7"/>',
    '    <delta pt="0" x="1" y="11"/>',
    '    <delta pt="1" x="2" y="22"/>',
    '    <delta pt="2" x="3" y="33"/>',
    '    <delta pt="3" x="4" y="44"/>',
    "  </tuple>",
    "</glyphVariations>",
]


GVAR_DATA_EMPTY_VARIATIONS = deHexStr(
    "0001 0000 "  #  0: majorVersion=1 minorVersion=0
    "0002 0000 "  #  4: axisCount=2 sharedTupleCount=0
    "0000001c "  #  8: offsetToSharedTuples=28
    "0003 0000 "  # 12: glyphCount=3 flags=0
    "0000001c "  # 16: offsetToGlyphVariationData=28
    "0000 0000 0000 0000"  # 20: offsets=[0, 0, 0, 0]
)  # 28: <end>


def hexencode(s):
    h = hexStr(s).upper()
    return " ".join([h[i : i + 2] for i in range(0, len(h), 2)])


class GVARTableTest(unittest.TestCase):
    def assertVariationsAlmostEqual(self, vars1, vars2):
        self.assertSetEqual(set(vars1.keys()), set(vars2.keys()))
        for glyphName, variations1 in vars1.items():
            variations2 = vars2[glyphName]
            self.assertEqual(len(variations1), len(variations2))
            for v1, v2 in zip(variations1, variations2):
                self.assertSetEqual(set(v1.axes), set(v2.axes))
                for axisTag, support1 in v1.axes.items():
                    support2 = v2.axes[axisTag]
                    self.assertEqual(len(support1), len(support2))
                    for s1, s2 in zip(support1, support2):
                        self.assertAlmostEqual(s1, s2)
                self.assertEqual(v1.coordinates, v2.coordinates)

    def makeFont(self, variations):
        glyphs = [".notdef", "space", "I"]
        Axis = getTableModule("fvar").Axis
        Glyph = getTableModule("glyf").Glyph
        glyf, fvar, gvar = newTable("glyf"), newTable("fvar"), newTable("gvar")
        font = FakeFont(glyphs)
        font.tables = {"glyf": glyf, "gvar": gvar, "fvar": fvar}
        glyf.glyphs = {glyph: Glyph() for glyph in glyphs}
        glyf.glyphs["I"].coordinates = [(10, 10), (10, 20), (20, 20), (20, 10)]
        fvar.axes = [Axis(), Axis()]
        fvar.axes[0].axisTag, fvar.axes[1].axisTag = "wght", "wdth"
        gvar.variations = variations
        return font, gvar

    def test_compile(self):
        font, gvar = self.makeFont(GVAR_VARIATIONS)
        self.assertEqual(hexStr(gvar.compile(font)), hexStr(GVAR_DATA))

    def test_compile_noVariations(self):
        font, gvar = self.makeFont({})
        self.assertEqual(hexStr(gvar.compile(font)), hexStr(GVAR_DATA_EMPTY_VARIATIONS))

    def test_compile_emptyVariations(self):
        font, gvar = self.makeFont({".notdef": [], "space": [], "I": []})
        self.assertEqual(hexStr(gvar.compile(font)), hexStr(GVAR_DATA_EMPTY_VARIATIONS))

    def test_decompile(self):
        for lazy in (True, False, None):
            with self.subTest(lazy=lazy):
                font, gvar = self.makeFont({})
                font.lazy = lazy
                gvar.decompile(GVAR_DATA, font)

                self.assertEqual(
                    all(callable(v) for v in gvar.variations.data.values()),
                    lazy is not False,
                )

                self.assertVariationsAlmostEqual(gvar.variations, GVAR_VARIATIONS)

    def test_decompile_noVariations(self):
        font, gvar = self.makeFont({})
        gvar.decompile(GVAR_DATA_EMPTY_VARIATIONS, font)
        self.assertEqual(gvar.variations, {".notdef": [], "space": [], "I": []})

    def test_fromXML(self):
        font, gvar = self.makeFont({})
        for name, attrs, content in parseXML(GVAR_XML):
            gvar.fromXML(name, attrs, content, ttFont=font)
        self.assertVariationsAlmostEqual(
            gvar.variations, {g: v for g, v in GVAR_VARIATIONS.items() if v}
        )

    def test_toXML(self):
        font, gvar = self.makeFont(GVAR_VARIATIONS)
        self.assertEqual(getXML(gvar.toXML, font), GVAR_XML)

    def test_compileOffsets_shortFormat(self):
        self.assertEqual(
            (deHexStr("00 00 00 02 FF C0"), 0),
            gvarClass.compileOffsets_([0, 4, 0x1FF80]),
        )

    def test_compileOffsets_longFormat(self):
        self.assertEqual(
            (deHexStr("00 00 00 00 00 00 00 04 CA FE BE EF"), 1),
            gvarClass.compileOffsets_([0, 4, 0xCAFEBEEF]),
        )

    def test_decompileOffsets_shortFormat(self):
        decompileOffsets = gvarClass.decompileOffsets_
        data = deHexStr("00 11 22 33 44 55 66 77 88 99 aa bb")
        self.assertEqual(
            [2 * 0x0011, 2 * 0x2233, 2 * 0x4455, 2 * 0x6677, 2 * 0x8899, 2 * 0xAABB],
            list(decompileOffsets(data, tableFormat=0, glyphCount=5)),
        )

    def test_decompileOffsets_longFormat(self):
        decompileOffsets = gvarClass.decompileOffsets_
        data = deHexStr("00 11 22 33 44 55 66 77 88 99 aa bb")
        self.assertEqual(
            [0x00112233, 0x44556677, 0x8899AABB],
            list(decompileOffsets(data, tableFormat=1, glyphCount=2)),
        )


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
