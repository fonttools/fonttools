from __future__ import print_function, division, absolute_import
from fontTools.cffLib import PrivateDict
from fontTools.cffLib.specializer import stringToProgram
from fontTools.misc.psCharStrings import T2CharString
import unittest


class T2CharStringTest(unittest.TestCase):

    @classmethod
    def stringToT2CharString(cls, string):
        return T2CharString(program=stringToProgram(string), private=PrivateDict())

    def test_calcBounds_empty(self):
        cs = self.stringToT2CharString("endchar")
        bounds = cs.calcBounds(None)
        self.assertEqual(bounds, None)

    def test_calcBounds_line(self):
        cs = self.stringToT2CharString("100 100 rmoveto 40 10 rlineto -20 50 rlineto endchar")
        bounds = cs.calcBounds(None)
        self.assertEqual(bounds, (100, 100, 140, 160))

    def test_calcBounds_curve(self):
        cs = self.stringToT2CharString("100 100 rmoveto -50 -150 200 0 -50 150 rrcurveto endchar")
        bounds = cs.calcBounds(None)
        self.assertEqual(bounds, (91.90524980688875, -12.5, 208.09475019311125, 100))

    def test_charstring_bytecode_optimization(self):
        cs = self.stringToT2CharString(
            "100.0 100 rmoveto -50.0 -150 200.5 0.0 -50 150 rrcurveto endchar")
        cs.isCFF2 = False
        cs.private._isCFF2 = False
        cs.compile()
        cs.decompile()
        self.assertEqual(
            cs.program, [100, 100, 'rmoveto', -50, -150, 200.5, 0, -50, 150,
                         'rrcurveto', 'endchar'])

        cs2 = self.stringToT2CharString(
            "100.0 rmoveto -50.0 -150 200.5 0.0 -50 150 rrcurveto")
        cs2.isCFF2 = True
        cs2.private._isCFF2 = True
        cs2.compile(isCFF2=True)
        cs2.decompile()
        self.assertEqual(
            cs2.program, [100, 'rmoveto', -50, -150, 200.5, 0, -50, 150,
                          'rrcurveto'])


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
