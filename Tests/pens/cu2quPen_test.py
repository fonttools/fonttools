# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import unittest

from fontTools.pens.cu2quPen import Cu2QuPen, Cu2QuPointPen, Cu2QuMultiPen
from fontTools.pens.recordingPen import RecordingPen, RecordingPointPen
from fontTools.misc.loggingTools import CapturingLogHandler
from textwrap import dedent
import logging
import pytest

try:
    from .utils import CUBIC_GLYPHS, QUAD_GLYPHS
    from .utils import DummyGlyph, DummyPointGlyph
    from .utils import DummyPen, DummyPointPen
except ImportError as e:
    pytest.skip(str(e), allow_module_level=True)


MAX_ERR = 1.0


class _TestPenMixin(object):
    """Collection of tests that are shared by both the SegmentPen and the
    PointPen test cases, plus some helper methods.
    """

    maxDiff = None

    def diff(self, expected, actual):
        import difflib

        expected = str(self.Glyph(expected)).splitlines(True)
        actual = str(self.Glyph(actual)).splitlines(True)
        diff = difflib.unified_diff(
            expected, actual, fromfile="expected", tofile="actual"
        )
        return "".join(diff)

    def convert_glyph(self, glyph, **kwargs):
        # draw source glyph onto a new glyph using a Cu2Qu pen and return it
        converted = self.Glyph()
        pen = getattr(converted, self.pen_getter_name)()
        quadpen = self.Cu2QuPen(pen, MAX_ERR, **kwargs)
        getattr(glyph, self.draw_method_name)(quadpen)
        return converted

    def expect_glyph(self, source, expected):
        converted = self.convert_glyph(source)
        self.assertNotEqual(converted, source)
        if not converted.approx(expected):
            print(self.diff(expected, converted))
            self.fail("converted glyph is different from expected")

    def test_convert_simple_glyph(self):
        self.expect_glyph(CUBIC_GLYPHS["a"], QUAD_GLYPHS["a"])
        self.expect_glyph(CUBIC_GLYPHS["A"], QUAD_GLYPHS["A"])

    def test_convert_composite_glyph(self):
        source = CUBIC_GLYPHS["Aacute"]
        converted = self.convert_glyph(source)
        # components don't change after quadratic conversion
        self.assertEqual(converted, source)

    def test_convert_mixed_glyph(self):
        # this contains a mix of contours and components
        self.expect_glyph(CUBIC_GLYPHS["Eacute"], QUAD_GLYPHS["Eacute"])

    def test_reverse_direction(self):
        for name in ("a", "A", "Eacute"):
            source = CUBIC_GLYPHS[name]
            normal_glyph = self.convert_glyph(source)
            reversed_glyph = self.convert_glyph(source, reverse_direction=True)

            # the number of commands is the same, just their order is iverted
            self.assertTrue(len(normal_glyph.outline), len(reversed_glyph.outline))
            self.assertNotEqual(normal_glyph, reversed_glyph)

    def test_stats(self):
        stats = {}
        for name in CUBIC_GLYPHS.keys():
            source = CUBIC_GLYPHS[name]
            self.convert_glyph(source, stats=stats)

        self.assertTrue(stats)
        self.assertTrue("1" in stats)
        self.assertEqual(type(stats["1"]), int)

    def test_addComponent(self):
        pen = self.Pen()
        quadpen = self.Cu2QuPen(pen, MAX_ERR)
        quadpen.addComponent("a", (1, 2, 3, 4, 5.0, 6.0))

        # components are passed through without changes
        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.addComponent('a', (1, 2, 3, 4, 5.0, 6.0))",
            ],
        )


class TestCu2QuPen(unittest.TestCase, _TestPenMixin):
    def __init__(self, *args, **kwargs):
        super(TestCu2QuPen, self).__init__(*args, **kwargs)
        self.Glyph = DummyGlyph
        self.Pen = DummyPen
        self.Cu2QuPen = Cu2QuPen
        self.pen_getter_name = "getPen"
        self.draw_method_name = "draw"

    def test_qCurveTo_1_point(self):
        pen = DummyPen()
        quadpen = Cu2QuPen(pen, MAX_ERR)
        quadpen.moveTo((0, 0))
        quadpen.qCurveTo((1, 1))

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.qCurveTo((1, 1))",
            ],
        )

    def test_qCurveTo_more_than_1_point(self):
        pen = DummyPen()
        quadpen = Cu2QuPen(pen, MAX_ERR)
        quadpen.moveTo((0, 0))
        quadpen.qCurveTo((1, 1), (2, 2))

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.qCurveTo((1, 1), (2, 2))",
            ],
        )

    def test_curveTo_1_point(self):
        pen = DummyPen()
        quadpen = Cu2QuPen(pen, MAX_ERR)
        quadpen.moveTo((0, 0))
        quadpen.curveTo((1, 1))

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.qCurveTo((1, 1))",
            ],
        )

    def test_curveTo_2_points(self):
        pen = DummyPen()
        quadpen = Cu2QuPen(pen, MAX_ERR)
        quadpen.moveTo((0, 0))
        quadpen.curveTo((1, 1), (2, 2))

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.qCurveTo((1, 1), (2, 2))",
            ],
        )

    def test_curveTo_3_points(self):
        pen = DummyPen()
        quadpen = Cu2QuPen(pen, MAX_ERR)
        quadpen.moveTo((0, 0))
        quadpen.curveTo((1, 1), (2, 2), (3, 3))

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.qCurveTo((0.75, 0.75), (2.25, 2.25), (3, 3))",
            ],
        )

    def test_curveTo_more_than_3_points(self):
        # a 'SuperBezier' as described in fontTools.basePen.AbstractPen
        pen = DummyPen()
        quadpen = Cu2QuPen(pen, MAX_ERR)
        quadpen.moveTo((0, 0))
        quadpen.curveTo((1, 1), (2, 2), (3, 3), (4, 4))

        self.assertEqual(
            str(pen).splitlines(),
            [
                "pen.moveTo((0, 0))",
                "pen.qCurveTo((0.75, 0.75), (1.625, 1.625), (2, 2))",
                "pen.qCurveTo((2.375, 2.375), (3.25, 3.25), (4, 4))",
            ],
        )


class TestCu2QuPointPen(unittest.TestCase, _TestPenMixin):
    def __init__(self, *args, **kwargs):
        super(TestCu2QuPointPen, self).__init__(*args, **kwargs)
        self.Glyph = DummyPointGlyph
        self.Pen = DummyPointPen
        self.Cu2QuPen = Cu2QuPointPen
        self.pen_getter_name = "getPointPen"
        self.draw_method_name = "drawPoints"

    def test_super_bezier_curve(self):
        pen = DummyPointPen()
        quadpen = Cu2QuPointPen(pen, MAX_ERR)
        quadpen.beginPath()
        quadpen.addPoint((0, 0), segmentType="move")
        quadpen.addPoint((1, 1))
        quadpen.addPoint((2, 2))
        quadpen.addPoint((3, 3))
        quadpen.addPoint(
            (4, 4), segmentType="curve", smooth=False, name="up", selected=1
        )
        quadpen.endPath()

        self.assertEqual(
            str(pen).splitlines(),
            """\
pen.beginPath()
pen.addPoint((0, 0), name=None, segmentType='move', smooth=False)
pen.addPoint((0.75, 0.75), name=None, segmentType=None, smooth=False)
pen.addPoint((1.625, 1.625), name=None, segmentType=None, smooth=False)
pen.addPoint((2, 2), name=None, segmentType='qcurve', smooth=True)
pen.addPoint((2.375, 2.375), name=None, segmentType=None, smooth=False)
pen.addPoint((3.25, 3.25), name=None, segmentType=None, smooth=False)
pen.addPoint((4, 4), name='up', segmentType='qcurve', selected=1, smooth=False)
pen.endPath()""".splitlines(),
        )

    def test__flushContour_restore_starting_point(self):
        pen = DummyPointPen()
        quadpen = Cu2QuPointPen(pen, MAX_ERR)

        # collect the output of _flushContour before it's sent to _drawPoints
        new_segments = []

        def _drawPoints(segments):
            new_segments.extend(segments)
            Cu2QuPointPen._drawPoints(quadpen, segments)

        quadpen._drawPoints = _drawPoints

        # a closed path (ie. no "move" segmentType)
        quadpen._flushContour(
            [
                (
                    "curve",
                    [
                        ((2, 2), False, None, {}),
                        ((1, 1), False, None, {}),
                        ((0, 0), False, None, {}),
                    ],
                ),
                (
                    "curve",
                    [
                        ((1, 1), False, None, {}),
                        ((2, 2), False, None, {}),
                        ((3, 3), False, None, {}),
                    ],
                ),
            ]
        )

        # the original starting point is restored: the last segment has become
        # the first
        self.assertEqual(new_segments[0][1][-1][0], (3, 3))
        self.assertEqual(new_segments[-1][1][-1][0], (0, 0))

        new_segments = []
        # an open path (ie. starting with "move")
        quadpen._flushContour(
            [
                (
                    "move",
                    [
                        ((0, 0), False, None, {}),
                    ],
                ),
                (
                    "curve",
                    [
                        ((1, 1), False, None, {}),
                        ((2, 2), False, None, {}),
                        ((3, 3), False, None, {}),
                    ],
                ),
            ]
        )

        # the segment order stays the same before and after _flushContour
        self.assertEqual(new_segments[0][1][-1][0], (0, 0))
        self.assertEqual(new_segments[-1][1][-1][0], (3, 3))

    def test_quad_no_oncurve(self):
        """When passed a contour which has no on-curve points, the
        Cu2QuPointPen will treat it as a special quadratic contour whose
        first point has 'None' coordinates.
        """
        self.maxDiff = None
        pen = DummyPointPen()
        quadpen = Cu2QuPointPen(pen, MAX_ERR)
        quadpen.beginPath()
        quadpen.addPoint((1, 1))
        quadpen.addPoint((2, 2))
        quadpen.addPoint((3, 3))
        quadpen.endPath()

        self.assertEqual(
            str(pen),
            dedent(
                """\
                pen.beginPath()
                pen.addPoint((1, 1), name=None, segmentType=None, smooth=False)
                pen.addPoint((2, 2), name=None, segmentType=None, smooth=False)
                pen.addPoint((3, 3), name=None, segmentType=None, smooth=False)
                pen.endPath()"""
            ),
        )


class TestCu2QuMultiPen(unittest.TestCase):
    def test_multi_pen(self):
        pens = [RecordingPen(), RecordingPen()]
        pen = Cu2QuMultiPen(pens, 0.1)
        pen.moveTo([((0, 0),), ((0, 0),)])
        pen.lineTo([((0, 1),), ((0, 1),)])
        pen.qCurveTo([((0, 2),), ((0, 2),)])
        pen.qCurveTo([((0, 3), (1, 3)), ((0, 3), (1, 4))])
        pen.curveTo([((2, 3), (0, 3), (0, 0)), ((1.1, 4), (0, 4), (0, 0))])
        pen.closePath()

        assert len(pens[0].value) == 6
        assert len(pens[1].value) == 6

        for op0, op1 in zip(pens[0].value, pens[1].value):
            assert op0[0] == op0[0]
            assert op0[0] != "curveTo"


class TestAllQuadraticFalse(unittest.TestCase):
    def test_segment_pen_cubic(self):
        rpen = RecordingPen()
        pen = Cu2QuPen(rpen, 0.1, all_quadratic=False)

        pen.moveTo((0, 0))
        pen.curveTo((0, 1), (2, 1), (2, 0))
        pen.closePath()

        assert rpen.value == [
            ("moveTo", ((0, 0),)),
            ("curveTo", ((0, 1), (2, 1), (2, 0))),
            ("closePath", ()),
        ]

    def test_segment_pen_quadratic(self):
        rpen = RecordingPen()
        pen = Cu2QuPen(rpen, 0.1, all_quadratic=False)

        pen.moveTo((0, 0))
        pen.curveTo((2, 2), (4, 2), (6, 0))
        pen.closePath()

        assert rpen.value == [
            ("moveTo", ((0, 0),)),
            ("qCurveTo", ((3, 3), (6, 0))),
            ("closePath", ()),
        ]

    def test_point_pen_cubic(self):
        rpen = RecordingPointPen()
        pen = Cu2QuPointPen(rpen, 0.1, all_quadratic=False)

        pen.beginPath()
        pen.addPoint((0, 0), "move")
        pen.addPoint((0, 1))
        pen.addPoint((2, 1))
        pen.addPoint((2, 0), "curve")
        pen.endPath()

        assert rpen.value == [
            ("beginPath", (), {}),
            ("addPoint", ((0, 0), "move", False, None), {}),
            ("addPoint", ((0, 1), None, False, None), {}),
            ("addPoint", ((2, 1), None, False, None), {}),
            ("addPoint", ((2, 0), "curve", False, None), {}),
            ("endPath", (), {}),
        ]

    def test_point_pen_quadratic(self):
        rpen = RecordingPointPen()
        pen = Cu2QuPointPen(rpen, 0.1, all_quadratic=False)

        pen.beginPath()
        pen.addPoint((0, 0), "move")
        pen.addPoint((2, 2))
        pen.addPoint((4, 2))
        pen.addPoint((6, 0), "curve")
        pen.endPath()

        assert rpen.value == [
            ("beginPath", (), {}),
            ("addPoint", ((0, 0), "move", False, None), {}),
            ("addPoint", ((3, 3), None, False, None), {}),
            ("addPoint", ((6, 0), "qcurve", False, None), {}),
            ("endPath", (), {}),
        ]


if __name__ == "__main__":
    unittest.main()
