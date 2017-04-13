from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
import pytest


class _TestGlyph(object):

    def draw(self, pen):
        pen.moveTo((0.0, 0.0))
        pen.lineTo((0.0, 100.0))
        pen.curveTo((50.0, 75.0), (60.0, 50.0), (50.0, 0.0))
        pen.closePath()


class RecordingPenTest(object):

    def test_addComponent(self):
        pen = RecordingPen()
        pen.addComponent("a", (2, 0, 0, 3, -10, 5))
        assert pen.value == [("addComponent", ("a", (2, 0, 0, 3, -10, 5)))]


class DecomposingRecordingPenTest(object):

    def test_addComponent_decomposed(self):
        pen = DecomposingRecordingPen({"a": _TestGlyph()})
        pen.addComponent("a", (2, 0, 0, 3, -10, 5))
        assert pen.value == [
            ('moveTo', ((-10.0, 5.0),)),
            ('lineTo', ((-10.0, 305.0),)),
            ('curveTo', ((90.0, 230.0), (110.0, 155.0), (90.0, 5.0),)),
            ('closePath', ())]

    def test_addComponent_missing_raises(self):
        pen = DecomposingRecordingPen(dict())
        with pytest.raises(KeyError) as excinfo:
            pen.addComponent("a", (1, 0, 0, 1, 0, 0))
        assert excinfo.value.args[0] == "a"
