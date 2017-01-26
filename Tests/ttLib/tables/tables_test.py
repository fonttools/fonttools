from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib import TTFont
from fontTools import ttLib
import difflib
import os
import sys
import unittest


class TablesTest(unittest.TestCase):

    # Font files in data/*.[ot]tf; output gets compared to data/*.ttx.*
    TESTS = {
        "aots/base.otf":					'(CFF','cmap','head','hhea','hmtx','maxp','name','OS2','post'),
        "aots/classdef1_font1.otf":				('GSUB'),
        "aots/classdef1_font2.otf":				('GSUB'),
        "aots/classdef1_font3.otf":				('GSUB'),
        "aots/classdef1_font4.otf":				('GSUB'),
        "aots/classdef2_font1.otf":				('GSUB'),
        "aots/classdef2_font2.otf":				('GSUB'),
        "aots/classdef2_font3.otf":				('GSUB'),
        "aots/classdef2_font4.otf":				('GSUB'),
        "aots/cmap0_font1.otf":					('cmap'),
        "aots/cmap10_font1.otf":				('cmap'),
        "aots/cmap10_font2.otf":				('cmap'),
        "aots/cmap12_font1.otf":				('cmap'),
        "aots/cmap14_font1.otf":				('cmap'),
        "aots/cmap2_font1.otf":					('cmap'),
        "aots/cmap4_font1.otf":					('cmap'),
        "aots/cmap4_font2.otf":					('cmap'),
        "aots/cmap4_font3.otf":					('cmap'),
        "aots/cmap4_font4.otf":					('cmap'),
        "aots/cmap6_font1.otf":					('cmap'),
        "aots/cmap6_font2.otf":					('cmap'),
        "aots/cmap8_font1.otf":					('cmap'),
        "aots/cmap_composition_font1.otf":			('cmap'),
        "aots/cmap_subtableselection_font1.otf":		('cmap'),
        "aots/cmap_subtableselection_font2.otf":		('cmap'),
        "aots/cmap_subtableselection_font3.otf":		('cmap'),
        "aots/cmap_subtableselection_font4.otf":		('cmap'),
        "aots/cmap_subtableselection_font5.otf":		('cmap'),
        "aots/gpos1_1_lookupflag_f1.otf":			('GDEF','GPOS'),
        "aots/gpos1_1_simple_f1.otf":				('GPOS'),
        "aots/gpos1_1_simple_f2.otf":				('GPOS'),
        "aots/gpos1_1_simple_f3.otf":				('GPOS'),
        "aots/gpos1_1_simple_f4.otf":				('GPOS'),
        "aots/gpos1_2_font1.otf":				('GPOS'),
        "aots/gpos1_2_font2.otf":				('GDEF','GPOS'),
        "aots/gpos2_1_font6.otf":				('GPOS'),
        "aots/gpos2_1_font7.otf":				('GPOS'),
        "aots/gpos2_1_lookupflag_f1.otf":			('GDEF','GPOS'),
        "aots/gpos2_1_lookupflag_f2.otf":			('GDEF','GPOS'),
        "aots/gpos2_1_next_glyph_f1.otf":			('GPOS'),
        "aots/gpos2_1_next_glyph_f2.otf":			('GPOS'),
        "aots/gpos2_1_simple_f1.otf":				('GPOS'),
        "aots/gpos2_2_font1.otf":				('GPOS'),
        "aots/gpos2_2_font2.otf":				('GDEF','GPOS'),
        "aots/gpos2_2_font3.otf":				('GDEF','GPOS'),
        "aots/gpos2_2_font4.otf":				('GPOS'),
        "aots/gpos2_2_font5.otf":				('GPOS'),
        "aots/gpos3_font1.otf":					('GPOS'),
        "aots/gpos3_font2.otf":					('GDEF','GPOS'),
        "aots/gpos3_font3.otf":					('GDEF','GPOS'),
        "aots/gpos4_lookupflag_f1.otf":				('GDEF','GPOS'),
        "aots/gpos4_lookupflag_f2.otf":				('GDEF','GPOS'),
        "aots/gpos4_multiple_anchors_1.otf":			('GDEF','GPOS'),
        "aots/gpos4_simple_1.otf":				('GDEF','GPOS'),
        "aots/gpos5_font1.otf":					('GDEF','GPOS','GSUB'),
        "aots/gpos6_font1.otf":					('GDEF','GPOS'),
        "aots/gpos7_1_font1.otf":				('GPOS'),
        "aots/gpos9_font1.otf":					('GPOS'),
        "aots/gpos9_font2.otf":					('GPOS'),
        "aots/gpos_chaining1_boundary_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining1_boundary_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining1_boundary_f3.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining1_boundary_f4.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining1_lookupflag_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining1_multiple_subrules_f1.otf":		('GDEF','GPOS'),
        "aots/gpos_chaining1_multiple_subrules_f2.otf":		('GDEF','GPOS'),
        "aots/gpos_chaining1_next_glyph_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining1_simple_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining1_simple_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining1_successive_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining2_boundary_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining2_boundary_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining2_boundary_f3.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining2_boundary_f4.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining2_lookupflag_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining2_multiple_subrules_f1.otf":		('GDEF','GPOS'),
        "aots/gpos_chaining2_multiple_subrules_f2.otf":		('GDEF','GPOS'),
        "aots/gpos_chaining2_next_glyph_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining2_simple_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining2_simple_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining2_successive_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining3_boundary_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining3_boundary_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining3_boundary_f3.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining3_boundary_f4.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining3_lookupflag_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining3_next_glyph_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining3_simple_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining3_simple_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_chaining3_successive_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context1_boundary_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context1_boundary_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_context1_expansion_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context1_lookupflag_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context1_lookupflag_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_context1_multiple_subrules_f1.otf":		('GDEF','GPOS'),
        "aots/gpos_context1_multiple_subrules_f2.otf":		('GDEF','GPOS'),
        "aots/gpos_context1_next_glyph_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context1_simple_f1.otf":				('GDEF','GPOS'),
        "aots/gpos_context1_simple_f2.otf":				('GDEF','GPOS'),
        "aots/gpos_context1_successive_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context2_boundary_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context2_boundary_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_context2_classes_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context2_classes_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_context2_expansion_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context2_lookupflag_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context2_lookupflag_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_context2_multiple_subrules_f1.otf":		('GDEF','GPOS'),
        "aots/gpos_context2_multiple_subrules_f2.otf":		('GDEF','GPOS'),
        "aots/gpos_context2_next_glyph_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context2_simple_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context2_simple_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_context2_successive_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context3_boundary_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context3_boundary_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_context3_lookupflag_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context3_lookupflag_f2.otf":			('GDEF','GPOS'),
        "aots/gpos_context3_next_glyph_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context3_simple_f1.otf":			('GDEF','GPOS'),
        "aots/gpos_context3_successive_f1.otf":			('GDEF','GPOS'),
        "aots/gsub1_1_lookupflag_f1.otf":			('GDEF','GSUB'),
        "aots/gsub1_1_modulo_f1.otf":				('GSUB'),
        "aots/gsub1_1_simple_f1.otf":				('GSUB'),
        "aots/gsub1_2_lookupflag_f1.otf":			('GDEF','GSUB'),
        "aots/gsub1_2_simple_f1.otf":				('GSUB'),
        "aots/gsub2_1_lookupflag_f1.otf":			('GDEF','GSUB'),
        "aots/gsub2_1_multiple_sequences_f1.otf":		('GSUB'),
        "aots/gsub2_1_simple_f1.otf":				('GSUB'),
        "aots/gsub3_1_lookupflag_f1.otf":			('GDEF','GSUB'),
        "aots/gsub3_1_multiple_f1.otf":				('GSUB'),
        "aots/gsub3_1_simple_f1.otf":				('GSUB'),
        "aots/gsub4_1_lookupflag_f1.otf":			('GDEF','GSUB'),
        "aots/gsub4_1_multiple_ligatures_f1.otf":		('GSUB'),
        "aots/gsub4_1_multiple_ligatures_f2.otf":		('GSUB'),
        "aots/gsub4_1_multiple_ligsets_f1.otf":			('GSUB'),
        "aots/gsub4_1_simple_f1.otf":				('GSUB'),
        "aots/gsub7_font1.otf":					('GSUB'),
        "aots/gsub7_font2.otf":					('GSUB'),
        "aots/gsub_chaining1_boundary_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining1_boundary_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining1_boundary_f3.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining1_boundary_f4.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining1_lookupflag_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining1_multiple_subrules_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining1_multiple_subrules_f2.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining1_next_glyph_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining1_simple_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining1_simple_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining1_successive_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining2_boundary_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining2_boundary_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining2_boundary_f3.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining2_boundary_f4.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining2_lookupflag_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining2_multiple_subrules_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining2_multiple_subrules_f2.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining2_next_glyph_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining2_simple_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining2_simple_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining2_successive_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining3_boundary_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining3_boundary_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining3_boundary_f3.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining3_boundary_f4.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining3_lookupflag_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining3_next_glyph_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_chaining3_simple_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining3_simple_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_chaining3_successive_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_context1_boundary_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context1_boundary_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_context1_expansion_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context1_lookupflag_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context1_lookupflag_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_context1_multiple_subrules_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_context1_multiple_subrules_f2.otf":		('GDEF','GSUB'),
        "aots/gsub_context1_next_glyph_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context1_simple_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context1_simple_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_context1_successive_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context2_boundary_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context2_boundary_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_context2_classes_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context2_classes_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_context2_expansion_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context2_lookupflag_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context2_lookupflag_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_context2_multiple_subrules_f1.otf":		('GDEF','GSUB'),
        "aots/gsub_context2_multiple_subrules_f2.otf":		('GDEF','GSUB'),
        "aots/gsub_context2_next_glyph_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context2_simple_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context2_simple_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_context2_successive_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context3_boundary_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context3_boundary_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_context3_lookupflag_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context3_lookupflag_f2.otf":			('GDEF','GSUB'),
        "aots/gsub_context3_next_glyph_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context3_simple_f1.otf":			('GDEF','GSUB'),
        "aots/gsub_context3_successive_f1.otf":			('GDEF','GSUB'),
        "aots/lookupflag_ignore_attach_f1.otf":			('GDEF','GSUB'),
        "aots/lookupflag_ignore_base_f1.otf":			('GDEF','GSUB'),
        "aots/lookupflag_ignore_combination_f1.otf":		('GDEF','GSUB'),
        "aots/lookupflag_ignore_ligatures_f1.otf":		('GDEF','GSUB'),
        "aots/lookupflag_ignore_marks_f1.otf":			('GDEF','GSUB'),
    ]

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @staticmethod
    def getpath(testfile):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "testdata", testfile)

    def expect_ttx(self, expected_ttx, actual_ttx, fromfile=None, tofile=None):
        expected = [l+'\n' for l in expected_ttx.split('\n')]
        actual = [l+'\n' for l in actual_ttx.split('\n')]
        if actual != expected:
            sys.stderr.write('\n')
            for line in difflib.unified_diff(
                    expected, actual, fromfile=fromfile, tofile=tofile):
                sys.stderr.write(line)
            self.fail("TTX output is different from expected")

    @classmethod
    def create_font(celf):
        font = TTFont()
        font.setGlyphOrder(celf.GLYPH_ORDER)
        return font

    def check_mti_file(self, name, tableTag=None):

        xml_expected_path = self.getpath("%s.ttx" % name + ('.'+tableTag if tableTag is not None else ''))
        with open(xml_expected_path, 'rt', encoding="utf-8") as xml_expected_file:
            xml_expected = xml_expected_file.read()

        font = self.create_font()

        with open(self.getpath("%s.txt" % name), 'rt', encoding="utf-8") as f:
            table = mtiLib.build(f, font, tableTag=tableTag)

        if tableTag is not None:
            self.assertEqual(tableTag, table.tableTag)
        tableTag = table.tableTag

        # Make sure it compiles.
        blob = table.compile(font)

        # Make sure it decompiles.
        decompiled = table.__class__()
        decompiled.decompile(blob, font)

        # XML from built object.
        writer = XMLWriter(StringIO(), newlinestr='\n')
        writer.begintag(tableTag); writer.newline()
        table.toXML(writer, font)
        writer.endtag(tableTag); writer.newline()
        xml_built = writer.file.getvalue()

        # XML from decompiled object.
        writer = XMLWriter(StringIO(), newlinestr='\n')
        writer.begintag(tableTag); writer.newline()
        decompiled.toXML(writer, font)
        writer.endtag(tableTag); writer.newline()
        xml_binary = writer.file.getvalue()

        self.expect_ttx(xml_binary,   xml_built, fromfile='decompiled',      tofile='built')
        self.expect_ttx(xml_expected, xml_built, fromfile=xml_expected_path, tofile='built')

        from fontTools.misc import xmlReader
        f = StringIO()
        f.write(xml_expected)
        f.seek(0)
        font2 = TTFont()
        font2.setGlyphOrder(font.getGlyphOrder())
        reader = xmlReader.XMLReader(f, font2)
        reader.read(rootless=True)

        # XML from object read from XML.
        writer = XMLWriter(StringIO(), newlinestr='\n')
        writer.begintag(tableTag); writer.newline()
        font2[tableTag].toXML(writer, font)
        writer.endtag(tableTag); writer.newline()
        xml_fromxml = writer.file.getvalue()

        self.expect_ttx(xml_expected, xml_fromxml, fromfile=xml_expected_path, tofile='fromxml')

def generate_mti_file_test(name, tableTag=None):
    return lambda self: self.check_mti_file(os.path.join(*name.split('/')), tableTag=tableTag)


for tableTag,tests in TablesTest.TESTS.items():
    for name in tests:
        setattr(TablesTest, "test_TablesFile_%s%s" % (name, '_'+tableTag if tableTag else ''),
                generate_mti_file_test(name, tableTag=tableTag))


if __name__ == "__main__":
    unittest.main()
