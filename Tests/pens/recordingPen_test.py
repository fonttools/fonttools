from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.recordingPen import RecordingPen, ContourRecordingPen
import unittest


class _TestGlyph:

    def draw(self, pen):
        pen.moveTo((0.0, 0.0))
        pen.lineTo((0.0, 100.0))
        pen.curveTo((50.0, 75.0), (60.0, 50.0), (50.0, 0.0))
        pen.closePath()


class RecordingPenTest(unittest.TestCase):

    def test_addComponent(self):
        pen = RecordingPen()
        pen.addComponent("a", (2, 0, 0, 3, -10, 5))
        self.assertEqual([("addComponent", ("a", (2, 0, 0, 3, -10, 5)))],
                         pen.value)


class ContourRecordingPenTest(unittest.TestCase):

    def test_addComponent_decomposed(self):
        pen = ContourRecordingPen({"a": _TestGlyph()})
        pen.addComponent("a", (2, 0, 0, 3, -10, 5))
        self.assertEqual([('moveTo', ((-10.0, 5.0),)),
                          ('lineTo', ((-10.0, 305.0),)),
                          ('curveTo', ((90.0, 230.0), (110.0, 155.0), (90.0, 5.0),)),
                          ('closePath', ())], pen.value)
