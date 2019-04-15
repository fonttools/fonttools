from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.testTools import getXML
from fontTools.otlLib import builder
from fontTools.ttLib.tables import otTables
from itertools import chain
import unittest


class BuilderTest(unittest.TestCase):
    GLYPHS = (".notdef space zero one two three four five six "
              "A B C a b c grave acute cedilla f_f_i f_i c_t").split()
    GLYPHMAP = {name: num for num, name in enumerate(GLYPHS)}

    ANCHOR1 = builder.buildAnchor(11, -11)
    ANCHOR2 = builder.buildAnchor(22, -22)
    ANCHOR3 = builder.buildAnchor(33, -33)

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

    def test_buildAnchor_format1(self):
        anchor = builder.buildAnchor(23, 42)
        self.assertEqual(getXML(anchor.toXML),
                         ['<Anchor Format="1">',
                          '  <XCoordinate value="23"/>',
                          '  <YCoordinate value="42"/>',
                          '</Anchor>'])

    def test_buildAnchor_format2(self):
        anchor = builder.buildAnchor(23, 42, point=17)
        self.assertEqual(getXML(anchor.toXML),
                         ['<Anchor Format="2">',
                          '  <XCoordinate value="23"/>',
                          '  <YCoordinate value="42"/>',
                          '  <AnchorPoint value="17"/>',
                          '</Anchor>'])

    def test_buildAnchor_format3(self):
        anchor = builder.buildAnchor(
            23, 42,
            deviceX=builder.buildDevice({1: 1, 0: 0}),
            deviceY=builder.buildDevice({7: 7}))
        self.assertEqual(getXML(anchor.toXML),
                         ['<Anchor Format="3">',
                          '  <XCoordinate value="23"/>',
                          '  <YCoordinate value="42"/>',
                          '  <XDeviceTable>',
                          '    <StartSize value="0"/>',
                          '    <EndSize value="1"/>',
                          '    <DeltaFormat value="1"/>',
                          '    <DeltaValue value="[0, 1]"/>',
                          '  </XDeviceTable>',
                          '  <YDeviceTable>',
                          '    <StartSize value="7"/>',
                          '    <EndSize value="7"/>',
                          '    <DeltaFormat value="2"/>',
                          '    <DeltaValue value="[7]"/>',
                          '  </YDeviceTable>',
                          '</Anchor>'])

    def test_buildAttachList(self):
        attachList = builder.buildAttachList({
            "zero": [23, 7], "one": [1],
        }, self.GLYPHMAP)
        self.assertEqual(getXML(attachList.toXML),
                         ['<AttachList>',
                          '  <Coverage>',
                          '    <Glyph value="zero"/>',
                          '    <Glyph value="one"/>',
                          '  </Coverage>',
                          '  <!-- GlyphCount=2 -->',
                          '  <AttachPoint index="0">',
                          '    <!-- PointCount=2 -->',
                          '    <PointIndex index="0" value="7"/>',
                          '    <PointIndex index="1" value="23"/>',
                          '  </AttachPoint>',
                          '  <AttachPoint index="1">',
                          '    <!-- PointCount=1 -->',
                          '    <PointIndex index="0" value="1"/>',
                          '  </AttachPoint>',
                          '</AttachList>'])

    def test_buildAttachList_empty(self):
        self.assertIsNone(builder.buildAttachList({}, self.GLYPHMAP))

    def test_buildAttachPoint(self):
        attachPoint = builder.buildAttachPoint([7, 3])
        self.assertEqual(getXML(attachPoint.toXML),
                         ['<AttachPoint>',
                          '  <!-- PointCount=2 -->',
                          '  <PointIndex index="0" value="3"/>',
                          '  <PointIndex index="1" value="7"/>',
                          '</AttachPoint>'])

    def test_buildAttachPoint_empty(self):
        self.assertIsNone(builder.buildAttachPoint([]))

    def test_buildAttachPoint_duplicate(self):
        attachPoint = builder.buildAttachPoint([7, 3, 7])
        self.assertEqual(getXML(attachPoint.toXML),
                         ['<AttachPoint>',
                          '  <!-- PointCount=2 -->',
                          '  <PointIndex index="0" value="3"/>',
                          '  <PointIndex index="1" value="7"/>',
                          '</AttachPoint>'])


    def test_buildBaseArray(self):
        anchor = builder.buildAnchor
        baseArray = builder.buildBaseArray({
            "a": {2: anchor(300, 80)},
            "c": {1: anchor(300, 80), 2: anchor(300, -20)}
        }, numMarkClasses=4, glyphMap=self.GLYPHMAP)
        self.assertEqual(getXML(baseArray.toXML),
                         ['<BaseArray>',
                          '  <!-- BaseCount=2 -->',
                          '  <BaseRecord index="0">',
                          '    <BaseAnchor index="0" empty="1"/>',
                          '    <BaseAnchor index="1" empty="1"/>',
                          '    <BaseAnchor index="2" Format="1">',
                          '      <XCoordinate value="300"/>',
                          '      <YCoordinate value="80"/>',
                          '    </BaseAnchor>',
                          '    <BaseAnchor index="3" empty="1"/>',
                          '  </BaseRecord>',
                          '  <BaseRecord index="1">',
                          '    <BaseAnchor index="0" empty="1"/>',
                          '    <BaseAnchor index="1" Format="1">',
                          '      <XCoordinate value="300"/>',
                          '      <YCoordinate value="80"/>',
                          '    </BaseAnchor>',
                          '    <BaseAnchor index="2" Format="1">',
                          '      <XCoordinate value="300"/>',
                          '      <YCoordinate value="-20"/>',
                          '    </BaseAnchor>',
                          '    <BaseAnchor index="3" empty="1"/>',
                          '  </BaseRecord>',
                          '</BaseArray>'])

    def test_buildBaseRecord(self):
        a = builder.buildAnchor
        rec = builder.buildBaseRecord([a(500, -20), None, a(300, -15)])
        self.assertEqual(getXML(rec.toXML),
                         ['<BaseRecord>',
                          '  <BaseAnchor index="0" Format="1">',
                          '    <XCoordinate value="500"/>',
                          '    <YCoordinate value="-20"/>',
                          '  </BaseAnchor>',
                          '  <BaseAnchor index="1" empty="1"/>',
                          '  <BaseAnchor index="2" Format="1">',
                          '    <XCoordinate value="300"/>',
                          '    <YCoordinate value="-15"/>',
                          '  </BaseAnchor>',
                          '</BaseRecord>'])

    def test_buildCaretValueForCoord(self):
        caret = builder.buildCaretValueForCoord(500)
        self.assertEqual(getXML(caret.toXML),
                         ['<CaretValue Format="1">',
                          '  <Coordinate value="500"/>',
                          '</CaretValue>'])

    def test_buildCaretValueForPoint(self):
        caret = builder.buildCaretValueForPoint(23)
        self.assertEqual(getXML(caret.toXML),
                         ['<CaretValue Format="2">',
                          '  <CaretValuePoint value="23"/>',
                          '</CaretValue>'])

    def test_buildComponentRecord(self):
        a = builder.buildAnchor
        rec = builder.buildComponentRecord([a(500, -20), None, a(300, -15)])
        self.assertEqual(getXML(rec.toXML),
                         ['<ComponentRecord>',
                          '  <LigatureAnchor index="0" Format="1">',
                          '    <XCoordinate value="500"/>',
                          '    <YCoordinate value="-20"/>',
                          '  </LigatureAnchor>',
                          '  <LigatureAnchor index="1" empty="1"/>',
                          '  <LigatureAnchor index="2" Format="1">',
                          '    <XCoordinate value="300"/>',
                          '    <YCoordinate value="-15"/>',
                          '  </LigatureAnchor>',
                          '</ComponentRecord>'])

    def test_buildComponentRecord_empty(self):
        self.assertIsNone(builder.buildComponentRecord([]))

    def test_buildComponentRecord_None(self):
        self.assertIsNone(builder.buildComponentRecord(None))

    def test_buildCoverage(self):
        cov = builder.buildCoverage({"two", "four"}, {"two": 2, "four": 4})
        self.assertEqual(getXML(cov.toXML),
                         ['<Coverage>',
                          '  <Glyph value="two"/>',
                          '  <Glyph value="four"/>',
                          '</Coverage>'])

    def test_buildCursivePos(self):
        pos = builder.buildCursivePosSubtable({
            "two": (self.ANCHOR1, self.ANCHOR2),
            "four": (self.ANCHOR3, self.ANCHOR1)
        }, self.GLYPHMAP)
        self.assertEqual(getXML(pos.toXML),
                         ['<CursivePos Format="1">',
                          '  <Coverage>',
                          '    <Glyph value="two"/>',
                          '    <Glyph value="four"/>',
                          '  </Coverage>',
                          '  <!-- EntryExitCount=2 -->',
                          '  <EntryExitRecord index="0">',
                          '    <EntryAnchor Format="1">',
                          '      <XCoordinate value="11"/>',
                          '      <YCoordinate value="-11"/>',
                          '    </EntryAnchor>',
                          '    <ExitAnchor Format="1">',
                          '      <XCoordinate value="22"/>',
                          '      <YCoordinate value="-22"/>',
                          '    </ExitAnchor>',
                          '  </EntryExitRecord>',
                          '  <EntryExitRecord index="1">',
                          '    <EntryAnchor Format="1">',
                          '      <XCoordinate value="33"/>',
                          '      <YCoordinate value="-33"/>',
                          '    </EntryAnchor>',
                          '    <ExitAnchor Format="1">',
                          '      <XCoordinate value="11"/>',
                          '      <YCoordinate value="-11"/>',
                          '    </ExitAnchor>',
                          '  </EntryExitRecord>',
                          '</CursivePos>'])

    def test_buildDevice_format1(self):
        device = builder.buildDevice({1:1, 0:0})
        self.assertEqual(getXML(device.toXML),
                         ['<Device>',
                          '  <StartSize value="0"/>',
                          '  <EndSize value="1"/>',
                          '  <DeltaFormat value="1"/>',
                          '  <DeltaValue value="[0, 1]"/>',
                          '</Device>'])

    def test_buildDevice_format2(self):
        device = builder.buildDevice({2:2, 0:1, 1:0})
        self.assertEqual(getXML(device.toXML),
                         ['<Device>',
                          '  <StartSize value="0"/>',
                          '  <EndSize value="2"/>',
                          '  <DeltaFormat value="2"/>',
                          '  <DeltaValue value="[1, 0, 2]"/>',
                          '</Device>'])

    def test_buildDevice_format3(self):
        device = builder.buildDevice({5:3, 1:77})
        self.assertEqual(getXML(device.toXML),
                         ['<Device>',
                          '  <StartSize value="1"/>',
                          '  <EndSize value="5"/>',
                          '  <DeltaFormat value="3"/>',
                          '  <DeltaValue value="[77, 0, 0, 0, 3]"/>',
                          '</Device>'])

    def test_buildLigatureArray(self):
        anchor = builder.buildAnchor
        ligatureArray = builder.buildLigatureArray({
            "f_i": [{2: anchor(300, -20)}, {}],
            "c_t": [{}, {1: anchor(500, 350), 2: anchor(1300, -20)}]
        }, numMarkClasses=4, glyphMap=self.GLYPHMAP)
        self.assertEqual(getXML(ligatureArray.toXML),
                         ['<LigatureArray>',
                          '  <!-- LigatureCount=2 -->',
                          '  <LigatureAttach index="0">',  # f_i
                          '    <!-- ComponentCount=2 -->',
                          '    <ComponentRecord index="0">',
                          '      <LigatureAnchor index="0" empty="1"/>',
                          '      <LigatureAnchor index="1" empty="1"/>',
                          '      <LigatureAnchor index="2" Format="1">',
                          '        <XCoordinate value="300"/>',
                          '        <YCoordinate value="-20"/>',
                          '      </LigatureAnchor>',
                          '      <LigatureAnchor index="3" empty="1"/>',
                          '    </ComponentRecord>',
                          '    <ComponentRecord index="1">',
                          '      <LigatureAnchor index="0" empty="1"/>',
                          '      <LigatureAnchor index="1" empty="1"/>',
                          '      <LigatureAnchor index="2" empty="1"/>',
                          '      <LigatureAnchor index="3" empty="1"/>',
                          '    </ComponentRecord>',
                          '  </LigatureAttach>',
                          '  <LigatureAttach index="1">',
                          '    <!-- ComponentCount=2 -->',
                          '    <ComponentRecord index="0">',
                          '      <LigatureAnchor index="0" empty="1"/>',
                          '      <LigatureAnchor index="1" empty="1"/>',
                          '      <LigatureAnchor index="2" empty="1"/>',
                          '      <LigatureAnchor index="3" empty="1"/>',
                          '    </ComponentRecord>',
                          '    <ComponentRecord index="1">',
                          '      <LigatureAnchor index="0" empty="1"/>',
                          '      <LigatureAnchor index="1" Format="1">',
                          '        <XCoordinate value="500"/>',
                          '        <YCoordinate value="350"/>',
                          '      </LigatureAnchor>',
                          '      <LigatureAnchor index="2" Format="1">',
                          '        <XCoordinate value="1300"/>',
                          '        <YCoordinate value="-20"/>',
                          '      </LigatureAnchor>',
                          '      <LigatureAnchor index="3" empty="1"/>',
                          '    </ComponentRecord>',
                          '  </LigatureAttach>',
                          '</LigatureArray>'])

    def test_buildLigatureAttach(self):
        anchor = builder.buildAnchor
        attach = builder.buildLigatureAttach([
            [anchor(500, -10), None],
            [None, anchor(300, -20), None]])
        self.assertEqual(getXML(attach.toXML),
                         ['<LigatureAttach>',
                          '  <!-- ComponentCount=2 -->',
                          '  <ComponentRecord index="0">',
                          '    <LigatureAnchor index="0" Format="1">',
                          '      <XCoordinate value="500"/>',
                          '      <YCoordinate value="-10"/>',
                          '    </LigatureAnchor>',
                          '    <LigatureAnchor index="1" empty="1"/>',
                          '  </ComponentRecord>',
                          '  <ComponentRecord index="1">',
                          '    <LigatureAnchor index="0" empty="1"/>',
                          '    <LigatureAnchor index="1" Format="1">',
                          '      <XCoordinate value="300"/>',
                          '      <YCoordinate value="-20"/>',
                          '    </LigatureAnchor>',
                          '    <LigatureAnchor index="2" empty="1"/>',
                          '  </ComponentRecord>',
                          '</LigatureAttach>'])

    def test_buildLigatureAttach_emptyComponents(self):
        attach = builder.buildLigatureAttach([[], None])
        self.assertEqual(getXML(attach.toXML),
                         ['<LigatureAttach>',
                          '  <!-- ComponentCount=2 -->',
                          '  <ComponentRecord index="0" empty="1"/>',
                          '  <ComponentRecord index="1" empty="1"/>',
                          '</LigatureAttach>'])

    def test_buildLigatureAttach_noComponents(self):
        attach = builder.buildLigatureAttach([])
        self.assertEqual(getXML(attach.toXML),
                         ['<LigatureAttach>',
                          '  <!-- ComponentCount=0 -->',
                          '</LigatureAttach>'])

    def test_buildLigCaretList(self):
        carets = builder.buildLigCaretList(
            {"f_f_i": [300, 600]}, {"c_t": [42]}, self.GLYPHMAP)
        self.assertEqual(getXML(carets.toXML),
                         ['<LigCaretList>',
                          '  <Coverage>',
                          '    <Glyph value="f_f_i"/>',
                          '    <Glyph value="c_t"/>',
                          '  </Coverage>',
                          '  <!-- LigGlyphCount=2 -->',
                          '  <LigGlyph index="0">',
                          '    <!-- CaretCount=2 -->',
                          '    <CaretValue index="0" Format="1">',
                          '      <Coordinate value="300"/>',
                          '    </CaretValue>',
                          '    <CaretValue index="1" Format="1">',
                          '      <Coordinate value="600"/>',
                          '    </CaretValue>',
                          '  </LigGlyph>',
                          '  <LigGlyph index="1">',
                          '    <!-- CaretCount=1 -->',
                          '    <CaretValue index="0" Format="2">',
                          '      <CaretValuePoint value="42"/>',
                          '    </CaretValue>',
                          '  </LigGlyph>',
                          '</LigCaretList>'])

    def test_buildLigCaretList_bothCoordsAndPointsForSameGlyph(self):
        carets = builder.buildLigCaretList(
            {"f_f_i": [300]}, {"f_f_i": [7]}, self.GLYPHMAP)
        self.assertEqual(getXML(carets.toXML),
                         ['<LigCaretList>',
                          '  <Coverage>',
                          '    <Glyph value="f_f_i"/>',
                          '  </Coverage>',
                          '  <!-- LigGlyphCount=1 -->',
                          '  <LigGlyph index="0">',
                          '    <!-- CaretCount=2 -->',
                          '    <CaretValue index="0" Format="1">',
                          '      <Coordinate value="300"/>',
                          '    </CaretValue>',
                          '    <CaretValue index="1" Format="2">',
                          '      <CaretValuePoint value="7"/>',
                          '    </CaretValue>',
                          '  </LigGlyph>',
                          '</LigCaretList>'])

    def test_buildLigCaretList_empty(self):
        self.assertIsNone(builder.buildLigCaretList({}, {}, self.GLYPHMAP))

    def test_buildLigCaretList_None(self):
        self.assertIsNone(builder.buildLigCaretList(None, None, self.GLYPHMAP))

    def test_buildLigGlyph_coords(self):
        lig = builder.buildLigGlyph([500, 800], None)
        self.assertEqual(getXML(lig.toXML),
                         ['<LigGlyph>',
                          '  <!-- CaretCount=2 -->',
                          '  <CaretValue index="0" Format="1">',
                          '    <Coordinate value="500"/>',
                          '  </CaretValue>',
                          '  <CaretValue index="1" Format="1">',
                          '    <Coordinate value="800"/>',
                          '  </CaretValue>',
                          '</LigGlyph>'])

    def test_buildLigGlyph_empty(self):
        self.assertIsNone(builder.buildLigGlyph([], []))

    def test_buildLigGlyph_None(self):
        self.assertIsNone(builder.buildLigGlyph(None, None))

    def test_buildLigGlyph_points(self):
        lig = builder.buildLigGlyph(None, [2])
        self.assertEqual(getXML(lig.toXML),
                         ['<LigGlyph>',
                          '  <!-- CaretCount=1 -->',
                          '  <CaretValue index="0" Format="2">',
                          '    <CaretValuePoint value="2"/>',
                          '  </CaretValue>',
                          '</LigGlyph>'])

    def test_buildLookup(self):
        s1 = builder.buildSingleSubstSubtable({"one": "two"})
        s2 = builder.buildSingleSubstSubtable({"three": "four"})
        lookup = builder.buildLookup([s1, s2], flags=7)
        self.assertEqual(getXML(lookup.toXML),
                         ['<Lookup>',
                          '  <LookupType value="1"/>',
                          '  <LookupFlag value="7"/>',
                          '  <!-- SubTableCount=2 -->',
                          '  <SingleSubst index="0">',
                          '    <Substitution in="one" out="two"/>',
                          '  </SingleSubst>',
                          '  <SingleSubst index="1">',
                          '    <Substitution in="three" out="four"/>',
                          '  </SingleSubst>',
                          '</Lookup>'])

    def test_buildLookup_badFlags(self):
        s = builder.buildSingleSubstSubtable({"one": "two"})
        self.assertRaisesRegex(
            AssertionError, "if markFilterSet is None, "
            "flags must not set LOOKUP_FLAG_USE_MARK_FILTERING_SET; "
            "flags=0x0010",
            builder.buildLookup, [s],
            builder.LOOKUP_FLAG_USE_MARK_FILTERING_SET, None)
        self.assertRaisesRegex(
            AssertionError, "if markFilterSet is not None, "
            "flags must set LOOKUP_FLAG_USE_MARK_FILTERING_SET; "
            "flags=0x0004",
            builder.buildLookup, [s],
            builder.LOOKUP_FLAG_IGNORE_LIGATURES, 777)

    def test_buildLookup_conflictingSubtableTypes(self):
        s1 = builder.buildSingleSubstSubtable({"one": "two"})
        s2 = builder.buildAlternateSubstSubtable({"one": ["two", "three"]})
        self.assertRaisesRegex(
            AssertionError, "all subtables must have the same LookupType",
            builder.buildLookup, [s1, s2])

    def test_buildLookup_noSubtables(self):
        self.assertIsNone(builder.buildLookup([]))
        self.assertIsNone(builder.buildLookup(None))
        self.assertIsNone(builder.buildLookup([None]))
        self.assertIsNone(builder.buildLookup([None, None]))

    def test_buildLookup_markFilterSet(self):
        s = builder.buildSingleSubstSubtable({"one": "two"})
        flags = (builder.LOOKUP_FLAG_RIGHT_TO_LEFT |
                 builder.LOOKUP_FLAG_USE_MARK_FILTERING_SET)
        lookup = builder.buildLookup([s], flags, markFilterSet=999)
        self.assertEqual(getXML(lookup.toXML),
                         ['<Lookup>',
                          '  <LookupType value="1"/>',
                          '  <LookupFlag value="17"/>',
                          '  <!-- SubTableCount=1 -->',
                          '  <SingleSubst index="0">',
                          '    <Substitution in="one" out="two"/>',
                          '  </SingleSubst>',
                          '  <MarkFilteringSet value="999"/>',
                          '</Lookup>'])

    def test_buildMarkArray(self):
        markArray = builder.buildMarkArray({
            "acute": (7, builder.buildAnchor(300, 800)),
            "grave": (2, builder.buildAnchor(10, 80))
        }, self.GLYPHMAP)
        self.assertLess(self.GLYPHMAP["grave"], self.GLYPHMAP["acute"])
        self.assertEqual(getXML(markArray.toXML),
                         ['<MarkArray>',
                          '  <!-- MarkCount=2 -->',
                          '  <MarkRecord index="0">',
                          '    <Class value="2"/>',
                          '    <MarkAnchor Format="1">',
                          '      <XCoordinate value="10"/>',
                          '      <YCoordinate value="80"/>',
                          '    </MarkAnchor>',
                          '  </MarkRecord>',
                          '  <MarkRecord index="1">',
                          '    <Class value="7"/>',
                          '    <MarkAnchor Format="1">',
                          '      <XCoordinate value="300"/>',
                          '      <YCoordinate value="800"/>',
                          '    </MarkAnchor>',
                          '  </MarkRecord>',
                          '</MarkArray>'])

    def test_buildMarkBasePosSubtable(self):
        anchor = builder.buildAnchor
        marks = {
            "acute": (0, anchor(300, 700)),
            "cedilla": (1, anchor(300, -100)),
            "grave": (0, anchor(300, 700))
        }
        bases = {
            # Make sure we can handle missing entries.
            "A": {},  # no entry for any markClass
            "B": {0: anchor(500, 900)},  # only markClass 0 specified
            "C": {1: anchor(500, -10)},  # only markClass 1 specified

            "a": {0: anchor(500, 400), 1: anchor(500, -20)},
            "b": {0: anchor(500, 800), 1: anchor(500, -20)}
        }
        table = builder.buildMarkBasePosSubtable(marks, bases, self.GLYPHMAP)
        self.assertEqual(getXML(table.toXML),
                         ['<MarkBasePos Format="1">',
                          '  <MarkCoverage>',
                          '    <Glyph value="grave"/>',
                          '    <Glyph value="acute"/>',
                          '    <Glyph value="cedilla"/>',
                          '  </MarkCoverage>',
                          '  <BaseCoverage>',
                          '    <Glyph value="A"/>',
                          '    <Glyph value="B"/>',
                          '    <Glyph value="C"/>',
                          '    <Glyph value="a"/>',
                          '    <Glyph value="b"/>',
                          '  </BaseCoverage>',
                          '  <!-- ClassCount=2 -->',
                          '  <MarkArray>',
                          '    <!-- MarkCount=3 -->',
                          '    <MarkRecord index="0">',  # grave
                          '      <Class value="0"/>',
                          '      <MarkAnchor Format="1">',
                          '        <XCoordinate value="300"/>',
                          '        <YCoordinate value="700"/>',
                          '      </MarkAnchor>',
                          '    </MarkRecord>',
                          '    <MarkRecord index="1">',  # acute
                          '      <Class value="0"/>',
                          '      <MarkAnchor Format="1">',
                          '        <XCoordinate value="300"/>',
                          '        <YCoordinate value="700"/>',
                          '      </MarkAnchor>',
                          '    </MarkRecord>',
                          '    <MarkRecord index="2">',  # cedilla
                          '      <Class value="1"/>',
                          '      <MarkAnchor Format="1">',
                          '        <XCoordinate value="300"/>',
                          '        <YCoordinate value="-100"/>',
                          '      </MarkAnchor>',
                          '    </MarkRecord>',
                          '  </MarkArray>',
                          '  <BaseArray>',
                          '    <!-- BaseCount=5 -->',
                          '    <BaseRecord index="0">',  # A
                          '      <BaseAnchor index="0" empty="1"/>',
                          '      <BaseAnchor index="1" empty="1"/>',
                          '    </BaseRecord>',
                          '    <BaseRecord index="1">',  # B
                          '      <BaseAnchor index="0" Format="1">',
                          '        <XCoordinate value="500"/>',
                          '        <YCoordinate value="900"/>',
                          '      </BaseAnchor>',
                          '      <BaseAnchor index="1" empty="1"/>',
                          '    </BaseRecord>',
                          '    <BaseRecord index="2">',  # C
                          '      <BaseAnchor index="0" empty="1"/>',
                          '      <BaseAnchor index="1" Format="1">',
                          '        <XCoordinate value="500"/>',
                          '        <YCoordinate value="-10"/>',
                          '      </BaseAnchor>',
                          '    </BaseRecord>',
                          '    <BaseRecord index="3">',  # a
                          '      <BaseAnchor index="0" Format="1">',
                          '        <XCoordinate value="500"/>',
                          '        <YCoordinate value="400"/>',
                          '      </BaseAnchor>',
                          '      <BaseAnchor index="1" Format="1">',
                          '        <XCoordinate value="500"/>',
                          '        <YCoordinate value="-20"/>',
                          '      </BaseAnchor>',
                          '    </BaseRecord>',
                          '    <BaseRecord index="4">',  # b
                          '      <BaseAnchor index="0" Format="1">',
                          '        <XCoordinate value="500"/>',
                          '        <YCoordinate value="800"/>',
                          '      </BaseAnchor>',
                          '      <BaseAnchor index="1" Format="1">',
                          '        <XCoordinate value="500"/>',
                          '        <YCoordinate value="-20"/>',
                          '      </BaseAnchor>',
                          '    </BaseRecord>',
                          '  </BaseArray>',
                          '</MarkBasePos>'])

    def test_buildMarkGlyphSetsDef(self):
        marksets = builder.buildMarkGlyphSetsDef(
            [{"acute", "grave"}, {"cedilla", "grave"}], self.GLYPHMAP)
        self.assertEqual(getXML(marksets.toXML),
                         ['<MarkGlyphSetsDef>',
                          '  <MarkSetTableFormat value="1"/>',
                          '  <!-- MarkSetCount=2 -->',
                          '  <Coverage index="0">',
                          '    <Glyph value="grave"/>',
                          '    <Glyph value="acute"/>',
                          '  </Coverage>',
                          '  <Coverage index="1">',
                          '    <Glyph value="grave"/>',
                          '    <Glyph value="cedilla"/>',
                          '  </Coverage>',
                          '</MarkGlyphSetsDef>'])

    def test_buildMarkGlyphSetsDef_empty(self):
        self.assertIsNone(builder.buildMarkGlyphSetsDef([], self.GLYPHMAP))

    def test_buildMarkGlyphSetsDef_None(self):
        self.assertIsNone(builder.buildMarkGlyphSetsDef(None, self.GLYPHMAP))

    def test_buildMarkLigPosSubtable(self):
        anchor = builder.buildAnchor
        marks = {
            "acute": (0, anchor(300, 700)),
            "cedilla": (1, anchor(300, -100)),
            "grave": (0, anchor(300, 700))
        }
        bases = {
            "f_i": [{}, {0: anchor(200, 400)}],  # nothing on f; only 1 on i
            "c_t": [
                {0: anchor(500, 600), 1: anchor(500, -20)},   # c
                {0: anchor(1300, 800), 1: anchor(1300, -20)}  # t
            ]
        }
        table = builder.buildMarkLigPosSubtable(marks, bases, self.GLYPHMAP)
        self.assertEqual(getXML(table.toXML),
                         ['<MarkLigPos Format="1">',
                          '  <MarkCoverage>',
                          '    <Glyph value="grave"/>',
                          '    <Glyph value="acute"/>',
                          '    <Glyph value="cedilla"/>',
                          '  </MarkCoverage>',
                          '  <LigatureCoverage>',
                          '    <Glyph value="f_i"/>',
                          '    <Glyph value="c_t"/>',
                          '  </LigatureCoverage>',
                          '  <!-- ClassCount=2 -->',
                          '  <MarkArray>',
                          '    <!-- MarkCount=3 -->',
                          '    <MarkRecord index="0">',
                          '      <Class value="0"/>',
                          '      <MarkAnchor Format="1">',
                          '        <XCoordinate value="300"/>',
                          '        <YCoordinate value="700"/>',
                          '      </MarkAnchor>',
                          '    </MarkRecord>',
                          '    <MarkRecord index="1">',
                          '      <Class value="0"/>',
                          '      <MarkAnchor Format="1">',
                          '        <XCoordinate value="300"/>',
                          '        <YCoordinate value="700"/>',
                          '      </MarkAnchor>',
                          '    </MarkRecord>',
                          '    <MarkRecord index="2">',
                          '      <Class value="1"/>',
                          '      <MarkAnchor Format="1">',
                          '        <XCoordinate value="300"/>',
                          '        <YCoordinate value="-100"/>',
                          '      </MarkAnchor>',
                          '    </MarkRecord>',
                          '  </MarkArray>',
                          '  <LigatureArray>',
                          '    <!-- LigatureCount=2 -->',
                          '    <LigatureAttach index="0">',
                          '      <!-- ComponentCount=2 -->',
                          '      <ComponentRecord index="0">',
                          '        <LigatureAnchor index="0" empty="1"/>',
                          '        <LigatureAnchor index="1" empty="1"/>',
                          '      </ComponentRecord>',
                          '      <ComponentRecord index="1">',
                          '        <LigatureAnchor index="0" Format="1">',
                          '          <XCoordinate value="200"/>',
                          '          <YCoordinate value="400"/>',
                          '        </LigatureAnchor>',
                          '        <LigatureAnchor index="1" empty="1"/>',
                          '      </ComponentRecord>',
                          '    </LigatureAttach>',
                          '    <LigatureAttach index="1">',
                          '      <!-- ComponentCount=2 -->',
                          '      <ComponentRecord index="0">',
                          '        <LigatureAnchor index="0" Format="1">',
                          '          <XCoordinate value="500"/>',
                          '          <YCoordinate value="600"/>',
                          '        </LigatureAnchor>',
                          '        <LigatureAnchor index="1" Format="1">',
                          '          <XCoordinate value="500"/>',
                          '          <YCoordinate value="-20"/>',
                          '        </LigatureAnchor>',
                          '      </ComponentRecord>',
                          '      <ComponentRecord index="1">',
                          '        <LigatureAnchor index="0" Format="1">',
                          '          <XCoordinate value="1300"/>',
                          '          <YCoordinate value="800"/>',
                          '        </LigatureAnchor>',
                          '        <LigatureAnchor index="1" Format="1">',
                          '          <XCoordinate value="1300"/>',
                          '          <YCoordinate value="-20"/>',
                          '        </LigatureAnchor>',
                          '      </ComponentRecord>',
                          '    </LigatureAttach>',
                          '  </LigatureArray>',
                          '</MarkLigPos>'])

    def test_buildMarkRecord(self):
        rec = builder.buildMarkRecord(17, builder.buildAnchor(500, -20))
        self.assertEqual(getXML(rec.toXML),
                         ['<MarkRecord>',
                          '  <Class value="17"/>',
                          '  <MarkAnchor Format="1">',
                          '    <XCoordinate value="500"/>',
                          '    <YCoordinate value="-20"/>',
                          '  </MarkAnchor>',
                          '</MarkRecord>'])

    def test_buildMark2Record(self):
        a = builder.buildAnchor
        rec = builder.buildMark2Record([a(500, -20), None, a(300, -15)])
        self.assertEqual(getXML(rec.toXML),
                         ['<Mark2Record>',
                          '  <Mark2Anchor index="0" Format="1">',
                          '    <XCoordinate value="500"/>',
                          '    <YCoordinate value="-20"/>',
                          '  </Mark2Anchor>',
                          '  <Mark2Anchor index="1" empty="1"/>',
                          '  <Mark2Anchor index="2" Format="1">',
                          '    <XCoordinate value="300"/>',
                          '    <YCoordinate value="-15"/>',
                          '  </Mark2Anchor>',
                          '</Mark2Record>'])

    def test_buildPairPosClassesSubtable(self):
        d20 = builder.buildValue({"XPlacement": -20})
        d50 = builder.buildValue({"XPlacement": -50})
        d0 = builder.buildValue({})
        d8020 = builder.buildValue({"XPlacement": -80, "YPlacement": -20})
        subtable = builder.buildPairPosClassesSubtable({
            (tuple("A",), tuple(["zero"])): (d0, d50),
            (tuple("A",), tuple(["one", "two"])):  (None, d20),
            (tuple(["B", "C"]), tuple(["zero"])): (d8020, d50),
        }, self.GLYPHMAP)
        self.assertEqual(getXML(subtable.toXML),
                         ['<PairPos Format="2">',
                          '  <Coverage>',
                          '    <Glyph value="A"/>',
                          '    <Glyph value="B"/>',
                          '    <Glyph value="C"/>',
                          '  </Coverage>',
                          '  <ValueFormat1 value="3"/>',
                          '  <ValueFormat2 value="1"/>',
                          '  <ClassDef1>',
                          '    <ClassDef glyph="A" class="1"/>',
                          '  </ClassDef1>',
                          '  <ClassDef2>',
                          '    <ClassDef glyph="one" class="1"/>',
                          '    <ClassDef glyph="two" class="1"/>',
                          '    <ClassDef glyph="zero" class="2"/>',
                          '  </ClassDef2>',
                          '  <!-- Class1Count=2 -->',
                          '  <!-- Class2Count=3 -->',
                          '  <Class1Record index="0">',
                          '    <Class2Record index="0">',
                          '    </Class2Record>',
                          '    <Class2Record index="1">',
                          '    </Class2Record>',
                          '    <Class2Record index="2">',
                          '      <Value1 XPlacement="-80" YPlacement="-20"/>',
                          '      <Value2 XPlacement="-50"/>',
                          '    </Class2Record>',
                          '  </Class1Record>',
                          '  <Class1Record index="1">',
                          '    <Class2Record index="0">',
                          '    </Class2Record>',
                          '    <Class2Record index="1">',
                          '      <Value2 XPlacement="-20"/>',
                          '    </Class2Record>',
                          '    <Class2Record index="2">',
                          '      <Value1/>',
                          '      <Value2 XPlacement="-50"/>',
                          '    </Class2Record>',
                          '  </Class1Record>',
                          '</PairPos>'])

    def test_buildPairPosGlyphs(self):
        d50 = builder.buildValue({"XPlacement": -50})
        d8020 = builder.buildValue({"XPlacement": -80, "YPlacement": -20})
        subtables = builder.buildPairPosGlyphs({
            ("A", "zero"): (None, d50),
            ("A", "one"):  (d8020, d50),
        }, self.GLYPHMAP)
        self.assertEqual(sum([getXML(t.toXML) for t in subtables], []),
                         ['<PairPos Format="1">',
                          '  <Coverage>',
                          '    <Glyph value="A"/>',
                          '  </Coverage>',
                          '  <ValueFormat1 value="0"/>',
                          '  <ValueFormat2 value="1"/>',
                          '  <!-- PairSetCount=1 -->',
                          '  <PairSet index="0">',
                          '    <!-- PairValueCount=1 -->',
                          '    <PairValueRecord index="0">',
                          '      <SecondGlyph value="zero"/>',
                          '      <Value2 XPlacement="-50"/>',
                          '    </PairValueRecord>',
                          '  </PairSet>',
                          '</PairPos>',
                          '<PairPos Format="1">',
                          '  <Coverage>',
                          '    <Glyph value="A"/>',
                          '  </Coverage>',
                          '  <ValueFormat1 value="3"/>',
                          '  <ValueFormat2 value="1"/>',
                          '  <!-- PairSetCount=1 -->',
                          '  <PairSet index="0">',
                          '    <!-- PairValueCount=1 -->',
                          '    <PairValueRecord index="0">',
                          '      <SecondGlyph value="one"/>',
                          '      <Value1 XPlacement="-80" YPlacement="-20"/>',
                          '      <Value2 XPlacement="-50"/>',
                          '    </PairValueRecord>',
                          '  </PairSet>',
                          '</PairPos>'])

    def test_buildPairPosGlyphsSubtable(self):
        d20 = builder.buildValue({"XPlacement": -20})
        d50 = builder.buildValue({"XPlacement": -50})
        d0 = builder.buildValue({})
        d8020 = builder.buildValue({"XPlacement": -80, "YPlacement": -20})
        subtable = builder.buildPairPosGlyphsSubtable({
            ("A", "zero"): (d0, d50),
            ("A", "one"):  (None, d20),
            ("B", "five"): (d8020, d50),
        }, self.GLYPHMAP)
        self.assertEqual(getXML(subtable.toXML),
                         ['<PairPos Format="1">',
                          '  <Coverage>',
                          '    <Glyph value="A"/>',
                          '    <Glyph value="B"/>',
                          '  </Coverage>',
                          '  <ValueFormat1 value="3"/>',
                          '  <ValueFormat2 value="1"/>',
                          '  <!-- PairSetCount=2 -->',
                          '  <PairSet index="0">',
                          '    <!-- PairValueCount=2 -->',
                          '    <PairValueRecord index="0">',
                          '      <SecondGlyph value="zero"/>',
                          '      <Value2 XPlacement="-50"/>',
                          '    </PairValueRecord>',
                          '    <PairValueRecord index="1">',
                          '      <SecondGlyph value="one"/>',
                          '      <Value2 XPlacement="-20"/>',
                          '    </PairValueRecord>',
                          '  </PairSet>',
                          '  <PairSet index="1">',
                          '    <!-- PairValueCount=1 -->',
                          '    <PairValueRecord index="0">',
                          '      <SecondGlyph value="five"/>',
                          '      <Value1 XPlacement="-80" YPlacement="-20"/>',
                          '      <Value2 XPlacement="-50"/>',
                          '    </PairValueRecord>',
                          '  </PairSet>',
                          '</PairPos>'])

    def test_buildSinglePos(self):
        subtables = builder.buildSinglePos({
            "one": builder.buildValue({"XPlacement": 500}),
            "two": builder.buildValue({"XPlacement": 500}),
            "three": builder.buildValue({"XPlacement": 200}),
            "four": builder.buildValue({"XPlacement": 400}),
            "five": builder.buildValue({"XPlacement": 500}),
            "six": builder.buildValue({"YPlacement": -6}),
        }, self.GLYPHMAP)
        self.assertEqual(sum([getXML(t.toXML) for t in subtables], []),
                         ['<SinglePos Format="2">',
                          '  <Coverage>',
                          '    <Glyph value="one"/>',
                          '    <Glyph value="two"/>',
                          '    <Glyph value="three"/>',
                          '    <Glyph value="four"/>',
                          '    <Glyph value="five"/>',
                          '  </Coverage>',
                          '  <ValueFormat value="1"/>',
                          '  <!-- ValueCount=5 -->',
                          '  <Value index="0" XPlacement="500"/>',
                          '  <Value index="1" XPlacement="500"/>',
                          '  <Value index="2" XPlacement="200"/>',
                          '  <Value index="3" XPlacement="400"/>',
                          '  <Value index="4" XPlacement="500"/>',
                          '</SinglePos>',
                          '<SinglePos Format="1">',
                          '  <Coverage>',
                          '    <Glyph value="six"/>',
                          '  </Coverage>',
                          '  <ValueFormat value="2"/>',
                          '  <Value YPlacement="-6"/>',
                          '</SinglePos>'])

    def test_buildSinglePos_ValueFormat0(self):
        subtables = builder.buildSinglePos({
            "zero": builder.buildValue({})
        }, self.GLYPHMAP)
        self.assertEqual(sum([getXML(t.toXML) for t in subtables], []),
                         ['<SinglePos Format="1">',
                          '  <Coverage>',
                          '    <Glyph value="zero"/>',
                          '  </Coverage>',
                          '  <ValueFormat value="0"/>',
                          '</SinglePos>'])

    def test_buildSinglePosSubtable_format1(self):
        subtable = builder.buildSinglePosSubtable({
            "one": builder.buildValue({"XPlacement": 777}),
            "two": builder.buildValue({"XPlacement": 777}),
        }, self.GLYPHMAP)
        self.assertEqual(getXML(subtable.toXML),
                         ['<SinglePos Format="1">',
                          '  <Coverage>',
                          '    <Glyph value="one"/>',
                          '    <Glyph value="two"/>',
                          '  </Coverage>',
                          '  <ValueFormat value="1"/>',
                          '  <Value XPlacement="777"/>',
                          '</SinglePos>'])

    def test_buildSinglePosSubtable_format2(self):
        subtable = builder.buildSinglePosSubtable({
            "one": builder.buildValue({"XPlacement": 777}),
            "two": builder.buildValue({"YPlacement": -888}),
        }, self.GLYPHMAP)
        self.assertEqual(getXML(subtable.toXML),
                         ['<SinglePos Format="2">',
                          '  <Coverage>',
                          '    <Glyph value="one"/>',
                          '    <Glyph value="two"/>',
                          '  </Coverage>',
                          '  <ValueFormat value="3"/>',
                          '  <!-- ValueCount=2 -->',
                          '  <Value index="0" XPlacement="777"/>',
                          '  <Value index="1" YPlacement="-888"/>',
                          '</SinglePos>'])

    def test_buildValue(self):
        value = builder.buildValue({"XPlacement": 7, "YPlacement": 23})
        func = lambda writer, font: value.toXML(writer, font, valueName="Val")
        self.assertEqual(getXML(func),
                         ['<Val XPlacement="7" YPlacement="23"/>'])

    def test_getLigatureKey(self):
        components = lambda s: [tuple(word) for word in s.split()]
        c = components("fi fl ff ffi fff")
        c.sort(key=builder._getLigatureKey)
        self.assertEqual(c, components("fff ffi ff fi fl"))

    def test_getSinglePosValueKey(self):
        device = builder.buildDevice({10:1, 11:3})
        a1 = builder.buildValue({"XPlacement": 500, "XPlaDevice": device})
        a2 = builder.buildValue({"XPlacement": 500, "XPlaDevice": device})
        b = builder.buildValue({"XPlacement": 500})
        keyA1 = builder._getSinglePosValueKey(a1)
        keyA2 = builder._getSinglePosValueKey(a1)
        keyB = builder._getSinglePosValueKey(b)
        self.assertEqual(keyA1, keyA2)
        self.assertEqual(hash(keyA1), hash(keyA2))
        self.assertNotEqual(keyA1, keyB)
        self.assertNotEqual(hash(keyA1), hash(keyB))


class ClassDefBuilderTest(unittest.TestCase):
    def test_build_usingClass0(self):
        b = builder.ClassDefBuilder(useClass0=True)
        b.add({"aa", "bb"})
        b.add({"a", "b"})
        b.add({"c"})
        b.add({"e", "f", "g", "h"})
        cdef = b.build()
        self.assertIsInstance(cdef, otTables.ClassDef)
        self.assertEqual(cdef.classDefs, {
            "a": 2,
            "b": 2,
            "c": 3,
            "aa": 1,
            "bb": 1
        })

    def test_build_notUsingClass0(self):
        b = builder.ClassDefBuilder(useClass0=False)
        b.add({"a", "b"})
        b.add({"c"})
        b.add({"e", "f", "g", "h"})
        cdef = b.build()
        self.assertIsInstance(cdef, otTables.ClassDef)
        self.assertEqual(cdef.classDefs, {
            "a": 2,
            "b": 2,
            "c": 3,
            "e": 1,
            "f": 1,
            "g": 1,
            "h": 1
        })

    def test_canAdd(self):
        b = builder.ClassDefBuilder(useClass0=True)
        b.add({"a", "b", "c", "d"})
        b.add({"e", "f"})
        self.assertTrue(b.canAdd({"a", "b", "c", "d"}))
        self.assertTrue(b.canAdd({"e", "f"}))
        self.assertTrue(b.canAdd({"g", "h", "i"}))
        self.assertFalse(b.canAdd({"b", "c", "d"}))
        self.assertFalse(b.canAdd({"a", "b", "c", "d", "e", "f"}))
        self.assertFalse(b.canAdd({"d", "e", "f"}))
        self.assertFalse(b.canAdd({"f"}))


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
