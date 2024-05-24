from fontTools.ttLib.tables.otConverters import UShort
from fontTools.colorLib.table_builder import TableBuilder


class WriteMe:
    value = None


def test_intValue_otRound():
    dest = WriteMe()
    converter = UShort("value", None, None)
    TableBuilder()._convert(dest, "value", converter, 85.6)
    assert dest.value == 86, "Should have used otRound"
