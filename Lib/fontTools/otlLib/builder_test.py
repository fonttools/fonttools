from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.testTools import getXML
from fontTools.otlLib import builder
import unittest


class BuilderTest(unittest.TestCase):
    GLYPHMAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}

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

    def test_buildSinglePos(self):
        self.maxDiff = None
        subtables = builder.buildSinglePos({
            "one": builder.buildValue({"XPlacement": 500}),
            "two": builder.buildValue({"XPlacement": 500}),
            "three": builder.buildValue({"XPlacement": 200}),
            "four": builder.buildValue({"XPlacement": 400}),
            "five": builder.buildValue({"XPlacement": 500}),
            "six": builder.buildValue({"YPlacement": -6}),
        }, self.GLYPHMAP)
        self.assertEqual(''.join([getXML(t.toXML) for t in subtables[:3]]),
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
