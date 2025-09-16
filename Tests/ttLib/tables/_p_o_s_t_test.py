import unittest

from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import newTable

POST_FORMAT_2_0_DATA = deHexStr(
    "0002 0000 "  # Version=2.0
    "0000 0000 "  # Italic Angle = 0.0
    "FF88 0028 "  # Underline position, -thickness
    "0000 0000 "  # isFixedPitch
    "0000 0000 "  # minMemType42
    "0000 0000 "  # maxMemType42
    "0000 0000 "  # minMemType1
    "0000 0000 "  # maxMemType1
    # Version 2.0 fields
    "0005 "  # numGlyphs
    "0000 0102 0103 0104 0105"  # glyphNameIndex[numGlyphs]
    "025859"  # XY
    "025859"  # XY
    "025859"  # XY
    "0458592E32"  # XY.2
)


POST_FORMAT_2_0_XML = [
    '<formatType value="2.0"/>',
    '<italicAngle value="0.0"/>',
    '<underlinePosition value="-120"/>',
    '<underlineThickness value="40"/>',
    '<isFixedPitch value="0"/>',
    '<minMemType42 value="0"/>',
    '<maxMemType42 value="0"/>',
    '<minMemType1 value="0"/>',
    '<maxMemType1 value="0"/>',
    "<psNames>",
    "  <!-- This file uses unique glyph names based on the information",
    "       found in the 'post' table. Since these names might not be unique,",
    "       we have to invent artificial names in case of clashes. In order to",
    "       be able to retain the original information, we need a name to",
    "       ps name mapping for those cases where they differ. That's what",
    "       you see below.",
    "        -->",
    '  <psName name="XY.1" psName="XY"/>',
    '  <psName name="XY.3" psName="XY"/>',
    "</psNames>",
    "<extraNames>",
    "  <!-- following are the name that are not taken from the standard Mac glyph order -->",
    '  <psName name="XY"/>',
    '  <psName name="XY"/>',
    '  <psName name="XY"/>',
    '  <psName name="XY.2"/>',
    "</extraNames>",
]


class FakeMaxp:
    def __init__(self, n: int) -> None:
        self.numGlyphs = n


class postTest(unittest.TestCase):
    def test_no_names(self):
        self.maxDiff = None
        font = FakeFont([".notdef", "XY", "XY", "XY", "XY.2"])
        font["maxp"] = FakeMaxp(5)
        table = newTable("post")
        table.decompile(POST_FORMAT_2_0_DATA, font)
        self.assertEqual(getXML(table.toXML), POST_FORMAT_2_0_XML)


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
