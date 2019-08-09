from fontTools.misc.py23 import *
from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr
from fontTools.ttLib import newTable
import unittest


STAT_DATA = deHexStr(
    '0001 0000 '           #   0: Version=1.0
    '0008 0002 '           #   4: DesignAxisSize=8, DesignAxisCount=2
    '0000 0012 '           #   8: OffsetToDesignAxes=18
    '0003 0000 0022 '      #  12: AxisValueCount=3, OffsetToAxisValueOffsets=34
    '7767 6874 '           #  18: DesignAxis[0].AxisTag='wght'
    '012D 0002 '           #  22: DesignAxis[0].NameID=301, .AxisOrdering=2
    '5445 5354 '           #  26: DesignAxis[1].AxisTag='TEST'
    '012E 0001 '           #  30: DesignAxis[1].NameID=302, .AxisOrdering=1
    '0006 0012 0026 '      #  34: AxisValueOffsets = [6, 18, 38] (+34)
    '0001 0000 0000  '     #  40: AxisValue[0].Format=1, .AxisIndex=0, .Flags=0
    '0191 0190 0000 '      #  46: AxisValue[0].ValueNameID=401, .Value=400.0
    '0002 0001 0000 '      #  52: AxisValue[1].Format=2, .AxisIndex=1, .Flags=0
    '0192 '                #  58: AxisValue[1].ValueNameID=402
    '0002 0000 '           #  60: AxisValue[1].NominalValue=2.0
    '0001 0000 '           #  64: AxisValue[1].RangeMinValue=1.0
    '0003 0000 '           #  68: AxisValue[1].RangeMaxValue=3.0
    '0003 0000 0000 '      #  72: AxisValue[2].Format=3, .AxisIndex=0, .Flags=0
    '0002 '                #  78: AxisValue[2].ValueNameID=2 'Regular'
    '0190 0000 02BC 0000 ' #  80: AxisValue[2].Value=400.0, .LinkedValue=700.0
)                          #  88: <end>
assert(len(STAT_DATA) == 88)


STAT_XML = [
    '<Version value="0x00010000"/>',
    '<DesignAxisRecordSize value="8"/>',
    '<!-- DesignAxisCount=2 -->',
    '<DesignAxisRecord>',
    '  <Axis index="0">',
    '    <AxisTag value="wght"/>',
    '    <AxisNameID value="301"/>',
    '    <AxisOrdering value="2"/>',
    '  </Axis>',
    '  <Axis index="1">',
    '    <AxisTag value="TEST"/>',
    '    <AxisNameID value="302"/>',
    '    <AxisOrdering value="1"/>',
    '  </Axis>',
    '</DesignAxisRecord>',
    '<!-- AxisValueCount=3 -->',
    '<AxisValueArray>',
    '  <AxisValue index="0" Format="1">',
    '    <AxisIndex value="0"/>',
    '    <Flags value="0"/>',
    '    <ValueNameID value="401"/>',
    '    <Value value="400.0"/>',
    '  </AxisValue>',
    '  <AxisValue index="1" Format="2">',
    '    <AxisIndex value="1"/>',
    '    <Flags value="0"/>',
    '    <ValueNameID value="402"/>',
    '    <NominalValue value="2.0"/>',
    '    <RangeMinValue value="1.0"/>',
    '    <RangeMaxValue value="3.0"/>',
    '  </AxisValue>',
    '  <AxisValue index="2" Format="3">',
    '    <AxisIndex value="0"/>',
    '    <Flags value="0"/>',
    '    <ValueNameID value="2"/>',
    '    <Value value="400.0"/>',
    '    <LinkedValue value="700.0"/>',
    '  </AxisValue>',
    '</AxisValueArray>',
]


# Contains junk data for making sure we get our offset decoding right.
STAT_DATA_WITH_AXIS_JUNK = deHexStr(
    '0001 0000 '           #   0: Version=1.0
    '000A 0002 '           #   4: DesignAxisSize=10, DesignAxisCount=2
    '0000 0012 '           #   8: OffsetToDesignAxes=18
    '0000 0000 0000 '      #  12: AxisValueCount=3, OffsetToAxisValueOffsets=34
    '7767 6874 '           #  18: DesignAxis[0].AxisTag='wght'
    '012D 0002 '           #  22: DesignAxis[0].NameID=301, .AxisOrdering=2
    'DEAD '                #  26: <junk>
    '5445 5354 '           #  28: DesignAxis[1].AxisTag='TEST'
    '012E 0001 '           #  32: DesignAxis[1].NameID=302, .AxisOrdering=1
    'BEEF '                #  36: <junk>
)                          #  38: <end>

assert(len(STAT_DATA_WITH_AXIS_JUNK) == 38)


STAT_XML_WITH_AXIS_JUNK = [
    '<Version value="0x00010000"/>',
    '<DesignAxisRecordSize value="10"/>',
    '<!-- DesignAxisCount=2 -->',
    '<DesignAxisRecord>',
    '  <Axis index="0">',
    '    <AxisTag value="wght"/>',
    '    <AxisNameID value="301"/>',
    '    <AxisOrdering value="2"/>',
    '    <MoreBytes index="0" value="222"/>',  # 0xDE
    '    <MoreBytes index="1" value="173"/>',  # 0xAD
    '  </Axis>',
    '  <Axis index="1">',
    '    <AxisTag value="TEST"/>',
    '    <AxisNameID value="302"/>',
    '    <AxisOrdering value="1"/>',
    '    <MoreBytes index="0" value="190"/>',  # 0xBE
    '    <MoreBytes index="1" value="239"/>',  # 0xEF
    '  </Axis>',
    '</DesignAxisRecord>',
    '<!-- AxisValueCount=0 -->',
]


STAT_DATA_AXIS_VALUE_FORMAT3 = deHexStr(
    '0001 0000 '  #  0: Version=1.0
    '0008 0001 '  #  4: DesignAxisSize=8, DesignAxisCount=1
    '0000 0012 '  #  8: OffsetToDesignAxes=18
    '0001 '       # 12: AxisValueCount=1
    '0000 001A '  # 14: OffsetToAxisValueOffsets=26
    '7767 6874 '  # 18: DesignAxis[0].AxisTag='wght'
    '0102  '      # 22: DesignAxis[0].AxisNameID=258 'Weight'
    '0000 '       # 24: DesignAxis[0].AxisOrdering=0
    '0002 '       # 26: AxisValueOffsets=[2] (+26)
    '0003 '       # 28: AxisValue[0].Format=3
    '0000 0002 '  # 30: AxisValue[0].AxisIndex=0, .Flags=0x2
    '0002 '       # 34: AxisValue[0].ValueNameID=2 'Regular'
    '0190 0000 '  # 36: AxisValue[0].Value=400.0
    '02BC 0000 '  # 40: AxisValue[0].LinkedValue=700.0
)                 # 44: <end>
assert(len(STAT_DATA_AXIS_VALUE_FORMAT3) == 44)


STAT_XML_AXIS_VALUE_FORMAT3 = [
    '<Version value="0x00010000"/>',
    '<DesignAxisRecordSize value="8"/>',
    '<!-- DesignAxisCount=1 -->',
    '<DesignAxisRecord>',
    '  <Axis index="0">',
    '    <AxisTag value="wght"/>',
    '    <AxisNameID value="258"/>',
    '    <AxisOrdering value="0"/>',
    '  </Axis>',
    '</DesignAxisRecord>',
    '<!-- AxisValueCount=1 -->',
    '<AxisValueArray>',
    '  <AxisValue index="0" Format="3">',
    '    <AxisIndex value="0"/>',
    '    <Flags value="2"/>',
    '    <ValueNameID value="2"/>',
    '    <Value value="400.0"/>',
    '    <LinkedValue value="700.0"/>',
    '  </AxisValue>',
    '</AxisValueArray>',
]


STAT_DATA_VERSION_1_1 = deHexStr(
    '0001 0001 '  #  0: Version=1.1
    '0008 0001 '  #  4: DesignAxisSize=8, DesignAxisCount=1
    '0000 0014 '  #  8: OffsetToDesignAxes=20
    '0001 '       # 12: AxisValueCount=1
    '0000 001C '  # 14: OffsetToAxisValueOffsets=28
    '0101 '       # 18: ElidedFallbackNameID: 257
    '7767 6874 '  # 20: DesignAxis[0].AxisTag='wght'
    '0102  '      # 24: DesignAxis[0].AxisNameID=258 'Weight'
    '0000 '       # 26: DesignAxis[0].AxisOrdering=0
    '0002 '       # 28: AxisValueOffsets=[2] (+28)
    '0003 '       # 30: AxisValue[0].Format=3
    '0000 0002 '  # 32: AxisValue[0].AxisIndex=0, .Flags=0x2
    '0002 '       # 36: AxisValue[0].ValueNameID=2 'Regular'
    '0190 0000 '  # 38: AxisValue[0].Value=400.0
    '02BC 0000 '  # 42: AxisValue[0].LinkedValue=700.0
)                 # 46: <end>
assert(len(STAT_DATA_VERSION_1_1) == 46)


STAT_XML_VERSION_1_1 = [
    '<Version value="0x00010001"/>',
    '<DesignAxisRecordSize value="8"/>',
    '<!-- DesignAxisCount=1 -->',
    '<DesignAxisRecord>',
    '  <Axis index="0">',
    '    <AxisTag value="wght"/>',
    '    <AxisNameID value="258"/>',
    '    <AxisOrdering value="0"/>',
    '  </Axis>',
    '</DesignAxisRecord>',
    '<!-- AxisValueCount=1 -->',
    '<AxisValueArray>',
    '  <AxisValue index="0" Format="3">',
    '    <AxisIndex value="0"/>',
    '    <Flags value="2"/>',
    '    <ValueNameID value="2"/>',
    '    <Value value="400.0"/>',
    '    <LinkedValue value="700.0"/>',
    '  </AxisValue>',
    '</AxisValueArray>',
    '<ElidedFallbackNameID value="257"/>',
]


class STATTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

    def test_decompile_toXML(self):
        table = newTable('STAT')
        table.decompile(STAT_DATA, font=FakeFont(['.notdef']))
        self.assertEqual(getXML(table.toXML), STAT_XML)

    def test_decompile_toXML_withAxisJunk(self):
        table = newTable('STAT')
        table.decompile(STAT_DATA_WITH_AXIS_JUNK, font=FakeFont(['.notdef']))
        self.assertEqual(getXML(table.toXML), STAT_XML_WITH_AXIS_JUNK)

    def test_decompile_toXML_format3(self):
        table = newTable('STAT')
        table.decompile(STAT_DATA_AXIS_VALUE_FORMAT3,
                        font=FakeFont(['.notdef']))
        self.assertEqual(getXML(table.toXML), STAT_XML_AXIS_VALUE_FORMAT3)

    def test_decompile_toXML_version_1_1(self):
        table = newTable('STAT')
        table.decompile(STAT_DATA_VERSION_1_1,
                        font=FakeFont(['.notdef']))
        self.assertEqual(getXML(table.toXML), STAT_XML_VERSION_1_1)

    def test_compile_fromXML(self):
        table = newTable('STAT')
        font = FakeFont(['.notdef'])
        for name, attrs, content in parseXML(STAT_XML):
            table.fromXML(name, attrs, content, font=font)
        self.assertEqual(table.compile(font), STAT_DATA)

    def test_compile_fromXML_withAxisJunk(self):
        table = newTable('STAT')
        font = FakeFont(['.notdef'])
        for name, attrs, content in parseXML(STAT_XML_WITH_AXIS_JUNK):
            table.fromXML(name, attrs, content, font=font)
        self.assertEqual(table.compile(font), STAT_DATA_WITH_AXIS_JUNK)

    def test_compile_fromXML_format3(self):
        table = newTable('STAT')
        font = FakeFont(['.notdef'])
        for name, attrs, content in parseXML(STAT_XML_AXIS_VALUE_FORMAT3):
            table.fromXML(name, attrs, content, font=font)
        self.assertEqual(table.compile(font), STAT_DATA_AXIS_VALUE_FORMAT3)

    def test_compile_fromXML_version_1_1(self):
        table = newTable('STAT')
        font = FakeFont(['.notdef'])
        for name, attrs, content in parseXML(STAT_XML_VERSION_1_1):
            table.fromXML(name, attrs, content, font=font)
        self.assertEqual(table.compile(font), STAT_DATA_VERSION_1_1)


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
