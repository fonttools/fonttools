from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.ttLib.tables._f_p_g_m import table__f_p_g_m
from fontTools.ttLib.tables import ttProgram


def test__bool__():
    fpgm = table__f_p_g_m()
    assert not bool(fpgm)

    p = ttProgram.Program()
    fpgm.program = p
    assert not bool(fpgm)

    bc = bytearray([0])
    p.fromBytecode(bc)
    assert bool(fpgm)

    p.bytecode.pop()
    assert not bool(fpgm)
