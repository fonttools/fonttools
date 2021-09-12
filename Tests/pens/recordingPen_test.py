from fontTools.pens.recordingPen import (
    RecordingPen,
    DecomposingRecordingPen,
    RecordingPointPen,
)
import pytest


class _TestGlyph(object):
    def draw(self, pen):
        pen.moveTo((0.0, 0.0))
        pen.lineTo((0.0, 100.0))
        pen.curveTo((50.0, 75.0), (60.0, 50.0), (50.0, 0.0))
        pen.closePath()

    def drawPoints(self, pen):
        pen.beginPath(identifier="abc")
        pen.addPoint((0.0, 0.0), "line", False, "start", identifier="0000")
        pen.addPoint((0.0, 100.0), "line", False, None, identifier="0001")
        pen.addPoint((50.0, 75.0), None, False, None, identifier="0002")
        pen.addPoint((60.0, 50.0), None, False, None, identifier="0003")
        pen.addPoint((50.0, 0.0), "curve", True, "last", identifier="0004")
        pen.endPath()


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
            ("moveTo", ((-10.0, 5.0),)),
            ("lineTo", ((-10.0, 305.0),)),
            ("curveTo", ((90.0, 230.0), (110.0, 155.0), (90.0, 5.0))),
            ("closePath", ()),
        ]

    def test_addComponent_missing_raises(self):
        pen = DecomposingRecordingPen(dict())
        with pytest.raises(KeyError) as excinfo:
            pen.addComponent("a", (1, 0, 0, 1, 0, 0))
        assert excinfo.value.args[0] == "a"


class RecordingPointPenTest:
    def test_record_and_replay(self):
        pen = RecordingPointPen()
        glyph = _TestGlyph()
        glyph.drawPoints(pen)
        pen.addComponent("a", (2, 0, 0, 2, -10, 5))

        assert pen.value == [
            ("beginPath", (), {"identifier": "abc"}),
            ("addPoint", ((0.0, 0.0), "line", False, "start"), {"identifier": "0000"}),
            ("addPoint", ((0.0, 100.0), "line", False, None), {"identifier": "0001"}),
            ("addPoint", ((50.0, 75.0), None, False, None), {"identifier": "0002"}),
            ("addPoint", ((60.0, 50.0), None, False, None), {"identifier": "0003"}),
            ("addPoint", ((50.0, 0.0), "curve", True, "last"), {"identifier": "0004"}),
            ("endPath", (), {}),
            ("addComponent", ("a", (2, 0, 0, 2, -10, 5)), {}),
        ]

        pen2 = RecordingPointPen()
        pen.replay(pen2)

        assert pen2.value == pen.value
