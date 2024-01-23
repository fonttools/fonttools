from fontTools.misc.fixedTools import floatToFixedToStr
from fontTools.pens.recordingPen import RecordingPen, RecordingPointPen
from fontTools.pens.roundingPen import RoundingPen, RoundingPointPen


def tt_scale_round(value):
    return float(floatToFixedToStr(value, precisionBits=14))


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
        # The 0.9130000305 is taken from a ttx dump of a scaled component.
        roundpen.addComponent("a", (0.9130000305, 0, 0, -1, 10.5, -10.5))
        # The value should compare equal to the shorter representation
        assert recpen.value == [
            ("addComponent", ("a", (0.913, 0, 0, -1, 11, -10))),
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
        # The 0.9130000305 is taken from a ttx dump of a scaled component.
        roundpen.addComponent("a", (0.9130000305, 0, 0, -1, 10.5, -10.5))
        # The value should compare equal to the shorter representation
        assert recpen.value == [
            ("addComponent", ("a", (0.913, 0, 0, -1, 11, -10)), {}),
        ]
