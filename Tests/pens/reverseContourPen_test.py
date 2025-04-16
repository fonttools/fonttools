from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
import pytest


TEST_DATA = [
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),
            ("lineTo", ((2, 2),)),
            ("lineTo", ((3, 3),)),  # last not on move, line is implied
            ("closePath", ()),
        ],
        False,  # outputImpliedClosingLine
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((3, 3),)),
            ("lineTo", ((2, 2),)),
            ("lineTo", ((1, 1),)),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),
            ("lineTo", ((2, 2),)),
            ("lineTo", ((3, 3),)),  # last line does not overlap move...
            ("closePath", ()),
        ],
        True,  # outputImpliedClosingLine
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((3, 3),)),
            ("lineTo", ((2, 2),)),
            ("lineTo", ((1, 1),)),
            ("lineTo", ((0, 0),)),  # ... but closing line is NOT implied
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),
            ("lineTo", ((2, 2),)),
            ("lineTo", ((0, 0),)),  # last line overlaps move, explicit line
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((2, 2),)),
            ("lineTo", ((1, 1),)),
            ("closePath", ()),  # closing line implied
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),
            ("lineTo", ((2, 2),)),
            ("lineTo", ((0, 0),)),  # last line overlaps move...
            ("closePath", ()),
        ],
        True,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((2, 2),)),
            ("lineTo", ((1, 1),)),
            ("lineTo", ((0, 0),)),  # ... but line is NOT implied
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((0, 0),)),  # duplicate lineTo following moveTo
            ("lineTo", ((1, 1),)),
            ("lineTo", ((2, 2),)),
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((2, 2),)),
            ("lineTo", ((1, 1),)),
            ("lineTo", ((0, 0),)),  # extra explicit lineTo is always emitted to
            ("lineTo", ((0, 0),)),  # disambiguate from an implicit closing line
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((0, 0),)),  # duplicate lineTo following moveTo
            ("lineTo", ((1, 1),)),
            ("lineTo", ((2, 2),)),
            ("closePath", ()),
        ],
        True,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((2, 2),)),
            ("lineTo", ((1, 1),)),
            ("lineTo", ((0, 0),)),  # duplicate lineTo is retained also in this case,
            ("lineTo", ((0, 0),)),  # same result as with outputImpliedClosingLine=False
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),
            ("closePath", ()),
        ],
        True,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),
            ("lineTo", ((0, 0),)),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("curveTo", ((1, 1), (2, 2), (3, 3))),
            ("curveTo", ((4, 4), (5, 5), (0, 0))),  # closed curveTo overlaps moveTo
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 0),)),  # no extra lineTo added here
            ("curveTo", ((5, 5), (4, 4), (3, 3))),
            ("curveTo", ((2, 2), (1, 1), (0, 0))),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("curveTo", ((1, 1), (2, 2), (3, 3))),
            ("curveTo", ((4, 4), (5, 5), (0, 0))),  # closed curveTo overlaps moveTo
            ("closePath", ()),
        ],
        True,
        [
            ("moveTo", ((0, 0),)),  # no extra lineTo added here, same as preceding
            ("curveTo", ((5, 5), (4, 4), (3, 3))),
            ("curveTo", ((2, 2), (1, 1), (0, 0))),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("curveTo", ((1, 1), (2, 2), (3, 3))),
            ("curveTo", ((4, 4), (5, 5), (6, 6))),  # closed curve not overlapping move
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((6, 6),)),  # the previously implied line
            ("curveTo", ((5, 5), (4, 4), (3, 3))),
            ("curveTo", ((2, 2), (1, 1), (0, 0))),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("curveTo", ((1, 1), (2, 2), (3, 3))),
            ("curveTo", ((4, 4), (5, 5), (6, 6))),  # closed curve not overlapping move
            ("closePath", ()),
        ],
        True,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((6, 6),)),  # the previously implied line (same as above)
            ("curveTo", ((5, 5), (4, 4), (3, 3))),
            ("curveTo", ((2, 2), (1, 1), (0, 0))),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),  # this line becomes implied
            ("curveTo", ((2, 2), (3, 3), (4, 4))),
            ("curveTo", ((5, 5), (6, 6), (7, 7))),
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((7, 7),)),
            ("curveTo", ((6, 6), (5, 5), (4, 4))),
            ("curveTo", ((3, 3), (2, 2), (1, 1))),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),  # this line...
            ("curveTo", ((2, 2), (3, 3), (4, 4))),
            ("curveTo", ((5, 5), (6, 6), (7, 7))),
            ("closePath", ()),
        ],
        True,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((7, 7),)),
            ("curveTo", ((6, 6), (5, 5), (4, 4))),
            ("curveTo", ((3, 3), (2, 2), (1, 1))),
            ("lineTo", ((0, 0),)),  # ... does NOT become implied
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("qCurveTo", ((1, 1), (2, 2))),
            ("qCurveTo", ((3, 3), (0, 0))),  # closed qCurve overlaps move
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 0),)),  # no extra lineTo added here
            ("qCurveTo", ((3, 3), (2, 2))),
            ("qCurveTo", ((1, 1), (0, 0))),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("qCurveTo", ((1, 1), (2, 2))),
            ("qCurveTo", ((3, 3), (0, 0))),  # closed qCurve overlaps move
            ("closePath", ()),
        ],
        True,  # <--
        [
            ("moveTo", ((0, 0),)),  # no extra lineTo added here, same as above
            ("qCurveTo", ((3, 3), (2, 2))),
            ("qCurveTo", ((1, 1), (0, 0))),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("qCurveTo", ((1, 1), (2, 2))),
            ("qCurveTo", ((3, 3), (4, 4))),  # closed qCurve not overlapping move
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((4, 4),)),  # the previously implied line
            ("qCurveTo", ((3, 3), (2, 2))),
            ("qCurveTo", ((1, 1), (0, 0))),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("qCurveTo", ((1, 1), (2, 2))),
            ("qCurveTo", ((3, 3), (4, 4))),  # closed qCurve not overlapping move
            ("closePath", ()),
        ],
        True,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((4, 4),)),  # the previously implied line (same as above)
            ("qCurveTo", ((3, 3), (2, 2))),
            ("qCurveTo", ((1, 1), (0, 0))),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),
            ("qCurveTo", ((2, 2), (3, 3))),
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((3, 3),)),
            ("qCurveTo", ((2, 2), (1, 1))),
            ("closePath", ()),
        ],
    ),
    (
        [("addComponent", ("a", (1, 0, 0, 1, 0, 0)))],
        False,
        [("addComponent", ("a", (1, 0, 0, 1, 0, 0)))],
    ),
    ([], False, []),
    (
        [
            ("moveTo", ((0, 0),)),
            ("endPath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 0),)),
            ("endPath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 0),)),
            ("endPath", ()),  # single-point paths is always open
        ],
    ),
    (
        [("moveTo", ((0, 0),)), ("lineTo", ((1, 1),)), ("endPath", ())],
        False,
        [("moveTo", ((1, 1),)), ("lineTo", ((0, 0),)), ("endPath", ())],
    ),
    (
        [("moveTo", ((0, 0),)), ("curveTo", ((1, 1), (2, 2), (3, 3))), ("endPath", ())],
        False,
        [("moveTo", ((3, 3),)), ("curveTo", ((2, 2), (1, 1), (0, 0))), ("endPath", ())],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("curveTo", ((1, 1), (2, 2), (3, 3))),
            ("lineTo", ((4, 4),)),
            ("endPath", ()),
        ],
        False,
        [
            ("moveTo", ((4, 4),)),
            ("lineTo", ((3, 3),)),
            ("curveTo", ((2, 2), (1, 1), (0, 0))),
            ("endPath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 0),)),
            ("lineTo", ((1, 1),)),
            ("curveTo", ((2, 2), (3, 3), (4, 4))),
            ("endPath", ()),
        ],
        False,
        [
            ("moveTo", ((4, 4),)),
            ("curveTo", ((3, 3), (2, 2), (1, 1))),
            ("lineTo", ((0, 0),)),
            ("endPath", ()),
        ],
    ),
    (
        [("qCurveTo", ((0, 0), (1, 1), (2, 2), None)), ("closePath", ())],
        False,
        [("qCurveTo", ((0, 0), (2, 2), (1, 1), None)), ("closePath", ())],
    ),
    (
        [("qCurveTo", ((0, 0), (1, 1), (2, 2), None)), ("endPath", ())],
        False,
        [
            ("qCurveTo", ((0, 0), (2, 2), (1, 1), None)),
            ("closePath", ()),  # this is always "closed"
        ],
    ),
    # Test case from:
    # https://github.com/googlei18n/cu2qu/issues/51#issue-179370514
    (
        [
            ("moveTo", ((848, 348),)),
            ("lineTo", ((848, 348),)),  # duplicate lineTo point after moveTo
            ("qCurveTo", ((848, 526), (649, 704), (449, 704))),
            ("qCurveTo", ((449, 704), (248, 704), (50, 526), (50, 348))),
            ("lineTo", ((50, 348),)),
            ("qCurveTo", ((50, 348), (50, 171), (248, -3), (449, -3))),
            ("qCurveTo", ((449, -3), (649, -3), (848, 171), (848, 348))),
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((848, 348),)),
            ("qCurveTo", ((848, 171), (649, -3), (449, -3), (449, -3))),
            ("qCurveTo", ((248, -3), (50, 171), (50, 348), (50, 348))),
            ("lineTo", ((50, 348),)),
            ("qCurveTo", ((50, 526), (248, 704), (449, 704), (449, 704))),
            ("qCurveTo", ((649, 704), (848, 526), (848, 348))),
            ("lineTo", ((848, 348),)),  # the duplicate point is kept
            ("closePath", ()),
        ],
    ),
    # Test case from https://github.com/googlefonts/fontmake/issues/572
    # An additional closing lineTo is required to disambiguate a duplicate
    # point at the end of a contour from the implied closing line.
    (
        [
            ("moveTo", ((0, 651),)),
            ("lineTo", ((0, 101),)),
            ("lineTo", ((0, 101),)),
            ("lineTo", ((0, 651),)),
            ("lineTo", ((0, 651),)),
            ("closePath", ()),
        ],
        False,
        [
            ("moveTo", ((0, 651),)),
            ("lineTo", ((0, 651),)),
            ("lineTo", ((0, 101),)),
            ("lineTo", ((0, 101),)),
            ("closePath", ()),
        ],
    ),
    (
        [
            ("moveTo", ((0, 651),)),
            ("lineTo", ((0, 101),)),
            ("lineTo", ((0, 101),)),
            ("lineTo", ((0, 651),)),
            ("lineTo", ((0, 651),)),
            ("closePath", ()),
        ],
        True,
        [
            ("moveTo", ((0, 651),)),
            ("lineTo", ((0, 651),)),
            ("lineTo", ((0, 101),)),
            ("lineTo", ((0, 101),)),
            ("lineTo", ((0, 651),)),  # closing line not implied
            ("closePath", ()),
        ],
    ),
]


@pytest.mark.parametrize("contour, outputImpliedClosingLine, expected", TEST_DATA)
def test_reverse_pen(contour, outputImpliedClosingLine, expected):
    recpen = RecordingPen()
    revpen = ReverseContourPen(recpen, outputImpliedClosingLine)
    for operator, operands in contour:
        getattr(revpen, operator)(*operands)
    assert recpen.value == expected


def test_reverse_pen_outputImpliedClosingLine():
    recpen = RecordingPen()
    revpen = ReverseContourPen(recpen)
    revpen.moveTo((0, 0))
    revpen.lineTo((10, 0))
    revpen.lineTo((0, 10))
    revpen.lineTo((0, 0))
    revpen.closePath()
    assert recpen.value == [
        ("moveTo", ((0, 0),)),
        ("lineTo", ((0, 10),)),
        ("lineTo", ((10, 0),)),
        # ("lineTo", ((0, 0),)),  # implied
        ("closePath", ()),
    ]

    recpen = RecordingPen()
    revpen = ReverseContourPen(recpen, outputImpliedClosingLine=True)
    revpen.moveTo((0, 0))
    revpen.lineTo((10, 0))
    revpen.lineTo((0, 10))
    revpen.lineTo((0, 0))
    revpen.closePath()
    assert recpen.value == [
        ("moveTo", ((0, 0),)),
        ("lineTo", ((0, 10),)),
        ("lineTo", ((10, 0),)),
        ("lineTo", ((0, 0),)),  # not implied
        ("closePath", ()),
    ]


@pytest.mark.parametrize("contour, outputImpliedClosingLine, expected", TEST_DATA)
def test_reverse_point_pen(contour, outputImpliedClosingLine, expected):
    from fontTools.pens.pointPen import (
        ReverseContourPointPen,
        PointToSegmentPen,
        SegmentToPointPen,
    )

    recpen = RecordingPen()
    pt2seg = PointToSegmentPen(recpen, outputImpliedClosingLine)
    revpen = ReverseContourPointPen(pt2seg)
    seg2pt = SegmentToPointPen(revpen)
    for operator, operands in contour:
        getattr(seg2pt, operator)(*operands)

    assert recpen.value == expected
