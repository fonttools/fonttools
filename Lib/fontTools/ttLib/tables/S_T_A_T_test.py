from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr
from fontTools.ttLib import getTableModule, newTable
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
    '0006 001C 0034 '      #  34: AxisValueOffsets = [6, TODO, TODO] (+34)
    '0001 0000 0000  '     #  40: AxisValue[0].Format=1, .AxisIndex=0, .Flags=0
    '0191 0190 0000 '      #  46: AxisValue[0].ValueNameID=401, .Value=400.0
    '0002 0001 0000 '      #  52: AxisValue[1].Format=2, .AxisIndex=1, .Flags=0
    '0192 '                #  58: AxisValue[1].ValueNameID=402
    '0002 0000 '           #  60: AxisValue[1].NominalValue=2.0
    '0001 0000 '           #  64: AxisValue[1].RangeMinValue=1.0
    '0003 0000 '           #  68: AxisValue[1].RangeMaxValue=3.0
    '0003 0000 0000 '      #  72: AxisValue[2].Format=3, .AxisIndex=0, .Flags=0
    '0190 0000 02BC 0000 ' #  78: AxisValue[2].Value=400.0, .LinkedValue=700.0
)                          #  86: <end>
assert(len(STAT_DATA) == 86)


# Contains junk data for making sure we get our offset decoding right.
# This is an entirely valid STAT table, just more verbose than the minimum.
STAT_DATA_WITH_JUNK = deHexStr(
    '0001 0000 '           #   0: Version=1.0
    '000C 0002 '           #   4: DesignAxisSize=12, DesignAxisCount=2
    '0000 0016 '           #   8: OffsetToDesignAxes=22
    '0003 0000 002E '      #  12: AxisValueCount=3, OffsetToAxisValueOffsets=46
    'DEAD BEEF '           #  18: <junk>
    '7767 6874 '           #  22: DesignAxis[0].AxisTag='wght'
    '012D 0002 '           #  26: DesignAxis[0].NameID=301, .AxisOrdering=2
    'DEAD BEEF '           #  30: <junk>
    '5445 5354 '           #  34: DesignAxis[1].AxisTag='TEST'
    '012E 0001 '           #  38: DesignAxis[1].NameID=302, .AxisOrdering=1
    'DEAD BEEF '           #  42: <junk>
    '000C 001C 0034 '      #  46: AxisValueOffsets = [12, 28, 52] (+46)
    'DEAD BEEF DEAD '      #  52: <junk>
    '0001 0000 0000 '      #  58: AxisValue[0].Format=1, .AxisIndex=0, .Flags=0
    '0191 0190 0000 '      #  64: AxisValue[0].ValueNameID=401, .Value=400.0
    'DEAD BEEF '           #  70: <junk>
    '0002 0001 0000 '      #  74: AxisValue[1].Format=2, .AxisIndex=1, .Flags=0
    '0192 '                #  80: AxisValue[1].ValueNameID=402
    '0002 0000 '           #  82: AxisValue[1].NominalValue=2.0
    '0001 0000 '           #  86: AxisValue[1].RangeMinValue=1.0
    '0003 0000 '           #  86: AxisValue[1].RangeMaxValue=3.0
    'DEAD BEEF '           #  94: <junk>
    '0003 0000 0000 '      #  98: AxisValue[2].Format=3, .AxisIndex=0, .Flags=0
    '0190 0000 02BC 0000 ' # 104: AxisValue[2].Value=400.0, .LinkedValue=700.0
)                          # 112: <end>
assert(len(STAT_DATA_WITH_JUNK) == 112)


STAT_XML = (
    '<Version value="0x00010000"/>'
    '<!-- DesignAxisRecordSize=12 -->'
    '<!-- DesignAxisCount=2 -->'
    '<DesignAxis index="0">'
    '  <AxisTag value="wght"/>'
    '  <AxisNameID value="301"/>'
    '  <AxisOrdering value="2"/>'
    '</DesignAxis>'
    '<DesignAxis index="1">'
    '  <AxisTag value="TEST"/>'
    '  <AxisNameID value="302"/>'
    '  <AxisOrdering value="1"/>'
    '</DesignAxis>'
    '<!-- AxisValueCount=3 -->'
    '<AxisValue index="0">'
    '  <Format value="1"/">'
    '  <AxisIndex value="0"/">'
    '  <Flags value="0x0"/">'
    '  <ValueNameID value="401"/">'
    '  <Value value="400.0"/">'
    '</AxisValue>'
    '<AxisValue index="1">'
    '  <Format value="2"/">'
    '  <AxisIndex value="1"/">'
    '  <Flags value="0x0"/">'
    '  <ValueNameID value="402"/">'
    '  <NominalValue value="2.0"/">'
    '  <RangeMinValue value="1.0"/">'
    '  <RangeMaxValue value="3.0"/">'
    '</AxisValue>'
    '<AxisValue index="2">'
    '  <Format value="3"/">'
    '  <AxisIndex value="0"/">'
    '  <Flags value="0x0"/">'
    '  <Value value="400.0"/">'
    '  <LinkedValue value="700.0"/">'
    '</AxisValue>'
)


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


STAT_XML_AXIS_VALUE_FORMAT3 = (
    '<Version value="0x00010000"/>'
    '<!-- DesignAxisRecordSize=8 -->'
    '<!-- DesignAxisCount=1 -->'
    '<DesignAxis index="0">'
    '  <AxisTag value="wght"/>'
    '  <AxisNameID value="258"/>'
    '  <AxisOrdering value="0"/>'
    '</DesignAxis>'
    '<!-- AxisValueCount=1 -->'
    '<AxisValue index="0">'
    '  <Format value="3"/">'
    '  <AxisIndex value="0"/">'
    '  <Flags value="0x2"/">'
    '  <Value value="400.0"/">'
    '  <LinkedValue value="700.0"/">'
    '</AxisValue>'
)


class STATTest(unittest.TestCase):
    def test_decompile_toXML(self):
        table = newTable('STAT')
        table.decompile(STAT_DATA, font=FakeFont(['.notdef']))
        self.maxDiff = None
        self.assertEqual(getXML(table.toXML), STAT_XML)

    def test_decompile_toXML_withJunk(self):
        table = newTable('STAT')
        table.decompile(STAT_DATA_WITH_JUNK, font=FakeFont(['.notdef']))
        expected_xml = STAT_XML.replace('DesignAxisRecordSize=8',
                                        'DesignAxisRecordSize=12')
        self.assertEqual(getXML(table.toXML), expected_xml)

    def test_decompile_toXML_format3(self):
        table = newTable('STAT')
        table.decompile(STAT_DATA_AXIS_VALUE_FORMAT3,
                        font=FakeFont(['.notdef']))
        self.assertEqual(getXML(table.toXML), STAT_XML_AXIS_VALUE_FORMAT3)


if __name__ == '__main__':
    unittest.main()
