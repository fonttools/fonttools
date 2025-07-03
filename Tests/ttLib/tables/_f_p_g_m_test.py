from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._f_p_g_m import table__f_p_g_m


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


def test_compile_without_program():
    # When read from XML, in an empty fpgm table, the program attribute is missing.
    # Make sure that the table can be compiled to a zero-length table.
    fpgm = table__f_p_g_m()
    assert fpgm.compile(None) == b""


def test_decompile_without_program():
    # VTT adds a zero-length table to a font if the program is empty.
    # Make sure it can be decompiled.
    fpgm = table__f_p_g_m()
    fpgm.decompile(b"", None)
