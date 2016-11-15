from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.testTools import parseXML
from fontTools.misc.textTools import deHexStr
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib import TTLibError
from fontTools.ttLib.tables._a_v_a_r import table__a_v_a_r
from fontTools.ttLib.tables._f_v_a_r import table__f_v_a_r, Axis
import collections
import logging
import unittest


TEST_DATA = deHexStr(
    "00 01 00 00 00 00 00 02 "
    "00 04 C0 00 C0 00 00 00 00 00 13 33 33 33 40 00 40 00 "
    "00 03 C0 00 C0 00 00 00 00 00 40 00 40 00")


class AxisVariationTableTest(unittest.TestCase):
    def test_compile(self):
        avar = table__a_v_a_r()
        avar.segments["wdth"] = {-1.0: -1.0, 0.0: 0.0, 0.3: 0.8, 1.0: 1.0}
        avar.segments["wght"] = {-1.0: -1.0, 0.0: 0.0, 1.0: 1.0}
        self.assertEqual(TEST_DATA, avar.compile(self.makeFont(["wdth", "wght"])))

    def test_decompile(self):
        avar = table__a_v_a_r()
        avar.decompile(TEST_DATA, self.makeFont(["wdth", "wght"]))
        self.assertEqual({
            "wdth": {-1.0: -1.0, 0.0: 0.0, 0.3: 0.8, 1.0: 1.0},
            "wght": {-1.0: -1.0, 0.0: 0.0, 1.0: 1.0}
        }, avar.segments)

    def test_decompile_unsupportedVersion(self):
        avar = table__a_v_a_r()
        font = self.makeFont(["wdth", "wght"])
        self.assertRaises(TTLibError, avar.decompile, deHexStr("02 01 03 06 00 00 00 00"), font)

    def test_toXML(self):
        avar = table__a_v_a_r()
        avar.segments["opsz"] = {-1.0: -1.0, 0.0: 0.0, 0.3: 0.8, 1.0: 1.0}
        writer = XMLWriter(BytesIO())
        avar.toXML(writer, self.makeFont(["opsz"]))
        self.assertEqual([
            '<segment axis="opsz">',
                '<mapping from="-1.0" to="-1.0"/>',
                '<mapping from="0.0" to="0.0"/>',
                '<mapping from="0.3" to="0.8"/>',
                '<mapping from="1.0" to="1.0"/>',
            '</segment>'
        ], self.xml_lines(writer))

    def test_fromXML(self):
        avar = table__a_v_a_r()
        for name, attrs, content in parseXML(
                '<segment axis="wdth">'
                '    <mapping from="-1.0" to="-1.0"/>'
                '    <mapping from="0.0" to="0.0"/>'
                '    <mapping from="0.7" to="0.2"/>'
                '    <mapping from="1.0" to="1.0"/>'
                '</segment>'):
            avar.fromXML(name, attrs, content, ttFont=None)
        self.assertEqual({"wdth": {-1: -1, 0: 0, 0.7: 0.2, 1.0: 1.0}},
                         avar.segments)

    def test_fixupSegments(self):
        avar = table__a_v_a_r()
        logger = logging.getLogger(table__a_v_a_r.__module__)
        sio = StringIO()
        logger.addHandler(logging.StreamHandler(stream=sio))
        avar.segments = {"wdth": {0.3: 0.8, 1.0: 0.7}}
        avar.fixupSegments_()
        self.assertEqual({"wdth": {-1.0: -1.0, 0.0: 0.0, 0.3: 0.8, 1.0: 1.0}}, avar.segments)
        self.assertEqual([
                "avar axis 'wdth' should map -1.0 to -1.0",
                "avar axis 'wdth' should map 0.0 to 0.0",
                "avar axis 'wdth' should map 1.0 to 1.0"
        ], sio.getvalue().splitlines())

    @staticmethod
    def makeFont(axisTags):
        """['opsz', 'wdth'] --> ttFont"""
        fvar = table__f_v_a_r()
        for tag in axisTags:
            axis = Axis()
            axis.axisTag = tag
            fvar.axes.append(axis)
        return {"fvar": fvar}

    @staticmethod
    def xml_lines(writer):
        content = writer.file.getvalue().decode("utf-8")
        return [line.strip() for line in content.splitlines()][1:]


if __name__ == "__main__":
    unittest.main()
