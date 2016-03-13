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
from functools import partial

n = 3 # Max Bezier degree; 3 for cubic, 2 for quadratic

t, x, y = sp.symbols('t x y', real=True)
Psymbol = sp.symbols('P')

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
	tuple(sum(P[i][j]*berstein for i,berstein in enumerate(bersteins))
		for j in range(2))
	for n,bersteins in enumerate(BernsteinPolynomial))

def green(f, Bezier=BezierCurve[n]):
	f1 = sp.integrate(f, y)
	f2 = f1.replace(y, Bezier[1]).replace(x, Bezier[0])
	return sp.integrate(f2 * sp.diff(Bezier[0], t), (t, 0, 1))

def lambdify(f):
	return sp.lambdify(Psymbol, f)

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

	def __init__(self, glyphset, func, scale=1):
		BasePen.__init__(self, glyphset)
		self._funcs = getGreenBezierFuncs(func)
		self._scale = scale
		self.value = 0

	def _segment(self, *P):
		scale = self._scale
		P = tuple((x/scale,y/scale) for x,y in P)
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

class GlyphStatistics(object):

	def __init__(self, glyph, glyphset=None, scale=1):
		self._glyph = glyph
		self._glyphset = glyphset
		self._scale = scale

	def _penAttr(self, attr):
		internalName = '_'+attr
		if internalName not in self.__dict__:
			Pen = globals()[attr+'Pen']
			pen = Pen(self._glyphset, scale=self._scale)
			self._glyph.draw(pen)
			self.__dict__[internalName] = pen.value
		return self.__dict__[internalName]

	Area = property(partial(_penAttr, attr='Area'))
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
		stats = GlyphStatistics(glyph, glyphset, scale=upem)
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
