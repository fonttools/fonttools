from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.filterPen import FilterPen
from fontTools.pens.transformPen import TransformPen


class DecomposingPen(FilterPen):

    """A filter pen that decomposes components before drawing them with
    another pen.
    """

    def __init__(self, outPen, glyphSet):
        super(DecomposingPen, self).__init__(outPen)
        self.glyphSet = glyphSet

    def addComponent(self, glyphName, transformation):
        """Transform the points of the base glyph and draw it onto self.
        """
        glyph = self.glyphSet[glyphName]
        tPen = TransformPen(self, transformation)
        glyph.draw(tPen)
