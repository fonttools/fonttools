from __future__ import print_function, absolute_import, division

from fontTools.misc.py23 import *
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import shapes
from fontTools.misc import etree
import pytest


@pytest.mark.parametrize(
    "rect, expected_path",
    [
        # minimal valid example
        (
            "<rect width='1' height='1'/>",
            "M0,0 H1 V1 H0 V0 z",
        ),
        # sharp corners
        (
            "<rect x='10' y='11' width='17' height='11'/>",
            "M10,11 H27 V22 H10 V11 z",
        ),
        # round corners
        (
            "<rect x='9' y='9' width='11' height='7' rx='2'/>",
            "M11,9 H18 A2,2 0 0 1 20,11 V14 A2,2 0 0 1 18,16 H11"
            " A2,2 0 0 1 9,14 V11 A2,2 0 0 1 11,9 z",
        )
    ]
)
def test_rect_to_path(rect, expected_path):
    pb = shapes.PathBuilder()
    pb.Rect(etree.fromstring(rect))
    assert [expected_path] == pb.pathes
