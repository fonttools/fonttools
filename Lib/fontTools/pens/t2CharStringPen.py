# Copyright (c) 2009 Type Supply LLC
# Author: Tal Leming


from __future__ import print_function, division, absolute_import

from fontTools.misc.py23 import *
from fontTools.misc.psCharStrings import T2CharString
from fontTools.pens.basePen import BasePen


def roundInt(v):
    return int(round(v))


def roundIntPoint(point):
    x, y = point
    return roundInt(x), roundInt(y)


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


class T2CharStringPen(RelativeCoordinatePen):

    def __init__(self, width, glyphSet):
        RelativeCoordinatePen.__init__(self, glyphSet)
        self._heldMove = None
        self._program = []
        if width is not None:
            self._program.append(roundInt(width))

    def _moveTo(self, pt):
        RelativeCoordinatePen._moveTo(self, roundIntPoint(pt))

    def _relativeMoveTo(self, pt):
        pt = roundIntPoint(pt)
        x, y = pt
        self._heldMove = [x, y, "rmoveto"]

    def _storeHeldMove(self):
        if self._heldMove is not None:
            self._program.extend(self._heldMove)
            self._heldMove = None

    def _lineTo(self, pt):
        RelativeCoordinatePen._lineTo(self, roundIntPoint(pt))

    def _relativeLineTo(self, pt):
        self._storeHeldMove()
        pt = roundIntPoint(pt)
        x, y = pt
        self._program.extend([x, y, "rlineto"])

    def _curveToOne(self, pt1, pt2, pt3):
        RelativeCoordinatePen._curveToOne(self, roundIntPoint(pt1), roundIntPoint(pt2), roundIntPoint(pt3))

    def _relativeCurveToOne(self, pt1, pt2, pt3):
        self._storeHeldMove()
        pt1 = roundIntPoint(pt1)
        pt2 = roundIntPoint(pt2)
        pt3 = roundIntPoint(pt3)
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
        charString = T2CharString(program=program, private=private, globalSubrs=globalSubrs)
        return charString
