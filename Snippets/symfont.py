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
from fontTools.pens.perimeterPen import PerimeterPen
from fontTools.pens.areaPen import AreaPen
from fontTools.misc.transform import Scale
from fontTools.misc.bezierTools import splitQuadraticAtT, splitCubicAtT
from functools import partial

n = 3 # Max Bezier degree; 3 for cubic, 2 for quadratic

t, x, y = sp.symbols('t x y', real=True)

P = tuple(zip(*(sp.symbols('%s:%d'%(w,n+1), real=True) for w in 'xy')))

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
	f1 = -sp.integrate(sp.sympify(f), y)
	f2 = f1.subs({x:Bezier[0], y:Bezier[1]})
	return sp.integrate(f2 * sp.diff(Bezier[0], t), (t, 0, 1))

class BezierFuncs(object):

	def __init__(self, symfunc):
		self._symfunc = symfunc
		self._bezfuncs = {}

	def __getitem__(self, i):
		if i not in self._bezfuncs:
			args = []
			for d in range(i+1):
				args.append('x%d' % d)
				args.append('y%d' % d)
			self._bezfuncs[i] = sp.lambdify(args, green(self._symfunc, Bezier=BezierCurve[i]))
		return self._bezfuncs[i]

_BezierFuncs = {}

def getGreenBezierFuncs(func):
	funcstr = str(func)
	global _BezierFuncs
	if not funcstr in _BezierFuncs:
		_BezierFuncs[funcstr] = BezierFuncs(func)
	return _BezierFuncs[funcstr]

def printCache(func):
	funcstr = str(func)
	print("_BezierFuncs['%s'] = [" % funcstr)
	for i in range(n+1):
		print('	lambda P:', green(func, Bezier=BezierCurve[i]), ',')
	print(']')

class GreenPen(BasePen):

	def __init__(self, func, glyphset=None):
		BasePen.__init__(self, glyphset)
		self._funcs = getGreenBezierFuncs(func)
		self.value = 0

	def _moveTo(self, p0):
		self.__startPoint = p0

	def _lineTo(self, p1):
		p0 = self._getCurrentPoint()
		self.value += self._funcs[1](p0[0],p0[1],p1[0],p1[1])

	def _qCurveToOne(self, p1, p2):
		p0 = self._getCurrentPoint()
		self.value += self._funcs[2](p0[0],p0[1],p1[0],p1[1],p2[0],p2[1])

	def _curveToOne(self, p1, p2, p3):
		p0 = self._getCurrentPoint()
		self.value += self._funcs[3](p0[0],p0[1],p1[0],p1[1],p2[0],p2[1],p3[0],p3[1])

	def _closePath(self):
		p0 = self._getCurrentPoint()
		if p0 != self.__startPoint:
			p1 = self.__startPoint
			self.value += self._funcs[1](p0[0],p0[1],p1[0],p1[1])

#AreaPen = partial(GreenPen, func=1)
Moment1XPen = partial(GreenPen, func=x)
Moment1YPen = partial(GreenPen, func=y)
Moment2XXPen = partial(GreenPen, func=x*x)
Moment2YYPen = partial(GreenPen, func=y*y)
Moment2XYPen = partial(GreenPen, func=x*y)



#
# Glyph statistics object
#

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
	test(font.getGlyphSet(), font['head'].unitsPerEm, glyphs)

if __name__ == '__main__':
	import sys
	main(sys.argv[1:])
