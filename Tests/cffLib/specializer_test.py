from fontTools.cffLib import maxStackLimit as maxStack
from fontTools.cffLib.specializer import (
    programToString,
    stringToProgram,
    generalizeProgram,
    specializeProgram,
    programToCommands,
    commandsToProgram,
    generalizeCommands,
    specializeCommands,
)
from fontTools.ttLib import TTFont
import os
import pytest
from fontTools.misc.testTools import parseXML, DataFilesHandler


def charstr_generalize(charstr, **kwargs):
    return programToString(generalizeProgram(stringToProgram(charstr), **kwargs))


def charstr_specialize(charstr, **kwargs):
    return programToString(specializeProgram(stringToProgram(charstr), **kwargs))


def program_stack_use(program, getNumRegions=None):
    vsindex = None
    maxStack = 0
    stack = []
    for token in program:
        if token == vsindex:
            vsindex = stack[-1]
            stack = []
        elif token == "blend":
            numBlends = stack[-1]
            numRegions = getNumRegions(vsindex)
            numOperandsToPop = 1 + numBlends * numRegions
            stack[-numOperandsToPop:] = []
        elif type(token) is str:
            stack = []
        else:
            stack.append(token)
            maxStack = max(maxStack, len(stack))

    return maxStack


class CFFGeneralizeProgramTest:
    @pytest.mark.parametrize(
        "charstr",
        [
            # no arguments/operands
            ("rmoveto"),  # test_rmoveto_none
            ("hmoveto"),  # test_hmoveto_none
            ("vmoveto"),  # test_vmoveto_none
            ("rlineto"),  # test_rlineto_none
            ("hlineto"),  # test_hlineto_none
            ("vlineto"),  # test_vlineto_none
            ("rrcurveto"),  # test_rrcurveto_none
            ("hhcurveto"),  # test_hhcurveto_none
            ("vvcurveto"),  # test_vvcurveto_none
            ("hvcurveto"),  # test_hvcurveto_none
            ("vhcurveto"),  # test_vhcurveto_none
            ("rcurveline"),  # test_rcurveline_none
            ("rlinecurve"),  # test_rlinecurve_none
        ],
    )
    def test_raises(self, charstr):
        try:
            charstr_generalize(charstr)
        except ValueError:
            return
        raise AssertionError("Expected to raise ValueError, but didn't.", charstr)

    @pytest.mark.parametrize(
        "charstr, expected",
        [
            # rmoveto
            ("0 0 rmoveto", None),  # test_rmoveto_zero
            ("100 0 0 rmoveto", None),  # test_rmoveto_zero_width
            (".55 -.8 rmoveto", "0.55 -0.8 rmoveto"),  # test_rmoveto
            ("100.5 50 -5.8 rmoveto", None),  # test_rmoveto_width
            # hmoveto
            ("0 hmoveto", "0 0 rmoveto"),  # test_hmoveto_zero
            ("100 0 hmoveto", "100 0 0 rmoveto"),  # test_hmoveto_zero_width
            (".67 hmoveto", "0.67 0 rmoveto"),  # test_hmoveto
            ("100 -70 hmoveto", "100 -70 0 rmoveto"),  # test_hmoveto_width
            # vmoveto
            ("0 vmoveto", "0 0 rmoveto"),  # test_vmoveto_zero
            ("100 0 vmoveto", "100 0 0 rmoveto"),  # test_vmoveto_zero_width
            ("-.24 vmoveto", "0 -0.24 rmoveto"),  # test_vmoveto
            ("100 44 vmoveto", "100 0 44 rmoveto"),  # test_vmoveto_width
            # rlineto
            ("0 0 rlineto", None),  # test_rlineto_zero
            (  # test_rlineto_zero_mult
                "0 0 0 0 0 0 rlineto",
                "0 0 rlineto " * 3,
            ),
            (".55 -.8 rlineto", "0.55 -0.8 rlineto"),  # test_rlineto
            (  # test_rlineto_mult
                ".55 -.8 .55 -.8 .55 -.8 rlineto",
                "0.55 -0.8 rlineto " * 3,
            ),
            # hlineto
            ("0 hlineto", "0 0 rlineto"),  # test_hlineto_zero
            (  # test_hlineto_zero_mult
                "0 0 0 0 hlineto",
                "0 0 rlineto " * 4,
            ),
            (".67 hlineto", "0.67 0 rlineto"),  # test_hlineto
            (  # test_hlineto_mult
                ".67 -6.0 .67 hlineto",
                "0.67 0 rlineto 0 -6.0 rlineto 0.67 0 rlineto",
            ),
            # vlineto
            ("0 vlineto", "0 0 rlineto"),  # test_vlineto_zero
            ("0 0 0 vlineto", "0 0 rlineto " * 3),  # test_vlineto_zero_mult
            ("-.24 vlineto", "0 -0.24 rlineto"),  # test_vlineto
            (  # test_vlineto_mult
                "-.24 +50 30 -4 vlineto",
                "0 -0.24 rlineto 50 0 rlineto 0 30 rlineto -4 0 rlineto",
            ),
            # rrcurveto
            ("-1 56 -2 57 -1 57 rrcurveto", None),  # test_rrcurveto
            (  # test_rrcurveto_mult
                "-30 8 -36 15 -37 22 44 54 31 61 22 68 rrcurveto",
                "-30 8 -36 15 -37 22 rrcurveto 44 54 31 61 22 68 rrcurveto",
            ),
            ("1 2 3 4 5 0 rrcurveto", None),  # test_rrcurveto_d3947b8
            (  # test_rrcurveto_v0_0h_h0
                "0 10 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto",
                "0 10 1 2 0 0 rrcurveto 0 0 1 2 0 1 rrcurveto 0 1 3 4 0 0 rrcurveto",
            ),
            (  # test_rrcurveto_h0_0h_h0
                "10 0 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto",
                "10 0 1 2 0 0 rrcurveto 0 0 1 2 0 1 rrcurveto 0 1 3 4 0 0 rrcurveto",
            ),
            (  # test_rrcurveto_00_0h_h0
                "0 0 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto",
                "0 0 1 2 0 0 rrcurveto 0 0 1 2 0 1 rrcurveto 0 1 3 4 0 0 rrcurveto",
            ),
            (  # test_rrcurveto_r0_0h_h0
                "10 10 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto",
                "10 10 1 2 0 0 rrcurveto 0 0 1 2 0 1 rrcurveto 0 1 3 4 0 0 rrcurveto",
            ),
            (  # test_rrcurveto_v0_0v_v0
                "0 10 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto",
                "0 10 1 2 0 0 rrcurveto 0 0 1 2 1 0 rrcurveto 1 0 3 4 0 0 rrcurveto",
            ),
            (  # test_rrcurveto_h0_0v_v0
                "10 0 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto",
                "10 0 1 2 0 0 rrcurveto 0 0 1 2 1 0 rrcurveto 1 0 3 4 0 0 rrcurveto",
            ),
            (  # test_rrcurveto_00_0v_v0
                "0 0 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto",
                "0 0 1 2 0 0 rrcurveto 0 0 1 2 1 0 rrcurveto 1 0 3 4 0 0 rrcurveto",
            ),
            (  # test_rrcurveto_r0_0v_v0
                "10 10 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto",
                "10 10 1 2 0 0 rrcurveto 0 0 1 2 1 0 rrcurveto 1 0 3 4 0 0 rrcurveto",
            ),
            # hhcurveto
            ("10 30 0 10 hhcurveto", "10 0 30 0 10 0 rrcurveto"),  # test_hhcurveto_4
            (  # test_hhcurveto_5
                "40 -38 -60 41 -91 hhcurveto",
                "-38 40 -60 41 -91 0 rrcurveto",
            ),
            (  # test_hhcurveto_mult_4_4
                "43 23 25 18 29 56 42 -84 hhcurveto",
                "43 0 23 25 18 0 rrcurveto 29 0 56 42 -84 0 rrcurveto",
            ),
            (  # test_hhcurveto_mult_5_4
                "43 23 25 18 29 56 42 -84 79 hhcurveto",
                "23 43 25 18 29 0 rrcurveto 56 0 42 -84 79 0 rrcurveto",
            ),
            (  # test_hhcurveto_mult_4_4_4
                "1 2 3 4 5 6 7 8 9 10 11 12 hhcurveto",
                "1 0 2 3 4 0 rrcurveto 5 0 6 7 8 0 rrcurveto 9 0 10 11 12 0 rrcurveto",
            ),
            (  # test_hhcurveto_mult_5_4_4
                "1 2 3 4 5 6 7 8 9 10 11 12 13 hhcurveto",
                "2 1 3 4 5 0 rrcurveto 6 0 7 8 9 0 rrcurveto 10 0 11 12 13 0 rrcurveto",
            ),
            # vvcurveto
            ("61 6 52 68 vvcurveto", "0 61 6 52 0 68 rrcurveto"),  # test_vvcurveto_4
            (  # test_vvcurveto_5
                "61 38 35 56 72 vvcurveto",
                "61 38 35 56 0 72 rrcurveto",
            ),
            (  # test_vvcurveto_mult_4_4
                "-84 -88 -30 -90 -13 19 23 -11 vvcurveto",
                "0 -84 -88 -30 0 -90 rrcurveto 0 -13 19 23 0 -11 rrcurveto",
            ),
            (  # test_vvcurveto_mult_5_4
                "43 12 17 32 65 68 -6 52 61 vvcurveto",
                "43 12 17 32 0 65 rrcurveto 0 68 -6 52 0 61 rrcurveto",
            ),
            (  # test_vvcurveto_mult_4_4_4
                "1 2 3 4 5 6 7 8 9 10 11 12 vvcurveto",
                "0 1 2 3 0 4 rrcurveto 0 5 6 7 0 8 rrcurveto 0 9 10 11 0 12 rrcurveto",
            ),
            (  # test_vvcurveto_mult_5_4_4
                "1 2 3 4 5 6 7 8 9 10 11 12 13 vvcurveto",
                "1 2 3 4 0 5 rrcurveto 0 6 7 8 0 9 rrcurveto 0 10 11 12 0 13 rrcurveto",
            ),
            # hvcurveto
            ("1 2 3 4 hvcurveto", "1 0 2 3 0 4 rrcurveto"),  # test_hvcurveto_4
            (  # test_hvcurveto_5
                "57 44 22 40 34 hvcurveto",
                "57 0 44 22 34 40 rrcurveto",
            ),
            (  # test_hvcurveto_4_4
                "65 33 -19 -45 -45 -29 -25 -71 hvcurveto",
                "65 0 33 -19 0 -45 rrcurveto 0 -45 -29 -25 -71 0 rrcurveto",
            ),
            (  # test_hvcurveto_4_5
                "97 69 41 86 58 -36 34 -64 11 hvcurveto",
                "97 0 69 41 0 86 rrcurveto 0 58 -36 34 -64 11 rrcurveto",
            ),
            (  # test_hvcurveto_4_4_4
                "1 2 3 4 5 6 7 8 9 10 11 12 hvcurveto",
                "1 0 2 3 0 4 rrcurveto 0 5 6 7 8 0 rrcurveto 9 0 10 11 0 12 rrcurveto",
            ),
            (  # test_hvcurveto_4_4_5
                "-124 -79 104 165 163 82 102 124 56 43 -25 -37 35 hvcurveto",
                "-124 0 -79 104 0 165 rrcurveto 0 163 82 102 124 0 rrcurveto 56 0 43 -25 35 -37 rrcurveto",
            ),
            (  # test_hvcurveto_4_4_4_4
                "32 25 22 32 31 -25 22 -32 -32 -25 -22 -31 -32 25 -22 32 hvcurveto",
                "32 0 25 22 0 32 rrcurveto 0 31 -25 22 -32 0 rrcurveto -32 0 -25 -22 0 -31 rrcurveto 0 -32 25 -22 32 0 rrcurveto",
            ),
            (  # test_hvcurveto_4_4_4_4_5
                "-170 -128 111 195 234 172 151 178 182 95 -118 -161 -130 -71 -77 -63 -55 -19 38 79 20 hvcurveto",
                "-170 0 -128 111 0 195 rrcurveto 0 234 172 151 178 0 rrcurveto 182 0 95 -118 0 -161 rrcurveto 0 -130 -71 -77 -63 0 rrcurveto -55 0 -19 38 20 79 rrcurveto",
            ),
            # vhcurveto
            (  # test_vhcurveto_4
                "-57 43 -30 53 vhcurveto",
                "0 -57 43 -30 53 0 rrcurveto",
            ),
            (  # test_vhcurveto_5
                "41 -27 19 -46 11 vhcurveto",
                "0 41 -27 19 -46 11 rrcurveto",
            ),
            (  # test_vhcurveto_4_4
                "1 2 3 4 5 6 7 8 vhcurveto",
                "0 1 2 3 4 0 rrcurveto 5 0 6 7 0 8 rrcurveto",
            ),
            (  # test_vhcurveto_4_5
                "-64 -23 -25 -45 -30 -24 14 33 -19 vhcurveto",
                "0 -64 -23 -25 -45 0 rrcurveto -30 0 -24 14 -19 33 rrcurveto",
            ),
            (  # test_vhcurveto_4_4_4
                "1 2 3 4 5 6 7 8 9 10 11 12 vhcurveto",
                "0 1 2 3 4 0 rrcurveto 5 0 6 7 0 8 rrcurveto 0 9 10 11 12 0 rrcurveto",
            ),
            (  # test_vhcurveto_4_4_5
                "108 59 81 98 99 59 -81 -108 -100 -46 -66 -63 -47 vhcurveto",
                "0 108 59 81 98 0 rrcurveto 99 0 59 -81 0 -108 rrcurveto 0 -100 -46 -66 -63 -47 rrcurveto",
            ),
            (  # test_vhcurveto_4_4_4_5
                "60 -26 37 -43 -33 -28 -22 -36 -37 27 -20 32 3 4 0 1 3 vhcurveto",
                "0 60 -26 37 -43 0 rrcurveto -33 0 -28 -22 0 -36 rrcurveto 0 -37 27 -20 32 0 rrcurveto 3 0 4 0 3 1 rrcurveto",
            ),
            # rcurveline
            (  # test_rcurveline_6_2
                "21 -76 21 -72 24 -73 31 -100 rcurveline",
                "21 -76 21 -72 24 -73 rrcurveto 31 -100 rlineto",
            ),
            (  # test_rcurveline_6_6_2
                "-73 80 -80 121 -49 96 60 65 55 41 54 17 -8 78 rcurveline",
                "-73 80 -80 121 -49 96 rrcurveto 60 65 55 41 54 17 rrcurveto -8 78 rlineto",
            ),
            (  # test_rcurveline_6_6_6_2
                "1 64 10 51 29 39 15 21 15 20 15 18 47 -89 63 -98 52 -59 91 8 rcurveline",
                "1 64 10 51 29 39 rrcurveto 15 21 15 20 15 18 rrcurveto 47 -89 63 -98 52 -59 rrcurveto 91 8 rlineto",
            ),
            (  # test_rcurveline_6_6_6_6_2
                "1 64 10 51 29 39 15 21 15 20 15 18 46 -88 63 -97 52 -59 -38 -57 -49 -62 -52 -54 96 -8 rcurveline",
                "1 64 10 51 29 39 rrcurveto 15 21 15 20 15 18 rrcurveto 46 -88 63 -97 52 -59 rrcurveto -38 -57 -49 -62 -52 -54 rrcurveto 96 -8 rlineto",
            ),
            # rlinecurve
            (  # test_rlinecurve_2_6
                "21 -76 21 -72 24 -73 31 -100 rlinecurve",
                "21 -76 rlineto 21 -72 24 -73 31 -100 rrcurveto",
            ),
            (  # test_rlinecurve_2_2_6
                "-73 80 -80 121 -49 96 60 65 55 41 rlinecurve",
                "-73 80 rlineto -80 121 rlineto -49 96 60 65 55 41 rrcurveto",
            ),
            (  # test_rlinecurve_2_2_2_6
                "1 64 10 51 29 39 15 21 15 20 15 18 rlinecurve",
                "1 64 rlineto 10 51 rlineto 29 39 rlineto 15 21 15 20 15 18 rrcurveto",
            ),
            (  # test_rlinecurve_2_2_2_2_6
                "1 64 10 51 29 39 15 21 15 20 15 18 46 -88 rlinecurve",
                "1 64 rlineto 10 51 rlineto 29 39 rlineto 15 21 rlineto 15 20 15 18 46 -88 rrcurveto",
            ),
            # hstem/vstem
            (  # test_hstem_vstem
                "95 0 58 542 60 hstem 89 65 344 67 vstem 89 45 rmoveto",
                None,
            ),
            # hstemhm/vstemhm
            (  # test_hstemhm_vstemhm
                "-16 577 60 24 60 hstemhm 98 55 236 55 vstemhm 343 577 rmoveto",
                None,
            ),
            # hintmask/cntrmask
            (  # test_hintmask_cntrmask
                "52 80 153 61 4 83 -71.5 71.5 hintmask 11011100 94 119 216 119 216 119 cntrmask 1110000 154 -12 rmoveto",
                None,
            ),
            # endchar
            ("-255 319 rmoveto 266 57 rlineto endchar", None),  # test_endchar
            # xtra
            ("-255 319 rmoveto 266 57 rlineto xtra 90 34", None),  # test_xtra
        ],
    )
    def test_generalize(self, charstr, expected):
        if expected is None:
            expected = charstr
        expected = expected.strip()
        generalized = charstr_generalize(charstr)
        assert generalized == expected, (generalized, expected)


class CFFSpecializeProgramTest:
    @pytest.mark.parametrize(
        "charstr",
        [
            # no arguments/operands
            ("rmoveto"),  # test_rmoveto_none
            ("hmoveto"),  # test_hmoveto_none
            ("vmoveto"),  # test_vmoveto_none
            ("rlineto"),  # test_rlineto_none
            ("hlineto"),  # test_hlineto_none
            ("vlineto"),  # test_vlineto_none
            ("rrcurveto"),  # test_rrcurveto_none
            ("hhcurveto"),  # test_hhcurveto_none
            ("vvcurveto"),  # test_vvcurveto_none
            ("hvcurveto"),  # test_hvcurveto_none
            ("vhcurveto"),  # test_vhcurveto_none
            ("rcurveline"),  # test_rcurveline_none
            ("rlinecurve"),  # test_rlinecurve_none
        ],
    )
    def test_raises(self, charstr):
        try:
            charstr_specialize(charstr)
        except ValueError:
            return
        raise AssertionError("Expected to raise ValueError, but didn't.", charstr)

    @pytest.mark.parametrize(
        "charstr, expected",
        [
            # rmoveto
            ("0 0 rmoveto", "0 hmoveto"),  # test_rmoveto_zero
            ("0 0 rmoveto " * 3, "0 hmoveto"),  # test_rmoveto_zero_mult
            ("100 0 0 rmoveto", "100 0 hmoveto"),  # test_rmoveto_zero_width
            (".55 -.8 rmoveto", "0.55 -0.8 rmoveto"),  # test_rmoveto
            ("55 -8 rmoveto " * 3, "165 -24 rmoveto"),  # test_rmoveto_mult
            ("100.5 50 -5.8 rmoveto", None),  # test_rmoveto_width
            # rlineto
            ("0 0 rlineto", ""),  # test_rlineto_zero
            ("0 0 rlineto " * 3, ""),  # test_rlineto_zero_mult
            (".55 -.8 rlineto", "0.55 -0.8 rlineto"),  # test_rlineto
            (  # test_rlineto_mult
                ".55 -.8 rlineto " * 3,
                "0.55 -0.8 0.55 -0.8 0.55 -0.8 rlineto",
            ),
            (".67 0 rlineto", "0.67 hlineto"),  # test_hlineto
            ("62 0 rlineto " * 3, "186 hlineto"),  # test_hlineto_zero_mult
            (  # test_hlineto_mult
                ".67 0 rlineto 0 -6.0 rlineto .67 0 rlineto",
                "0.67 -6.0 0.67 hlineto",
            ),
            ("0 -.24 rlineto", "-0.24 vlineto"),  # test_vlineto
            ("0 -24 rlineto " * 3, "-72 vlineto"),  # test_vlineto_zero_mult
            (  # test_vlineto_mult
                "0 -.24 rlineto +50 0 rlineto 0 30 rlineto -4 0 rlineto",
                "-0.24 50 30 -4 vlineto",
            ),
            ("1 2 0 0 3 4 rlineto", "1 2 3 4 rlineto"),  # test_0lineto_peephole
            ("1 2 5 0 3 4 rlineto", None),  # test_hlineto_peephole
            ("1 2 0 5 3 4 rlineto", None),  # test_vlineto_peephole
            # rrcurveto
            ("-1 56 -2 57 -1 57 rrcurveto", None),  # test_rrcurveto
            (  # test_rrcurveto_mult
                "-30 8 -36 15 -37 22 rrcurveto 44 54 31 61 22 68 rrcurveto",
                "-30 8 -36 15 -37 22 44 54 31 61 22 68 rrcurveto",
            ),
            ("1 2 3 4 5 0 rrcurveto", "2 1 3 4 5 hhcurveto"),  # test_rrcurveto_d3947b8
            ("10 0 30 0 10 0 rrcurveto", "10 30 0 10 hhcurveto"),  # test_hhcurveto_4
            (  # test_hhcurveto_5
                "-38 40 -60 41 -91 0 rrcurveto",
                "40 -38 -60 41 -91 hhcurveto",
            ),
            (  # test_hhcurveto_mult_4_4
                "43 0 23 25 18 0 rrcurveto 29 0 56 42 -84 0 rrcurveto",
                "43 23 25 18 29 56 42 -84 hhcurveto",
            ),
            (  # test_hhcurveto_mult_5_4
                "23 43 25 18 29 0 rrcurveto 56 0 42 -84 79 0 rrcurveto",
                "43 23 25 18 29 56 42 -84 79 hhcurveto",
            ),
            (  # test_hhcurveto_mult_4_4_4
                "1 0 2 3 4 0 rrcurveto 5 0 6 7 8 0 rrcurveto 9 0 10 11 12 0 rrcurveto",
                "1 2 3 4 5 6 7 8 9 10 11 12 hhcurveto",
            ),
            (  # test_hhcurveto_mult_5_4_4
                "2 1 3 4 5 0 rrcurveto 6 0 7 8 9 0 rrcurveto 10 0 11 12 13 0 rrcurveto",
                "1 2 3 4 5 6 7 8 9 10 11 12 13 hhcurveto",
            ),
            ("0 61 6 52 0 68 rrcurveto", "61 6 52 68 vvcurveto"),  # test_vvcurveto_4
            (  # test_vvcurveto_5
                "61 38 35 56 0 72 rrcurveto",
                "61 38 35 56 72 vvcurveto",
            ),
            (  # test_vvcurveto_mult_4_4
                "0 -84 -88 -30 0 -90 rrcurveto 0 -13 19 23 0 -11 rrcurveto",
                "-84 -88 -30 -90 -13 19 23 -11 vvcurveto",
            ),
            (  # test_vvcurveto_mult_5_4
                "43 12 17 32 0 65 rrcurveto 0 68 -6 52 0 61 rrcurveto",
                "43 12 17 32 65 68 -6 52 61 vvcurveto",
            ),
            (  # test_vvcurveto_mult_4_4_4
                "0 1 2 3 0 4 rrcurveto 0 5 6 7 0 8 rrcurveto 0 9 10 11 0 12 rrcurveto",
                "1 2 3 4 5 6 7 8 9 10 11 12 vvcurveto",
            ),
            (  # test_vvcurveto_mult_5_4_4
                "1 2 3 4 0 5 rrcurveto 0 6 7 8 0 9 rrcurveto 0 10 11 12 0 13 rrcurveto",
                "1 2 3 4 5 6 7 8 9 10 11 12 13 vvcurveto",
            ),
            ("1 0 2 3 0 4 rrcurveto", "1 2 3 4 hvcurveto"),  # test_hvcurveto_4
            (  # test_hvcurveto_5
                "57 0 44 22 34 40 rrcurveto",
                "57 44 22 40 34 hvcurveto",
            ),
            (  # test_hvcurveto_4_4
                "65 0 33 -19 0 -45 rrcurveto 0 -45 -29 -25 -71 0 rrcurveto",
                "65 33 -19 -45 -45 -29 -25 -71 hvcurveto",
            ),
            (  # test_hvcurveto_4_5
                "97 0 69 41 0 86 rrcurveto 0 58 -36 34 -64 11 rrcurveto",
                "97 69 41 86 58 -36 34 -64 11 hvcurveto",
            ),
            (  # test_hvcurveto_4_4_4
                "1 0 2 3 0 4 rrcurveto 0 5 6 7 8 0 rrcurveto 9 0 10 11 0 12 rrcurveto",
                "1 2 3 4 5 6 7 8 9 10 11 12 hvcurveto",
            ),
            (  # test_hvcurveto_4_4_5
                "-124 0 -79 104 0 165 rrcurveto 0 163 82 102 124 0 rrcurveto 56 0 43 -25 35 -37 rrcurveto",
                "-124 -79 104 165 163 82 102 124 56 43 -25 -37 35 hvcurveto",
            ),
            (  # test_hvcurveto_4_4_4_4
                "32 0 25 22 0 32 rrcurveto 0 31 -25 22 -32 0 rrcurveto -32 0 -25 -22 0 -31 rrcurveto 0 -32 25 -22 32 0 rrcurveto",
                "32 25 22 32 31 -25 22 -32 -32 -25 -22 -31 -32 25 -22 32 hvcurveto",
            ),
            (  # test_hvcurveto_4_4_4_4_5
                "-170 0 -128 111 0 195 rrcurveto 0 234 172 151 178 0 rrcurveto 182 0 95 -118 0 -161 rrcurveto 0 -130 -71 -77 -63 0 rrcurveto -55 0 -19 38 20 79 rrcurveto",
                "-170 -128 111 195 234 172 151 178 182 95 -118 -161 -130 -71 -77 -63 -55 -19 38 79 20 hvcurveto",
            ),
            (  # test_vhcurveto_4
                "0 -57 43 -30 53 0 rrcurveto",
                "-57 43 -30 53 vhcurveto",
            ),
            (  # test_vhcurveto_5
                "0 41 -27 19 -46 11 rrcurveto",
                "41 -27 19 -46 11 vhcurveto",
            ),
            (  # test_vhcurveto_4_4
                "0 1 2 3 4 0 rrcurveto 5 0 6 7 0 8 rrcurveto",
                "1 2 3 4 5 6 7 8 vhcurveto",
            ),
            (  # test_vhcurveto_4_5
                "0 -64 -23 -25 -45 0 rrcurveto -30 0 -24 14 -19 33 rrcurveto",
                "-64 -23 -25 -45 -30 -24 14 33 -19 vhcurveto",
            ),
            (  # test_vhcurveto_4_4_4
                "0 1 2 3 4 0 rrcurveto 5 0 6 7 0 8 rrcurveto 0 9 10 11 12 0 rrcurveto",
                "1 2 3 4 5 6 7 8 9 10 11 12 vhcurveto",
            ),
            (  # test_vhcurveto_4_4_5
                "0 108 59 81 98 0 rrcurveto 99 0 59 -81 0 -108 rrcurveto 0 -100 -46 -66 -63 -47 rrcurveto",
                "108 59 81 98 99 59 -81 -108 -100 -46 -66 -63 -47 vhcurveto",
            ),
            (  # test_vhcurveto_4_4_4_5
                "0 60 -26 37 -43 0 rrcurveto -33 0 -28 -22 0 -36 rrcurveto 0 -37 27 -20 32 0 rrcurveto 3 0 4 0 3 1 rrcurveto",
                "60 -26 37 -43 -33 -28 -22 -36 -37 27 -20 32 3 4 0 1 3 vhcurveto",
            ),
            (  # test_rrcurveto_v0_0h_h0
                "0 10 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto",
                "10 1 2 0 0 1 2 1 1 3 4 0 vhcurveto",
            ),
            (  # test_rrcurveto_h0_0h_h0
                "10 0 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto",
                "10 1 2 0 hhcurveto 0 1 2 1 1 3 4 0 hvcurveto",
            ),
            (  # test_rrcurveto_00_0h_h0
                "0 0 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto",
                "1 2 rlineto 0 1 2 1 1 3 4 0 hvcurveto",
            ),
            (  # test_rrcurveto_r0_0h_h0
                "10 10 1 2 0 0 0 0 1 2 0 1 0 1 3 4 0 0 rrcurveto",
                "10 10 1 2 0 0 1 2 1 1 3 4 0 vvcurveto",
            ),
            (  # test_rrcurveto_v0_0v_v0
                "0 10 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto",
                "10 1 2 0 vhcurveto 0 1 2 1 1 3 4 0 hhcurveto",
            ),
            (  # test_rrcurveto_h0_0v_v0
                "10 0 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto",
                "10 1 2 0 0 1 2 1 1 3 4 0 hhcurveto",
            ),
            (  # test_rrcurveto_00_0v_v0
                "0 0 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto",
                "1 2 rlineto 0 1 2 1 1 3 4 0 hhcurveto",
            ),
            (  # test_rrcurveto_r0_0v_v0
                "10 10 1 2 0 0 0 0 1 2 1 0 1 0 3 4 0 0 rrcurveto",
                "10 10 1 2 0 0 1 2 1 1 3 4 0 hhcurveto",
            ),
            (  # test_hhcurveto_peephole
                "1 2 3 4 5 6 1 2 3 4 5 0 1 2 3 4 5 6 rrcurveto",
                None,
            ),
            (  # test_vvcurveto_peephole
                "1 2 3 4 5 6 1 2 3 4 0 6 1 2 3 4 5 6 rrcurveto",
                None,
            ),
            (  # test_hvcurveto_peephole
                "1 2 3 4 5 6 1 0 3 4 5 6 1 2 3 4 5 6 rrcurveto",
                None,
            ),
            (  # test_vhcurveto_peephole
                "1 2 3 4 5 6 0 2 3 4 5 6 1 2 3 4 5 6 rrcurveto",
                None,
            ),
            (  # test_rcurveline_6_2
                "21 -76 21 -72 24 -73 rrcurveto 31 -100 rlineto",
                "21 -76 21 -72 24 -73 31 -100 rcurveline",
            ),
            (  # test_rcurveline_6_6_2
                "-73 80 -80 121 -49 96 rrcurveto 60 65 55 41 54 17 rrcurveto -8 78 rlineto",
                "-73 80 -80 121 -49 96 60 65 55 41 54 17 -8 78 rcurveline",
            ),
            (  # test_rcurveline_6_6_6_2
                "1 64 10 51 29 39 rrcurveto 15 21 15 20 15 18 rrcurveto 47 -89 63 -98 52 -59 rrcurveto 91 8 rlineto",
                "1 64 10 51 29 39 15 21 15 20 15 18 47 -89 63 -98 52 -59 91 8 rcurveline",
            ),
            (  # test_rlinecurve_2_6
                "21 -76 rlineto 21 -72 24 -73 31 -100 rrcurveto",
                "21 -76 21 -72 24 -73 31 -100 rlinecurve",
            ),
            (  # test_rlinecurve_2_2_6
                "-73 80 rlineto -80 121 rlineto -49 96 60 65 55 41 rrcurveto",
                "-73 80 -80 121 -49 96 60 65 55 41 rlinecurve",
            ),
            (  # test_rlinecurve_2_2_2_6
                "1 64 rlineto 10 51 rlineto 29 39 rlineto 15 21 15 20 15 18 rrcurveto",
                "1 64 10 51 29 39 15 21 15 20 15 18 rlinecurve",
            ),
        ],
    )
    def test_specialize(self, charstr, expected):
        if expected is None:
            expected = charstr
        expected = expected.strip()
        specialized = charstr_specialize(charstr)
        assert specialized == expected, (specialized, expected)

    # maxstack CFF=48, specializer uses up to 47
    def test_maxstack(self):
        operands = "1 2 3 4 5 6 "
        operator = "rrcurveto "
        charstr = (operands + operator) * 9
        expected = (operands * 2 + operator + operands * 7 + operator).rstrip()
        specialized = charstr_specialize(charstr)
        assert specialized == expected, (specialized, expected)

    # maxstack CFF2=513, specializer uses up to 512
    def test_maxstack_blends(self):
        numRegions = 15
        numOps = 600
        getNumRegions = lambda iv: numRegions
        blend_one = [i for i in range(1 + numRegions)] + [1, "blend"]
        operands = blend_one * 6
        operator = "rrcurveto"
        program = (operands + [operator]) * numOps
        specialized = specializeProgram(
            program,
            getNumRegions=getNumRegions,
            maxstack=maxStack,
            generalizeFirst=False,
        )
        stack_use = program_stack_use(specialized, getNumRegions=getNumRegions)
        assert maxStack - numRegions < stack_use < maxStack

    def test_maxstack_commands(self):
        # See if two commands with deep blends are merged into one
        numRegions = 400
        numOps = 2
        getNumRegions = lambda iv: numRegions
        blend_one = [i for i in range(1 + numRegions)] + [1, "blend"]
        operands = blend_one * 6
        operator = "rrcurveto"
        program = (operands + [operator]) * numOps
        specialized = specializeProgram(
            program,
            getNumRegions=getNumRegions,
            maxstack=maxStack,
            generalizeFirst=False,
        )
        assert specialized.index("rrcurveto") == len(specialized) - 1


class CFF2VFTestSpecialize(DataFilesHandler):
    def test_blend_round_trip(self):
        ttx_path = self.getpath("TestSparseCFF2VF.ttx")
        ttf_font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        ttf_font.importXML(ttx_path)
        fontGlyphList = ttf_font.getGlyphOrder()
        topDict = ttf_font["CFF2"].cff.topDictIndex[0]
        charstrings = topDict.CharStrings
        for glyphName in fontGlyphList:
            cs = charstrings[glyphName]
            cs.decompile()
            cmds = programToCommands(cs.program, getNumRegions=cs.getNumRegions)
            cmds_g = generalizeCommands(cmds)
            cmds = specializeCommands(cmds_g, generalizeFirst=False)
            program = commandsToProgram(cmds)
            assert program == cs.program, (program, cs.program)
            program = specializeProgram(program, getNumRegions=cs.getNumRegions)
            assert program == cs.program, (program, cs.program)
            program_g = generalizeProgram(program, getNumRegions=cs.getNumRegions)
            program = commandsToProgram(cmds_g)
            assert program == program_g, (program, program_g)

    def test_blend_programToCommands(self):
        ttx_path = self.getpath("TestCFF2Widths.ttx")
        ttf_font = TTFont(recalcBBoxes=False, recalcTimestamp=False)
        ttf_font.importXML(ttx_path)
        fontGlyphList = ttf_font.getGlyphOrder()
        topDict = ttf_font["CFF2"].cff.topDictIndex[0]
        charstrings = topDict.CharStrings
        for glyphName in fontGlyphList:
            cs = charstrings[glyphName]
            cs.decompile()
            cmds = programToCommands(cs.program, getNumRegions=cs.getNumRegions)
            program = commandsToProgram(cmds)
            assert program == cs.program, (program, cs.program)


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(sys.argv))
