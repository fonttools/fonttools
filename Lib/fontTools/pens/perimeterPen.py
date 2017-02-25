# -*- coding: utf-8 -*-
"""Calculate the perimeter of a glyph."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.pens.basePen import BasePen
from fontTools.misc.bezierTools import splitQuadraticAtT, splitCubicAtT
import math


__all__ = ["PerimeterPen"]


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

		# Choose which algorithm to use for quadratic and for cubic.
		# Quadrature is faster but has fixed error characteristic with no strong
		# error bound.  The cutoff points are derived empirically.
		self._addCubic = self._addCubicQuadrature if tolerance >= 0.0015 else self._addCubicRecursive
		self._addQuadratic = self._addQuadraticQuadrature if tolerance >= 0.00075 else self._addQuadraticExact

	def _moveTo(self, p0):
		self.__startPoint = p0

	def _closePath(self):
		p0 = self._getCurrentPoint()
		if p0 != self.__startPoint:
			self._lineTo(self.__startPoint)

	def _lineTo(self, p1):
		p0 = self._getCurrentPoint()
		self.value += _distance(p0, p1)

	def _addQuadraticExact(self, c0, c1, c2):
		# Analytical solution to the length of a quadratic bezier.
		# I'll explain how I arrived at this later.
		d0 = c1 - c0
		d1 = c2 - c1
		d = d1 - d0
		n = d * 1j
		scale = abs(n)
		if scale == 0.:
			self.value += abs(c2-c0)
			return
		origDist = _dot(n,d0)
		if origDist == 0.:
			if _dot(d0,d1) >= 0:
				self.value += abs(c2-c0)
				return
			assert 0 # TODO handle cusps
		x0 = _dot(d,d0) / origDist
		x1 = _dot(d,d1) / origDist
		Len = abs(2 * (_intSecAtan(x1) - _intSecAtan(x0)) * origDist / (scale * (x1 - x0)))
		self.value += Len

	def _addQuadraticQuadrature(self, c0, c1, c2):
		# Approximate length of quadratic Bezier curve using Gauss-Legendre quadrature
		# with n=3 points.
		#
		# This, essentially, approximates the length-of-derivative function
		# to be integrated with the best-matching fifth-degree polynomial
		# approximation of it.
		#
		#https://en.wikipedia.org/wiki/Gaussian_quadrature#Gauss.E2.80.93Legendre_quadrature

		# abs(BezierCurveC[2].diff(t).subs({t:T})) for T in sorted(.5, .5±sqrt(3/5)/2),
		# weighted 5/18, 8/18, 5/18 respectively.
		v0 = abs(-0.492943519233745*c0 + 0.430331482911935*c1 + 0.0626120363218102*c2)
		v1 = abs(c2-c0)*0.4444444444444444
		v2 = abs(-0.0626120363218102*c0 - 0.430331482911935*c1 + 0.492943519233745*c2)

		self.value += v0 + v1 + v2

	def _qCurveToOne(self, p1, p2):
		p0 = self._getCurrentPoint()
		self._addQuadratic(complex(*p0), complex(*p1), complex(*p2))

	def _addCubicRecursive(self, p0, p1, p2, p3):
		arch = abs(p0-p3)
		box = abs(p0-p1) + abs(p1-p2) + abs(p2-p3)
		if arch * self._mult >= box:
			self.value += (arch + box) * .5
		else:
			one,two = _split_cubic_into_two(p0,p1,p2,p3)
			self._addCubicRecursive(*one)
			self._addCubicRecursive(*two)

	def _addCubicQuadrature(self, c0, c1, c2, c3):
		# Approximate length of cubic Bezier curve using Gauss-Lobatto quadrature
		# with n=5 points.
		#
		# This, essentially, approximates the length-of-derivative function
		# to be integrated with the best-matching seventh-degree polynomial
		# approximation of it.
		#
		# https://en.wikipedia.org/wiki/Gaussian_quadrature#Gauss.E2.80.93Lobatto_rules

		# abs(BezierCurveC[3].diff(t).subs({t:T})) for T in sorted(0, .5±(3/7)**.5/2, .5, 1),
		# weighted 1/20, 49/180, 32/90, 49/180, 1/20 respectively.
		v0 = abs(c1-c0)*.15
		v1 = abs(-0.558983582205757*c0 + 0.325650248872424*c1 + 0.208983582205757*c2 + 0.024349751127576*c3)
		v2 = abs(c3-c0+c2-c1)*0.26666666666666666
		v3 = abs(-0.024349751127576*c0 - 0.208983582205757*c1 - 0.325650248872424*c2 + 0.558983582205757*c3)
		v4 = abs(c3-c2)*.15

		self.value += v0 + v1 + v2 + v3 + v4

	def _curveToOne(self, p1, p2, p3):
		p0 = self._getCurrentPoint()
		self._addCubic(complex(*p0), complex(*p1), complex(*p2), complex(*p3))
