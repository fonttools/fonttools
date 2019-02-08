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
            "M0,0 H1 V1 H0 V0",
        )
    ]
)
def test_rect_to_path(rect, expected_path):
    pb = shapes.PathBuilder()
    pb.Rect(etree.fromstring(rect))
    assert pb.pathes == [expected_path]
