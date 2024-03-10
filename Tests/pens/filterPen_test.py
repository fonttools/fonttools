import logging
from types import MappingProxyType

from fontTools.pens.basePen import MissingComponentError
from fontTools.pens.filterPen import DecomposingFilterPen, DecomposingFilterPointPen
from fontTools.pens.pointPen import PointToSegmentPen
from fontTools.pens.recordingPen import RecordingPen, RecordingPointPen

import pytest


class SimpleGlyph:
    def draw(self, pen):
        pen.moveTo((0, 0))
        pen.curveTo((1, 1), (2, 2), (3, 3))
        pen.closePath()

    def drawPoints(self, pen):
        pen.beginPath()
        pen.addPoint((0, 0), "line")
        pen.addPoint((1, 1))
        pen.addPoint((2, 2))
        pen.addPoint((3, 3), "curve")
        pen.endPath()


class CompositeGlyph:
    def draw(self, pen):
        pen.addComponent("simple_glyph", (1, 0, 0, 1, -1, 1))

    def drawPoints(self, pen):
        self.draw(pen)


class MissingComponent(CompositeGlyph):
    def draw(self, pen):
        pen.addComponent("foobar", (1, 0, 0, 1, 0, 0))


class FlippedComponent(CompositeGlyph):
    def draw(self, pen):
        pen.addComponent("simple_glyph", (1, 0, 0, 1, 0, 0))
        pen.addComponent("composite_glyph", (-1, 0, 0, 1, 0, 0))


GLYPHSET = MappingProxyType(
    {
        "simple_glyph": SimpleGlyph(),
        "composite_glyph": CompositeGlyph(),
        "missing_component": MissingComponent(),
        "flipped_component": FlippedComponent(),
    }
)


def _is_point_pen(pen):
    return hasattr(pen, "addPoint")


def _draw(glyph, pen):
    if _is_point_pen(pen):
        # point pen
        glyph.drawPoints(pen)
    else:
        # segment pen
        glyph.draw(pen)


@pytest.fixture(params=[DecomposingFilterPen, DecomposingFilterPointPen])
def FilterPen(request):
    return request.param


def _init_rec_and_filter_pens(FilterPenClass, *args, **kwargs):
    rec = out = RecordingPen()
    if _is_point_pen(FilterPenClass):
        out = PointToSegmentPen(rec)
    fpen = FilterPenClass(out, GLYPHSET, *args, **kwargs)
    return rec, fpen


@pytest.mark.parametrize(
    "glyph_name, expected",
    [
        (
            "simple_glyph",
            [
                ("moveTo", ((0, 0),)),
                ("curveTo", ((1, 1), (2, 2), (3, 3))),
                ("closePath", ()),
            ],
        ),
        (
            "composite_glyph",
            [
                ("moveTo", ((-1, 1),)),
                ("curveTo", ((0, 2), (1, 3), (2, 4))),
                ("closePath", ()),
            ],
        ),
        ("missing_component", MissingComponentError),
        (
            "flipped_component",
            [
                ("moveTo", ((0, 0),)),
                ("curveTo", ((1, 1), (2, 2), (3, 3))),
                ("closePath", ()),
                ("moveTo", ((1, 1),)),
                ("curveTo", ((0, 2), (-1, 3), (-2, 4))),
                ("closePath", ()),
            ],
        ),
    ],
)
def test_decomposing_filter_pen(FilterPen, glyph_name, expected):
    rec, fpen = _init_rec_and_filter_pens(FilterPen)
    glyph = GLYPHSET[glyph_name]
    try:
        _draw(glyph, fpen)
    except Exception as e:
        assert isinstance(e, expected)
    else:
        assert rec.value == expected


def test_decomposing_filter_pen_skip_missing(FilterPen, caplog):
    rec, fpen = _init_rec_and_filter_pens(FilterPen, skipMissingComponents=True)
    glyph = GLYPHSET["missing_component"]
    with caplog.at_level(logging.WARNING, logger="fontTools.pens.filterPen"):
        _draw(glyph, fpen)
    assert rec.value == []
    assert "glyph 'foobar' is missing from glyphSet; skipped" in caplog.text


def test_decomposing_filter_pen_reverse_flipped(FilterPen):
    rec, fpen = _init_rec_and_filter_pens(FilterPen, reverseFlipped=True)
    glyph = GLYPHSET["flipped_component"]
    _draw(glyph, fpen)
    assert rec.value == [
        ("moveTo", ((0, 0),)),
        ("curveTo", ((1, 1), (2, 2), (3, 3))),
        ("closePath", ()),
        ("moveTo", ((1, 1),)),
        ("lineTo", ((-2, 4),)),
        ("curveTo", ((-1, 3), (0, 2), (1, 1))),
        ("closePath", ()),
    ]


@pytest.mark.parametrize(
    "decomposeNested, expected",
    [
        (
            True,
            [
                ("addComponent", ("simple_glyph", (1, 0, 0, 1, 0, 0))),
                ("moveTo", ((1, 1),)),
                ("curveTo", ((0, 2), (-1, 3), (-2, 4))),
                ("closePath", ()),
            ],
        ),
        (
            False,
            [
                ("addComponent", ("simple_glyph", (1, 0, 0, 1, 0, 0))),
                ("addComponent", ("simple_glyph", (-1, 0, 0, 1, 1, 1))),
            ],
        ),
    ],
)
def test_decomposing_filter_pen_include_decomposeNested(
    FilterPen, decomposeNested, expected
):
    rec, fpen = _init_rec_and_filter_pens(
        FilterPen, include={"composite_glyph"}, decomposeNested=decomposeNested
    )
    glyph = GLYPHSET["flipped_component"]
    _draw(glyph, fpen)
    assert rec.value == expected
