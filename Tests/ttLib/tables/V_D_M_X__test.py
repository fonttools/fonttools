from fontTools.misc.testTools import getXML, parseXML
from fontTools.misc.textTools import deHexStr
from fontTools.ttLib import newTable

VDMX_DATA = deHexStr(
    "0001 0001 0001 "  # version=1, numRecs=1, numRatios=1
    "01 00 00 00 "  # ratRange: bCharSet=1, xRatio=0, yStartRatio=0, yEndRatio=0
    "000C "  # offset to group 0
    "0002 08 09 "  # group 0: recs=2, startsz=8, endsz=9
    "0008 0007 FFFE "  # yPelHeight=8, yMax=7, yMin=-2
    "0009 0008 FFFE"  # yPelHeight=9, yMax=8, yMin=-2
)

VDMX_DATA_EMPTY = deHexStr("0001 0000 0000")


def _xmlRoundTrip(table, font):
    result = newTable("VDMX")
    for name, attrs, content in parseXML(getXML(table.toXML, font)):
        result.fromXML(name, attrs, content, font)
    return result


def test_decompile_compile():
    table = newTable("VDMX")
    table.decompile(VDMX_DATA, None)
    assert table.ratRanges == [
        {
            "bCharSet": 1,
            "xRatio": 0,
            "yStartRatio": 0,
            "yEndRatio": 0,
            "groupIndex": 0,
        }
    ]
    assert table.groups == [{8: (7, -2), 9: (8, -2)}]
    assert table.compile(None) == VDMX_DATA


def test_compile_updates_counts():
    table = newTable("VDMX")
    table.decompile(VDMX_DATA, None)
    table.ratRanges.append(
        {
            "bCharSet": 0,
            "xRatio": 1,
            "yStartRatio": 1,
            "yEndRatio": 1,
            "groupIndex": 1,
        }
    )
    table.groups.append({10: (9, -3)})

    data = table.compile(None)

    table2 = newTable("VDMX")
    table2.decompile(data, None)
    assert table2.numRatios == 2
    assert table2.numRecs == 2
    assert table2.ratRanges == table.ratRanges
    assert table2.groups == table.groups


def test_compile_empty():
    table = newTable("VDMX")
    table.decompile(VDMX_DATA, None)
    table.ratRanges = []
    table.groups = []
    assert table.compile(None) == VDMX_DATA_EMPTY


def test_xml_round_trip():
    table = newTable("VDMX")
    table.decompile(VDMX_DATA, None)
    assert _xmlRoundTrip(table, None).compile(None) == VDMX_DATA


def test_xml_round_trip_empty():
    table = newTable("VDMX")
    table.decompile(VDMX_DATA_EMPTY, None)
    assert getXML(table.toXML, None) == [
        '<version value="1"/>',
        "<ratRanges>",
        "</ratRanges>",
        "<groups>",
        "</groups>",
    ]
    assert _xmlRoundTrip(table, None).compile(None) == VDMX_DATA_EMPTY
