from __future__ import print_function, division, absolute_import
from fontTools.cffLib import PrivateDict
from fontTools.cffLib.specializer import stringToProgram
from fontTools.misc.psCharStrings import T2CharString
import unittest


class T2CharStringTest(unittest.TestCase):

    @classmethod
    def stringToT2CharString(cls, string):
        return T2CharString(program=stringToProgram(string), private=PrivateDict())

    def test_recalcBounds_empty(self):
        cs = self.stringToT2CharString("endchar")
        cs.recalcBounds()
        self.assertEqual(cs.bounds, None)

    def test_recalcBounds_line(self):
        cs = self.stringToT2CharString("100 100 rmoveto 40 10 rlineto -20 50 rlineto endchar")
        cs.recalcBounds()
        self.assertEqual(cs.bounds, (100, 100, 140, 160))

    def test_recalcBounds_curve(self):
        cs = self.stringToT2CharString("100 100 rmoveto -50 -150 200 0 -50 150 rrcurveto endchar")
        cs.recalcBounds()
        self.assertEqual(cs.bounds, (91.90524980688875, -12.5, 208.09475019311125, 100))


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
