import logging
from types import MappingProxyType

from fontTools.pens.basePen import MissingComponentError
from fontTools.pens.filterPen import (
    DecomposingFilterPen,
    DecomposingFilterPointPen,
    FilterPointPen,
    OnCurveFirstPointPen,
)
from fontTools.pens.pointPen import PointToSegmentPen, ReverseFlipped
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


def test_filter_point_pen_positional_identifier():
    rec = RecordingPointPen()
    pen = FilterPointPen(rec)

    pen.beginPath("glyph1")
    pen.addPoint((0, 0), "line", False, None, "pt1")
    pen.endPath()

    assert rec.value == [
        ("beginPath", (), {"identifier": "glyph1"}),
        ("addPoint", ((0, 0), "line", False, None), {"identifier": "pt1"}),
        ("endPath", (), {}),
    ]


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


class TestOnCurveFirstPointPen:
    def test_closed_contour_starting_with_offcurve(self):
        """Test that a closed contour starting with an off-curve point gets rotated."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        # Draw a "closed" (not starting with 'move') contour, starting with off-curve
        pen.beginPath()
        pen.addPoint((0, 0), None)
        pen.addPoint((100, 100), "line")  # first on-curve, should become start
        pen.addPoint((200, 0), None)
        pen.addPoint((300, 100), "curve")
        pen.endPath()

        assert rec.value == [
            ("beginPath", (), {}),
            ("addPoint", ((100, 100), "line", False, None), {}),
            ("addPoint", ((200, 0), None, False, None), {}),
            ("addPoint", ((300, 100), "curve", False, None), {}),
            ("addPoint", ((0, 0), None, False, None), {}),
            ("endPath", (), {}),
        ]

    def test_closed_contour_already_starting_with_oncurve(self):
        """Test that a closed contour already starting with on-curve passes through
        unchanged."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        pen.beginPath()
        pen.addPoint((100, 100), "line")
        pen.addPoint((200, 0), None)
        pen.addPoint((300, 100), "curve")
        pen.endPath()

        assert rec.value == [
            ("beginPath", (), {}),
            ("addPoint", ((100, 100), "line", False, None), {}),
            ("addPoint", ((200, 0), None, False, None), {}),
            ("addPoint", ((300, 100), "curve", False, None), {}),
            ("endPath", (), {}),
        ]

    def test_open_contour(self):
        """Test that open contours pass through unchanged."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        # "Open" contour starts with "move"
        pen.beginPath()
        pen.addPoint((0, 0), "move")
        pen.addPoint((100, 100), "line")
        pen.addPoint((200, 200), "curve")
        pen.endPath()

        assert rec.value == [
            ("beginPath", (), {}),
            ("addPoint", ((0, 0), "move", False, None), {}),
            ("addPoint", ((100, 100), "line", False, None), {}),
            ("addPoint", ((200, 200), "curve", False, None), {}),
            ("endPath", (), {}),
        ]

    def test_all_offcurve_points(self):
        """Test contour with all off-curve points (TrueType special case)
        passes through unchanged."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        pen.beginPath()
        pen.addPoint((0, 0), None)
        pen.addPoint((100, 100), None)
        pen.addPoint((200, 0), None)
        pen.endPath()

        # there's no on-curve to rotate to
        assert rec.value == [
            ("beginPath", (), {}),
            ("addPoint", ((0, 0), None, False, None), {}),
            ("addPoint", ((100, 100), None, False, None), {}),
            ("addPoint", ((200, 0), None, False, None), {}),
            ("endPath", (), {}),
        ]

    def test_components_pass_through(self):
        """Test that components pass through unchanged."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        pen.addComponent("a", (1, 0, 0, 1, 10, 20))

        assert rec.value == [
            ("addComponent", ("a", (1, 0, 0, 1, 10, 20)), {}),
        ]

    def test_positional_identifier(self):
        """Test that positional identifier arguments are forwarded."""
        rec = RecordingPointPen()
        pen = OnCurveFirstPointPen(rec)

        pen.beginPath("path1")
        pen.addPoint((0, 0), "move", False, None, "start")
        pen.addPoint((100, 100), "line", False, None, "line-id")
        pen.endPath()

        assert rec.value == [
            ("beginPath", (), {"identifier": "path1"}),
            ("addPoint", ((0, 0), "move", False, None), {"identifier": "start"}),
            ("addPoint", ((100, 100), "line", False, None), {"identifier": "line-id"}),
            ("endPath", (), {}),
        ]


class SimpleGlyphStartingWithOffCurve:
    def drawPoints(self, pen):
        pen.beginPath()
        pen.addPoint((0, 0), None)
        pen.addPoint((50, 50), None)
        pen.addPoint((100, 0), "qcurve")
        pen.addPoint((50, -50), None)
        pen.endPath()


@pytest.mark.parametrize(
    "reverseFlipped", [True, ReverseFlipped.KEEP_START, "keep_start"]
)
def test_decomposing_filter_point_pen_reverse_flipped_keep_start(reverseFlipped):
    """Test DecomposingFilterPointPen with reverseFlipped='keep_start' enum value"""
    from fontTools.pens.filterPen import DecomposingFilterPointPen
    from fontTools.pens.recordingPen import RecordingPointPen

    glyphSet = {"base": SimpleGlyphStartingWithOffCurve()}

    rec = RecordingPointPen()
    fpen = DecomposingFilterPointPen(rec, glyphSet, reverseFlipped=reverseFlipped)
    # Add a flipped component (negative determinant)
    fpen.addComponent("base", (-1, 0, 0, 1, 200, 0))

    # The contour should be reversed but still start with off-curve (segmentType=None)
    assert len(rec.value) == 6  # beginPath + 4 points + endPath
    assert rec.value[0][0] == "beginPath"
    first_point = rec.value[1]
    assert first_point[0] == "addPoint"
    assert first_point[1][:2] == ((200, 0), None)


@pytest.mark.parametrize(
    "reverseFlipped", [ReverseFlipped.ON_CURVE_FIRST, "on_curve_first"]
)
def test_decomposing_filter_point_pen_reverse_flipped_on_curve_first(reverseFlipped):
    """Test DecomposingFilterPointPen with reverseFlipped='on_curve_first' enum value"""
    from fontTools.pens.filterPen import DecomposingFilterPointPen
    from fontTools.pens.recordingPen import RecordingPointPen

    glyphSet = {"base": SimpleGlyphStartingWithOffCurve()}

    rec = RecordingPointPen()
    fpen = DecomposingFilterPointPen(rec, glyphSet, reverseFlipped=reverseFlipped)
    # Add a flipped component (negative determinant)
    fpen.addComponent("base", (-1, 0, 0, 1, 200, 0))

    # The contour should be reversed AND rotated to start with on-curve
    assert len(rec.value) == 6  # beginPath + 4 points + endPath
    assert rec.value[0][0] == "beginPath"
    # First point should now be on-curve
    first_point = rec.value[1]
    assert first_point[0] == "addPoint"
    assert first_point[1][:2] == ((100, 0), "qcurve")


@pytest.mark.parametrize("reverseFlipped", [False, ReverseFlipped.NO, "no"])
def test_decomposing_filter_point_pen_reverse_flipped_no(reverseFlipped):
    """Test DecomposingFilterPointPen with reverseFlipped='no' enum value"""
    from fontTools.pens.filterPen import DecomposingFilterPointPen
    from fontTools.pens.recordingPen import RecordingPointPen

    glyphSet = {"base": SimpleGlyphStartingWithOffCurve()}

    rec = RecordingPointPen()
    fpen = DecomposingFilterPointPen(rec, glyphSet, reverseFlipped=reverseFlipped)
    # Add a flipped component (negative determinant)
    fpen.addComponent("base", (-1, 0, 0, 1, 200, 0))

    # Should not be reversed, so should start with first off-curve but NOT reversed
    assert len(rec.value) == 6
    assert rec.value[0][0] == "beginPath"
    # Check that it's NOT reversed - the points should be transformed but in original order
    first_point = rec.value[1]
    assert first_point[0] == "addPoint"
    assert first_point[1][:2] == ((200, 0), None)
