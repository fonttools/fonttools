from fontTools.misc.py23 import *
from fontTools.misc.testTools import getXML, parseXML
from fontTools.misc.textTools import deHexStr
from fontTools.ttLib import getTableModule, newTable
import unittest


CPAL_DATA_V0 = deHexStr(
    '0000 0002 '          # version=0, numPaletteEntries=2
    '0002 0004 '          # numPalettes=2, numColorRecords=4
    '00000010 '           # offsetToFirstColorRecord=16
    '0000 0002 '          # colorRecordIndex=[0, 2]
    '000000FF FFCC66FF '  # colorRecord #0, #1 (blue/green/red/alpha)
    '000000FF 000080FF')  # colorRecord #2, #3


CPAL_DATA_V0_SHARING_COLORS = deHexStr(
    '0000 0003 '                   # version=0, numPaletteEntries=3
    '0004 0006 '                   # numPalettes=4, numColorRecords=6
    '00000014 '                    # offsetToFirstColorRecord=20
    '0000 0000 0003 0000 '         # colorRecordIndex=[0, 0, 3, 0]
    '443322FF 77889911 55555555 '  # colorRecord #0, #1, #2 (BGRA)
    '443322FF 77889911 FFFFFFFF')  # colorRecord #3, #4, #5


CPAL_DATA_V1_NOLABELS_NOTYPES = deHexStr(
    '0001 0003 '                   # version=1, numPaletteEntries=3
    '0002 0006 '                   # numPalettes=2, numColorRecords=6
    '0000001C  '                   # offsetToFirstColorRecord=28
    '0000 0003 '                   # colorRecordIndex=[0, 3]
    '00000000  '                   # offsetToPaletteTypeArray=0
    '00000000  '                   # offsetToPaletteLabelArray=0
    '00000000  '                   # offsetToPaletteEntryLabelArray=0
    'CAFECAFE 00112233 44556677 '  # colorRecord #0, #1, #2 (BGRA)
    '31415927 42424242 00331337')  # colorRecord #3, #4, #5


CPAL_DATA_V1 = deHexStr(
    '0001 0003 '                   # version=1, numPaletteEntries=3
    '0002 0006 '                   # numPalettes=2, numColorRecords=6
    '0000001C  '                   # offsetToFirstColorRecord=28
    '0000 0003 '                   # colorRecordIndex=[0, 3]
    '00000034  '                   # offsetToPaletteTypeArray=52
    '0000003C  '                   # offsetToPaletteLabelArray=60
    '00000040  '                   # offsetToPaletteEntryLabelArray=64
    'CAFECAFE 00112233 44556677 '  # colorRecord #0, #1, #2 (BGRA)
    '31415927 42424242 00331337 '  # colorRecord #3, #4, #5
    '00000001 00000002 '           # paletteType=[1, 2]
    '0102 0103 '                   # paletteLabel=[258, 259]
    '0201 0202 0203')              # paletteEntryLabel=[513, 514, 515]


class FakeNameTable(object):
    def __init__(self, names):
        self.names = names

    def getDebugName(self, nameID):
        return self.names.get(nameID)


class CPALTest(unittest.TestCase):
    def test_decompile_v0(self):
        cpal = newTable('CPAL')
        cpal.decompile(CPAL_DATA_V0, ttFont=None)
        self.assertEqual(cpal.version, 0)
        self.assertEqual(cpal.numPaletteEntries, 2)
        self.assertEqual(repr(cpal.palettes),
                         '[[#000000FF, #66CCFFFF], [#000000FF, #800000FF]]')

    def test_decompile_v0_sharingColors(self):
        cpal = newTable('CPAL')
        cpal.decompile(CPAL_DATA_V0_SHARING_COLORS, ttFont=None)
        self.assertEqual(cpal.version, 0)
        self.assertEqual(cpal.numPaletteEntries, 3)
        self.assertEqual([repr(p) for p in cpal.palettes], [
            '[#223344FF, #99887711, #55555555]',
            '[#223344FF, #99887711, #55555555]',
            '[#223344FF, #99887711, #FFFFFFFF]',
            '[#223344FF, #99887711, #55555555]'])

    def test_decompile_v1_noLabelsNoTypes(self):
        cpal = newTable('CPAL')
        cpal.decompile(CPAL_DATA_V1_NOLABELS_NOTYPES, ttFont=None)
        self.assertEqual(cpal.version, 1)
        self.assertEqual(cpal.numPaletteEntries, 3)
        self.assertEqual([repr(p) for p in cpal.palettes], [
            '[#CAFECAFE, #22110033, #66554477]',  # RGBA
            '[#59413127, #42424242, #13330037]'])
        self.assertEqual(cpal.paletteLabels, [cpal.NO_NAME_ID] * len(cpal.palettes))
        self.assertEqual(cpal.paletteTypes, [0, 0])
        self.assertEqual(cpal.paletteEntryLabels,
                        [cpal.NO_NAME_ID] * cpal.numPaletteEntries)

    def test_decompile_v1(self):
        cpal = newTable('CPAL')
        cpal.decompile(CPAL_DATA_V1, ttFont=None)
        self.assertEqual(cpal.version, 1)
        self.assertEqual(cpal.numPaletteEntries, 3)
        self.assertEqual([repr(p) for p in cpal.palettes], [
            '[#CAFECAFE, #22110033, #66554477]',  # RGBA
            '[#59413127, #42424242, #13330037]'])
        self.assertEqual(cpal.paletteTypes, [1, 2])
        self.assertEqual(cpal.paletteLabels, [258, 259])
        self.assertEqual(cpal.paletteEntryLabels, [513, 514, 515])

    def test_compile_v0(self):
        cpal = newTable('CPAL')
        cpal.decompile(CPAL_DATA_V0, ttFont=None)
        self.assertEqual(cpal.compile(ttFont=None), CPAL_DATA_V0)

    def test_compile_v0_sharingColors(self):
        cpal = newTable('CPAL')
        cpal.version = 0
        Color = getTableModule('CPAL').Color
        palette1 = [Color(red=0x22, green=0x33, blue=0x44, alpha=0xff),
                    Color(red=0x99, green=0x88, blue=0x77, alpha=0x11),
                    Color(red=0x55, green=0x55, blue=0x55, alpha=0x55)]
        palette2 = [Color(red=0x22, green=0x33, blue=0x44, alpha=0xff),
                    Color(red=0x99, green=0x88, blue=0x77, alpha=0x11),
                    Color(red=0xFF, green=0xFF, blue=0xFF, alpha=0xFF)]
        cpal.numPaletteEntries = len(palette1)
        cpal.palettes = [palette1, palette1, palette2, palette1]
        self.assertEqual(cpal.compile(ttFont=None),
                         CPAL_DATA_V0_SHARING_COLORS)

    def test_compile_v1(self):
        cpal = newTable('CPAL')
        cpal.decompile(CPAL_DATA_V1, ttFont=None)
        self.assertEqual(cpal.compile(ttFont=None), CPAL_DATA_V1)

    def test_compile_v1_noLabelsNoTypes(self):
        cpal = newTable('CPAL')
        cpal.decompile(CPAL_DATA_V1_NOLABELS_NOTYPES, ttFont=None)
        self.assertEqual(cpal.compile(ttFont=None),
                         CPAL_DATA_V1_NOLABELS_NOTYPES)

    def test_toXML_v0(self):
        cpal = newTable('CPAL')
        cpal.decompile(CPAL_DATA_V0, ttFont=None)
        self.assertEqual(getXML(cpal.toXML),
                         ['<version value="0"/>',
                          '<numPaletteEntries value="2"/>',
                          '<palette index="0">',
                          '  <color index="0" value="#000000FF"/>',
                          '  <color index="1" value="#66CCFFFF"/>',
                          '</palette>',
                          '<palette index="1">',
                          '  <color index="0" value="#000000FF"/>',
                          '  <color index="1" value="#800000FF"/>',
                          '</palette>'])

    def test_toXML_v1(self):
        name = FakeNameTable({258: "Spring theme", 259: "Winter theme",
                              513: "darks", 515: "lights"})
        cpal = newTable('CPAL')
        ttFont = {"name": name, "CPAL": cpal}
        cpal.decompile(CPAL_DATA_V1, ttFont)
        self.assertEqual(getXML(cpal.toXML, ttFont),
                         ['<version value="1"/>',
                          '<numPaletteEntries value="3"/>',
                          '<palette index="0" label="258" type="1">',
                          '  <!-- Spring theme -->',
                          '  <color index="0" value="#CAFECAFE"/>',
                          '  <color index="1" value="#22110033"/>',
                          '  <color index="2" value="#66554477"/>',
                          '</palette>',
                          '<palette index="1" label="259" type="2">',
                          '  <!-- Winter theme -->',
                          '  <color index="0" value="#59413127"/>',
                          '  <color index="1" value="#42424242"/>',
                          '  <color index="2" value="#13330037"/>',
                          '</palette>',
                          '<paletteEntryLabels>',
                          '  <label index="0" value="513"/><!-- darks -->',
                          '  <label index="1" value="514"/>',
                          '  <label index="2" value="515"/><!-- lights -->',
                          '</paletteEntryLabels>'])

    def test_fromXML_v0(self):
        cpal = newTable('CPAL')
        for name, attrs, content in parseXML(
                '<version value="0"/>'
                '<numPaletteEntries value="2"/>'
                '<palette index="0">'
                '  <color index="0" value="#12345678"/>'
                '  <color index="1" value="#FEDCBA98"/>'
                '</palette>'):
            cpal.fromXML(name, attrs, content, ttFont=None)
        self.assertEqual(cpal.version, 0)
        self.assertEqual(cpal.numPaletteEntries, 2)
        self.assertEqual(repr(cpal.palettes), '[[#12345678, #FEDCBA98]]')

    def test_fromXML_v1(self):
        cpal = newTable('CPAL')
        for name, attrs, content in parseXML(
                '<version value="1"/>'
                '<numPaletteEntries value="3"/>'
                '<palette index="0" label="259" type="2">'
                '  <color index="0" value="#12345678"/>'
                '  <color index="1" value="#FEDCBA98"/>'
                '  <color index="2" value="#CAFECAFE"/>'
                '</palette>'
                '<paletteEntryLabels>'
                '  <label index="1" value="262"/>'
                '</paletteEntryLabels>'):
            cpal.fromXML(name, attrs, content, ttFont=None)
        self.assertEqual(cpal.version, 1)
        self.assertEqual(cpal.numPaletteEntries, 3)
        self.assertEqual(repr(cpal.palettes),
                         '[[#12345678, #FEDCBA98, #CAFECAFE]]')
        self.assertEqual(cpal.paletteLabels, [259])
        self.assertEqual(cpal.paletteTypes, [2])
        self.assertEqual(cpal.paletteEntryLabels,
                        [cpal.NO_NAME_ID, 262, cpal.NO_NAME_ID])


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
