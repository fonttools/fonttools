from fontTools.misc.testTools import FakeFont, getXML, parseXML
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.ttLib import newTable, TTFont
import unittest


MVAR_DATA = deHexStr(
    "0001 0000 "  # 0:   version=1.0
    "0000 0008 "  # 4:   reserved=0, valueRecordSize=8
    "0009 "  # 8:   valueRecordCount=9
    "0054 "  # 10:  offsetToItemVariationStore=84
    "6861 7363 "  # 12:  ValueRecord.valueTag="hasc"
    "0000 "  # 16:  ValueRecord.deltaSetOuterIndex
    "0003 "  # 18:  ValueRecord.deltaSetInnerIndex
    "6863 6C61 "  # 20:  ValueRecord.valueTag="hcla"
    "0000 "  # 24:  ValueRecord.deltaSetOuterIndex
    "0003 "  # 26:  ValueRecord.deltaSetInnerIndex
    "6863 6C64 "  # 28:  ValueRecord.valueTag="hcld"
    "0000 "  # 32:  ValueRecord.deltaSetOuterIndex
    "0003 "  # 34:  ValueRecord.deltaSetInnerIndex
    "6864 7363 "  # 36:  ValueRecord.valueTag="hdsc"
    "0000 "  # 40:  ValueRecord.deltaSetOuterIndex
    "0000 "  # 42:  ValueRecord.deltaSetInnerIndex
    "686C 6770 "  # 44:  ValueRecord.valueTag="hlgp"
    "0000 "  # 48:  ValueRecord.deltaSetOuterIndex
    "0002 "  # 50:  ValueRecord.deltaSetInnerIndex
    "7362 796F "  # 52:  ValueRecord.valueTag="sbyo"
    "0000 "  # 56:  ValueRecord.deltaSetOuterIndex
    "0001 "  # 58:  ValueRecord.deltaSetInnerIndex
    "7370 796F "  # 60:  ValueRecord.valueTag="spyo"
    "0000 "  # 64:  ValueRecord.deltaSetOuterIndex
    "0002 "  # 66:  ValueRecord.deltaSetInnerIndex
    "7465 7374 "  # 68:  ValueRecord.valueTag="test"
    "0000 "  # 72:  ValueRecord.deltaSetOuterIndex
    "0002 "  # 74:  ValueRecord.deltaSetInnerIndex
    "7465 7332 "  # 76:  ValueRecord.valueTag="tes2"
    "0000 "  # 78:  ValueRecord.deltaSetOuterIndex
    "0002 "  # 82:  ValueRecord.deltaSetInnerIndex
    "0001 "  # 84:  VarStore.format=1
    "0000 000C "  # 86:  VarStore.offsetToVariationRegionList=12
    "0001 "  # 90:  VarStore.itemVariationDataCount=1
    "0000 0016 "  # 92:  VarStore.itemVariationDataOffsets[0]=22
    "0001 "  # 96:  VarRegionList.axisCount=1
    "0001 "  # 98:  VarRegionList.regionCount=1
    "0000 "  # 100:  variationRegions[0].regionAxes[0].startCoord=0.0
    "4000 "  # 102:  variationRegions[0].regionAxes[0].peakCoord=1.0
    "4000 "  # 104:  variationRegions[0].regionAxes[0].endCoord=1.0
    "0004 "  # 106:  VarData.ItemCount=4
    "0001 "  # 108:  VarData.NumShorts=1
    "0001 "  # 110:  VarData.VarRegionCount=1
    "0000 "  # 112:  VarData.VarRegionIndex[0]=0
    "FF38 "  # 114:  VarData.deltaSets[0]=-200
    "FFCE "  # 116: VarData.deltaSets[0]=-50
    "0064 "  # 118: VarData.deltaSets[0]=100
    "00C8 "  # 120: VarData.deltaSets[0]=200
)

MVAR_XML = [
    '<Version value="0x00010000"/>',
    '<Reserved value="0"/>',
    '<ValueRecordSize value="8"/>',
    "<!-- ValueRecordCount=9 -->",
    '<VarStore Format="1">',
    '  <Format value="1"/>',
    "  <VarRegionList>",
    "    <!-- RegionAxisCount=1 -->",
    "    <!-- RegionCount=1 -->",
    '    <Region index="0">',
    '      <VarRegionAxis index="0">',
    '        <StartCoord value="0.0"/>',
    '        <PeakCoord value="1.0"/>',
    '        <EndCoord value="1.0"/>',
    "      </VarRegionAxis>",
    "    </Region>",
    "  </VarRegionList>",
    "  <!-- VarDataCount=1 -->",
    '  <VarData index="0">',
    "    <!-- ItemCount=4 -->",
    '    <NumShorts value="1"/>',
    "    <!-- VarRegionCount=1 -->",
    '    <VarRegionIndex index="0" value="0"/>',
    '    <Item index="0" value="[-200]"/>',
    '    <Item index="1" value="[-50]"/>',
    '    <Item index="2" value="[100]"/>',
    '    <Item index="3" value="[200]"/>',
    "  </VarData>",
    "</VarStore>",
    '<ValueRecord index="0">',
    '  <ValueTag value="hasc"/>',
    '  <VarIdx value="3"/>',
    "</ValueRecord>",
    '<ValueRecord index="1">',
    '  <ValueTag value="hcla"/>',
    '  <VarIdx value="3"/>',
    "</ValueRecord>",
    '<ValueRecord index="2">',
    '  <ValueTag value="hcld"/>',
    '  <VarIdx value="3"/>',
    "</ValueRecord>",
    '<ValueRecord index="3">',
    '  <ValueTag value="hdsc"/>',
    '  <VarIdx value="0"/>',
    "</ValueRecord>",
    '<ValueRecord index="4">',
    '  <ValueTag value="hlgp"/>',
    '  <VarIdx value="2"/>',
    "</ValueRecord>",
    '<ValueRecord index="5">',
    '  <ValueTag value="sbyo"/>',
    '  <VarIdx value="1"/>',
    "</ValueRecord>",
    '<ValueRecord index="6">',
    '  <ValueTag value="spyo"/>',
    '  <VarIdx value="2"/>',
    "</ValueRecord>",
    '<ValueRecord index="7">',
    '  <ValueTag value="test"/>',
    '  <VarIdx value="2"/>',
    "</ValueRecord>",
    '<ValueRecord index="8">',
    '  <ValueTag value="tes2"/>',
    '  <VarIdx value="2"/>',
    "</ValueRecord>",
]


class MVARTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

    def test_decompile_toXML(self):
        mvar = newTable("MVAR")
        font = TTFont()
        mvar.decompile(MVAR_DATA, font)
        self.assertEqual(getXML(mvar.toXML), MVAR_XML)

    def test_decompile_toXML_lazy(self):
        mvar = newTable("MVAR")
        font = TTFont(lazy=True)
        mvar.decompile(MVAR_DATA, font)
        self.assertEqual(getXML(mvar.toXML), MVAR_XML)

    def test_compile_fromXML(self):
        mvar = newTable("MVAR")
        font = TTFont()
        for name, attrs, content in parseXML(MVAR_XML):
            mvar.fromXML(name, attrs, content, font=font)
        data = MVAR_DATA
        self.assertEqual(hexStr(mvar.compile(font)), hexStr(data))


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
