from __future__ import print_function, division, absolute_import
from fontTools.cffLib.specializer import generalizeProgram
import unittest


def charstr2program(string):
    program = []
    for token in string.split():
        try:
            token = int(token)
        except ValueError:
            try:
                token = float(token)
            except ValueError:
                pass
        program.append(token)
    return program


def program2charstr(lst):
    return ' '.join(str(x) for x in lst)


def get_generalized_charstr(charstr):
    return program2charstr(generalizeProgram(charstr2program(charstr)))


class CFFGeneralizeProgramTest(unittest.TestCase):

# rmoveto
    def test_rmoveto_origin(self):
        test_charstr = 'rmoveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rmoveto_zero(self):
        test_charstr = '0 0 rmoveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rmoveto_zero_width(self):
        test_charstr = '100 0 0 rmoveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rmoveto(self):
        test_charstr = '.55 -.8 rmoveto'
        xpct_charstr = '0.55 -0.8 rmoveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rmoveto_width(self):
        test_charstr = '100.5 50 -5.8 rmoveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# hmoveto
    def test_hmoveto_zero(self):
        test_charstr = '0 hmoveto'
        xpct_charstr = '0 0 rmoveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hmoveto_zero_width(self):
        test_charstr = '100 0 hmoveto'
        xpct_charstr = '100 0 0 rmoveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hmoveto(self):
        test_charstr = '.67 hmoveto'
        xpct_charstr = '0.67 0 rmoveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hmoveto_width(self):
        test_charstr = '100 -70 hmoveto'
        xpct_charstr = '100 -70 0 rmoveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# vmoveto
    def test_vmoveto_zero(self):
        test_charstr = '0 vmoveto'
        xpct_charstr = '0 0 rmoveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vmoveto_zero_width(self):
        test_charstr = '100 0 vmoveto'
        xpct_charstr = '100 0 0 rmoveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vmoveto(self):
        test_charstr = '-.24 vmoveto'
        xpct_charstr = '0 -0.24 rmoveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vmoveto_width(self):
        test_charstr = '100 44 vmoveto'
        xpct_charstr = '100 0 44 rmoveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# rlineto
    def test_rlineto_none(self):
        test_charstr = 'rlineto'
        xpct_charstr = ''
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rlineto_none_mult(self):
        test_charstr = 'rlineto '*3
        xpct_charstr = ''
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rlineto_zero(self):
        test_charstr = '0 0 rlineto'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rlineto_zero_mult(self):
        test_charstr = '0 0 0 0 0 0 rlineto'
        xpct_charstr = ('0 0 rlineto '*3).rstrip()
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rlineto(self):
        test_charstr = '.55 -.8 rlineto'
        xpct_charstr = '0.55 -0.8 rlineto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rlineto_mult(self):
        test_charstr = '.55 -.8 .55 -.8 .55 -.8 rlineto'
        xpct_charstr = ('0.55 -0.8 rlineto '*3).rstrip()
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# hlineto
    def test_hlineto_zero(self):
        test_charstr = '0 hlineto'
        xpct_charstr = '0 0 rlineto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hlineto_zero_mult(self):
        test_charstr = '0 0 0 0 hlineto'
        xpct_charstr = ('0 0 rlineto '*4).rstrip()
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hlineto(self):
        test_charstr = '.67 hlineto'
        xpct_charstr = '0.67 0 rlineto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hlineto_mult(self):
        test_charstr = '.67 -6.0 .67 hlineto'
        xpct_charstr = '0.67 0 rlineto 0 -6.0 rlineto 0.67 0 rlineto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# vlineto
    def test_vlineto_zero(self):
        test_charstr = '0 vlineto'
        xpct_charstr = '0 0 rlineto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vlineto_zero_mult(self):
        test_charstr = '0 0 0 vlineto'
        xpct_charstr = ('0 0 rlineto '*3).rstrip()
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vlineto(self):
        test_charstr = '-.24 vlineto'
        xpct_charstr = '0 -0.24 rlineto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vlineto_mult(self):
        test_charstr = '-.24 +50 30 -4 vlineto'
        xpct_charstr = '0 -0.24 rlineto 50 0 rlineto 0 30 rlineto -4 0 rlineto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# rrcurveto
    def test_rrcurveto(self):
        test_charstr = '-1 56 -2 57 -1 57 rrcurveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_mult(self):
        test_charstr = '-30 8 -36 15 -37 22 44 54 31 61 22 68 rrcurveto'
        xpct_charstr = '-30 8 -36 15 -37 22 rrcurveto 44 54 31 61 22 68 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# hhcurveto
    def test_hhcurveto_4(self):
        test_charstr = '10 30 0 10 hhcurveto'
        xpct_charstr = '10 0 30 0 10 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_5(self):
        test_charstr = '40 -38 -60 41 -91 hhcurveto'
        xpct_charstr = '-38 40 -60 41 -91 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_mult_4_4(self):
        test_charstr = '43 23 25 18 29 56 42 -84 hhcurveto'
        xpct_charstr = '43 0 23 25 18 0 rrcurveto 29 0 56 42 -84 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_mult_5_4(self):
        test_charstr = '43 23 25 18 29 56 42 -84 79 hhcurveto'
        xpct_charstr = '23 43 25 18 29 0 rrcurveto 56 0 42 -84 79 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_mult_4_4_4(self):
        test_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 hhcurveto'
        xpct_charstr = '1 0 2 3 4 0 rrcurveto 5 0 6 7 8 0 rrcurveto 9 0 10 11 12 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_mult_5_4_4(self):
        test_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 13 hhcurveto'
        xpct_charstr = '2 1 3 4 5 0 rrcurveto 6 0 7 8 9 0 rrcurveto 10 0 11 12 13 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# vvcurveto
    def test_vvcurveto_4(self):
        test_charstr = '61 6 52 68 vvcurveto'
        xpct_charstr = '0 61 6 52 0 68 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_5(self):
        test_charstr = '61 38 35 56 72 vvcurveto'
        xpct_charstr = '61 38 35 56 0 72 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_mult_4_4(self):
        test_charstr = '-84 -88 -30 -90 -13 19 23 -11 vvcurveto'
        xpct_charstr = '0 -84 -88 -30 0 -90 rrcurveto 0 -13 19 23 0 -11 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_mult_5_4(self):
        test_charstr = '43 12 17 32 65 68 -6 52 61 vvcurveto'
        xpct_charstr = '43 12 17 32 0 65 rrcurveto 0 68 -6 52 0 61 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_mult_4_4_4(self):
        test_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 vvcurveto'
        xpct_charstr = '0 1 2 3 0 4 rrcurveto 0 5 6 7 0 8 rrcurveto 0 9 10 11 0 12 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_mult_5_4_4(self):
        test_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 13 vvcurveto'
        xpct_charstr = '1 2 3 4 0 5 rrcurveto 0 6 7 8 0 9 rrcurveto 0 10 11 12 0 13 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# hvcurveto
    def test_hvcurveto_4(self):
        test_charstr = '1 2 3 4 hvcurveto'
        xpct_charstr = '1 0 2 3 0 4 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_5(self):
        test_charstr = '57 44 22 40 34 hvcurveto'
        xpct_charstr = '57 0 44 22 34 40 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_4(self):
        test_charstr = '65 33 -19 -45 -45 -29 -25 -71 hvcurveto'
        xpct_charstr = '65 0 33 -19 0 -45 rrcurveto 0 -45 -29 -25 -71 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_5(self):
        test_charstr = '97 69 41 86 58 -36 34 -64 11 hvcurveto'
        xpct_charstr = '97 0 69 41 0 86 rrcurveto 0 58 -36 34 -64 11 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_4_4(self):
        test_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 hvcurveto'
        xpct_charstr = '1 0 2 3 0 4 rrcurveto 0 5 6 7 8 0 rrcurveto 9 0 10 11 0 12 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_4_5(self):
        test_charstr = '-124 -79 104 165 163 82 102 124 56 43 -25 -37 35 hvcurveto'
        xpct_charstr = '-124 0 -79 104 0 165 rrcurveto 0 163 82 102 124 0 rrcurveto 56 0 43 -25 35 -37 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_4_4_4(self):
        test_charstr = '32 25 22 32 31 -25 22 -32 -32 -25 -22 -31 -32 25 -22 32 hvcurveto'
        xpct_charstr = '32 0 25 22 0 32 rrcurveto 0 31 -25 22 -32 0 rrcurveto -32 0 -25 -22 0 -31 rrcurveto 0 -32 25 -22 32 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_4_4_4_5(self):
        test_charstr = '-170 -128 111 195 234 172 151 178 182 95 -118 -161 -130 -71 -77 -63 -55 -19 38 79 20 hvcurveto'
        xpct_charstr = '-170 0 -128 111 0 195 rrcurveto 0 234 172 151 178 0 rrcurveto 182 0 95 -118 0 -161 rrcurveto 0 -130 -71 -77 -63 0 rrcurveto -55 0 -19 38 20 79 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# vhcurveto
    def test_vhcurveto_4(self):
        test_charstr = '-57 43 -30 53 vhcurveto'
        xpct_charstr = '0 -57 43 -30 53 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_5(self):
        test_charstr = '41 -27 19 -46 11 vhcurveto'
        xpct_charstr = '0 41 -27 19 -46 11 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_4_4(self):
        test_charstr = '1 2 3 4 5 6 7 8 vhcurveto'
        xpct_charstr = '0 1 2 3 4 0 rrcurveto 5 0 6 7 0 8 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_4_5(self):
        test_charstr = '-64 -23 -25 -45 -30 -24 14 33 -19 vhcurveto'
        xpct_charstr = '0 -64 -23 -25 -45 0 rrcurveto -30 0 -24 14 -19 33 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_4_4_4(self):
        test_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 vhcurveto'
        xpct_charstr = '0 1 2 3 4 0 rrcurveto 5 0 6 7 0 8 rrcurveto 0 9 10 11 12 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_4_4_5(self):
        test_charstr = '108 59 81 98 99 59 -81 -108 -100 -46 -66 -63 -47 vhcurveto'
        xpct_charstr = '0 108 59 81 98 0 rrcurveto 99 0 59 -81 0 -108 rrcurveto 0 -100 -46 -66 -63 -47 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_4_4_4_5(self):
        test_charstr = '60 -26 37 -43 -33 -28 -22 -36 -37 27 -20 32 3 4 0 1 3 vhcurveto'
        xpct_charstr = '0 60 -26 37 -43 0 rrcurveto -33 0 -28 -22 0 -36 rrcurveto 0 -37 27 -20 32 0 rrcurveto 3 0 4 0 3 1 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# rcurveline
    def test_rcurveline_6_2(self):
        test_charstr = '21 -76 21 -72 24 -73 31 -100 rcurveline'
        xpct_charstr = '21 -76 21 -72 24 -73 rrcurveto 31 -100 rlineto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rcurveline_6_6_2(self):
        test_charstr = '-73 80 -80 121 -49 96 60 65 55 41 54 17 -8 78 rcurveline'
        xpct_charstr = '-73 80 -80 121 -49 96 rrcurveto 60 65 55 41 54 17 rrcurveto -8 78 rlineto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rcurveline_6_6_6_2(self):
        test_charstr = '1 64 10 51 29 39 15 21 15 20 15 18 47 -89 63 -98 52 -59 91 8 rcurveline'
        xpct_charstr = '1 64 10 51 29 39 rrcurveto 15 21 15 20 15 18 rrcurveto 47 -89 63 -98 52 -59 rrcurveto 91 8 rlineto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rcurveline_6_6_6_6_2(self):
        test_charstr = '1 64 10 51 29 39 15 21 15 20 15 18 46 -88 63 -97 52 -59 -38 -57 -49 -62 -52 -54 96 -8 rcurveline'
        xpct_charstr = '1 64 10 51 29 39 rrcurveto 15 21 15 20 15 18 rrcurveto 46 -88 63 -97 52 -59 rrcurveto -38 -57 -49 -62 -52 -54 rrcurveto 96 -8 rlineto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# rlinecurve
    def test_rlinecurve_2_6(self):
        test_charstr = '21 -76 21 -72 24 -73 31 -100 rlinecurve'
        xpct_charstr = '21 -76 rlineto 21 -72 24 -73 31 -100 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rlinecurve_2_2_6(self):
        test_charstr = '-73 80 -80 121 -49 96 60 65 55 41 rlinecurve'
        xpct_charstr = '-73 80 rlineto -80 121 rlineto -49 96 60 65 55 41 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rlinecurve_2_2_2_6(self):
        test_charstr = '1 64 10 51 29 39 15 21 15 20 15 18 rlinecurve'
        xpct_charstr = '1 64 rlineto 10 51 rlineto 29 39 rlineto 15 21 15 20 15 18 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rlinecurve_2_2_2_2_6(self):
        test_charstr = '1 64 10 51 29 39 15 21 15 20 15 18 46 -88 rlinecurve'
        xpct_charstr = '1 64 rlineto 10 51 rlineto 29 39 rlineto 15 21 rlineto 15 20 15 18 46 -88 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
