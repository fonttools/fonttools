from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import newTable
import unittest


# Glyph Metamorphosis Table Examples
# Example 1: Non-contextual Glyph Substitution
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6mort.html
# The example given by Apple's 'mort' specification is suboptimally
# encoded: it uses AAT lookup format 6 even though format 8 would be
# more compact.  Because our encoder always uses the most compact
# encoding, this breaks our round-trip testing. Therefore, we changed
# the example to use GlyphID 13 instead of 12 for the 'parenright'
# character; the non-contiguous glyph range for the AAT lookup makes
# format 6 to be most compact.
MORT_NONCONTEXTUAL_DATA = deHexStr(
    "0001 0000 "  #  0: Version=1.0
    "0000 0001 "  #  4: MorphChainCount=1
    "0000 0001 "  #  8: DefaultFlags=1
    "0000 0050 "  # 12: StructLength=80
    "0003 0001 "  # 16: MorphFeatureCount=3, MorphSubtableCount=1
    "0004 0000 "  # 20: Feature[0].FeatureType=4/VertSubst, .FeatureSetting=on
    "0000 0001 "  # 24: Feature[0].EnableFlags=0x00000001
    "FFFF FFFF "  # 28: Feature[0].DisableFlags=0xFFFFFFFF
    "0004 0001 "  # 32: Feature[1].FeatureType=4/VertSubst, .FeatureSetting=off
    "0000 0000 "  # 36: Feature[1].EnableFlags=0x00000000
    "FFFF FFFE "  # 40: Feature[1].DisableFlags=0xFFFFFFFE
    "0000 0001 "  # 44: Feature[2].FeatureType=0/GlyphEffects, .FeatSetting=off
    "0000 0000 "  # 48: Feature[2].EnableFlags=0 (required for last feature)
    "0000 0000 "  # 52: Feature[2].EnableFlags=0 (required for last feature)
    "0020 "  # 56: Subtable[0].StructLength=32
    "80 "  # 58: Subtable[0].CoverageFlags=0x80
    "04 "  # 59: Subtable[0].MorphType=4/NoncontextualMorph
    "0000 0001 "  # 60: Subtable[0].SubFeatureFlags=0x1
    "0006 0004 "  # 64: LookupFormat=6, UnitSize=4
    "0002 0008 "  # 68: NUnits=2, SearchRange=8
    "0001 0000 "  # 72: EntrySelector=1, RangeShift=0
    "000B 0087 "  # 76: Glyph=11 (parenleft); Value=135 (parenleft.vertical)
    "000D 0088 "  # 80: Glyph=13 (parenright); Value=136 (parenright.vertical)
    "FFFF 0000 "  # 84: Glyph=<end>; Value=0
)  # 88: <end>
assert len(MORT_NONCONTEXTUAL_DATA) == 88


MORT_NONCONTEXTUAL_XML = [
    '<Version value="0x00010000"/>',
    "<!-- MorphChainCount=1 -->",
    '<MorphChain index="0">',
    '  <DefaultFlags value="0x00000001"/>',
    "  <!-- StructLength=80 -->",
    "  <!-- MorphFeatureCount=3 -->",
    "  <!-- MorphSubtableCount=1 -->",
    '  <MorphFeature index="0">',
    '    <FeatureType value="4"/>',
    '    <FeatureSetting value="0"/>',
    '    <EnableFlags value="0x00000001"/>',
    '    <DisableFlags value="0xFFFFFFFF"/>',
    "  </MorphFeature>",
    '  <MorphFeature index="1">',
    '    <FeatureType value="4"/>',
    '    <FeatureSetting value="1"/>',
    '    <EnableFlags value="0x00000000"/>',
    '    <DisableFlags value="0xFFFFFFFE"/>',
    "  </MorphFeature>",
    '  <MorphFeature index="2">',
    '    <FeatureType value="0"/>',
    '    <FeatureSetting value="1"/>',
    '    <EnableFlags value="0x00000000"/>',
    '    <DisableFlags value="0x00000000"/>',
    "  </MorphFeature>",
    '  <MorphSubtable index="0">',
    "    <!-- StructLength=32 -->",
    '    <CoverageFlags value="128"/>',
    "    <!-- MorphType=4 -->",
    '    <SubFeatureFlags value="0x00000001"/>',
    "    <NoncontextualMorph>",
    "      <Substitution>",
    '        <Lookup glyph="parenleft" value="parenleft.vertical"/>',
    '        <Lookup glyph="parenright" value="parenright.vertical"/>',
    "      </Substitution>",
    "    </NoncontextualMorph>",
    "  </MorphSubtable>",
    "</MorphChain>",
]


class MORTNoncontextualGlyphSubstitutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        glyphs = [".notdef"] + ["g.%d" % i for i in range(1, 140)]
        glyphs[11], glyphs[13] = "parenleft", "parenright"
        glyphs[135], glyphs[136] = "parenleft.vertical", "parenright.vertical"
        cls.font = FakeFont(glyphs)

    def test_decompile_toXML(self):
        table = newTable("mort")
        table.decompile(MORT_NONCONTEXTUAL_DATA, self.font)
        self.assertEqual(getXML(table.toXML), MORT_NONCONTEXTUAL_XML)

    def test_compile_fromXML(self):
        table = newTable("mort")
        for name, attrs, content in parseXML(MORT_NONCONTEXTUAL_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(
            hexStr(table.compile(self.font)), hexStr(MORT_NONCONTEXTUAL_DATA)
        )


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
