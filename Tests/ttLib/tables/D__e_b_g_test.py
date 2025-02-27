from fontTools.misc.testTools import parseXmlInto, getXML
from fontTools.ttLib.tables.D__e_b_g import table_D__e_b_g


DEBG_DATA = {
    "com.github.fonttools.feaLib": {
        "GPOS": {"0": ["<features>:6:5", "kern_Default", ["DFLT", "dflt", "kern"]]}
    }
}


DEBG_XML = """\
<json>
  <![CDATA[{
    "com.github.fonttools.feaLib": {
      "GPOS": {
        "0": [
          "<features>:6:5",
          "kern_Default",
          [
            "DFLT",
            "dflt",
            "kern"
          ]
        ]
      }
    }
  }]]>
</json>
"""


def test_compile_decompile_and_roundtrip_ttx():
    ttFont = None
    table = table_D__e_b_g()
    assert table.tableTag == "Debg"
    assert table.data == {}
    table.data = DEBG_DATA

    data = table.compile(ttFont)

    table2 = table_D__e_b_g()
    table2.decompile(data, ttFont)

    assert table.data == table2.data

    assert getXML(table2.toXML) == DEBG_XML.splitlines()

    table3 = table_D__e_b_g()
    parseXmlInto(ttFont, table3, DEBG_XML)

    assert table3.data == DEBG_DATA
