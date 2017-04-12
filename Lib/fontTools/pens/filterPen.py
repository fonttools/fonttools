from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.basePen import AbstractPen


class FilterPen(AbstractPen):

    """ Base class for pens that apply some transformation to the coordinates
    they receive and pass them to another pen.

    You can override any of its methods. The default implementation does
    nothing, but passes the commands unmodified to the other pen.
    """

    def __init__(self, outPen, *args, **kwargs):
        self._outPen = outPen

    def moveTo(self, pt):
        self._outPen.moveTo(pt)

    def lineTo(self, pt):
        self._outPen.lineTo(pt)

    def curveTo(self, *points):
        self._outPen.curveTo(*points)

    def qCurveTo(self, *points):
        self._outPen.qCurveTo(*points)

    def closePath(self):
        self._outPen.closePath()

    def endPath(self):
        self._outPen.endPath()

    def addComponent(self, glyphName, transformation):
        self._outPen.addComponent(glyphName, transformation)
