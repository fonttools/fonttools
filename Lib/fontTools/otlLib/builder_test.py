from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.testTools import getXML
from fontTools.otlLib import builder
import unittest


class BuilderTest(unittest.TestCase):
    def test_buildDevice_format1(self):
        device = builder.buildDevice([(1, 1), (0, 0)])
        self.assertEqual(getXML(device, ttFont=None),
                         '<Device>'
                         '  <StartSize value="0"/>'
                         '  <EndSize value="1"/>'
                         '  <DeltaFormat value="1"/>'
                         '  <DeltaValue value="[0, 1]"/>'
                         '</Device>')

    def test_buildDevice_format2(self):
        device = builder.buildDevice([(1, 2), (-1, 1), (0, 0)])
        self.assertEqual(getXML(device, ttFont=None),
                         '<Device>'
                         '  <StartSize value="-1"/>'
                         '  <EndSize value="1"/>'
                         '  <DeltaFormat value="2"/>'
                         '  <DeltaValue value="[1, 0, 2]"/>'
                         '</Device>')

    def test_buildDevice_format3(self):
        device = builder.buildDevice([(5, 3), (1, 77)])
        self.assertEqual(getXML(device, ttFont=None),
                         '<Device>'
                         '  <StartSize value="1"/>'
                         '  <EndSize value="5"/>'
                         '  <DeltaFormat value="3"/>'
                         '  <DeltaValue value="[77, 0, 0, 0, 3]"/>'
                         '</Device>')

    def test_getLigatureKey(self):
        components = lambda s: [tuple(word) for word in s.split()]
        c = components("fi fl ff ffi fff")
        c.sort(key=builder.getLigatureKey)
        self.assertEqual(c, components("fff ffi ff fi fl"))


if __name__ == "__main__":
    unittest.main()
