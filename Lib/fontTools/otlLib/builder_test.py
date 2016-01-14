from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.testTools import getXML
from fontTools.otlLib import builder
import unittest


class BuilderTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
