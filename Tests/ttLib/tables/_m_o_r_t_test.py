import copy

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


# Paired with TestAATMorx.ttf in unicode-org/text-rendering-tests. This table
# exercises all five metamorphosis subtable types.
MORT_ALL_TYPES_DATA = deHexStr(
    "00010000000000010000001f0000021000000005004420000000000100060008"
    "002a00300000001e010104050101010101010101010101010101010101010101"
    "010101010101000000000102002a0000002a8000002a20010088200100000002"
    "0005000a002c003200420000001e010101010401010101010101010101010101"
    "010101010101010101010101000000000100002c000000000000002c00000000"
    "0021000000000000000000050000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "00d42002000000040006000e0030003c0048005000c80000001e010101010101"
    "0405010101010101010101010101010101010101010101010000000001000000"
    "0000000200300000003680000030804800000028800000460000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000c800c800c800c800c800c8"
    "00c800c800c800c800c800c800c800c800c800c800c800c800c800c800c800c8"
    "00c800c800c800c800c800c800c800c8000f0000001820040000000800060004"
    "000100040000000000080009004c2005000000100005000a002c003200420000"
    "001e010101010101010101010104010101010101010101010101010101010101"
    "000000000100002c0000ffffffff002c00200000ffff000c"
)
assert len(MORT_ALL_TYPES_DATA) == 536


# Converted from HarfBuzz's TestMORXFourtyone.ttf. The ligature component
# table contains relative zeroes in the range covered by the final action.
MORT_LIGATURE_REBASE_DATA = deHexStr(
    "00010000000000010000000100000078000200010004000000000001ffffffff"
    "00000001000000000000000000542002000000010007000e001a002200300038"
    "00480000000701010405060101000000000001010200001a0000001a8000001a"
    "803000000000001a8000001e00000002000000000048004a0048004800050006"
)
assert len(MORT_LIGATURE_REBASE_DATA) == 128


# Modeled on the contextual subtables of Apple's CharcoalCY/GenevaCY/
# HelveticaCY: the entry's mark offset is negative, arranged so that
# 2 * (offset + glyphID) lands inside the substitution table only for the
# glyphs the entry can apply to. Words outside the substitution table mean
# "no substitution", so per-entry windows are trimmed rather than covering
# the whole glyph repertoire.
MORT_TRIMMED_CONTEXTUAL_DATA = deHexStr(
    "0001000000000001000000010000004c0000000100400001000000010005000a"
    "0010001a0032001e000104000000000001000000000200100000000000000015"
    "80000000000000100000fffb0000001f00000000"
)
assert len(MORT_TRIMMED_CONTEXTUAL_DATA) == 84


# Same layout, but the entries carry three distinct offsets: -5 (trimmed by
# both bounds), 24 (clamped only by the subtable end, overlapping the first
# window), and 100 (entirely out of bounds, so an empty per-glyph window that
# must still keep its lookup index).
MORT_TRIMMED_CONTEXTUAL_WINDOWS_DATA = deHexStr(
    "0001000000000001000000010000004c0000000100400001000000010005000a"
    "0010001a0032001e000104000000000001000000000200100000000000000015"
    "80000064000000100000fffb0018001f00000000"
)
assert len(MORT_TRIMMED_CONTEXTUAL_WINDOWS_DATA) == 84


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


class MORTAllSubtableTypesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.font = FakeFont(
            [
                ".notdef",
                "space",
                "A",
                "B",
                "C",
                "D",
                "E",
                "F",
                "G",
                "H",
                "O",
                "X",
                "Y",
                "Z",
                "zero",
                "one",
                "one_zero",
                "one_one",
                "one_two",
                "one_three",
                "one_four",
                "one_five",
                "two",
                "three",
                "four",
                "five",
                "six",
                "seven",
                "eight",
                "nine",
            ]
        )

    def decompile(self, data):
        table = newTable("mort")
        table.decompile(data, self.font)
        return table

    def assertSemantics(self, table):
        subtables = table.table.MorphChain[0].MorphSubtable
        self.assertEqual(
            [subtable.MorphType for subtable in subtables], [0, 1, 2, 4, 5]
        )

        rearrangement = subtables[0].SubStruct.StateTable
        self.assertTrue(rearrangement.States[0].Transitions[4].MarkFirst)
        transition = rearrangement.States[0].Transitions[5]
        self.assertTrue(transition.MarkLast)
        self.assertEqual(transition.Verb, 1)

        contextual = subtables[1].SubStruct.StateTable
        self.assertEqual(contextual.PerGlyphLookups, [{"C": "D"}])
        self.assertEqual(contextual.States[0].Transitions[4].CurrentIndex, 0)

        ligature = subtables[2].SubStruct.StateTable
        transition = ligature.States[1].Transitions[5]
        self.assertTrue(transition.SetComponent)
        self.assertEqual(
            [(action.GlyphIndexDelta, action.Store) for action in transition.Actions],
            [(0, False), (30, False)],
        )
        self.assertEqual(ligature.LigComponents, [0] * 60)
        self.assertEqual(ligature.Ligatures, ["one"])

        self.assertEqual(subtables[3].SubStruct.Substitution, {"G": "H"})

        insertion = subtables[4].SubStruct.StateTable
        transition = insertion.States[0].Transitions[4]
        self.assertEqual(transition.CurrentInsertionAction, ["Y"])

    def test_decompile_all_types(self):
        self.assertSemantics(self.decompile(MORT_ALL_TYPES_DATA))

    def test_binary_roundtrip(self):
        table = self.decompile(MORT_ALL_TYPES_DATA)
        self.assertSemantics(self.decompile(table.compile(self.font)))

    def test_xml_roundtrip(self):
        table = self.decompile(MORT_ALL_TYPES_DATA)
        compiled = newTable("mort")
        for name, attrs, content in parseXML(getXML(table.toXML)):
            compiled.fromXML(name, attrs, content, font=self.font)
        self.assertSemantics(self.decompile(compiled.compile(self.font)))

    def test_xml_roundtrip_preserves_unused_glyph_class(self):
        table = self.decompile(MORT_ALL_TYPES_DATA)
        stateTable = table.table.MorphChain[0].MorphSubtable[0].SubStruct.StateTable
        stateTable.GlyphClassCount = 7
        for state in stateTable.States:
            state.Transitions[6] = copy.deepcopy(state.Transitions[5])

        compiled = newTable("mort")
        for name, attrs, content in parseXML(getXML(table.toXML)):
            compiled.fromXML(name, attrs, content, font=self.font)

        stateTable = (
            self.decompile(compiled.compile(self.font))
            .table.MorphChain[0]
            .MorphSubtable[0]
            .SubStruct.StateTable
        )
        self.assertEqual(stateTable.GlyphClassCount, 7)
        self.assertIn(6, stateTable.States[0].Transitions)


class MORTTrimmedContextualTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.font = FakeFont(
            [".notdef"]
            + ["g%d" % i for i in range(1, 30)]
            + ["hyphen", "emdash"]
            + ["h%d" % i for i in range(32, 40)]
        )

    def decompile(self, data):
        table = newTable("mort")
        table.decompile(data, self.font)
        return table

    def assertSemantics(self, table):
        stateTable = table.table.MorphChain[0].MorphSubtable[0].SubStruct.StateTable
        self.assertEqual(stateTable.PerGlyphLookups, [{"hyphen": "emdash"}])
        self.assertEqual(stateTable.GlyphClasses, {"hyphen": 4})
        transition = stateTable.States[1].Transitions[4]
        self.assertEqual(transition.MarkIndex, 0)
        self.assertEqual(transition.CurrentIndex, 0xFFFF)

    def test_decompile_trimmed_window(self):
        self.assertSemantics(self.decompile(MORT_TRIMMED_CONTEXTUAL_DATA))

    def test_binary_roundtrip(self):
        table = self.decompile(MORT_TRIMMED_CONTEXTUAL_DATA)
        self.assertSemantics(self.decompile(table.compile(self.font)))

    def test_xml_roundtrip(self):
        table = self.decompile(MORT_TRIMMED_CONTEXTUAL_DATA)
        compiled = newTable("mort")
        for name, attrs, content in parseXML(getXML(table.toXML)):
            compiled.fromXML(name, attrs, content, font=self.font)
        self.assertSemantics(self.decompile(compiled.compile(self.font)))

    def assertWindowSemantics(self, table):
        stateTable = table.table.MorphChain[0].MorphSubtable[0].SubStruct.StateTable
        self.assertEqual(
            stateTable.PerGlyphLookups, [{"hyphen": "emdash"}, {"g1": "emdash"}, {}]
        )
        transition = stateTable.States[0].Transitions[4]
        self.assertEqual(transition.MarkIndex, 2)
        self.assertEqual(transition.CurrentIndex, 0xFFFF)
        transition = stateTable.States[1].Transitions[4]
        self.assertEqual(transition.MarkIndex, 0)
        self.assertEqual(transition.CurrentIndex, 1)

    def test_decompile_empty_and_tail_clamped_windows(self):
        self.assertWindowSemantics(self.decompile(MORT_TRIMMED_CONTEXTUAL_WINDOWS_DATA))

    def test_windows_binary_roundtrip(self):
        table = self.decompile(MORT_TRIMMED_CONTEXTUAL_WINDOWS_DATA)
        self.assertWindowSemantics(self.decompile(table.compile(self.font)))

    def test_windows_xml_roundtrip(self):
        table = self.decompile(MORT_TRIMMED_CONTEXTUAL_WINDOWS_DATA)
        compiled = newTable("mort")
        for name, attrs, content in parseXML(getXML(table.toXML)):
            compiled.fromXML(name, attrs, content, font=self.font)
        self.assertWindowSemantics(self.decompile(compiled.compile(self.font)))


class MORTLigatureRoundTripTest(unittest.TestCase):
    def test_binary_roundtrip_preserves_component_rebasing(self):
        font = FakeFont([".notdef", "space", "a", "b", "c", "a_c", "b_c"])
        table = newTable("mort")
        table.decompile(MORT_LIGATURE_REBASE_DATA, font)
        self.assertEqual(table.compile(font), MORT_LIGATURE_REBASE_DATA)

    def test_xml_roundtrip_preserves_component_rebasing(self):
        font = FakeFont([".notdef", "space", "a", "b", "c", "a_c", "b_c"])
        table = newTable("mort")
        table.decompile(MORT_LIGATURE_REBASE_DATA, font)
        xml = getXML(table.toXML)
        first = xml.index("        <MortLigatureRebase>")
        last = xml.index("        </MortLigatureRebase>", first) + 1
        self.assertEqual(
            xml[first:last],
            [
                "        <MortLigatureRebase>",
                '          <Component index="4"/>',
                '          <Component index="5"/>',
                '          <Component index="6"/>',
                '          <Component index="7"/>',
                "        </MortLigatureRebase>",
            ],
        )

        compiled = newTable("mort")
        for name, attrs, content in parseXML(xml):
            compiled.fromXML(name, attrs, content, font=font)

        self.assertEqual(compiled.compile(font), MORT_LIGATURE_REBASE_DATA)


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
