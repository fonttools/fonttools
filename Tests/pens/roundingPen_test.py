from fontTools.misc.fixedTools import floatToFixedToFloat
from fontTools.pens.recordingPen import RecordingPen, RecordingPointPen
from fontTools.pens.roundingPen import RoundingPen, RoundingPointPen
from functools import partial


tt_scale_round = partial(floatToFixedToFloat, precisionBits=14)


class RoundingPenTest(object):
    def test_general(self):
        recpen = RecordingPen()
        roundpen = RoundingPen(recpen)
        roundpen.moveTo((0.4, 0.6))
        roundpen.lineTo((1.6, 2.5))
        roundpen.qCurveTo((2.4, 4.6), (3.3, 5.7), (4.9, 6.1))
        roundpen.curveTo((6.4, 8.6), (7.3, 9.7), (8.9, 10.1))
        roundpen.addComponent("a", (1.5, 0, 0, 1.5, 10.5, -10.5))
        assert recpen.value == [
            ("moveTo", ((0, 1),)),
            ("lineTo", ((2, 3),)),
            ("qCurveTo", ((2, 5), (3, 6), (5, 6))),
            ("curveTo", ((6, 9), (7, 10), (9, 10))),
            ("addComponent", ("a", (1.5, 0, 0, 1.5, 11, -10))),
        ]

    def test_transform_round(self):
        recpen = RecordingPen()
        roundpen = RoundingPen(recpen, transformRoundFunc=tt_scale_round)
        roundpen.addComponent("a", (0.913, 0, 0, -1, 10.5, -10.5))
        # The 0.913 should have been rounded to F2Dot14 precision
        assert recpen.value == [
            ("addComponent", ("a", (0.913025, 0, 0, -1, 11, -10))),
        ]


class RoundingPointPenTest(object):
    def test_general(self):
        recpen = RecordingPointPen()
        roundpen = RoundingPointPen(recpen)
        roundpen.beginPath()
        roundpen.addPoint((0.4, 0.6), "line")
        roundpen.addPoint((1.6, 2.5), "line")
        roundpen.addPoint((2.4, 4.6))
        roundpen.addPoint((3.3, 5.7))
        roundpen.addPoint((4.9, 6.1), "qcurve")
        roundpen.endPath()
        roundpen.addComponent("a", (1.5, 0, 0, 1.5, 10.5, -10.5))
        assert recpen.value == [
            ("beginPath", (), {}),
            ("addPoint", ((0, 1), "line", False, None), {}),
            ("addPoint", ((2, 3), "line", False, None), {}),
            ("addPoint", ((2, 5), None, False, None), {}),
            ("addPoint", ((3, 6), None, False, None), {}),
            ("addPoint", ((5, 6), "qcurve", False, None), {}),
            ("endPath", (), {}),
            ("addComponent", ("a", (1.5, 0, 0, 1.5, 11, -10)), {}),
        ]

    def test_transform_round(self):
        recpen = RecordingPointPen()
        roundpen = RoundingPointPen(recpen, transformRoundFunc=tt_scale_round)
        roundpen.addComponent("a", (0.913, 0, 0, -1, 10.5, -10.5))
        # The 0.913 should have been rounded to F2Dot14 precision
        assert recpen.value == [
            ("addComponent", ("a", (0.913025, 0, 0, -1, 11, -10)), {}),
        ]
