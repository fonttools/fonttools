"""Calculate the perimeter of a glyph."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.basePen import BasePen
from fontTools.misc.bezierTools import splitCubicAtT
import math


def distance(p0, p1):
	return math.hypot(p0[0] - p1[0], p0[1] - p1[1])


class PerimeterPen(BasePen):

	def __init__(self, glyphset=None, tolerance=0.005):
		BasePen.__init__(self, glyphset)
		self.value = 0
		self._mult = 1. + tolerance

	def _moveTo(self, p0):
		self.__startPoint = p0

	def _lineTo(self, p1):
		p0 = self._getCurrentPoint()
		self.value += distance(p0, p1)

	def _addCubic(self, p0, p1, p2, p3):
		arch = distance(p0, p3)
		box = distance(p0, p1) + distance(p1, p2) + distance(p2, p3)
		if arch * self._mult >= box:
			self.value += (arch + box) * .5
		else:
			for c in splitCubicAtT(p0, p1, p2, p3, .5):
				self._addCubic(*c)

	def _curveToOne(self, p1, p2, p3):
		p0 = self._getCurrentPoint()
		self._addCubic(p0, p1, p2, p3)

	def _closePath(self):
		p0 = self._getCurrentPoint()
		if p0 != self.__startPoint:
			self.value += distance(p0, self.__startPoint)
