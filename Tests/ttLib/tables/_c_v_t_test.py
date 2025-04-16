from fontTools.ttLib.tables._c_v_t import table__c_v_t


def test_compile_without_values():
    # When read from XML, in an empty cvt table, the values attribute is missing.
    # Make sure that the table can be compiled to a zero-length table.
    cvt = table__c_v_t()
    assert cvt.compile(None) == b""


def test_decompile_without_values():
    # VTT adds a zero-length table to a font if the Control Values are empty.
    # Make sure it can be decompiled.
    cvt = table__c_v_t()
    cvt.decompile(b"", None)
