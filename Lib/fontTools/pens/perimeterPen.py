"""Calculate the perimeter of a glyph."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.basePen import BasePen
from fontTools.misc.bezierTools import splitQuadraticAtT, splitCubicAtT
import math


def _distance(p0, p1):
	return math.hypot(p0[0] - p1[0], p0[1] - p1[1])
def _dot(v1, v2):
    return (v1 * v2.conjugate()).real
def _intSecAtan(x):
	# In : sympy.integrate(sp.sec(sp.atan(x)))
	# Out: x*sqrt(x**2 + 1)/2 + asinh(x)/2
	return x * math.sqrt(x**2 + 1)/2 + math.asinh(x)/2

def _split_cubic_into_two(p0, p1, p2, p3):
    mid = (p0 + 3 * (p1 + p2) + p3) * .125
    deriv3 = (p3 + p2 - p1 - p0) * .125
    return ((p0, (p0 + p1) * .5, mid - deriv3, mid),
            (mid, mid + deriv3, (p2 + p3) * .5, p3))

class PerimeterPen(BasePen):

	def __init__(self, glyphset=None, tolerance=0.005):
		BasePen.__init__(self, glyphset)
		self.value = 0
		self._mult = 1.+1.5*tolerance # The 1.5 is a empirical hack; no math

	def _moveTo(self, p0):
		self.__startPoint = p0

	def _lineTo(self, p1):
		p0 = self._getCurrentPoint()
		self.value += _distance(p0, p1)

	def _qCurveToOne(self, p1, p2):
		# Analytical solution to the length of a quadratic bezier.
		# I'll explain how I arrived at this later.
		p0 = self._getCurrentPoint()
		_p1 = complex(*p1)
		d0 = _p1 - complex(*p0)
		d1 = complex(*p2) - _p1
		d = d1 - d0
		n = d * 1j
		scale = abs(n)
		if scale == 0.:
			self._lineTo(p2)
			return
		origDist = _dot(n,d0)
		if origDist == 0.:
			if _dot(d0,d1) >= 0:
				self._lineTo(p2)
				return
			assert 0 # TODO handle cusps
		x0 = _dot(d,d0) / origDist
		x1 = _dot(d,d1) / origDist
		Len = abs(2 * (_intSecAtan(x1) - _intSecAtan(x0)) * origDist / (scale * (x1 - x0)))
		self.value += Len

	def _addCubic(self, p0, p1, p2, p3):
		arch = abs(p0-p3)
		box = abs(p0-p1) + abs(p1-p2) + abs(p2-p3)
		if arch * self._mult >= box:
			self.value += (arch + box) * .5
		else:
			one,two = _split_cubic_into_two(p0,p1,p2,p3)
			self._addCubic(*one)
			self._addCubic(*two)

	def _curveToOne(self, p1, p2, p3):
		p0 = self._getCurrentPoint()
		self._addCubic(complex(*p0), complex(*p1), complex(*p2), complex(*p3))

	def _closePath(self):
		p0 = self._getCurrentPoint()
		if p0 != self.__startPoint:
			self.value += _distance(p0, self.__startPoint)
