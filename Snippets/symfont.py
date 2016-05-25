#! /usr/bin/env python

"""
Pen to calculate geometrical glyph statistics.

When this is fully fleshed out, it will be moved to a more prominent
place, like fontTools.pens.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

import sympy as sp
import math
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Scale
from fontTools.misc.bezierTools import splitCubicAtT
from functools import partial

n = 3 # Max Bezier degree; 3 for cubic, 2 for quadratic

t, x, y = sp.symbols('t x y', real=True)

P = tuple(sp.symbols('P[:%d][:2]' % (n+1), real=True))
P = tuple(P[2*i:2*(i+1)] for i in range(len(P) // 2))

# Cubic Bernstein basis functions
BinomialCoefficient = [(1, 0)]
for i in range(1, n+1):
	last = BinomialCoefficient[-1]
	this = tuple(last[j-1]+last[j] for j in range(len(last)))+(0,)
	BinomialCoefficient.append(this)
BinomialCoefficient = tuple(tuple(item[:-1]) for item in BinomialCoefficient)

BernsteinPolynomial = tuple(
	tuple(c * t**i * (1-t)**(n-i) for i,c in enumerate(coeffs))
	for n,coeffs in enumerate(BinomialCoefficient))

BezierCurve = tuple(
	tuple(sum(P[i][j]*bernstein for i,bernstein in enumerate(bernsteins))
		for j in range(2))
	for n,bernsteins in enumerate(BernsteinPolynomial))

def green(f, Bezier=BezierCurve[n]):
	f1 = sp.integrate(f, y)
	f2 = f1.replace(y, Bezier[1]).replace(x, Bezier[0])
	return sp.integrate(f2 * sp.diff(Bezier[0], t), (t, 0, 1))

def lambdify(f):
	return sp.lambdify('P', f)

class BezierFuncs(object):

	def __init__(self, symfunc):
		self._symfunc = symfunc
		self._bezfuncs = {}

	def __getitem__(self, i):
		if i not in self._bezfuncs:
			self._bezfuncs[i] = lambdify(green(self._symfunc, Bezier=BezierCurve[i]))
		return self._bezfuncs[i]

_BezierFuncs = {}

def getGreenBezierFuncs(func):
	func = sp.sympify(func)
	funcstr = str(func)
	global _BezierFuncs
	if not funcstr in _BezierFuncs:
		_BezierFuncs[funcstr] = BezierFuncs(func)
	return _BezierFuncs[funcstr]

class GreenPen(BasePen):

	def __init__(self, func, glyphset=None):
		BasePen.__init__(self, glyphset)
		self._funcs = getGreenBezierFuncs(func)
		self.value = 0

	def _segment(self, *P):
		self.value += self._funcs[len(P) - 1](P)

	def _moveTo(self, p0):
		self._segment(p0)

	def _lineTo(self, p1):
		p0 = self._getCurrentPoint()
		self._segment(p0,p1)

	def _qCurveToOne(self, p1, p2):
		p0 = self._getCurrentPoint()
		self._segment(p0,p1,p2)

	def _curveToOne(self, p1, p2, p3):
		p0 = self._getCurrentPoint()
		self._segment(p0,p1,p2,p3)

AreaPen = partial(GreenPen, func=1)
Moment1XPen = partial(GreenPen, func=x)
Moment1YPen = partial(GreenPen, func=y)
Moment2XXPen = partial(GreenPen, func=x*x)
Moment2YYPen = partial(GreenPen, func=y*y)
Moment2XYPen = partial(GreenPen, func=x*y)

def distance(p0, p1):
	return math.hypot(p0[0] - p1[0], p0[1] - p1[1])

class PerimeterPen(BasePen):

	def __init__(self, tolerance=0.005, glyphset=None):
		BasePen.__init__(self, glyphset)
		self.value = 0
		self._mult = 1.+tolerance

	def _moveTo(self, p0):
		pass

	def _lineTo(self, p1):
		p0 = self._getCurrentPoint()
		self.value += distance(p0, p1)

	def _addCubic(self, p0, p1, p2, p3):
		arch = distance(p0, p3)
		box = distance(p0, p1) + distance(p1, p2) + distance(p2, p3)
		if arch * self._mult >= box:
			self.value += (arch + box) * .5
		else:
			for c in splitCubicAtT(p0,p1,p2,p3,.5):
				self._addCubic(*c)

	def _curveToOne(self, p1, p2, p3):
		p0 = self._getCurrentPoint()
		self._addCubic(p0, p1, p2, p3)

class GlyphStatistics(object):

	def __init__(self, glyph, transform=None, glyphset=None):
		self._glyph = glyph
		self._glyphset = glyphset
		self._transform = transform

	def _penAttr(self, attr):
		internalName = '_'+attr
		if internalName not in self.__dict__:
			Pen = globals()[attr+'Pen']
			pen = transformer = Pen(glyphset=self._glyphset)
			if self._transform:
				transformer = TransformPen(pen, self._transform)
			self._glyph.draw(transformer)
			self.__dict__[internalName] = pen.value
		return self.__dict__[internalName]

	Area = property(partial(_penAttr, attr='Area'))
	Perimeter = property(partial(_penAttr, attr='Perimeter'))
	Moment1X = property(partial(_penAttr, attr='Moment1X'))
	Moment1Y = property(partial(_penAttr, attr='Moment1Y'))
	Moment2XX = property(partial(_penAttr, attr='Moment2XX'))
	Moment2YY = property(partial(_penAttr, attr='Moment2YY'))
	Moment2XY = property(partial(_penAttr, attr='Moment2XY'))

	# TODO Memoize properties below

	# Center of mass
	# https://en.wikipedia.org/wiki/Center_of_mass#A_continuous_volume
	@property
	def MeanX(self):
		return self.Moment1X / self.Area
	@property
	def MeanY(self):
		return self.Moment1Y / self.Area

	# https://en.wikipedia.org/wiki/Second_moment_of_area

	#  Var(X) = E[X^2] - E[X]^2
	@property
	def VarianceX(self):
		return self.Moment2XX / self.Area - self.MeanX**2
	@property
	def VarianceY(self):
		return self.Moment2YY / self.Area - self.MeanY**2
	
	@property
	def StdDevX(self):
		return self.VarianceX**.5
	@property
	def StdDevY(self):
		return self.VarianceY**.5

	#  Covariance(X,Y) = ( E[X.Y] - E[X]E[Y] )
	@property
	def Covariance(self):
		return self.Moment2XY / self.Area - self.MeanX*self.MeanY

	@property
	def _CovarianceMatrix(self):
		cov = self.Covariance
		return ((self.VarianceX, cov), (cov, self.VarianceY))

	@property
	def _Eigen(self):
		mat = self.CovarianceMatrix
		from numpy.linalg import eigh
		vals,vecs = eigh(mat)
		# Note: we return eigen-vectors row-major, unlike Matlab, et al
		return tuple(vals), tuple(tuple(row) for row in vecs)

	#  Correlation(X,Y) = Covariance(X,Y) / ( StdDev(X) * StdDev(Y)) )
	# https://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient
	@property
	def Correlation(self):
		corr = self.Covariance / (self.StdDevX * self.StdDevY)
		if abs(corr) < 1e-3: corr = 0
		return corr

	@property
	def Slant(self):
		slant = self.Covariance / self.VarianceY
		if abs(slant) < 1e-3: slant = 0
		return slant


def test(glyphset, upem, glyphs):
	print('upem', upem)

	for glyph_name in glyphs:
		print()
		print("glyph:", glyph_name)
		glyph = glyphset[glyph_name]
		stats = GlyphStatistics(glyph, transform=Scale(1./upem), glyphset=glyphset)
		for item in dir(stats):
			if item[0] == '_': continue
			print ("%s: %g" % (item, getattr(stats, item)))


def main(args):
	filename, glyphs = args[0], args[1:]
	if not glyphs:
		glyphs = ['e', 'o', 'I', 'slash', 'E', 'zero', 'eight', 'minus', 'equal']
	from fontTools.ttLib import TTFont
	font = TTFont(filename)
	glyphset = font.getGlyphSet()
	test(font.getGlyphSet(), font['head'].unitsPerEm, glyphs)

if __name__ == '__main__':
	import sys
	main(sys.argv[1:])
