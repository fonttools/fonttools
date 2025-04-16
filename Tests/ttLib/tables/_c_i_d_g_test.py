from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import newTable
import unittest


# On macOS X 10.12.6, the first font in /System/Library/Fonts/PingFang.ttc
# has a ‘cidg’ table with a similar structure as this test data, just larger.
CIDG_DATA = deHexStr(
    "0000 0000 "  #   0: Format=0, Flags=0
    "0000 0098 "  #   4: StructLength=152
    "0000 "  #   8: Registry=0
    "41 64 6F 62 65 "  #  10: RegistryName="Adobe"
    + ("00" * 59)
    + "0002 "  #  15: <padding>  #  74: Order=2
    "43 4E 53 31 "  #  76: Order="CNS1"
    + ("00" * 60)
    + "0000 "  #  80: <padding>  # 140: SupplementVersion=0
    "0004 "  # 142: Count
    "0000 "  # 144: GlyphID[0]=.notdef
    "FFFF "  # 146: CIDs[1]=<None>
    "0003 "  # 148: CIDs[2]=C
    "0001 "  # 150: CIDs[3]=A
)  # 152: <end>
assert len(CIDG_DATA) == 152, len(CIDG_DATA)


CIDG_XML = [
    '<CIDGlyphMapping Format="0">',
    '  <DataFormat value="0"/>',
    "  <!-- StructLength=152 -->",
    '  <Registry value="0"/>',
    '  <RegistryName value="Adobe"/>',
    '  <Order value="2"/>',
    '  <OrderName value="CNS1"/>',
    '  <SupplementVersion value="0"/>',
    "  <Mapping>",
    '    <CID cid="0" glyph=".notdef"/>',
    '    <CID cid="2" glyph="C"/>',
    '    <CID cid="3" glyph="A"/>',
    "  </Mapping>",
    "</CIDGlyphMapping>",
]


class GCIDTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.font = FakeFont([".notdef", "A", "B", "C", "D"])

    def testDecompileToXML(self):
        table = newTable("cidg")
        table.decompile(CIDG_DATA, self.font)
        self.assertEqual(getXML(table.toXML, self.font), CIDG_XML)

    def testCompileFromXML(self):
        table = newTable("cidg")
        for name, attrs, content in parseXML(CIDG_XML):
            table.fromXML(name, attrs, content, font=self.font)
        self.assertEqual(hexStr(table.compile(self.font)), hexStr(CIDG_DATA))


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
