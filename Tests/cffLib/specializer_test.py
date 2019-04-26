from __future__ import print_function, division, absolute_import
from fontTools.cffLib.specializer import (programToString, stringToProgram,
                                          generalizeProgram, specializeProgram,
                                          programToCommands, commandsToProgram,
                                          generalizeCommands,
                                          specializeCommands)
from fontTools.ttLib import TTFont
import os
import unittest

# TODO
# https://github.com/fonttools/fonttools/pull/959#commitcomment-22059841
# Maybe we should make these data driven. Each entry will have an input string,
# and a generalized and specialized. For the latter two, if they are None, they
# are considered equal to the input. Then we can do roundtripping tests as well...
# There are a few other places (aosp tests for example) where we generate tests
# from data.


def get_generalized_charstr(charstr, **kwargs):
    return programToString(generalizeProgram(stringToProgram(charstr), **kwargs))


def get_specialized_charstr(charstr, **kwargs):
    return programToString(specializeProgram(stringToProgram(charstr), **kwargs))


class CFFGeneralizeProgramTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

# no arguments/operands
    def test_rmoveto_none(self):
        test_charstr = 'rmoveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_hmoveto_none(self):
        test_charstr = 'hmoveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_vmoveto_none(self):
        test_charstr = 'vmoveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_rlineto_none(self):
        test_charstr = 'rlineto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_hlineto_none(self):
        test_charstr = 'hlineto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_vlineto_none(self):
        test_charstr = 'vlineto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_rrcurveto_none(self):
        test_charstr = 'rrcurveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_hhcurveto_none(self):
        test_charstr = 'hhcurveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_vvcurveto_none(self):
        test_charstr = 'vvcurveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_hvcurveto_none(self):
        test_charstr = 'hvcurveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_vhcurveto_none(self):
        test_charstr = 'vhcurveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_rcurveline_none(self):
        test_charstr = 'rcurveline'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

    def test_rlinecurve_none(self):
        test_charstr = 'rlinecurve'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_generalized_charstr(test_charstr)

# rmoveto
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

    def test_rrcurveto_d3947b8(self):
        test_charstr = '1 2 3 4 5 0 rrcurveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_v0_0h_h0(self):
        test_charstr = '0 10 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto'
        xpct_charstr = '0 10 1 2 0 0 rrcurveto 0 0 1 2 0 1 rrcurveto 0 1 3 4 0 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_h0_0h_h0(self):
        test_charstr = '10 0 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto'
        xpct_charstr = '10 0 1 2 0 0 rrcurveto 0 0 1 2 0 1 rrcurveto 0 1 3 4 0 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_00_0h_h0(self):
        test_charstr = '0 0 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto'
        xpct_charstr = '0 0 1 2 0 0 rrcurveto 0 0 1 2 0 1 rrcurveto 0 1 3 4 0 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_r0_0h_h0(self):
        test_charstr = '10 10 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto'
        xpct_charstr = '10 10 1 2 0 0 rrcurveto 0 0 1 2 0 1 rrcurveto 0 1 3 4 0 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_v0_0v_v0(self):
        test_charstr = '0 10 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto'
        xpct_charstr = '0 10 1 2 0 0 rrcurveto 0 0 1 2 1 0 rrcurveto 1 0 3 4 0 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_h0_0v_v0(self):
        test_charstr = '10 0 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto'
        xpct_charstr = '10 0 1 2 0 0 rrcurveto 0 0 1 2 1 0 rrcurveto 1 0 3 4 0 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_00_0v_v0(self):
        test_charstr = '0 0 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto'
        xpct_charstr = '0 0 1 2 0 0 rrcurveto 0 0 1 2 1 0 rrcurveto 1 0 3 4 0 0 rrcurveto'
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_r0_0v_v0(self):
        test_charstr = '10 10 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto'
        xpct_charstr = '10 10 1 2 0 0 rrcurveto 0 0 1 2 1 0 rrcurveto 1 0 3 4 0 0 rrcurveto'
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

# hstem/vstem
    def test_hstem_vstem(self):
        test_charstr = '95 0 58 542 60 hstem 89 65 344 67 vstem 89 45 rmoveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# hstemhm/vstemhm
    def test_hstemhm_vstemhm(self):
        test_charstr = '-16 577 60 24 60 hstemhm 98 55 236 55 vstemhm 343 577 rmoveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# hintmask/cntrmask
    def test_hintmask_cntrmask(self):
        test_charstr = '52 80 153 61 4 83 -71.5 71.5 hintmask 11011100 94 119 216 119 216 119 cntrmask 1110000 154 -12 rmoveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# endchar
    def test_endchar(self):
        test_charstr = '-255 319 rmoveto 266 57 rlineto endchar'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)

# xtra
    def test_xtra(self):
        test_charstr = '-255 319 rmoveto 266 57 rlineto xtra 90 34'
        xpct_charstr = test_charstr
        self.assertEqual(get_generalized_charstr(test_charstr), xpct_charstr)


class CFFSpecializeProgramTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

# no arguments/operands
    def test_rmoveto_none(self):
        test_charstr = 'rmoveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_hmoveto_none(self):
        test_charstr = 'hmoveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_vmoveto_none(self):
        test_charstr = 'vmoveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_rlineto_none(self):
        test_charstr = 'rlineto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_hlineto_none(self):
        test_charstr = 'hlineto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_vlineto_none(self):
        test_charstr = 'vlineto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_rrcurveto_none(self):
        test_charstr = 'rrcurveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_hhcurveto_none(self):
        test_charstr = 'hhcurveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_vvcurveto_none(self):
        test_charstr = 'vvcurveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_hvcurveto_none(self):
        test_charstr = 'hvcurveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_vhcurveto_none(self):
        test_charstr = 'vhcurveto'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_rcurveline_none(self):
        test_charstr = 'rcurveline'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

    def test_rlinecurve_none(self):
        test_charstr = 'rlinecurve'
        with self.assertRaisesRegex(ValueError, r'\[\]'):
            get_specialized_charstr(test_charstr)

# rmoveto
    def test_rmoveto_zero(self):
        test_charstr = '0 0 rmoveto'
        xpct_charstr = '0 hmoveto'
        self.assertEqual(get_specialized_charstr(test_charstr,
                                        generalizeFirst=False), xpct_charstr)

    def test_rmoveto_zero_mult(self):
        test_charstr = '0 0 rmoveto '*3
        xpct_charstr = '0 hmoveto'
        self.assertEqual(get_specialized_charstr(test_charstr,
                                        generalizeFirst=False), xpct_charstr)

    def test_rmoveto_zero_width(self):
        test_charstr = '100 0 0 rmoveto'
        xpct_charstr = '100 0 hmoveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rmoveto(self):
        test_charstr = '.55 -.8 rmoveto'
        xpct_charstr = '0.55 -0.8 rmoveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rmoveto_mult(self):
        test_charstr = '55 -8 rmoveto '*3
        xpct_charstr = '165 -24 rmoveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rmoveto_width(self):
        test_charstr = '100.5 50 -5.8 rmoveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

# rlineto
    def test_rlineto_zero(self):
        test_charstr = '0 0 rlineto'
        xpct_charstr = ''
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rlineto_zero_mult(self):
        test_charstr = '0 0 rlineto '*3
        xpct_charstr = ''
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rlineto(self):
        test_charstr = '.55 -.8 rlineto'
        xpct_charstr = '0.55 -0.8 rlineto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rlineto_mult(self):
        test_charstr = '.55 -.8 rlineto '*3
        xpct_charstr = '0.55 -0.8 0.55 -0.8 0.55 -0.8 rlineto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hlineto(self):
        test_charstr = '.67 0 rlineto'
        xpct_charstr = '0.67 hlineto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hlineto_zero_mult(self):
        test_charstr = '62 0 rlineto '*3
        xpct_charstr = '186 hlineto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hlineto_mult(self):
        test_charstr = '.67 0 rlineto 0 -6.0 rlineto .67 0 rlineto'
        xpct_charstr = '0.67 -6.0 0.67 hlineto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vlineto(self):
        test_charstr = '0 -.24 rlineto'
        xpct_charstr = '-0.24 vlineto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vlineto_zero_mult(self):
        test_charstr = '0 -24 rlineto '*3
        xpct_charstr = '-72 vlineto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vlineto_mult(self):
        test_charstr = '0 -.24 rlineto +50 0 rlineto 0 30 rlineto -4 0 rlineto'
        xpct_charstr = '-0.24 50 30 -4 vlineto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_0lineto_peephole(self):
        test_charstr = '1 2 0 0 3 4 rlineto'
        xpct_charstr = '1 2 3 4 rlineto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hlineto_peephole(self):
        test_charstr = '1 2 5 0 3 4 rlineto'
        xpct_charstr = test_charstr
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vlineto_peephole(self):
        test_charstr = '1 2 0 5 3 4 rlineto'
        xpct_charstr = test_charstr
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

# rrcurveto
    def test_rrcurveto(self):
        test_charstr = '-1 56 -2 57 -1 57 rrcurveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_mult(self):
        test_charstr = '-30 8 -36 15 -37 22 rrcurveto 44 54 31 61 22 68 rrcurveto'
        xpct_charstr = '-30 8 -36 15 -37 22 44 54 31 61 22 68 rrcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_d3947b8(self):
        test_charstr = '1 2 3 4 5 0 rrcurveto'
        xpct_charstr = '2 1 3 4 5 hhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_4(self):
        test_charstr = '10 0 30 0 10 0 rrcurveto'
        xpct_charstr = '10 30 0 10 hhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_5(self):
        test_charstr = '-38 40 -60 41 -91 0 rrcurveto'
        xpct_charstr = '40 -38 -60 41 -91 hhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_mult_4_4(self):
        test_charstr = '43 0 23 25 18 0 rrcurveto 29 0 56 42 -84 0 rrcurveto'
        xpct_charstr = '43 23 25 18 29 56 42 -84 hhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_mult_5_4(self):
        test_charstr = '23 43 25 18 29 0 rrcurveto 56 0 42 -84 79 0 rrcurveto'
        xpct_charstr = '43 23 25 18 29 56 42 -84 79 hhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_mult_4_4_4(self):
        test_charstr = '1 0 2 3 4 0 rrcurveto 5 0 6 7 8 0 rrcurveto 9 0 10 11 12 0 rrcurveto'
        xpct_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 hhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_mult_5_4_4(self):
        test_charstr = '2 1 3 4 5 0 rrcurveto 6 0 7 8 9 0 rrcurveto 10 0 11 12 13 0 rrcurveto'
        xpct_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 13 hhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_4(self):
        test_charstr = '0 61 6 52 0 68 rrcurveto'
        xpct_charstr = '61 6 52 68 vvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_5(self):
        test_charstr = '61 38 35 56 0 72 rrcurveto'
        xpct_charstr = '61 38 35 56 72 vvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_mult_4_4(self):
        test_charstr = '0 -84 -88 -30 0 -90 rrcurveto 0 -13 19 23 0 -11 rrcurveto'
        xpct_charstr = '-84 -88 -30 -90 -13 19 23 -11 vvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_mult_5_4(self):
        test_charstr = '43 12 17 32 0 65 rrcurveto 0 68 -6 52 0 61 rrcurveto'
        xpct_charstr = '43 12 17 32 65 68 -6 52 61 vvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_mult_4_4_4(self):
        test_charstr = '0 1 2 3 0 4 rrcurveto 0 5 6 7 0 8 rrcurveto 0 9 10 11 0 12 rrcurveto'
        xpct_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 vvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_mult_5_4_4(self):
        test_charstr = '1 2 3 4 0 5 rrcurveto 0 6 7 8 0 9 rrcurveto 0 10 11 12 0 13 rrcurveto'
        xpct_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 13 vvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4(self):
        test_charstr = '1 0 2 3 0 4 rrcurveto'
        xpct_charstr = '1 2 3 4 hvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_5(self):
        test_charstr = '57 0 44 22 34 40 rrcurveto'
        xpct_charstr = '57 44 22 40 34 hvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_4(self):
        test_charstr = '65 0 33 -19 0 -45 rrcurveto 0 -45 -29 -25 -71 0 rrcurveto'
        xpct_charstr = '65 33 -19 -45 -45 -29 -25 -71 hvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_5(self):
        test_charstr = '97 0 69 41 0 86 rrcurveto 0 58 -36 34 -64 11 rrcurveto'
        xpct_charstr = '97 69 41 86 58 -36 34 -64 11 hvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_4_4(self):
        test_charstr = '1 0 2 3 0 4 rrcurveto 0 5 6 7 8 0 rrcurveto 9 0 10 11 0 12 rrcurveto'
        xpct_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 hvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_4_5(self):
        test_charstr = '-124 0 -79 104 0 165 rrcurveto 0 163 82 102 124 0 rrcurveto 56 0 43 -25 35 -37 rrcurveto'
        xpct_charstr = '-124 -79 104 165 163 82 102 124 56 43 -25 -37 35 hvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_4_4_4(self):
        test_charstr = '32 0 25 22 0 32 rrcurveto 0 31 -25 22 -32 0 rrcurveto -32 0 -25 -22 0 -31 rrcurveto 0 -32 25 -22 32 0 rrcurveto'
        xpct_charstr = '32 25 22 32 31 -25 22 -32 -32 -25 -22 -31 -32 25 -22 32 hvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_4_4_4_4_5(self):
        test_charstr = '-170 0 -128 111 0 195 rrcurveto 0 234 172 151 178 0 rrcurveto 182 0 95 -118 0 -161 rrcurveto 0 -130 -71 -77 -63 0 rrcurveto -55 0 -19 38 20 79 rrcurveto'
        xpct_charstr = '-170 -128 111 195 234 172 151 178 182 95 -118 -161 -130 -71 -77 -63 -55 -19 38 79 20 hvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_4(self):
        test_charstr = '0 -57 43 -30 53 0 rrcurveto'
        xpct_charstr = '-57 43 -30 53 vhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_5(self):
        test_charstr = '0 41 -27 19 -46 11 rrcurveto'
        xpct_charstr = '41 -27 19 -46 11 vhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_4_4(self):
        test_charstr = '0 1 2 3 4 0 rrcurveto 5 0 6 7 0 8 rrcurveto'
        xpct_charstr = '1 2 3 4 5 6 7 8 vhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_4_5(self):
        test_charstr = '0 -64 -23 -25 -45 0 rrcurveto -30 0 -24 14 -19 33 rrcurveto'
        xpct_charstr = '-64 -23 -25 -45 -30 -24 14 33 -19 vhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_4_4_4(self):
        test_charstr = '0 1 2 3 4 0 rrcurveto 5 0 6 7 0 8 rrcurveto 0 9 10 11 12 0 rrcurveto'
        xpct_charstr = '1 2 3 4 5 6 7 8 9 10 11 12 vhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_4_4_5(self):
        test_charstr = '0 108 59 81 98 0 rrcurveto 99 0 59 -81 0 -108 rrcurveto 0 -100 -46 -66 -63 -47 rrcurveto'
        xpct_charstr = '108 59 81 98 99 59 -81 -108 -100 -46 -66 -63 -47 vhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_4_4_4_5(self):
        test_charstr = '0 60 -26 37 -43 0 rrcurveto -33 0 -28 -22 0 -36 rrcurveto 0 -37 27 -20 32 0 rrcurveto 3 0 4 0 3 1 rrcurveto'
        xpct_charstr = '60 -26 37 -43 -33 -28 -22 -36 -37 27 -20 32 3 4 0 1 3 vhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_v0_0h_h0(self):
        test_charstr = '0 10 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto'
        xpct_charstr = '10 1 2 0 0 1 2 1 1 3 4 0 vhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_h0_0h_h0(self):
        test_charstr = '10 0 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto'
        xpct_charstr = '10 1 2 0 hhcurveto 0 1 2 1 1 3 4 0 hvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_00_0h_h0(self):
        test_charstr = '0 0 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto'
        xpct_charstr = '1 2 rlineto 0 1 2 1 1 3 4 0 hvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_r0_0h_h0(self):
        test_charstr = '10 10 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto'
        xpct_charstr = '10 10 1 2 0 0 1 2 1 1 3 4 0 vvcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_v0_0v_v0(self):
        test_charstr = '0 10 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto'
        xpct_charstr = '10 1 2 0 vhcurveto 0 1 2 1 1 3 4 0 hhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_h0_0v_v0(self):
        test_charstr = '10 0 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto'
        xpct_charstr = '10 1 2 0 0 1 2 1 1 3 4 0 hhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_00_0v_v0(self):
        test_charstr = '0 0 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto'
        xpct_charstr = '1 2 rlineto 0 1 2 1 1 3 4 0 hhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rrcurveto_r0_0v_v0(self):
        test_charstr = '10 10 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto'
        xpct_charstr = '10 10 1 2 0 0 1 2 1 1 3 4 0 hhcurveto'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hhcurveto_peephole(self):
        test_charstr = '1 2 3 4 5 6 1 2 3 4 5 0 1 2 3 4 5 6 rrcurveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vvcurveto_peephole(self):
        test_charstr = '1 2 3 4 5 6 1 2 3 4 0 6 1 2 3 4 5 6 rrcurveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_hvcurveto_peephole(self):
        test_charstr = '1 2 3 4 5 6 1 0 3 4 5 6 1 2 3 4 5 6 rrcurveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_vhcurveto_peephole(self):
        test_charstr = '1 2 3 4 5 6 0 2 3 4 5 6 1 2 3 4 5 6 rrcurveto'
        xpct_charstr = test_charstr
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rcurveline_6_2(self):
        test_charstr = '21 -76 21 -72 24 -73 rrcurveto 31 -100 rlineto'
        xpct_charstr = '21 -76 21 -72 24 -73 31 -100 rcurveline'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rcurveline_6_6_2(self):
        test_charstr = '-73 80 -80 121 -49 96 rrcurveto 60 65 55 41 54 17 rrcurveto -8 78 rlineto'
        xpct_charstr = '-73 80 -80 121 -49 96 60 65 55 41 54 17 -8 78 rcurveline'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rcurveline_6_6_6_2(self):
        test_charstr = '1 64 10 51 29 39 rrcurveto 15 21 15 20 15 18 rrcurveto 47 -89 63 -98 52 -59 rrcurveto 91 8 rlineto'
        xpct_charstr = '1 64 10 51 29 39 15 21 15 20 15 18 47 -89 63 -98 52 -59 91 8 rcurveline'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rlinecurve_2_6(self):
        test_charstr = '21 -76 rlineto 21 -72 24 -73 31 -100 rrcurveto'
        xpct_charstr = '21 -76 21 -72 24 -73 31 -100 rlinecurve'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rlinecurve_2_2_6(self):
        test_charstr = '-73 80 rlineto -80 121 rlineto -49 96 60 65 55 41 rrcurveto'
        xpct_charstr = '-73 80 -80 121 -49 96 60 65 55 41 rlinecurve'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

    def test_rlinecurve_2_2_2_6(self):
        test_charstr = '1 64 rlineto 10 51 rlineto 29 39 rlineto 15 21 15 20 15 18 rrcurveto'
        xpct_charstr = '1 64 10 51 29 39 15 21 15 20 15 18 rlinecurve'
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)

# maxstack CFF=48, specializer uses up to 47
    def test_maxstack(self):
        operands = '1 2 3 4 5 6 '
        operator = 'rrcurveto '
        test_charstr = (operands + operator)*9
        xpct_charstr = (operands*2 + operator + operands*7 + operator).rstrip()
        self.assertEqual(get_specialized_charstr(test_charstr), xpct_charstr)


class CFF2VFTestSpecialize(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    @staticmethod
    def get_test_input(test_file_or_folder):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "data", test_file_or_folder)

    def test_blend_round_trip(self):
        otfvf_path = self.get_test_input('TestSparseCFF2VF.otf')
        ttf_font = TTFont(otfvf_path)
        fontGlyphList = ttf_font.getGlyphOrder()
        topDict = ttf_font['CFF2'].cff.topDictIndex[0]
        charstrings = topDict.CharStrings
        for glyphName in fontGlyphList:
            print(glyphName)
            cs = charstrings[glyphName]
            cs.decompile()
            cmds = programToCommands(cs.program, getNumRegions=cs.getNumRegions)
            cmds_g = generalizeCommands(cmds)
            cmds = specializeCommands(cmds_g, generalizeFirst=False)
            program = commandsToProgram(cmds)
            self.assertEqual(program, cs.program)
            program = specializeProgram(program, getNumRegions=cs.getNumRegions)
            self.assertEqual(program, cs.program)
            program_g = generalizeProgram(program, getNumRegions=cs.getNumRegions)
            program = commandsToProgram(cmds_g)
            self.assertEqual(program, program_g)


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
