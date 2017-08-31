from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import newTable
import unittest


# A simple 'morx' table with non-contextual glyph substitution.
# Unfortunately, the Apple spec for 'morx' does not contain a complete example.
# The test case has therefore been adapted from the example 'mort' table in
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6mort.html
MORX_NONCONTEXTUAL_DATA = deHexStr(
    '0002 0000 '  #  0: Version=2, Reserved=0
    '0000 0001 '  #  4: MorphChainCount=1
    '0000 0001 '  #  8: DefaultFlags=1
    '0000 0058 '  # 12: StructLength=88
    '0000 0003 '  # 16: MorphFeatureCount=3
    '0000 0001 '  # 20: MorphSubtableCount=1
    '0004 0000 '  # 24: Feature[0].FeatureType=4/VertSubst, .FeatureSetting=on
    '0000 0001 '  # 28: Feature[0].EnableFlags=0x00000001
    'FFFF FFFF '  # 32: Feature[0].DisableFlags=0xFFFFFFFF
    '0004 0001 '  # 36: Feature[1].FeatureType=4/VertSubst, .FeatureSetting=off
    '0000 0000 '  # 40: Feature[1].EnableFlags=0x00000000
    'FFFF FFFE '  # 44: Feature[1].DisableFlags=0xFFFFFFFE
    '0000 0001 '  # 48: Feature[2].FeatureType=0/GlyphEffects, .FeatSetting=off
    '0000 0000 '  # 52: Feature[2].EnableFlags=0 (required for last feature)
    '0000 0000 '  # 56: Feature[2].EnableFlags=0 (required for last feature)
    '0000 0024 '  # 60: Subtable[0].StructLength=36
    '80 '         # 64: Subtable[0].CoverageFlags=0x80
    '00 00 '      # 65: Subtable[0].Reserved=0
    '04 '         # 67: Subtable[0].MorphType=4/NoncontextualMorph
    '0000 0001 '  # 68: Subtable[0].SubFeatureFlags=0x1
    '0006 0004 '  # 72: LookupFormat=6, UnitSize=4
    '0002 0008 '  # 76: NUnits=2, SearchRange=8
    '0001 0000 '  # 80: EntrySelector=1, RangeShift=0
    '000B 0087 '  # 84: Glyph=11 (parenleft); Value=135 (parenleft.vertical)
    '000D 0088 '  # 88: Glyph=13 (parenright); Value=136 (parenright.vertical)
    'FFFF 0000 '  # 92: Glyph=<end>; Value=0
)                 # 96: <end>
assert len(MORX_NONCONTEXTUAL_DATA) == 96


MORX_NONCONTEXTUAL_XML = [
    '<Version value="2"/>',
    '<Reserved value="0"/>',
    '<!-- MorphChainCount=1 -->',
    '<MorphChain index="0">',
    '  <DefaultFlags value="0x00000001"/>',
    '  <!-- StructLength=88 -->',
    '  <!-- MorphFeatureCount=3 -->',
    '  <!-- MorphSubtableCount=1 -->',
    '  <MorphFeature index="0">',
    '    <FeatureType value="4"/>',
    '    <FeatureSetting value="0"/>',
    '    <EnableFlags value="0x00000001"/>',
    '    <DisableFlags value="0xFFFFFFFF"/>',
    '  </MorphFeature>',
    '  <MorphFeature index="1">',
    '    <FeatureType value="4"/>',
    '    <FeatureSetting value="1"/>',
    '    <EnableFlags value="0x00000000"/>',
    '    <DisableFlags value="0xFFFFFFFE"/>',
    '  </MorphFeature>',
    '  <MorphFeature index="2">',
    '    <FeatureType value="0"/>',
    '    <FeatureSetting value="1"/>',
    '    <EnableFlags value="0x00000000"/>',
    '    <DisableFlags value="0x00000000"/>',
    '  </MorphFeature>',
    '  <MorphSubtable index="0">',
    '    <!-- StructLength=36 -->',
    '    <CoverageFlags value="128"/>',
    '    <Reserved value="0"/>',
    '    <!-- MorphType=4 -->',
    '    <SubFeatureFlags value="0x00000001"/>',
    '    <NoncontextualMorph>',
    '      <Substitution>',
    '        <Lookup glyph="parenleft" value="parenleft.vertical"/>',
    '        <Lookup glyph="parenright" value="parenright.vertical"/>',
    '      </Substitution>',
    '    </NoncontextualMorph>',
    '  </MorphSubtable>',
    '</MorphChain>',
]


class MORXNoncontextualGlyphSubstitutionTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        glyphs = ['.notdef'] + ['g.%d' % i for i in range (1, 140)]
        glyphs[11], glyphs[13] = 'parenleft', 'parenright'
        glyphs[135], glyphs[136] = 'parenleft.vertical', 'parenright.vertical'
        cls.font = FakeFont(glyphs)

    def test_decompile_toXML(self):
        table = newTable('morx')
        table.decompile(MORX_NONCONTEXTUAL_DATA, self.font)
        self.assertEqual(getXML(table.toXML, self.font), MORX_NONCONTEXTUAL_XML)

    def test_compile_fromXML(self):
        table = newTable('morx')
        for name, attrs, content in parseXML(MORX_NONCONTEXTUAL_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(MORX_NONCONTEXTUAL_DATA))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

