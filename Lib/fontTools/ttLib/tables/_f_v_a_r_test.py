from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
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

FVAR_INSTANCE_DATA = deHexStr("01 59 00 00 00 00 b3 33 00 00 80 00")


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
    axes = [("wght", "Weight", 100, 400, 900), ("wdth", "Width", 50, 100, 200)]
    instances = [("Light", 300, 100), ("Light Condensed", 300, 75)]
    fvarTable = table__f_v_a_r()
    font = {"fvar": fvarTable}
    for tag, name, minValue, defaultValue, maxValue in axes:
        axis = Axis()
        axis.axisTag = tag
        axis.defaultValue = defaultValue
        axis.minValue, axis.maxValue = minValue, maxValue
        axis.nameID = AddName(font, name).nameID
        fvarTable.axes.append(axis)
    for name, weight, width in instances:
        inst = NamedInstance()
        inst.nameID = AddName(font, name).nameID
        inst.coordinates = {"wght": weight, "wdth": width}
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
        self.assertEqual([259, 260], [i.nameID for i in fvar.instances])

    def test_toXML(self):
        font = MakeFont()
        writer = XMLWriter(StringIO())
        font["fvar"].toXML(writer, font)
        xml = writer.file.getvalue().decode("utf-8")
        self.assertEqual(2, xml.count("<Axis>"))
        self.assertTrue("<AxisTag>wght</AxisTag>" in xml)
        self.assertTrue("<AxisTag>wdth</AxisTag>" in xml)
        self.assertEqual(2, xml.count("<NamedInstance "))
        self.assertTrue("<!-- Light -->" in xml)
        self.assertTrue("<!-- Light Condensed -->" in xml)

    def test_fromXML(self):
        fvar = table__f_v_a_r()
        fvar.fromXML("Axis", {}, [("AxisTag", {}, ["opsz"])], ttFont=None)
        fvar.fromXML("Axis", {}, [("AxisTag", {}, ["slnt"])], ttFont=None)
        fvar.fromXML("NamedInstance", {"nameID": "765"}, [], ttFont=None)
        fvar.fromXML("NamedInstance", {"nameID": "234"}, [], ttFont=None)
        self.assertEqual(["opsz", "slnt"], [a.axisTag for a in fvar.axes])
        self.assertEqual([765, 234], [i.nameID for i in fvar.instances])


class AxisTest(unittest.TestCase):
    def test_compile(self):
        axis = Axis()
        axis.axisTag, axis.nameID = ('opsz', 345)
        axis.minValue, axis.defaultValue, axis.maxValue = (-0.5, 1.3, 1.5)
        self.assertEqual(FVAR_AXIS_DATA, axis.compile())

    def test_decompile(self):
        axis = Axis()
        axis.decompile(FVAR_AXIS_DATA)
        self.assertEqual("opsz", axis.axisTag)
        self.assertEqual(345, axis.nameID)
        self.assertEqual(-0.5, axis.minValue)
        self.assertEqual(1.3, axis.defaultValue)
        self.assertEqual(1.5, axis.maxValue)

    def test_toXML(self):
        font = MakeFont()
        axis = Axis()
        axis.decompile(FVAR_AXIS_DATA)
        AddName(font, "Optical Size").nameID = 256
        axis.nameID = 256
        writer = XMLWriter(StringIO())
        axis.toXML(writer, font)
        self.assertEqual([
            '',
            '<!-- Optical Size -->',
            '<Axis>',
                '<AxisTag>opsz</AxisTag>',
                '<MinValue>-0.5</MinValue>',
                '<DefaultValue>1.3</DefaultValue>',
                '<MaxValue>1.5</MaxValue>',
                '<NameID>256</NameID>',
            '</Axis>'
        ], xml_lines(writer))

    def test_fromXML(self):
        axis = Axis()
        axis.fromXML("Axis", {}, [
            ("AxisTag", {}, ["wght"]),
            ("MinValue", {}, ["100"]),
            ("DefaultValue", {}, ["400"]),
            ("MaxValue", {}, ["900"]),
            ("NameID", {}, ["256"])
        ], ttFont=None)
        self.assertEqual("wght", axis.axisTag)
        self.assertEqual(100, axis.minValue)
        self.assertEqual(400, axis.defaultValue)
        self.assertEqual(900, axis.maxValue)
        self.assertEqual(256, axis.nameID)


class NamedInstanceTest(unittest.TestCase):
    def test_compile(self):
        inst = NamedInstance()
        inst.nameID = 345
        inst.coordinates = {"wght": 0.7, "wdth": 0.5}
        self.assertEqual(FVAR_INSTANCE_DATA, inst.compile(["wght", "wdth"]))

    def test_decompile(self):
        inst = NamedInstance()
        inst.decompile(FVAR_INSTANCE_DATA, ["wght", "wdth"])
        self.assertEqual(345, inst.nameID)
        self.assertEqual({"wght": 0.7, "wdth": 0.5}, inst.coordinates)

    def test_toXML(self):
        font = MakeFont()
        inst = NamedInstance()
        inst.nameID = AddName(font, "Light Condensed").nameID
        inst.coordinates = {"wght": 0.7, "wdth": 0.5}
        writer = XMLWriter(StringIO())
        inst.toXML(writer, font)
        self.assertEqual([
            '',
            '<!-- Light Condensed -->',
            '<NamedInstance nameID="%s">' % inst.nameID,
              '<coord axis="wght" value="0.7"/>',
              '<coord axis="wdth" value="0.5"/>',
            '</NamedInstance>'
        ], xml_lines(writer))

    def test_fromXML(self):
        inst = NamedInstance()
        attrs = {"nameID": "345"}
        inst.fromXML("NamedInstance", attrs, [
                ("coord", {"axis": "wght", "value": "0.7"}, []),
                ("coord", {"axis": "wdth", "value": "0.5"}, []),
                ], ttFont=MakeFont())
        self.assertEqual(345, inst.nameID)
        self.assertEqual({"wght": 0.7, "wdth": 0.5}, inst.coordinates)


if __name__ == "__main__":
    unittest.main()
