from __future__ import print_function, division, absolute_import
from fontTools.cffLib import PrivateDict
from fontTools.cffLib.specializer import stringToProgram
from fontTools.misc.psCharStrings import T2CharString, encodeFloat, read_realNumber
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

    def test_encodeFloat(self):
        import sys
        def hexenc(s):
            return ' '.join('%02x' % ord(x) for x in s)
        if sys.version_info[0] >= 3:
            def hexenc_py3(s):
                return ' '.join('%02x' % x for x in s)
            hexenc = hexenc_py3

        testNums = [
            # value                expected result
            (-9.399999999999999,   '1e e9 a4 ff'),  # -9.4
            (9.399999999999999999, '1e 9a 4f'),  # 9.4
            (456.8,                '1e 45 6a 8f'),  # 456.8
            (0.0,                  '1e 0f'),  # 0
            (-0.0,                 '1e 0f'),  # 0
            (1.0,                  '1e 1f'),  # 1
            (-1.0,                 '1e e1 ff'),  # -1
            (98765.37e2,           '1e 98 76 53 7f'),  # 9876537
            (1234567890.0,         '1e 1a 23 45 67 9b 09 ff'),  # 1234567890
            (9.876537e-4,          '1e a0 00 98 76 53 7f'),  # 9.876537e-24
            (9.876537e+4,          '1e 98 76 5a 37 ff'),  # 9.876537e+24
        ]

        for sample in testNums:
            encoded_result = encodeFloat(sample[0])
            
            # check to see if we got the expected bytes
            self.assertEqual(hexenc(encoded_result), sample[1])

            # check to see if we get the same value by decoding the data
            decoded_result = read_realNumber(
                None,
                None,
                encoded_result,
                1,
            )
            self.assertEqual(decoded_result[0], float('%.8g' % sample[0]))
            # We limit to 8 digits of precision to match the implementation
            # of encodeFloat.


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
