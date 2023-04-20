from fontTools.ttLib import TTFont, tagToXML
from io import StringIO
import os
import sys
import re
import contextlib
import pytest

try:
    import unicodedata2
except ImportError:
    if sys.version_info[:2] < (3, 6):
        unicodedata2 = None
    else:
        # on 3.6 the built-in unicodedata is the same as unicodedata2 backport
        import unicodedata

        unicodedata2 = unicodedata


# Font files in data/*.{o,t}tf; output gets compared to data/*.ttx.*
TESTS = {
    "aots/base.otf": (
        "CFF ",
        "cmap",
        "head",
        "hhea",
        "hmtx",
        "maxp",
        "name",
        "OS/2",
        "post",
    ),
    "aots/classdef1_font1.otf": ("GSUB",),
    "aots/classdef1_font2.otf": ("GSUB",),
    "aots/classdef1_font3.otf": ("GSUB",),
    "aots/classdef1_font4.otf": ("GSUB",),
    "aots/classdef2_font1.otf": ("GSUB",),
    "aots/classdef2_font2.otf": ("GSUB",),
    "aots/classdef2_font3.otf": ("GSUB",),
    "aots/classdef2_font4.otf": ("GSUB",),
    "aots/cmap0_font1.otf": ("cmap",),
    "aots/cmap10_font1.otf": ("cmap",),
    "aots/cmap10_font2.otf": ("cmap",),
    "aots/cmap12_font1.otf": ("cmap",),
    "aots/cmap14_font1.otf": ("cmap",),
    "aots/cmap2_font1.otf": ("cmap",),
    "aots/cmap4_font1.otf": ("cmap",),
    "aots/cmap4_font2.otf": ("cmap",),
    "aots/cmap4_font3.otf": ("cmap",),
    "aots/cmap4_font4.otf": ("cmap",),
    "aots/cmap6_font1.otf": ("cmap",),
    "aots/cmap6_font2.otf": ("cmap",),
    "aots/cmap8_font1.otf": ("cmap",),
    "aots/cmap_composition_font1.otf": ("cmap",),
    "aots/cmap_subtableselection_font1.otf": ("cmap",),
    "aots/cmap_subtableselection_font2.otf": ("cmap",),
    "aots/cmap_subtableselection_font3.otf": ("cmap",),
    "aots/cmap_subtableselection_font4.otf": ("cmap",),
    "aots/cmap_subtableselection_font5.otf": ("cmap",),
    "aots/gpos1_1_lookupflag_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos1_1_simple_f1.otf": ("GPOS",),
    "aots/gpos1_1_simple_f2.otf": ("GPOS",),
    "aots/gpos1_1_simple_f3.otf": ("GPOS",),
    "aots/gpos1_1_simple_f4.otf": ("GPOS",),
    "aots/gpos1_2_font1.otf": ("GPOS",),
    "aots/gpos1_2_font2.otf": ("GDEF", "GPOS"),
    "aots/gpos2_1_font6.otf": ("GPOS",),
    "aots/gpos2_1_font7.otf": ("GPOS",),
    "aots/gpos2_1_lookupflag_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos2_1_lookupflag_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos2_1_next_glyph_f1.otf": ("GPOS",),
    "aots/gpos2_1_next_glyph_f2.otf": ("GPOS",),
    "aots/gpos2_1_simple_f1.otf": ("GPOS",),
    "aots/gpos2_2_font1.otf": ("GPOS",),
    "aots/gpos2_2_font2.otf": ("GDEF", "GPOS"),
    "aots/gpos2_2_font3.otf": ("GDEF", "GPOS"),
    "aots/gpos2_2_font4.otf": ("GPOS",),
    "aots/gpos2_2_font5.otf": ("GPOS",),
    "aots/gpos3_font1.otf": ("GPOS",),
    "aots/gpos3_font2.otf": ("GDEF", "GPOS"),
    "aots/gpos3_font3.otf": ("GDEF", "GPOS"),
    "aots/gpos4_lookupflag_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos4_lookupflag_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos4_multiple_anchors_1.otf": ("GDEF", "GPOS"),
    "aots/gpos4_simple_1.otf": ("GDEF", "GPOS"),
    "aots/gpos5_font1.otf": ("GDEF", "GPOS", "GSUB"),
    "aots/gpos6_font1.otf": ("GDEF", "GPOS"),
    "aots/gpos7_1_font1.otf": ("GPOS",),
    "aots/gpos9_font1.otf": ("GPOS",),
    "aots/gpos9_font2.otf": ("GPOS",),
    "aots/gpos_chaining1_boundary_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining1_boundary_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining1_boundary_f3.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining1_boundary_f4.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining1_lookupflag_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining1_multiple_subrules_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining1_multiple_subrules_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining1_next_glyph_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining1_simple_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining1_simple_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining1_successive_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining2_boundary_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining2_boundary_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining2_boundary_f3.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining2_boundary_f4.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining2_lookupflag_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining2_multiple_subrules_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining2_multiple_subrules_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining2_next_glyph_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining2_simple_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining2_simple_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining2_successive_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining3_boundary_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining3_boundary_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining3_boundary_f3.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining3_boundary_f4.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining3_lookupflag_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining3_next_glyph_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining3_simple_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining3_simple_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_chaining3_successive_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context1_boundary_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context1_boundary_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_context1_expansion_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context1_lookupflag_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context1_lookupflag_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_context1_multiple_subrules_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context1_multiple_subrules_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_context1_next_glyph_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context1_simple_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context1_simple_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_context1_successive_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_boundary_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_boundary_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_classes_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_classes_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_expansion_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_lookupflag_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_lookupflag_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_multiple_subrules_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_multiple_subrules_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_next_glyph_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_simple_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_simple_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_context2_successive_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context3_boundary_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context3_boundary_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_context3_lookupflag_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context3_lookupflag_f2.otf": ("GDEF", "GPOS"),
    "aots/gpos_context3_next_glyph_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context3_simple_f1.otf": ("GDEF", "GPOS"),
    "aots/gpos_context3_successive_f1.otf": ("GDEF", "GPOS"),
    "aots/gsub1_1_lookupflag_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub1_1_modulo_f1.otf": ("GSUB",),
    "aots/gsub1_1_simple_f1.otf": ("GSUB",),
    "aots/gsub1_2_lookupflag_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub1_2_simple_f1.otf": ("GSUB",),
    "aots/gsub2_1_lookupflag_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub2_1_multiple_sequences_f1.otf": ("GSUB",),
    "aots/gsub2_1_simple_f1.otf": ("GSUB",),
    "aots/gsub3_1_lookupflag_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub3_1_multiple_f1.otf": ("GSUB",),
    "aots/gsub3_1_simple_f1.otf": ("GSUB",),
    "aots/gsub4_1_lookupflag_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub4_1_multiple_ligatures_f1.otf": ("GSUB",),
    "aots/gsub4_1_multiple_ligatures_f2.otf": ("GSUB",),
    "aots/gsub4_1_multiple_ligsets_f1.otf": ("GSUB",),
    "aots/gsub4_1_simple_f1.otf": ("GSUB",),
    "aots/gsub7_font1.otf": ("GSUB",),
    "aots/gsub7_font2.otf": ("GSUB",),
    "aots/gsub_chaining1_boundary_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining1_boundary_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining1_boundary_f3.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining1_boundary_f4.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining1_lookupflag_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining1_multiple_subrules_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining1_multiple_subrules_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining1_next_glyph_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining1_simple_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining1_simple_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining1_successive_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining2_boundary_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining2_boundary_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining2_boundary_f3.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining2_boundary_f4.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining2_lookupflag_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining2_multiple_subrules_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining2_multiple_subrules_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining2_next_glyph_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining2_simple_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining2_simple_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining2_successive_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining3_boundary_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining3_boundary_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining3_boundary_f3.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining3_boundary_f4.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining3_lookupflag_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining3_next_glyph_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining3_simple_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining3_simple_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_chaining3_successive_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context1_boundary_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context1_boundary_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_context1_expansion_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context1_lookupflag_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context1_lookupflag_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_context1_multiple_subrules_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context1_multiple_subrules_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_context1_next_glyph_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context1_simple_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context1_simple_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_context1_successive_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_boundary_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_boundary_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_classes_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_classes_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_expansion_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_lookupflag_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_lookupflag_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_multiple_subrules_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_multiple_subrules_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_next_glyph_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_simple_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_simple_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_context2_successive_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context3_boundary_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context3_boundary_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_context3_lookupflag_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context3_lookupflag_f2.otf": ("GDEF", "GSUB"),
    "aots/gsub_context3_next_glyph_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context3_simple_f1.otf": ("GDEF", "GSUB"),
    "aots/gsub_context3_successive_f1.otf": ("GDEF", "GSUB"),
    "aots/lookupflag_ignore_attach_f1.otf": ("GDEF", "GSUB"),
    "aots/lookupflag_ignore_base_f1.otf": ("GDEF", "GSUB"),
    "aots/lookupflag_ignore_combination_f1.otf": ("GDEF", "GSUB"),
    "aots/lookupflag_ignore_ligatures_f1.otf": ("GDEF", "GSUB"),
    "aots/lookupflag_ignore_marks_f1.otf": ("GDEF", "GSUB"),
    "graphite/graphite_tests.ttf": ("Silf", "Glat", "Feat", "Sill"),
}


TEST_REQUIREMENTS = {
    "aots/cmap4_font4.otf": ("unicodedata2",),
}


ttLibVersion_RE = re.compile(r' ttLibVersion=".*"')


def getpath(testfile):
    path = os.path.dirname(__file__)
    return os.path.join(path, "data", testfile)


def read_expected_ttx(testfile, tableTag):
    name = os.path.splitext(testfile)[0]
    xml_expected_path = getpath("%s.ttx.%s" % (name, tagToXML(tableTag)))
    with open(xml_expected_path, "r", encoding="utf-8") as xml_file:
        xml_expected = ttLibVersion_RE.sub("", xml_file.read())
    return xml_expected


def dump_ttx(font, tableTag):
    f = StringIO()
    font.saveXML(f, tables=[tableTag])
    return ttLibVersion_RE.sub("", f.getvalue())


def load_ttx(ttx):
    f = StringIO()
    f.write(ttx)
    f.seek(0)
    font = TTFont()
    font.importXML(f)
    return font


@contextlib.contextmanager
def open_font(testfile):
    font = TTFont(getpath(testfile))
    try:
        yield font
    finally:
        font.close()


def _skip_if_requirement_missing(testfile):
    if testfile in TEST_REQUIREMENTS:
        for req in TEST_REQUIREMENTS[testfile]:
            if globals()[req] is None:
                pytest.skip("%s not installed" % req)


def test_xml_from_binary(testfile, tableTag):
    """Check XML from decompiled object."""
    _skip_if_requirement_missing(testfile)

    xml_expected = read_expected_ttx(testfile, tableTag)

    with open_font(testfile) as font:
        xml_from_binary = dump_ttx(font, tableTag)

    assert xml_expected == xml_from_binary


def test_xml_from_xml(testfile, tableTag):
    """Check XML from object read from XML."""
    _skip_if_requirement_missing(testfile)

    xml_expected = read_expected_ttx(testfile, tableTag)

    font = load_ttx(xml_expected)
    name = os.path.splitext(testfile)[0]
    setupfile = getpath("%s.ttx.%s.setup" % (name, tagToXML(tableTag)))
    if os.path.exists(setupfile):
        #        import pdb; pdb.set_trace()
        font.importXML(setupfile)
    xml_from_xml = dump_ttx(font, tableTag)

    assert xml_expected == xml_from_xml


def pytest_generate_tests(metafunc):
    # http://doc.pytest.org/en/latest/parametrize.html#basic-pytest-generate-tests-example
    fixturenames = metafunc.fixturenames
    argnames = ("testfile", "tableTag")
    if all(fn in fixturenames for fn in argnames):
        argvalues = [
            (testfile, tableTag)
            for testfile, tableTags in sorted(TESTS.items())
            for tableTag in tableTags
        ]
        metafunc.parametrize(argnames, argvalues)


if __name__ == "__main__":
    sys.exit(pytest.main(sys.argv))
