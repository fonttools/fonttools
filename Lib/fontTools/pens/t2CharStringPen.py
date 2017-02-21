# Copyright (c) 2009 Type Supply LLC
# Author: Tal Leming

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.psCharStrings import T2CharString
from fontTools.pens.basePen import BasePen


class RelativeCoordinatePen(BasePen):

    def __init__(self, glyphSet):
        BasePen.__init__(self, glyphSet)
        self._lastX = None
        self._lastY = None
        self._heldAbsoluteMove = None

    def _makePointRelative(self, pt):
        absX, absY = pt
        absX = absX
        absY = absY
        # no points have been added
        # so no conversion is needed
        if self._lastX is None:
            relX, relY = absX, absY
        # otherwise calculate the relative coordinates
        else:
            relX = absX - self._lastX
            relY = absY - self._lastY
        # store the absolute coordinates
        self._lastX = absX
        self._lastY = absY
        # now return the relative coordinates
        return relX, relY

    def _moveTo(self, pt):
        self._heldAbsoluteMove = pt

    def _releaseHeldMove(self):
        if self._heldAbsoluteMove is not None:
            pt = self._makePointRelative(self._heldAbsoluteMove)
            self._relativeMoveTo(pt)
            self._heldAbsoluteMove = None

    def _relativeMoveTo(self, pt):
        raise NotImplementedError

    def _lineTo(self, pt):
        self._releaseHeldMove()
        pt = self._makePointRelative(pt)
        self._relativeLineTo(pt)

    def _relativeLineTo(self, pt):
        raise NotImplementedError

    def _curveToOne(self, pt1, pt2, pt3):
        self._releaseHeldMove()
        pt1 = self._makePointRelative(pt1)
        pt2 = self._makePointRelative(pt2)
        pt3 = self._makePointRelative(pt3)
        self._relativeCurveToOne(pt1, pt2, pt3)

    def _relativeCurveToOne(self, pt1, pt2, pt3):
        raise NotImplementedError


def makeRoundFunc(tolerance):
    if tolerance < 0:
        raise ValueError("Rounding tolerance must be positive")

    def _round(number):
        if tolerance == 0:
            return number  # no-op
        rounded = round(number)
        # return rounded integer if the tolerance >= 0.5, or if the absolute
        # difference between the original float and the rounded integer is
        # within the tolerance
        if tolerance >= .5 or abs(rounded - number) <= tolerance:
            return rounded
        else:
            # else return the value un-rounded
            return number

    def roundPoint(point):
        x, y = point
        return _round(x), _round(y)

    return roundPoint


class T2CharStringPen(RelativeCoordinatePen):
    """Pen to draw Type 2 CharStrings.

    The 'roundTolerance' argument controls the rounding of point coordinates.
    It is defined as the maximum absolute difference between the original
    float and the rounded integer value.
    The default tolerance of 0.5 means that all floats are rounded to integer;
    a value of 0 disables rounding; values in between will only round floats
    which are close to their integral part within the tolerated range.
    """

    def __init__(self, width, glyphSet, roundTolerance=0.5):
        RelativeCoordinatePen.__init__(self, glyphSet)
        self.roundPoint = makeRoundFunc(roundTolerance)
        self._heldMove = None
        self._program = []
        if width is not None:
            self._program.append(round(width))

    def _moveTo(self, pt):
        RelativeCoordinatePen._moveTo(self, self.roundPoint(pt))

    def _relativeMoveTo(self, pt):
        pt = self.roundPoint(pt)
        x, y = pt
        self._heldMove = [x, y, "rmoveto"]

    def _storeHeldMove(self):
        if self._heldMove is not None:
            self._program.extend(self._heldMove)
            self._heldMove = None

    def _lineTo(self, pt):
        RelativeCoordinatePen._lineTo(self, self.roundPoint(pt))

    def _relativeLineTo(self, pt):
        self._storeHeldMove()
        pt = self.roundPoint(pt)
        x, y = pt
        self._program.extend([x, y, "rlineto"])

    def _curveToOne(self, pt1, pt2, pt3):
        RelativeCoordinatePen._curveToOne(self,
                                          self.roundPoint(pt1),
                                          self.roundPoint(pt2),
                                          self.roundPoint(pt3))

    def _relativeCurveToOne(self, pt1, pt2, pt3):
        self._storeHeldMove()
        pt1 = self.roundPoint(pt1)
        pt2 = self.roundPoint(pt2)
        pt3 = self.roundPoint(pt3)
        x1, y1 = pt1
        x2, y2 = pt2
        x3, y3 = pt3
        self._program.extend([x1, y1, x2, y2, x3, y3, "rrcurveto"])

    def _closePath(self):
        pass

    def _endPath(self):
        pass

    def getCharString(self, private=None, globalSubrs=None):
        program = self._program + ["endchar"]
        charString = T2CharString(
            program=program, private=private, globalSubrs=globalSubrs)
        return charString
