from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals

import os
import pytest
from fontTools.ttLib import TTFont
from fontTools.otlLib.maxContextCalc import maxCtxFont
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString


def test_max_ctx_calc_no_features():
    font = TTFont()
    assert maxCtxFont(font) == 0
    font.setGlyphOrder(['.notdef'])
    addOpenTypeFeaturesFromString(font, '')
    assert maxCtxFont(font) == 0


def test_max_ctx_calc_features():
    glyphs = '.notdef space A B C a b c'.split()
    features = """
    lookup GSUB_EXT useExtension {
        sub a by b;
    } GSUB_EXT;

    lookup GPOS_EXT useExtension {
        pos a b -10;
    } GPOS_EXT;

    feature sub1 {
        sub A by a;
        sub A B by b;
        sub A B C by c;
        sub [A B] C by c;
        sub [A B] C [A B] by c;
        sub A by A B;
        sub A' C by A B;
        sub a' by b;
        sub a' b by c;
        sub a from [A B C];
        rsub a by b;
        rsub a' by b;
        rsub a b' by c;
        rsub a b' c by A;
        rsub [a b] c' by A;
        rsub [a b] c' [a b] by B;
        lookup GSUB_EXT;
    } sub1;

    feature pos1 {
        pos A 20;
        pos A B -50;
        pos A B' 10 C;
        lookup GPOS_EXT;
    } pos1;
    """
    font = TTFont()
    font.setGlyphOrder(glyphs)
    addOpenTypeFeaturesFromString(font, features)

    assert maxCtxFont(font) == 3


@pytest.mark.parametrize('file_name, max_context', [
    ('gsub_51', 2),
    ('gsub_52', 2),
    ('gsub_71', 1),
    ('gpos_91', 1),
])
def test_max_ctx_calc_features_ttx(file_name, max_context):
    ttx_path = os.path.join(os.path.dirname(__file__),
                            'data', '{}.ttx'.format(file_name))
    font = TTFont()
    font.importXML(ttx_path)

    assert maxCtxFont(font) == max_context
