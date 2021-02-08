from fontTools.misc.py23 import *
from fontTools.misc.testTools import parseXML
from fontTools.misc.textTools import deHexStr
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib import TTLibError
from fontTools.ttLib.tables._f_v_a_r import table__f_v_a_r, Axis, NamedInstance
from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e, NameRecord
import unittest



FVAR_DATA = deHexStr(
    "00 01 00 00 00 10 00 02 00 02 00 14 00 02 00 0C "
    "77 67 68 74 00 64 00 00 01 90 00 00 03 84 00 00 00 00 01 01 "
    "77 64 74 68 00 32 00 00 00 64 00 00 00 c8 00 00 00 00 01 02 "
    "01 03 00 00 01 2c 00 00 00 64 00 00 "
    "01 04 00 00 01 2c 00 00 00 4b 00 00")

FVAR_AXIS_DATA = deHexStr(
    "6F 70 73 7a ff ff 80 00 00 01 4c cd 00 01 80 00 00 00 01 59")

FVAR_INSTANCE_DATA_WITHOUT_PSNAME = deHexStr(
    "01 59 00 00 00 00 b3 33 00 00 80 00")

FVAR_INSTANCE_DATA_WITH_PSNAME = (
    FVAR_INSTANCE_DATA_WITHOUT_PSNAME + deHexStr("02 34"))

FVAR_DATA_WITH_DUPLICATE_AXIS_TAGS = deHexStr(
    "00 01 00 00 00 10 00 02 00 02 00 14 00 02 00 0C "
    "44 55 50 50 00 64 00 00 01 90 00 00 03 84 00 00 00 00 01 01 "
    "44 55 50 50 00 32 00 00 00 64 00 00 00 c8 00 00 00 00 01 02 "
    "01 03 00 00 01 2c 00 00 00 64 00 00 "
    "01 04 00 00 01 2c 00 00 00 4b 00 00")


def xml_lines(writer):
    content = writer.file.getvalue().decode("utf-8")
    return [line.strip() for line in content.splitlines()][1:]


def AddName(font, name):
    nameTable = font.get("name")
    if nameTable is None:
        nameTable = font["name"] = table__n_a_m_e()
        nameTable.names = []
    namerec = NameRecord()
    namerec.nameID = 1 + max([n.nameID for n in nameTable.names] + [256])
    namerec.string = name.encode('mac_roman')
    namerec.platformID, namerec.platEncID, namerec.langID = (1, 0, 0)
    nameTable.names.append(namerec)
    return namerec


def MakeFont():
    axes = [("weight", "wght", "Weight", 100, 400, 900), ("width", "wdth", "Width", 50, 100, 200)]
    instances = [("Light", 300, 100), ("Light Condensed", 300, 75)]
    fvarTable = table__f_v_a_r()
    font = {"fvar": fvarTable}
    for axisId, tag, name, minValue, defaultValue, maxValue in axes:
        axis = Axis()
        axis.axisId = axisId
        axis.axisTag = tag
        axis.defaultValue = defaultValue
        axis.minValue, axis.maxValue = minValue, maxValue
        axis.axisNameID = AddName(font, name).nameID
        fvarTable.axes.append(axis)
    for name, weight, width in instances:
        inst = NamedInstance()
        inst.subfamilyNameID = AddName(font, name).nameID
        inst.coordinates = {"weight": weight, "width": width}
        fvarTable.instances.append(inst)
    return font


def MakeFontWithDuplicateAxisTags():
    axes = [("duplicate", "DUPP", "Duplicate", 100, 400, 900), ("duplicate2", "DUPP", "Duplicate", 50, 100, 200)]
    instances = [("Light", 300, 100), ("Light Condensed", 300, 75)]
    fvarTable = table__f_v_a_r()
    font = {"fvar": fvarTable}
    for axisId, tag, name, minValue, defaultValue, maxValue in axes:
        axis = Axis()
        axis.axisId = axisId
        axis.axisTag = tag
        axis.defaultValue = defaultValue
        axis.minValue, axis.maxValue = minValue, maxValue
        axis.axisNameID = AddName(font, name).nameID
        fvarTable.axes.append(axis)
    for name, weight, width in instances:
        inst = NamedInstance()
        inst.subfamilyNameID = AddName(font, name).nameID
        inst.coordinates = {"duplicate": weight, "duplicate2": width}
        fvarTable.instances.append(inst)
    return font


class FontVariationTableTest(unittest.TestCase):
    def test_compile(self):
        font = MakeFont()
        h = font["fvar"].compile(font)
        self.assertEqual(FVAR_DATA, font["fvar"].compile(font))

    def test_decompile(self):
        fvar = table__f_v_a_r()
        fvar.decompile(FVAR_DATA, ttFont={"fvar": fvar})
        self.assertEqual(["wght", "wdth"], [a.axisTag for a in fvar.axes])
        self.assertEqual([259, 260], [i.subfamilyNameID for i in fvar.instances])

    def test_toXML(self):
        font = MakeFont()
        writer = XMLWriter(BytesIO())
        font["fvar"].toXML(writer, font)
        xml = writer.file.getvalue().decode("utf-8")
        self.assertTrue("<Axis name=\"weight\">" in xml)
        self.assertTrue("<Axis name=\"width\">" in xml)
        self.assertTrue("<AxisTag>wght</AxisTag>" in xml)
        self.assertTrue("<AxisTag>wdth</AxisTag>" in xml)
        self.assertEqual(2, xml.count("<NamedInstance "))
        self.assertTrue("<!-- Light -->" in xml)
        self.assertTrue("<!-- Light Condensed -->" in xml)

    def test_fromXML(self):
        fvar = table__f_v_a_r()
        for name, attrs, content in parseXML(
                '<Axis name="optical_size">'
                '    <AxisTag>opsz</AxisTag>'
                '</Axis>'
                '<Axis name="slant">'
                '    <AxisTag>slnt</AxisTag>'
                '    <Flags>0x123</Flags>'
                '</Axis>'
                '<NamedInstance subfamilyNameID="765"/>'
                '<NamedInstance subfamilyNameID="234"/>'):
            fvar.fromXML(name, attrs, content, ttFont=None)
        self.assertEqual(["opsz", "slnt"], [a.axisTag for a in fvar.axes])
        self.assertEqual(["optical_size", "slant"], [a.axisId for a in fvar.axes])
        self.assertEqual([0, 0x123], [a.flags for a in fvar.axes])
        self.assertEqual([765, 234], [i.subfamilyNameID for i in fvar.instances])

    def test_compile_duplicate_axis_tags(self):
        font = MakeFontWithDuplicateAxisTags()
        h = font["fvar"].compile(font)
        self.assertEqual(FVAR_DATA_WITH_DUPLICATE_AXIS_TAGS, font["fvar"].compile(font))

    def test_compile_duplicate_axis_tags_conflicting_ids(self):
        font = MakeFontWithDuplicateAxisTags()
        for axis in font["fvar"].axes:
            axis.axisId = "DUPP"
        font["fvar"].instances = []
        with self.assertRaises(TTLibError):
            h = font["fvar"].compile(font)

    def test_decompile_duplicate_axis_tags(self):
        fvar = table__f_v_a_r()
        fvar.decompile(FVAR_DATA_WITH_DUPLICATE_AXIS_TAGS, ttFont={"fvar": fvar})
        expectedAxisIds = ["DUPP", "DUPP#1"]
        expectedAxisTags = ["DUPP", "DUPP"]
        self.assertEqual(expectedAxisIds, [axis.axisId for axis in fvar.axes])
        self.assertEqual(expectedAxisTags, [axis.axisTag for axis in fvar.axes])
        self.assertEqual([expectedAxisIds] * 2, [sorted(i.coordinates.keys()) for i in fvar.instances])

    def test_toXML_duplicate_axis_tags(self):
        font = MakeFontWithDuplicateAxisTags()
        writer = XMLWriter(BytesIO())
        font["fvar"].toXML(writer, font)
        xml = writer.file.getvalue().decode("utf-8")
        self.assertTrue("<Axis name=\"duplicate\">" in xml)
        self.assertTrue("<Axis name=\"duplicate2\">" in xml)
        self.assertEqual(2, xml.count("<AxisTag>DUPP</AxisTag>"))
        self.assertEqual(2, xml.count("<NamedInstance "))
        self.assertTrue("<!-- Light -->" in xml)
        self.assertTrue("<!-- Light Condensed -->" in xml)

    def test_fromXML_duplicate_axis_tags(self):
        fvar = table__f_v_a_r()
        for name, attrs, content in parseXML(
                '<Axis>'
                '    <AxisTag>DUPP</AxisTag>'
                '</Axis>'
                '<Axis name="duplicate">'
                '    <AxisTag>DUPP</AxisTag>'
                '    <Flags>0x123</Flags>'
                '</Axis>'
                '<NamedInstance subfamilyNameID="765"/>'
                '<NamedInstance subfamilyNameID="234"/>'):
            fvar.fromXML(name, attrs, content, ttFont=None)
        self.assertEqual(["DUPP", "DUPP"], [a.axisTag for a in fvar.axes])
        self.assertEqual(["DUPP", "duplicate"], [a.axisId for a in fvar.axes])
        self.assertEqual([0, 0x123], [a.flags for a in fvar.axes])
        self.assertEqual([765, 234], [i.subfamilyNameID for i in fvar.instances])

    def test_fromXML_duplicate_axis_tags_conflicting_ids(self):
        fvar = table__f_v_a_r()
        with self.assertRaises(TTLibError):
            for name, attrs, content in parseXML(
                    '<Axis>'
                    '    <AxisTag>DUPP</AxisTag>'
                    '</Axis>'
                    '<Axis>'
                    '    <AxisTag>DUPP</AxisTag>'
                    '    <Flags>0x123</Flags>'
                    '</Axis>'):
                fvar.fromXML(name, attrs, content, ttFont=None)


class AxisTest(unittest.TestCase):
    def test_compile(self):
        axis = Axis()
        axis.axisId, axis.axisTag, axis.axisNameID = ('optical_size', 'opsz', 345)
        axis.minValue, axis.defaultValue, axis.maxValue = (-0.5, 1.3, 1.5)
        self.assertEqual(FVAR_AXIS_DATA, axis.compile())

    def test_decompile(self):
        axis = Axis()
        axis.decompile(FVAR_AXIS_DATA)
        self.assertIsNone(axis.axisId)
        self.assertEqual("opsz", axis.axisTag)
        self.assertEqual(345, axis.axisNameID)
        self.assertEqual(-0.5, axis.minValue)
        self.assertAlmostEqual(1.3000031, axis.defaultValue)
        self.assertEqual(1.5, axis.maxValue)

    def test_toXML(self):
        font = MakeFont()
        axis = Axis()
        axis.decompile(FVAR_AXIS_DATA)
        AddName(font, "Optical Size").nameID = 256
        axis.axisId = "optical_size"
        axis.axisNameID = 256
        axis.flags = 0xABC
        writer = XMLWriter(BytesIO())
        axis.toXML(writer, font)
        self.assertEqual([
            '',
            '<!-- Optical Size -->',
            '<Axis name="optical_size">',
                '<AxisTag>opsz</AxisTag>',
                '<Flags>0xABC</Flags>',
                '<MinValue>-0.5</MinValue>',
                '<DefaultValue>1.3</DefaultValue>',
                '<MaxValue>1.5</MaxValue>',
                '<AxisNameID>256</AxisNameID>',
            '</Axis>'
        ], xml_lines(writer))

    def test_fromXML(self):
        axis = Axis()
        for name, attrs, content in parseXML(
                '<Axis name="weight">'
                '    <AxisTag>wght</AxisTag>'
                '    <Flags>0x123ABC</Flags>'
                '    <MinValue>100</MinValue>'
                '    <DefaultValue>400</DefaultValue>'
                '    <MaxValue>900</MaxValue>'
                '    <AxisNameID>256</AxisNameID>'
                '</Axis>'):
            axis.fromXML(name, attrs, content, ttFont=None)
        self.assertEqual("weight", axis.axisId)
        self.assertEqual("wght", axis.axisTag)
        self.assertEqual(0x123ABC, axis.flags)
        self.assertEqual(100, axis.minValue)
        self.assertEqual(400, axis.defaultValue)
        self.assertEqual(900, axis.maxValue)
        self.assertEqual(256, axis.axisNameID)


class NamedInstanceTest(unittest.TestCase):
    def assertDictAlmostEqual(self, dict1, dict2):
        self.assertEqual(set(dict1.keys()), set(dict2.keys()))
        for key in dict1:
            self.assertAlmostEqual(dict1[key], dict2[key])

    def test_compile_withPostScriptName(self):
        inst = NamedInstance()
        inst.subfamilyNameID = 345
        inst.postscriptNameID = 564
        inst.coordinates = {"wght": 0.7, "wdth": 0.5}
        self.assertEqual(FVAR_INSTANCE_DATA_WITH_PSNAME,
                         inst.compile(["wght", "wdth"], True))

    def test_compile_withoutPostScriptName(self):
        inst = NamedInstance()
        inst.subfamilyNameID = 345
        inst.postscriptNameID = 564
        inst.coordinates = {"wght": 0.7, "wdth": 0.5}
        self.assertEqual(FVAR_INSTANCE_DATA_WITHOUT_PSNAME,
                         inst.compile(["wght", "wdth"], False))

    def test_decompile_withPostScriptName(self):
        inst = NamedInstance()
        inst.decompile(FVAR_INSTANCE_DATA_WITH_PSNAME, ["wght", "wdth"])
        self.assertEqual(564, inst.postscriptNameID)
        self.assertEqual(345, inst.subfamilyNameID)
        self.assertDictAlmostEqual({"wght": 0.6999969, "wdth": 0.5}, inst.coordinates)

    def test_decompile_withoutPostScriptName(self):
        inst = NamedInstance()
        inst.decompile(FVAR_INSTANCE_DATA_WITHOUT_PSNAME, ["wght", "wdth"])
        self.assertEqual(0xFFFF, inst.postscriptNameID)
        self.assertEqual(345, inst.subfamilyNameID)
        self.assertDictAlmostEqual({"wght": 0.6999969, "wdth": 0.5}, inst.coordinates)

    def test_toXML_withPostScriptName(self):
        font = MakeFont()
        inst = NamedInstance()
        inst.flags = 0xE9
        inst.subfamilyNameID = AddName(font, "Light Condensed").nameID
        inst.postscriptNameID = AddName(font, "Test-LightCondensed").nameID
        inst.coordinates = {"weight": 0.7, "width": 0.5}
        writer = XMLWriter(BytesIO())
        inst.toXML(writer, font)
        self.assertEqual([
            '',
            '<!-- Light Condensed -->',
            '<!-- PostScript: Test-LightCondensed -->',
            '<NamedInstance flags="0xE9" postscriptNameID="%s" subfamilyNameID="%s">' % (
                inst.postscriptNameID, inst.subfamilyNameID),
              '<coord axis="weight" value="0.7"/>',
              '<coord axis="width" value="0.5"/>',
            '</NamedInstance>'
        ], xml_lines(writer))

    def test_toXML_withoutPostScriptName(self):
        font = MakeFont()
        inst = NamedInstance()
        inst.flags = 0xABC
        inst.subfamilyNameID = AddName(font, "Light Condensed").nameID
        inst.coordinates = {"weight": 0.7, "width": 0.5}
        writer = XMLWriter(BytesIO())
        inst.toXML(writer, font)
        self.assertEqual([
            '',
            '<!-- Light Condensed -->',
            '<NamedInstance flags="0xABC" subfamilyNameID="%s">' %
                inst.subfamilyNameID,
              '<coord axis="weight" value="0.7"/>',
              '<coord axis="width" value="0.5"/>',
            '</NamedInstance>'
        ], xml_lines(writer))

    def test_fromXML_withPostScriptName(self):
        inst = NamedInstance()
        for name, attrs, content in parseXML(
                '<NamedInstance flags="0x0" postscriptNameID="257" subfamilyNameID="345">'
                '    <coord axis="weight" value="0.7"/>'
                '    <coord axis="width" value="0.5"/>'
                '</NamedInstance>'):
            inst.fromXML(name, attrs, content, ttFont=MakeFont())
        self.assertEqual(257, inst.postscriptNameID)
        self.assertEqual(345, inst.subfamilyNameID)
        self.assertDictAlmostEqual({"weight": 0.6999969, "width": 0.5}, inst.coordinates)

    def test_fromXML_withoutPostScriptName(self):
        inst = NamedInstance()
        for name, attrs, content in parseXML(
                '<NamedInstance flags="0x123ABC" subfamilyNameID="345">'
                '    <coord axis="wght" value="0.7"/>'
                '    <coord axis="wdth" value="0.5"/>'
                '</NamedInstance>'):
            inst.fromXML(name, attrs, content, ttFont=MakeFont())
        self.assertEqual(0x123ABC, inst.flags)
        self.assertEqual(345, inst.subfamilyNameID)
        self.assertDictAlmostEqual({"wght": 0.6999969, "wdth": 0.5}, inst.coordinates)


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
