from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.testTools import getXML
from fontTools.otlLib import builder
import unittest


class BuilderTest(unittest.TestCase):
    GLYPHS = (".notdef space zero one two three four five six f_f_i c_t "
              "grave acute cedilla").split()
    GLYPHMAP = {name: num for num, name in enumerate(GLYPHS)}

    ANCHOR1 = builder.buildAnchor(11, -11)
    ANCHOR2 = builder.buildAnchor(22, -22)
    ANCHOR3 = builder.buildAnchor(33, -33)

    def test_buildAnchor_format1(self):
        anchor = builder.buildAnchor(23, 42)
        self.assertEqual(getXML(anchor.toXML),
                         '<Anchor Format="1">'
                         '  <XCoordinate value="23"/>'
                         '  <YCoordinate value="42"/>'
                         '</Anchor>')

    def test_buildAnchor_format2(self):
        anchor = builder.buildAnchor(23, 42, point=17)
        self.assertEqual(getXML(anchor.toXML),
                         '<Anchor Format="2">'
                         '  <XCoordinate value="23"/>'
                         '  <YCoordinate value="42"/>'
                         '  <AnchorPoint value="17"/>'
                         '</Anchor>')

    def test_buildAnchor_format3(self):
        anchor = builder.buildAnchor(
            23, 42,
            deviceX=builder.buildDevice([(1, 1), (0, 0)]),
            deviceY=builder.buildDevice([(7, 7)]))
        self.assertEqual(getXML(anchor.toXML),
                         '<Anchor Format="3">'
                         '  <XCoordinate value="23"/>'
                         '  <YCoordinate value="42"/>'
                         '  <XDeviceTable>'
                         '    <StartSize value="0"/>'
                         '    <EndSize value="1"/>'
                         '    <DeltaFormat value="1"/>'
                         '    <DeltaValue value="[0, 1]"/>'
                         '  </XDeviceTable>'
                         '  <YDeviceTable>'
                         '    <StartSize value="7"/>'
                         '    <EndSize value="7"/>'
                         '    <DeltaFormat value="2"/>'
                         '    <DeltaValue value="[7]"/>'
                         '  </YDeviceTable>'
                         '</Anchor>')

    def test_buildAttachList(self):
        attachList = builder.buildAttachList({
            "zero": [23, 7], "one": [1],
        }, self.GLYPHMAP)
        self.assertEqual(getXML(attachList.toXML),
                         '<AttachList>'
                         '  <Coverage>'
                         '    <Glyph value="zero"/>'
                         '    <Glyph value="one"/>'
                         '  </Coverage>'
                         '  <!-- GlyphCount=2 -->'
                         '  <AttachPoint index="0">'
                         '    <!-- PointCount=2 -->'
                         '    <PointIndex index="0" value="7"/>'
                         '    <PointIndex index="1" value="23"/>'
                         '  </AttachPoint>'
                         '  <AttachPoint index="1">'
                         '    <!-- PointCount=1 -->'
                         '    <PointIndex index="0" value="1"/>'
                         '  </AttachPoint>'
                         '</AttachList>')

    def test_buildAttachList_empty(self):
        self.assertIsNone(builder.buildAttachList({}, self.GLYPHMAP))

    def test_buildAttachPoint(self):
        attachPoint = builder.buildAttachPoint([7, 3])
        self.assertEqual(getXML(attachPoint.toXML),
                         '<AttachPoint>'
                         '  <!-- PointCount=2 -->'
                         '  <PointIndex index="0" value="3"/>'
                         '  <PointIndex index="1" value="7"/>'
                         '</AttachPoint>')

    def test_buildCaretValueForCoord(self):
        caret = builder.buildCaretValueForCoord(500)
        self.assertEqual(getXML(caret.toXML),
                         '<CaretValue Format="1">'
                         '  <Coordinate value="500"/>'
                         '</CaretValue>')

    def test_buildCaretValueForPoint(self):
        caret = builder.buildCaretValueForPoint(23)
        self.assertEqual(getXML(caret.toXML),
                         '<CaretValue Format="2">'
                         '  <CaretValuePoint value="23"/>'
                         '</CaretValue>')

    def test_buildCoverage(self):
        cov = builder.buildCoverage({"two", "four"}, {"two": 2, "four": 4})
        self.assertEqual(getXML(cov.toXML),
                         '<Coverage>'
                         '  <Glyph value="two"/>'
                         '  <Glyph value="four"/>'
                         '</Coverage>')

    def test_buildCursivePos(self):
        pos = builder.buildCursivePos({
            "two": (self.ANCHOR1, self.ANCHOR2),
            "four": (self.ANCHOR3, self.ANCHOR1)
        }, self.GLYPHMAP)
        self.assertEqual(getXML(pos.toXML),
                         '<CursivePos Format="1">'
                         '  <Coverage>'
                         '    <Glyph value="two"/>'
                         '    <Glyph value="four"/>'
                         '  </Coverage>'
                         '  <!-- EntryExitCount=2 -->'
                         '  <EntryExitRecord index="0">'
                         '    <EntryAnchor Format="1">'
                         '      <XCoordinate value="11"/>'
                         '      <YCoordinate value="-11"/>'
                         '    </EntryAnchor>'
                         '    <ExitAnchor Format="1">'
                         '      <XCoordinate value="22"/>'
                         '      <YCoordinate value="-22"/>'
                         '    </ExitAnchor>'
                         '  </EntryExitRecord>'
                         '  <EntryExitRecord index="1">'
                         '    <EntryAnchor Format="1">'
                         '      <XCoordinate value="33"/>'
                         '      <YCoordinate value="-33"/>'
                         '    </EntryAnchor>'
                         '    <ExitAnchor Format="1">'
                         '      <XCoordinate value="11"/>'
                         '      <YCoordinate value="-11"/>'
                         '    </ExitAnchor>'
                         '  </EntryExitRecord>'
                         '</CursivePos>')

    def test_buildDevice_format1(self):
        device = builder.buildDevice([(1, 1), (0, 0)])
        self.assertEqual(getXML(device.toXML),
                         '<Device>'
                         '  <StartSize value="0"/>'
                         '  <EndSize value="1"/>'
                         '  <DeltaFormat value="1"/>'
                         '  <DeltaValue value="[0, 1]"/>'
                         '</Device>')

    def test_buildDevice_format2(self):
        device = builder.buildDevice([(1, 2), (-1, 1), (0, 0)])
        self.assertEqual(getXML(device.toXML),
                         '<Device>'
                         '  <StartSize value="-1"/>'
                         '  <EndSize value="1"/>'
                         '  <DeltaFormat value="2"/>'
                         '  <DeltaValue value="[1, 0, 2]"/>'
                         '</Device>')

    def test_buildDevice_format3(self):
        device = builder.buildDevice([(5, 3), (1, 77)])
        self.assertEqual(getXML(device.toXML),
                         '<Device>'
                         '  <StartSize value="1"/>'
                         '  <EndSize value="5"/>'
                         '  <DeltaFormat value="3"/>'
                         '  <DeltaValue value="[77, 0, 0, 0, 3]"/>'
                         '</Device>')

    def test_buildLigCaretList(self):
        carets = builder.buildLigCaretList(
            {"f_f_i": [300, 600]}, {"c_t": [42]}, self.GLYPHMAP)
        self.assertEqual(getXML(carets.toXML),
                         '<LigCaretList>'
                         '  <Coverage>'
                         '    <Glyph value="f_f_i"/>'
                         '    <Glyph value="c_t"/>'
                         '  </Coverage>'
                         '  <!-- LigGlyphCount=2 -->'
                         '  <LigGlyph index="0">'
                         '    <!-- CaretCount=2 -->'
                         '    <CaretValue index="0" Format="1">'
                         '      <Coordinate value="300"/>'
                         '    </CaretValue>'
                         '    <CaretValue index="1" Format="1">'
                         '      <Coordinate value="600"/>'
                         '    </CaretValue>'
                         '  </LigGlyph>'
                         '  <LigGlyph index="1">'
                         '    <!-- CaretCount=1 -->'
                         '    <CaretValue index="0" Format="2">'
                         '      <CaretValuePoint value="42"/>'
                         '    </CaretValue>'
                         '  </LigGlyph>'
                         '</LigCaretList>')

    def test_buildLigCaretList_bothCoordsAndPointsForSameGlyph(self):
        carets = builder.buildLigCaretList(
            {"f_f_i": [300]}, {"f_f_i": [7]}, self.GLYPHMAP)
        self.assertEqual(getXML(carets.toXML),
                         '<LigCaretList>'
                         '  <Coverage>'
                         '    <Glyph value="f_f_i"/>'
                         '  </Coverage>'
                         '  <!-- LigGlyphCount=1 -->'
                         '  <LigGlyph index="0">'
                         '    <!-- CaretCount=2 -->'
                         '    <CaretValue index="0" Format="1">'
                         '      <Coordinate value="300"/>'
                         '    </CaretValue>'
                         '    <CaretValue index="1" Format="2">'
                         '      <CaretValuePoint value="7"/>'
                         '    </CaretValue>'
                         '  </LigGlyph>'
                         '</LigCaretList>')

    def test_buildLigCaretList_empty(self):
        self.assertIsNone(builder.buildLigCaretList({}, {}, self.GLYPHMAP))

    def test_buildLigCaretList_None(self):
        self.assertIsNone(builder.buildLigCaretList(None, None, self.GLYPHMAP))

    def test_buildLigGlyph_coords(self):
        lig = builder.buildLigGlyph([500, 800], None)
        self.assertEqual(getXML(lig.toXML),
                         '<LigGlyph>'
                         '  <!-- CaretCount=2 -->'
                         '  <CaretValue index="0" Format="1">'
                         '    <Coordinate value="500"/>'
                         '  </CaretValue>'
                         '  <CaretValue index="1" Format="1">'
                         '    <Coordinate value="800"/>'
                         '  </CaretValue>'
                         '</LigGlyph>')

    def test_buildLigGlyph_empty(self):
        self.assertIsNone(builder.buildLigGlyph([], []))

    def test_buildLigGlyph_None(self):
        self.assertIsNone(builder.buildLigGlyph(None, None))

    def test_buildLigGlyph_points(self):
        lig = builder.buildLigGlyph(None, [2])
        self.assertEqual(getXML(lig.toXML),
                         '<LigGlyph>'
                         '  <!-- CaretCount=1 -->'
                         '  <CaretValue index="0" Format="2">'
                         '    <CaretValuePoint value="2"/>'
                         '  </CaretValue>'
                         '</LigGlyph>')

    def test_buildMarkGlyphSetsDef(self):
        marksets = builder.buildMarkGlyphSetsDef(
            [{"acute", "grave"}, {"cedilla", "grave"}], self.GLYPHMAP)
        self.assertEqual(getXML(marksets.toXML),
                         '<MarkGlyphSetsDef>'
                         '  <MarkSetTableFormat value="1"/>'
                         '  <!-- MarkSetCount=2 -->'
                         '  <Coverage index="0">'
                         '    <Glyph value="grave"/>'
                         '    <Glyph value="acute"/>'
                         '  </Coverage>'
                         '  <Coverage index="1">'
                         '    <Glyph value="grave"/>'
                         '    <Glyph value="cedilla"/>'
                         '  </Coverage>'
                         '</MarkGlyphSetsDef>')

    def test_buildMarkGlyphSetsDef_empty(self):
        self.assertIsNone(builder.buildMarkGlyphSetsDef([], self.GLYPHMAP))

    def test_buildMarkGlyphSetsDef_None(self):
        self.assertIsNone(builder.buildMarkGlyphSetsDef(None, self.GLYPHMAP))

    def test_buildSinglePos(self):
        subtables = builder.buildSinglePos({
            "one": builder.buildValue({"XPlacement": 500}),
            "two": builder.buildValue({"XPlacement": 500}),
            "three": builder.buildValue({"XPlacement": 200}),
            "four": builder.buildValue({"XPlacement": 400}),
            "five": builder.buildValue({"XPlacement": 500}),
            "six": builder.buildValue({"YPlacement": -6}),
        }, self.GLYPHMAP)
        self.assertEqual(''.join([getXML(t.toXML) for t in subtables]),
                         '<SinglePos Format="1">'
                         '  <Coverage>'
                         '    <Glyph value="one"/>'
                         '    <Glyph value="two"/>'
                         '    <Glyph value="five"/>'
                         '  </Coverage>'
                         '  <ValueFormat value="1"/>'
                         '  <Value XPlacement="500"/>'
                         '</SinglePos>'
                         '<SinglePos Format="2">'
                         '  <Coverage>'
                         '    <Glyph value="three"/>'
                         '    <Glyph value="four"/>'
                         '  </Coverage>'
                         '  <ValueFormat value="1"/>'
                         '  <!-- ValueCount=2 -->'
                         '  <Value index="0" XPlacement="200"/>'
                         '  <Value index="1" XPlacement="400"/>'
                         '</SinglePos>'
                         '<SinglePos Format="1">'
                         '  <Coverage>'
                         '    <Glyph value="six"/>'
                         '  </Coverage>'
                         '  <ValueFormat value="2"/>'
                         '  <Value YPlacement="-6"/>'
                         '</SinglePos>')

    def test_buildSinglePos_ValueFormat0(self):
        subtables = builder.buildSinglePos({
            "zero": builder.buildValue({})
        }, self.GLYPHMAP)
        self.assertEqual(''.join([getXML(t.toXML) for t in subtables]),
                         '<SinglePos Format="1">'
                         '  <Coverage>'
                         '    <Glyph value="zero"/>'
                         '  </Coverage>'
                         '  <ValueFormat value="0"/>'
                         '</SinglePos>')

    def test_buildSinglePosSubtable_format1(self):
        subtable = builder.buildSinglePosSubtable({
            "one": builder.buildValue({"XPlacement": 777}),
            "two": builder.buildValue({"XPlacement": 777}),
        }, self.GLYPHMAP)
        self.assertEqual(getXML(subtable.toXML),
                         '<SinglePos Format="1">'
                         '  <Coverage>'
                         '    <Glyph value="one"/>'
                         '    <Glyph value="two"/>'
                         '  </Coverage>'
                         '  <ValueFormat value="1"/>'
                         '  <Value XPlacement="777"/>'
                         '</SinglePos>')

    def test_buildSinglePosSubtable_format2(self):
        subtable = builder.buildSinglePosSubtable({
            "one": builder.buildValue({"XPlacement": 777}),
            "two": builder.buildValue({"YPlacement": -888}),
        }, self.GLYPHMAP)
        self.maxDiff = None
        self.assertEqual(getXML(subtable.toXML),
                         '<SinglePos Format="2">'
                         '  <Coverage>'
                         '    <Glyph value="one"/>'
                         '    <Glyph value="two"/>'
                         '  </Coverage>'
                         '  <ValueFormat value="3"/>'
                         '  <!-- ValueCount=2 -->'
                         '  <Value index="0" XPlacement="777"/>'
                         '  <Value index="1" YPlacement="-888"/>'
                         '</SinglePos>')

    def test_buildValue(self):
        value = builder.buildValue({"XPlacement": 7, "YPlacement": 23})
        func = lambda writer, font: value.toXML(writer, font, valueName="Val")
        self.assertEqual(getXML(func),
                         '<Val XPlacement="7" YPlacement="23"/>')

    def test_getLigatureKey(self):
        components = lambda s: [tuple(word) for word in s.split()]
        c = components("fi fl ff ffi fff")
        c.sort(key=builder._getLigatureKey)
        self.assertEqual(c, components("fff ffi ff fi fl"))

    def test_getSinglePosValueKey(self):
        device = builder.buildDevice([(10, 1), (11, 3)])
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


if __name__ == "__main__":
    unittest.main()
