from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.fixedTools import fixedToFloat, floatToFixed
import unittest


class FixedToolsTest(unittest.TestCase):

    def test_roundtrip(self):
        for bits in range(0, 15):
            for value in range(-(2**(bits+1)), 2**(bits+1)):
                self.assertEqual(value, floatToFixed(fixedToFloat(value, bits), bits))

    def test_fixedToFloat_precision14(self):
        self.assertEqual(0.8, fixedToFloat(13107, 14))
        self.assertEqual(0.0, fixedToFloat(0, 14))
        self.assertEqual(1.0, fixedToFloat(16384, 14))
        self.assertEqual(-1.0, fixedToFloat(-16384, 14))
        self.assertEqual(0.99994, fixedToFloat(16383, 14))
        self.assertEqual(-0.99994, fixedToFloat(-16383, 14))

    def test_fixedToFloat_precision6(self):
        self.assertAlmostEqual(-9.98, fixedToFloat(-639, 6))
        self.assertAlmostEqual(-10.0, fixedToFloat(-640, 6))
        self.assertAlmostEqual(9.98, fixedToFloat(639, 6))
        self.assertAlmostEqual(10.0, fixedToFloat(640, 6))

    def test_floatToFixed_precision14(self):
        self.assertEqual(13107, floatToFixed(0.8, 14))
        self.assertEqual(16384, floatToFixed(1.0, 14))
        self.assertEqual(16384, floatToFixed(1, 14))
        self.assertEqual(-16384, floatToFixed(-1.0, 14))
        self.assertEqual(-16384, floatToFixed(-1, 14))
        self.assertEqual(0, floatToFixed(0, 14))

    def test_fixedToFloat_return_float(self):
        value = fixedToFloat(16384, 14)
        self.assertIsInstance(value, float)


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
