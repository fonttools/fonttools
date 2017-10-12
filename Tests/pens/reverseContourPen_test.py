from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
import pytest


TEST_DATA = [
    (
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((1, 1),)),
            ('lineTo', ((2, 2),)),
            ('lineTo', ((3, 3),)),  # last not on move, line is implied
            ('closePath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((3, 3),)),
            ('lineTo', ((2, 2),)),
            ('lineTo', ((1, 1),)),
            ('closePath', ()),
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((1, 1),)),
            ('lineTo', ((2, 2),)),
            ('lineTo', ((0, 0),)),  # last on move, no implied line
            ('closePath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((2, 2),)),
            ('lineTo', ((1, 1),)),
            ('closePath', ()),
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((0, 0),)),
            ('lineTo', ((1, 1),)),
            ('lineTo', ((2, 2),)),
            ('closePath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((2, 2),)),
            ('lineTo', ((1, 1),)),
            ('lineTo', ((0, 0),)),
            ('closePath', ()),
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((1, 1),)),
            ('closePath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((1, 1),)),
            ('closePath', ()),
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('curveTo', ((1, 1), (2, 2), (3, 3))),
            ('curveTo', ((4, 4), (5, 5), (0, 0))),
            ('closePath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('curveTo', ((5, 5), (4, 4), (3, 3))),
            ('curveTo', ((2, 2), (1, 1), (0, 0))),
            ('closePath', ()),
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('curveTo', ((1, 1), (2, 2), (3, 3))),
            ('curveTo', ((4, 4), (5, 5), (6, 6))),
            ('closePath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((6, 6),)),  # implied line
            ('curveTo', ((5, 5), (4, 4), (3, 3))),
            ('curveTo', ((2, 2), (1, 1), (0, 0))),
            ('closePath', ()),
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((1, 1),)),  # this line becomes implied
            ('curveTo', ((2, 2), (3, 3), (4, 4))),
            ('curveTo', ((5, 5), (6, 6), (7, 7))),
            ('closePath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((7, 7),)),
            ('curveTo', ((6, 6), (5, 5), (4, 4))),
            ('curveTo', ((3, 3), (2, 2), (1, 1))),
            ('closePath', ()),
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('qCurveTo', ((1, 1), (2, 2))),
            ('qCurveTo', ((3, 3), (0, 0))),
            ('closePath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('qCurveTo', ((3, 3), (2, 2))),
            ('qCurveTo', ((1, 1), (0, 0))),
            ('closePath', ()),
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('qCurveTo', ((1, 1), (2, 2))),
            ('qCurveTo', ((3, 3), (4, 4))),
            ('closePath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((4, 4),)),
            ('qCurveTo', ((3, 3), (2, 2))),
            ('qCurveTo', ((1, 1), (0, 0))),
            ('closePath', ()),
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((1, 1),)),
            ('qCurveTo', ((2, 2), (3, 3))),
            ('closePath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((3, 3),)),
            ('qCurveTo', ((2, 2), (1, 1))),
            ('closePath', ()),
        ]
    ),
    (
        [
            ('addComponent', ('a', (1, 0, 0, 1, 0, 0)))
        ],
        [
            ('addComponent', ('a', (1, 0, 0, 1, 0, 0)))
        ]
    ),
    (
        [], []
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('endPath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('endPath', ()),
        ],
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('closePath', ()),
        ],
        [
            ('moveTo', ((0, 0),)),
            ('endPath', ()),  # single-point paths is always open
        ],
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((1, 1),)),
            ('endPath', ())
        ],
        [
            ('moveTo', ((1, 1),)),
            ('lineTo', ((0, 0),)),
            ('endPath', ())
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('curveTo', ((1, 1), (2, 2), (3, 3))),
            ('endPath', ())
        ],
        [
            ('moveTo', ((3, 3),)),
            ('curveTo', ((2, 2), (1, 1), (0, 0))),
            ('endPath', ())
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('curveTo', ((1, 1), (2, 2), (3, 3))),
            ('lineTo', ((4, 4),)),
            ('endPath', ())
        ],
        [
            ('moveTo', ((4, 4),)),
            ('lineTo', ((3, 3),)),
            ('curveTo', ((2, 2), (1, 1), (0, 0))),
            ('endPath', ())
        ]
    ),
    (
        [
            ('moveTo', ((0, 0),)),
            ('lineTo', ((1, 1),)),
            ('curveTo', ((2, 2), (3, 3), (4, 4))),
            ('endPath', ())
        ],
        [
            ('moveTo', ((4, 4),)),
            ('curveTo', ((3, 3), (2, 2), (1, 1))),
            ('lineTo', ((0, 0),)),
            ('endPath', ())
        ]
    ),
    (
        [
            ('qCurveTo', ((0, 0), (1, 1), (2, 2), None)),
            ('closePath', ())
        ],
        [
            ('qCurveTo', ((0, 0), (2, 2), (1, 1), None)),
            ('closePath', ())
        ]
    ),
    (
        [
            ('qCurveTo', ((0, 0), (1, 1), (2, 2), None)),
            ('endPath', ())
        ],
        [
            ('qCurveTo', ((0, 0), (2, 2), (1, 1), None)),
            ('closePath', ())  # this is always "closed"
        ]
    )
]


@pytest.mark.parametrize("contour, expected", TEST_DATA)
def test_reverse_pen(contour, expected):
    recpen = RecordingPen()
    revpen = ReverseContourPen(recpen)
    for operator, operands in contour:
        getattr(revpen, operator)(*operands)
    assert recpen.value == expected


@pytest.mark.parametrize("contour, expected", TEST_DATA)
def test_reverse_point_pen(contour, expected):
    try:
        from ufoLib.pointPen import (
            ReverseContourPointPen, PointToSegmentPen, SegmentToPointPen)
    except ImportError:
        pytest.skip("ufoLib not installed")

    recpen = RecordingPen()
    pt2seg = PointToSegmentPen(recpen)
    revpen = ReverseContourPointPen(pt2seg)
    seg2pt = SegmentToPointPen(revpen)
    for operator, operands in contour:
        getattr(seg2pt, operator)(*operands)
    assert recpen.value == expected
