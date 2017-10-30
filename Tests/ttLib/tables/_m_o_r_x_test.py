# coding: utf-8
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
    '    <TextDirection value="Vertical"/>',
    '    <ProcessingOrder value="LayoutOrder"/>',
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


MORX_REARRANGEMENT_DATA = deHexStr(
    '0002 0000 '  #  0: Version=2, Reserved=0
    '0000 0001 '  #  4: MorphChainCount=1
    '0000 0001 '  #  8: DefaultFlags=1
    '0000 0078 '  # 12: StructLength=120 (+8=128)
    '0000 0000 '  # 16: MorphFeatureCount=0
    '0000 0001 '  # 20: MorphSubtableCount=1
    '0000 0068 '  # 24: Subtable[0].StructLength=104 (+24=128)
    '80 '         # 28: Subtable[0].CoverageFlags=0x80
    '00 00 '      # 29: Subtable[0].Reserved=0
    '00 '         # 31: Subtable[0].MorphType=0/RearrangementMorph
    '0000 0001 '  # 32: Subtable[0].SubFeatureFlags=0x1
    '0000 0006 '  # 36: STXHeader.ClassCount=6
    '0000 0010 '  # 40: STXHeader.ClassTableOffset=16 (+36=52)
    '0000 0028 '  # 44: STXHeader.StateArrayOffset=40 (+36=76)
    '0000 004C '  # 48: STXHeader.EntryTableOffset=76 (+36=112)
    '0006 0004 '  # 52: ClassTable.LookupFormat=6, .UnitSize=4
    '0002 0008 '  # 56:   .NUnits=2, .SearchRange=8
    '0001 0000 '  # 60:   .EntrySelector=1, .RangeShift=0
    '0001 0005 '  # 64:   Glyph=A; Class=5
    '0003 0004 '  # 68:   Glyph=C; Class=4
    'FFFF 0000 '  # 72:   Glyph=<end>; Value=0
    '0000 0001 0002 0003 0002 0001 '  #  76: State[0][0..5]
    '0003 0003 0003 0003 0003 0003 '  #  88: State[1][0..5]
    '0001 0003 0003 0003 0002 0002 '  # 100: State[2][0..5]
    '0002 FFFF '  # 112: Entries[0].NewState=2, .Flags=0xFFFF
    '0001 A00D '  # 116: Entries[1].NewState=1, .Flags=0xA00D
    '0000 8006 '  # 120: Entries[2].NewState=0, .Flags=0x8006
    '0002 0000 '  # 124: Entries[3].NewState=2, .Flags=0x0000
)                 # 128: <end>
assert len(MORX_REARRANGEMENT_DATA) == 128, len(MORX_REARRANGEMENT_DATA)


MORX_REARRANGEMENT_XML = [
    '<Version value="2"/>',
    '<Reserved value="0"/>',
    '<!-- MorphChainCount=1 -->',
    '<MorphChain index="0">',
    '  <DefaultFlags value="0x00000001"/>',
    '  <!-- StructLength=120 -->',
    '  <!-- MorphFeatureCount=0 -->',
    '  <!-- MorphSubtableCount=1 -->',
    '  <MorphSubtable index="0">',
    '    <!-- StructLength=104 -->',
    '    <TextDirection value="Vertical"/>',
    '    <ProcessingOrder value="LayoutOrder"/>',
    '    <!-- MorphType=0 -->',
    '    <SubFeatureFlags value="0x00000001"/>',
    '    <RearrangementMorph>',
    '      <StateTable>',
    '        <!-- GlyphClassCount=6 -->',
    '        <GlyphClass glyph="A" value="5"/>',
    '        <GlyphClass glyph="C" value="4"/>',
    '        <State index="0">',
    '          <Transition onGlyphClass="0">',
    '            <NewState value="2"/>',
    '            <Flags value="MarkFirst,DontAdvance,MarkLast"/>',
    '            <ReservedFlags value="0x1FF0"/>',
    '            <Verb value="15"/><!-- ABxCD ⇒ DCxBA -->',
    '          </Transition>',
    '          <Transition onGlyphClass="1">',
    '            <NewState value="1"/>',
    '            <Flags value="MarkFirst,MarkLast"/>',
    '            <Verb value="13"/><!-- ABxCD ⇒ CDxBA -->',
    '          </Transition>',
    '          <Transition onGlyphClass="2">',
    '            <NewState value="0"/>',
    '            <Flags value="MarkFirst"/>',
    '            <Verb value="6"/><!-- xCD ⇒ CDx -->',
    '          </Transition>',
    '          <Transition onGlyphClass="3">',
    '            <NewState value="2"/>',
    '            <Verb value="0"/><!-- no change -->',
    '          </Transition>',
    '          <Transition onGlyphClass="4">',
    '            <NewState value="0"/>',
    '            <Flags value="MarkFirst"/>',
    '            <Verb value="6"/><!-- xCD ⇒ CDx -->',
    '          </Transition>',
    '          <Transition onGlyphClass="5">',
    '            <NewState value="1"/>',
    '            <Flags value="MarkFirst,MarkLast"/>',
    '            <Verb value="13"/><!-- ABxCD ⇒ CDxBA -->',
    '          </Transition>',
    '        </State>',
    '        <State index="1">',
    '          <Transition onGlyphClass="0">',
    '            <NewState value="2"/>',
    '            <Verb value="0"/><!-- no change -->',
    '          </Transition>',
    '          <Transition onGlyphClass="1">',
    '            <NewState value="2"/>',
    '            <Verb value="0"/><!-- no change -->',
    '          </Transition>',
    '          <Transition onGlyphClass="2">',
    '            <NewState value="2"/>',
    '            <Verb value="0"/><!-- no change -->',
    '          </Transition>',
    '          <Transition onGlyphClass="3">',
    '            <NewState value="2"/>',
    '            <Verb value="0"/><!-- no change -->',
    '          </Transition>',
    '          <Transition onGlyphClass="4">',
    '            <NewState value="2"/>',
    '            <Verb value="0"/><!-- no change -->',
    '          </Transition>',
    '          <Transition onGlyphClass="5">',
    '            <NewState value="2"/>',
    '            <Verb value="0"/><!-- no change -->',
    '          </Transition>',
    '        </State>',
    '        <State index="2">',
    '          <Transition onGlyphClass="0">',
    '            <NewState value="1"/>',
    '            <Flags value="MarkFirst,MarkLast"/>',
    '            <Verb value="13"/><!-- ABxCD ⇒ CDxBA -->',
    '          </Transition>',
    '          <Transition onGlyphClass="1">',
    '            <NewState value="2"/>',
    '            <Verb value="0"/><!-- no change -->',
    '          </Transition>',
    '          <Transition onGlyphClass="2">',
    '            <NewState value="2"/>',
    '            <Verb value="0"/><!-- no change -->',
    '          </Transition>',
    '          <Transition onGlyphClass="3">',
    '            <NewState value="2"/>',
    '            <Verb value="0"/><!-- no change -->',
    '          </Transition>',
    '          <Transition onGlyphClass="4">',
    '            <NewState value="0"/>',
    '            <Flags value="MarkFirst"/>',
    '            <Verb value="6"/><!-- xCD ⇒ CDx -->',
    '          </Transition>',
    '          <Transition onGlyphClass="5">',
    '            <NewState value="0"/>',
    '            <Flags value="MarkFirst"/>',
    '            <Verb value="6"/><!-- xCD ⇒ CDx -->',
    '          </Transition>',
    '        </State>',
    '      </StateTable>',
    '    </RearrangementMorph>',
    '  </MorphSubtable>',
    '</MorphChain>',
]


# Taken from “Example 1: A contextal substituation table” in
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6morx.html
# as retrieved on 2017-09-05.
#
# Compared to the example table in Apple’s specification, we’ve
# made the following changes:
#
# * at offsets 0..35, we’ve prepended 36 bytes of boilerplate
#   to make the data a structurally valid ‘morx’ table;
#
# * at offset 36 (offset 0 in Apple’s document), we’ve changed
#   the number of glyph classes from 5 to 6 because the encoded
#   finite-state machine has transitions for six different glyph
#   classes (0..5);
#
# * at offset 52 (offset 16 in Apple’s document), we’ve replaced
#   the presumably leftover ‘XXX’ mark by an actual data offset;
#
# * at offset 72 (offset 36 in Apple’s document), we’ve changed
#   the input GlyphID from 51 to 52. With the original value of 51,
#   the glyph class lookup table can be encoded with equally many
#   bytes in either format 2 or 6; after changing the GlyphID to 52,
#   the most compact encoding is lookup format 6, as used in Apple’s
#   example;
#
# * at offset 90 (offset 54 in Apple’s document), we’ve changed
#   the value for the lookup end-of-table marker from 1 to 0.
#   Fonttools always uses zero for this value, whereas Apple’s
#   spec examples are inconsistently using one of {0, 1, 0xFFFF}
#   for this filler value;
#
# * at offset 172 (offset 136 in Apple’s document), we’ve again changed
#   the input GlyphID from 51 to 52, for the same reason as above.
#
# TODO: Ask Apple to fix “Example 1” in the ‘morx’ specification.
MORX_CONTEXTUAL_DATA = deHexStr(
    '0002 0000 '  #  0: Version=2, Reserved=0
    '0000 0001 '  #  4: MorphChainCount=1
    '0000 0001 '  #  8: DefaultFlags=1
    '0000 00B4 '  # 12: StructLength=180 (+8=188)
    '0000 0000 '  # 16: MorphFeatureCount=0
    '0000 0001 '  # 20: MorphSubtableCount=1
    '0000 00A4 '  # 24: Subtable[0].StructLength=164 (+24=188)
    '80 '         # 28: Subtable[0].CoverageFlags=0x80
    '00 00 '      # 29: Subtable[0].Reserved=0
    '01 '         # 31: Subtable[0].MorphType=1/ContextualMorph
    '0000 0001 '  # 32: Subtable[0].SubFeatureFlags=0x1
    '0000 0006 '  # 36: STXHeader.ClassCount=6
    '0000 0014 '  # 40: STXHeader.ClassTableOffset=20 (+36=56)
    '0000 0038 '  # 44: STXHeader.StateArrayOffset=56 (+36=92)
    '0000 005C '  # 48: STXHeader.EntryTableOffset=92 (+36=128)
    '0000 0074 '  # 52: STXHeader.PerGlyphTableOffset=116 (+36=152)

    # Glyph class table.
    '0006 0004 '  # 56: ClassTable.LookupFormat=6, .UnitSize=4
    '0005 0010 '  # 60:   .NUnits=5, .SearchRange=16
    '0002 0004 '  # 64:   .EntrySelector=2, .RangeShift=4
    '0032 0004 '  # 68:   Glyph=50; Class=4
    '0034 0004 '  # 72:   Glyph=52; Class=4
    '0050 0005 '  # 76:   Glyph=80; Class=5
    '00C9 0004 '  # 80:   Glyph=201; Class=4
    '00CA 0004 '  # 84:   Glyph=202; Class=4
    'FFFF 0000 '  # 88:   Glyph=<end>; Value=<filler>

    # State array.
    '0000 0000 0000 0000 0000 0001 '  #  92: State[0][0..5]
    '0000 0000 0000 0000 0000 0001 '  # 104: State[1][0..5]
    '0000 0000 0000 0000 0002 0001 '  # 116: State[2][0..5]

    # Entry table.
    '0000 0000 '  # 128: Entries[0].NewState=0, .Flags=0
    'FFFF FFFF '  # 132: Entries[0].MarkSubst=None, .CurSubst=None
    '0002 0000 '  # 136: Entries[1].NewState=2, .Flags=0
    'FFFF FFFF '  # 140: Entries[1].MarkSubst=None, .CurSubst=None
    '0000 0000 '  # 144: Entries[2].NewState=0, .Flags=0
    'FFFF 0000 '  # 148: Entries[2].MarkSubst=None, .CurSubst=PerGlyph #0
                  # 152: <no padding needed for 4-byte alignment>

    # Per-glyph lookup tables.
    '0000 0004 '  # 152: Offset from this point to per-glyph lookup #0.

    # Per-glyph lookup #0.
    '0006 0004 '  # 156: ClassTable.LookupFormat=6, .UnitSize=4
    '0004 0010 '  # 160:   .NUnits=4, .SearchRange=16
    '0002 0000 '  # 164:   .EntrySelector=2, .RangeShift=0
    '0032 0258 '  # 168:   Glyph=50; ReplacementGlyph=600
    '0034 0259 '  # 172:   Glyph=52; ReplacementGlyph=601
    '00C9 025A '  # 176:   Glyph=201; ReplacementGlyph=602
    '00CA 0384 '  # 180:   Glyph=202; ReplacementGlyph=900
    'FFFF 0000 '  # 184:   Glyph=<end>; Value=<filler>

)                 # 188: <end>
assert len(MORX_CONTEXTUAL_DATA) == 188, len(MORX_CONTEXTUAL_DATA)


MORX_CONTEXTUAL_XML = [
    '<Version value="2"/>',
    '<Reserved value="0"/>',
    '<!-- MorphChainCount=1 -->',
    '<MorphChain index="0">',
    '  <DefaultFlags value="0x00000001"/>',
    '  <!-- StructLength=180 -->',
    '  <!-- MorphFeatureCount=0 -->',
    '  <!-- MorphSubtableCount=1 -->',
    '  <MorphSubtable index="0">',
    '    <!-- StructLength=164 -->',
    '    <TextDirection value="Vertical"/>',
    '    <ProcessingOrder value="LayoutOrder"/>',
    '    <!-- MorphType=1 -->',
    '    <SubFeatureFlags value="0x00000001"/>',
    '    <ContextualMorph>',
    '      <StateTable>',
    '        <!-- GlyphClassCount=6 -->',
    '        <GlyphClass glyph="A" value="4"/>',
    '        <GlyphClass glyph="B" value="4"/>',
    '        <GlyphClass glyph="C" value="5"/>',
    '        <GlyphClass glyph="X" value="4"/>',
    '        <GlyphClass glyph="Y" value="4"/>',
    '        <State index="0">',
    '          <Transition onGlyphClass="0">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="1">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="2">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="3">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="4">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="5">',
    '            <NewState value="2"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '        </State>',
    '        <State index="1">',
    '          <Transition onGlyphClass="0">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="1">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="2">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="3">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="4">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="5">',
    '            <NewState value="2"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '        </State>',
    '        <State index="2">',
    '          <Transition onGlyphClass="0">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="1">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="2">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="3">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="4">',
    '            <NewState value="0"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="5">',
    '            <NewState value="2"/>',
    '            <MarkIndex value="65535"/>',
    '            <CurrentIndex value="65535"/>',
    '          </Transition>',
    '        </State>',
    '        <PerGlyphLookup index="0">',
    '          <Lookup glyph="A" value="A.swash"/>',
    '          <Lookup glyph="B" value="B.swash"/>',
    '          <Lookup glyph="X" value="X.swash"/>',
    '          <Lookup glyph="Y" value="Y.swash"/>',
    '        </PerGlyphLookup>',
    '      </StateTable>',
    '    </ContextualMorph>',
    '  </MorphSubtable>',
    '</MorphChain>',
]


# Taken from “Example 2: A ligature table” in
# https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6morx.html
# as retrieved on 2017-09-11.
#
# Compared to the example table in Apple’s specification, we’ve
# made the following changes:
#
# * at offsets 0..35, we’ve prepended 36 bytes of boilerplate
#   to make the data a structurally valid ‘morx’ table;
#
# * at offsets 88..91 (offsets 52..55 in Apple’s document), we’ve
#   changed the range of the third segment from 23..24 to 26..28.
#   The hexdump values in Apple’s specification are completely wrong;
#   the values from the comments would work, but they can be encoded
#   more compactly than in the specification example. For round-trip
#   testing, we omit the ‘f’ glyph, which makes AAT lookup format 2
#   the most compact encoding;
#
# * at offsets 92..93 (offsets 56..57 in Apple’s document), we’ve
#   changed the glyph class of the third segment from 5 to 6, which
#   matches the values from the comments to the spec (but not the
#   Apple’s hexdump).
#
# TODO: Ask Apple to fix “Example 2” in the ‘morx’ specification.
MORX_LIGATURE_DATA = deHexStr(
    '0002 0000 '  #  0: Version=2, Reserved=0
    '0000 0001 '  #  4: MorphChainCount=1
    '0000 0001 '  #  8: DefaultFlags=1
    '0000 00DA '  # 12: StructLength=218 (+8=226)
    '0000 0000 '  # 16: MorphFeatureCount=0
    '0000 0001 '  # 20: MorphSubtableCount=1
    '0000 00CA '  # 24: Subtable[0].StructLength=202 (+24=226)
    '80 '         # 28: Subtable[0].CoverageFlags=0x80
    '00 00 '      # 29: Subtable[0].Reserved=0
    '02 '         # 31: Subtable[0].MorphType=2/LigatureMorph
    '0000 0001 '  # 32: Subtable[0].SubFeatureFlags=0x1

    # State table header.
    '0000 0007 '  # 36: STXHeader.ClassCount=7
    '0000 001C '  # 40: STXHeader.ClassTableOffset=28 (+36=64)
    '0000 0040 '  # 44: STXHeader.StateArrayOffset=64 (+36=100)
    '0000 0078 '  # 48: STXHeader.EntryTableOffset=120 (+36=156)
    '0000 0090 '  # 52: STXHeader.LigActionsOffset=144 (+36=180)
    '0000 009C '  # 56: STXHeader.LigComponentsOffset=156 (+36=192)
    '0000 00AE '  # 60: STXHeader.LigListOffset=174 (+36=210)

    # Glyph class table.
    '0002 0006 '       # 64: ClassTable.LookupFormat=2, .UnitSize=6
    '0003 000C '       # 68:   .NUnits=3, .SearchRange=12
    '0001 0006 '       # 72:   .EntrySelector=1, .RangeShift=6
    '0016 0014 0004 '  # 76: GlyphID 20..22 [a..c] -> GlyphClass 4
    '0018 0017 0005 '  # 82: GlyphID 23..24 [d..e] -> GlyphClass 5
    '001C 001A 0006 '  # 88: GlyphID 26..28 [g..i] -> GlyphClass 6
    'FFFF FFFF 0000 '  # 94: <end of lookup>

    # State array.
    '0000 0000 0000 0000 0001 0000 0000 '  # 100: State[0][0..6]
    '0000 0000 0000 0000 0001 0000 0000 '  # 114: State[1][0..6]
    '0000 0000 0000 0000 0001 0002 0000 '  # 128: State[2][0..6]
    '0000 0000 0000 0000 0001 0002 0003 '  # 142: State[3][0..6]

    # Entry table.
    '0000 0000 '  # 156: Entries[0].NewState=0, .Flags=0
    '0000 '       # 160: Entries[0].ActionIndex=<n/a> because no 0x2000 flag
    '0002 8000 '  # 162: Entries[1].NewState=2, .Flags=0x8000 (SetComponent)
    '0000 '       # 166: Entries[1].ActionIndex=<n/a> because no 0x2000 flag
    '0003 8000 '  # 168: Entries[2].NewState=3, .Flags=0x8000 (SetComponent)
    '0000 '       # 172: Entries[2].ActionIndex=<n/a> because no 0x2000 flag
    '0000 A000 '  # 174: Entries[3].NewState=0, .Flags=0xA000 (SetComponent,Act)
    '0000 '       # 178: Entries[3].ActionIndex=0 (start at Action[0])

    # Ligature actions table.
    '3FFF FFE7 '  # 180: Action[0].Flags=0, .GlyphIndexDelta=-25
    '3FFF FFED '  # 184: Action[1].Flags=0, .GlyphIndexDelta=-19
    'BFFF FFF2 '  # 188: Action[2].Flags=<end of list>, .GlyphIndexDelta=-14

    # Ligature component table.
    '0000 0001 '  # 192: LigComponent[0]=0, LigComponent[1]=1
    '0002 0003 '  # 196: LigComponent[2]=2, LigComponent[3]=3
    '0000 0004 '  # 200: LigComponent[4]=0, LigComponent[5]=4
    '0000 0008 '  # 204: LigComponent[6]=0, LigComponent[7]=8
    '0010      '  # 208: LigComponent[8]=16

    # Ligature list.
    '03E8 03E9 '  # 210: LigList[0]=1000, LigList[1]=1001
    '03EA 03EB '  # 214: LigList[2]=1002, LigList[3]=1003
    '03EC 03ED '  # 218: LigList[4]=1004, LigList[3]=1005
    '03EE 03EF '  # 222: LigList[5]=1006, LigList[6]=1007
)   # 226: <end>
assert len(MORX_LIGATURE_DATA) == 226, len(MORX_LIGATURE_DATA)


MORX_LIGATURE_XML = [
    '<Version value="2"/>',
    '<Reserved value="0"/>',
    '<!-- MorphChainCount=1 -->',
    '<MorphChain index="0">',
    '  <DefaultFlags value="0x00000001"/>',
    '  <!-- StructLength=218 -->',
    '  <!-- MorphFeatureCount=0 -->',
    '  <!-- MorphSubtableCount=1 -->',
    '  <MorphSubtable index="0">',
    '    <!-- StructLength=202 -->',
    '    <TextDirection value="Vertical"/>',
    '    <ProcessingOrder value="LayoutOrder"/>',
    '    <!-- MorphType=2 -->',
    '    <SubFeatureFlags value="0x00000001"/>',
    '    <LigatureMorph>',
    '      <StateTable>',
    '        <!-- GlyphClassCount=7 -->',
    '        <GlyphClass glyph="a" value="4"/>',
    '        <GlyphClass glyph="b" value="4"/>',
    '        <GlyphClass glyph="c" value="4"/>',
    '        <GlyphClass glyph="d" value="5"/>',
    '        <GlyphClass glyph="e" value="5"/>',
    '        <GlyphClass glyph="g" value="6"/>',
    '        <GlyphClass glyph="h" value="6"/>',
    '        <GlyphClass glyph="i" value="6"/>',
    '        <State index="0">',
    '          <Transition onGlyphClass="0">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="1">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="2">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="3">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="4">',
    '            <NewState value="2"/>',
    '            <Flags value="SetComponent"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="5">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="6">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '        </State>',
    '        <State index="1">',
    '          <Transition onGlyphClass="0">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="1">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="2">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="3">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="4">',
    '            <NewState value="2"/>',
    '            <Flags value="SetComponent"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="5">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="6">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '        </State>',
    '        <State index="2">',
    '          <Transition onGlyphClass="0">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="1">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="2">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="3">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="4">',
    '            <NewState value="2"/>',
    '            <Flags value="SetComponent"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="5">',
    '            <NewState value="3"/>',
    '            <Flags value="SetComponent"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="6">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '        </State>',
    '        <State index="3">',
    '          <Transition onGlyphClass="0">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="1">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="2">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="3">',
    '            <NewState value="0"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="4">',
    '            <NewState value="2"/>',
    '            <Flags value="SetComponent"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="5">',
    '            <NewState value="3"/>',
    '            <Flags value="SetComponent"/>',
    '          </Transition>',
    '          <Transition onGlyphClass="6">',
    '            <NewState value="0"/>',
    '            <Flags value="SetComponent"/>',
    '            <Action GlyphIndexDelta="-25"/>',
    '            <Action GlyphIndexDelta="-19"/>',
    '            <Action GlyphIndexDelta="-14"/>',
    '          </Transition>',
    '        </State>',
    '        <LigComponents>',
    '          <LigComponent index="0" value="0"/>',
    '          <LigComponent index="1" value="1"/>',
    '          <LigComponent index="2" value="2"/>',
    '          <LigComponent index="3" value="3"/>',
    '          <LigComponent index="4" value="0"/>',
    '          <LigComponent index="5" value="4"/>',
    '          <LigComponent index="6" value="0"/>',
    '          <LigComponent index="7" value="8"/>',
    '          <LigComponent index="8" value="16"/>',
    '        </LigComponents>',
    '        <Ligatures>',
    '          <Ligature glyph="adf" index="0"/>',
    '          <Ligature glyph="adg" index="1"/>',
    '          <Ligature glyph="adh" index="2"/>',
    '          <Ligature glyph="adi" index="3"/>',
    '          <Ligature glyph="aef" index="4"/>',
    '          <Ligature glyph="aeg" index="5"/>',
    '          <Ligature glyph="aeh" index="6"/>',
    '          <Ligature glyph="aei" index="7"/>',
    '        </Ligatures>',
    '      </StateTable>',
    '    </LigatureMorph>',
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
        self.assertEqual(getXML(table.toXML), MORX_NONCONTEXTUAL_XML)

    def test_compile_fromXML(self):
        table = newTable('morx')
        for name, attrs, content in parseXML(MORX_NONCONTEXTUAL_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(MORX_NONCONTEXTUAL_DATA))


class MORXRearrangementTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.font = FakeFont(['.nodef', 'A', 'B', 'C'])

    def test_decompile_toXML(self):
        table = newTable('morx')
        table.decompile(MORX_REARRANGEMENT_DATA, self.font)
        self.assertEqual(getXML(table.toXML), MORX_REARRANGEMENT_XML)

    def test_compile_fromXML(self):
        table = newTable('morx')
        for name, attrs, content in parseXML(MORX_REARRANGEMENT_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(MORX_REARRANGEMENT_DATA))


class MORXContextualSubstitutionTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        g = ['.notdef'] + ['g.%d' % i for i in range (1, 910)]
        g[80] = 'C'
        g[50], g[52], g[201], g[202] = 'A', 'B', 'X', 'Y'
        g[600], g[601], g[602], g[900] = (
            'A.swash', 'B.swash', 'X.swash', 'Y.swash')
        cls.font = FakeFont(g)

    def test_decompile_toXML(self):
        table = newTable('morx')
        table.decompile(MORX_CONTEXTUAL_DATA, self.font)
        self.assertEqual(getXML(table.toXML), MORX_CONTEXTUAL_XML)

    def test_compile_fromXML(self):
        table = newTable('morx')
        for name, attrs, content in parseXML(MORX_CONTEXTUAL_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(MORX_CONTEXTUAL_DATA))


class MORXLigatureSubstitutionTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        g = ['.notdef'] + ['g.%d' % i for i in range (1, 1515)]
        g[20:29] = 'a b c d e f g h i'.split()
        g[1000:1008] = 'adf adg adh adi aef aeg aeh aei'.split()
        g[1008:1016] = 'bdf bdg bdh bdi bef beg beh bei'.split()
        g[1500:1507] = 'cdf cdg cdh cdi cef ceg ceh'.split()
        g[1511] = 'cei'
        cls.font = FakeFont(g)

    def test_decompile_toXML(self):
        table = newTable('morx')
        table.decompile(MORX_LIGATURE_DATA, self.font)
        self.assertEqual(getXML(table.toXML), MORX_LIGATURE_XML)

    def test_compile_fromXML(self):
        table = newTable('morx')
        for name, attrs, content in parseXML(MORX_LIGATURE_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)),
                         hexStr(MORX_LIGATURE_DATA))


class MORXCoverageFlagsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.font = FakeFont(['.notdef', 'A', 'B', 'C'])

    def checkFlags(self, flags, textDirection, processingOrder,
                   checkCompile=True):
        data = bytesjoin([
            MORX_REARRANGEMENT_DATA[:28],
            bytechr(flags << 4),
            MORX_REARRANGEMENT_DATA[29:]])
        xml = []
        for line in MORX_REARRANGEMENT_XML:
            if line.startswith('    <TextDirection '):
                line = '    <TextDirection value="%s"/>' % textDirection
            elif line.startswith('    <ProcessingOrder '):
                line = '    <ProcessingOrder value="%s"/>' % processingOrder
            xml.append(line)
        table1 = newTable('morx')
        table1.decompile(data, self.font)
        self.assertEqual(getXML(table1.toXML), xml)
        if checkCompile:
            table2 = newTable('morx')
            for name, attrs, content in parseXML(xml):
                table2.fromXML(name, attrs, content, font=self.font)
            self.assertEqual(hexStr(table2.compile(self.font)), hexStr(data))

    def test_CoverageFlags(self):
        self.checkFlags(0x0, "Horizontal", "LayoutOrder")
        self.checkFlags(0x1, "Horizontal", "LogicalOrder")
        self.checkFlags(0x2, "Any", "LayoutOrder")
        self.checkFlags(0x3, "Any", "LogicalOrder")
        self.checkFlags(0x4, "Horizontal", "ReversedLayoutOrder")
        self.checkFlags(0x5, "Horizontal", "ReversedLogicalOrder")
        self.checkFlags(0x6, "Any", "ReversedLayoutOrder")
        self.checkFlags(0x7, "Any", "ReversedLogicalOrder")
        self.checkFlags(0x8, "Vertical", "LayoutOrder")
        self.checkFlags(0x9, "Vertical", "LogicalOrder")
        # We do not always check the compilation to binary data:
        # some flag combinations do not make sense to emit in binary.
        # Specifically, if bit 28 (TextDirection=Any) is set in
        # CoverageFlags, bit 30 (TextDirection=Vertical) is to be
        # ignored according to the 'morx' specification. We still want
        # to test the _decoding_ of 'morx' subtables whose CoverageFlags
        # have both bits 28 and 30 set, since this is a valid flag
        # combination with defined semantics.  However, our encoder
        # does not set TextDirection=Vertical when TextDirection=Any.
        self.checkFlags(0xA, "Any", "LayoutOrder", checkCompile=False)
        self.checkFlags(0xB, "Any", "LogicalOrder", checkCompile=False)
        self.checkFlags(0xC, "Vertical", "ReversedLayoutOrder")
        self.checkFlags(0xD, "Vertical", "ReversedLogicalOrder")
        self.checkFlags(0xE, "Any", "ReversedLayoutOrder", checkCompile=False)
        self.checkFlags(0xF, "Any", "ReversedLogicalOrder", checkCompile=False)

    def test_ReservedCoverageFlags(self):
        # 8A BC DE = TextDirection=Vertical, Reserved=0xABCDE
        # Note that the lower 4 bits of the first byte are already
        # part of the Reserved value. We test the full round-trip
        # to encoding and decoding is quite hairy.
        data = bytesjoin([
            MORX_REARRANGEMENT_DATA[:28],
            bytechr(0x8A), bytechr(0xBC), bytechr(0xDE),
            MORX_REARRANGEMENT_DATA[31:]])
        table = newTable('morx')
        table.decompile(data, self.font)
        subtable = table.table.MorphChain[0].MorphSubtable[0]
        self.assertEqual(subtable.Reserved, 0xABCDE)
        xml = getXML(table.toXML)
        self.assertIn('    <Reserved value="0xabcde"/>', xml)
        table2 = newTable('morx')
        for name, attrs, content in parseXML(xml):
            table2.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table2.compile(self.font)[28:31]), "8abcde")


class UnsupportedMorxLookupTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def test_unsupportedLookupType(self):
        data = bytesjoin([
            MORX_NONCONTEXTUAL_DATA[:67],
            bytechr(66),
            MORX_NONCONTEXTUAL_DATA[69:]])
        with self.assertRaisesRegex(AssertionError,
                                    r"unsupported 'morx' lookup type 66"):
            morx = newTable('morx')
            morx.decompile(data, FakeFont(['.notdef']))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
