import os

from fontTools.misc.testTools import getXML
from fontTools.ttLib import TTFont, newTable

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "graphite")


def test_compile_decompiled_table():
    font = TTFont(os.path.join(DATA_DIR, "graphite_tests.ttf"))
    table = font["Silf"]
    expected = getXML(table.toXML, font)

    table2 = newTable("Silf")
    table2.decompile(table.compile(font), font)

    assert getXML(table.toXML, font) == expected
    assert getXML(table2.toXML, font) == expected


def test_compile_decompiled_empty_action():
    font = TTFont(os.path.join(DATA_DIR, "graphite_tests.ttf"))
    table = font["Silf"]
    table.silfs[0].passes[0].actions[1] = b""
    data = table.compile(font)

    table2 = newTable("Silf")
    table2.decompile(data, font)

    assert table2.compile(font) == data
