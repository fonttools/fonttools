"""Calculate the perimeter of a glyph."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.basePen import BasePen
from fontTools.misc.bezierTools import splitQuadraticAtT, splitCubicAtT
import math


def _distance(p0, p1):
	return math.hypot(p0[0] - p1[0], p0[1] - p1[1])
def _diff(a, b):
	return (b[0]-a[0], b[1]-a[1])
def _dot(a, b):
	return a[0]*b[0] + a[1]*b[1]
def _intSecAtan(x):
	# In : sympy.integrate(sp.sec(sp.atan(x)))
	# Out: x*sqrt(x**2 + 1)/2 + asinh(x)/2
	return x * math.sqrt(x**2 + 1)/2 + math.asinh(x)/2

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
		Len = 0
		d0 = _diff(p0, p1)
		d1 = _diff(p1, p2)
		d = _diff(d0, d1)
		n = (d[1],-d[0])
		scale = math.hypot(n[0],n[1])
		if scale == 0.:
			self._lineTo(p2)
			return
		origDist = _dot(n,d0)
		if origDist == 0.:
			if _dot(d0,d1) > 0:
				self._lineTo(p2)
				return
			assert 0 # TODO handle cusps
		x0 = _dot(d,d0) / origDist
		x1 = _dot(d,d1) / origDist
		Len = abs(2 * (_intSecAtan(x1) - _intSecAtan(x0)) * origDist / (scale * (x1 - x0)))
		self.value += Len

	def _addCubic(self, p0, p1, p2, p3):
		arch = _distance(p0, p3)
		box = _distance(p0, p1) + _distance(p1, p2) + _distance(p2, p3)
		if arch * self._mult >= box:
			self.value += (arch + box) * .5
		else:
			for c in splitCubicAtT(p0,p1,p2,p3,.2,.4,.6,.8):
				self._addCubic(*c)

	def _curveToOne(self, p1, p2, p3):
		p0 = self._getCurrentPoint()
		self._addCubic(p0, p1, p2, p3)

	def _closePath(self):
		p0 = self._getCurrentPoint()
		if p0 != self.__startPoint:
			self.value += _distance(p0, self.__startPoint)
