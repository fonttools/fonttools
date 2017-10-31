from __future__ import print_function, division, absolute_import
import os

from fontTools.misc.loggingTools import CapturingLogHandler
from defcon import Font, Glyph
from cu2qu.ufo import (
    fonts_to_quadratic,
    font_to_quadratic,
    glyphs_to_quadratic,
    glyph_to_quadratic,
    logger,
    IncompatibleGlyphsError
)

from . import DATADIR
import pytest


TEST_UFOS = [
    os.path.join(DATADIR, "RobotoSubset-Regular.ufo"),
    os.path.join(DATADIR, "RobotoSubset-Bold.ufo"),
]


@pytest.fixture
def fonts():
    return [Font(ufo) for ufo in TEST_UFOS]


class FontsToQuadraticTest(object):

    def test_modified(self, fonts):
        modified = fonts_to_quadratic(fonts)
        assert modified

    def test_stats(self, fonts):
        stats = {}
        fonts_to_quadratic(fonts, stats=stats)
        assert stats == {'1': 1, '2': 79, '3': 130, '4': 2}

    def test_dump_stats(self, fonts):
        with CapturingLogHandler(logger, "INFO") as captor:
            fonts_to_quadratic(fonts, dump_stats=True)
        assert captor.assertRegex("New spline lengths:")

    def test_different_glyphsets(self, fonts):
        del fonts[0]['a']
        assert 'a' not in fonts[0]
        assert 'a' in fonts[1]
        assert fonts_to_quadratic(fonts)

    def test_max_err_em_float(self, fonts):
        stats = {}
        fonts_to_quadratic(fonts, max_err_em=0.002, stats=stats)
        assert stats == {'1': 5, '2': 193, '3': 14}

    def test_max_err_em_list(self, fonts):
        stats = {}
        fonts_to_quadratic(fonts, max_err_em=[0.002, 0.002], stats=stats)
        assert stats == {'1': 5, '2': 193, '3': 14}

    def test_max_err_float(self, fonts):
        stats = {}
        fonts_to_quadratic(fonts, max_err=4.096, stats=stats)
        assert stats == {'1': 5, '2': 193, '3': 14}

    def test_max_err_list(self, fonts):
        stats = {}
        fonts_to_quadratic(fonts, max_err=[4.096, 4.096], stats=stats)
        assert stats == {'1': 5, '2': 193, '3': 14}

    def test_both_max_err_and_max_err_em(self, fonts):
        with pytest.raises(TypeError, match="Only one .* can be specified"):
            fonts_to_quadratic(fonts, max_err=1.000, max_err_em=0.001)

    def test_single_font(self, fonts):
        assert font_to_quadratic(fonts[0], max_err_em=0.002,
                                 reverse_direction=True)


class GlyphsToQuadraticTest(object):

    @pytest.mark.parametrize(
        ["glyph", "expected"],
        [('A', False),  # contains no curves, it is not modified
         ('a', True)],
        ids=['lines-only', 'has-curves']
    )
    def test_modified(self, fonts, glyph, expected):
        glyphs = [f[glyph] for f in fonts]
        assert glyphs_to_quadratic(glyphs) == expected

    def test_stats(self, fonts):
        stats = {}
        glyphs_to_quadratic([f['a'] for f in fonts], stats=stats)
        assert stats == {'2': 1, '3': 7, '4': 3, '5': 1}

    def test_max_err_float(self, fonts):
        glyphs = [f['a'] for f in fonts]
        stats = {}
        glyphs_to_quadratic(glyphs, max_err=4.096, stats=stats)
        assert stats == {'2': 11, '3': 1}

    def test_max_err_list(self, fonts):
        glyphs = [f['a'] for f in fonts]
        stats = {}
        glyphs_to_quadratic(glyphs, max_err=[4.096, 4.096], stats=stats)
        assert stats == {'2': 11, '3': 1}

    def test_reverse_direction(self, fonts):
        glyphs = [f['A'] for f in fonts]
        assert glyphs_to_quadratic(glyphs, reverse_direction=True)

    def test_single_glyph(self, fonts):
        assert glyph_to_quadratic(fonts[0]['a'], max_err=4.096,
                                  reverse_direction=True)

    @pytest.mark.parametrize(
        "outlines",
        [
            [
                [
                    ('moveTo', ((0, 0),)),
                    ('curveTo', ((1, 1), (2, 2), (3, 3))),
                    ('curveTo', ((4, 4), (5, 5), (6, 6))),
                    ('closePath', ()),
                ],
                [
                    ('moveTo', ((7, 7),)),
                    ('curveTo', ((8, 8), (9, 9), (10, 10))),
                    ('closePath', ()),
                ]
            ],
            [
                [
                    ('moveTo', ((0, 0),)),
                    ('curveTo', ((1, 1), (2, 2), (3, 3))),
                    ('closePath', ()),
                ],
                [
                    ('moveTo', ((4, 4),)),
                    ('lineTo', ((5, 5),)),
                    ('closePath', ()),
                ],
            ]
        ],
        ids=[
            "unequal-length",
            "different-segment-types",
        ]
    )
    def test_incompatible(self, outlines):
        glyphs = []
        for i, outline in enumerate(outlines):
            glyph = Glyph()
            glyph.name = "glyph%d" % i
            pen = glyph.getPen()
            for operator, args in outline:
                getattr(pen, operator)(*args)
            glyphs.append(glyph)
        with pytest.raises(IncompatibleGlyphsError) as excinfo:
            glyphs_to_quadratic(glyphs)
        assert excinfo.match("^'glyph[0-9]+'(, 'glyph[0-9]+')*$")

    def test_already_quadratic(self):
        glyph = Glyph()
        pen = glyph.getPen()
        pen.moveTo((0, 0))
        pen.qCurveTo((1, 1), (2, 2))
        pen.closePath()
        assert not glyph_to_quadratic(glyph)

    def test_open_paths(self):
        glyph = Glyph()
        pen = glyph.getPen()
        pen.moveTo((0, 0))
        pen.lineTo((1, 1))
        pen.curveTo((2, 2), (3, 3), (4, 4))
        pen.endPath()
        assert glyph_to_quadratic(glyph)
        # open contour is still open
        assert glyph[-1][0].segmentType == "move"

    def test_ignore_components(self):
        glyph = Glyph()
        pen = glyph.getPen()
        pen.addComponent('a', (1, 0, 0, 1, 0, 0))
        pen.moveTo((0, 0))
        pen.curveTo((1, 1), (2, 2), (3, 3))
        pen.closePath()
        assert glyph_to_quadratic(glyph)
        assert len(glyph.components) == 1
