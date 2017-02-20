#! /usr/bin/env python

"""
Pen to calculate geometrical glyph statistics.

When this is fully fleshed out, it will be moved to a more prominent
place, like fontTools.pens.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

import sympy as sp
import sys
import math
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.perimeterPen import PerimeterPen
from momentsPen import MomentsPen
from fontTools.pens.areaPen import AreaPen
from fontTools.misc.transform import Scale
from functools import partial
from itertools import count

n = 3 # Max Bezier degree; 3 for cubic, 2 for quadratic

t, x, y = sp.symbols('t x y', real=True)
c = sp.symbols('c', real=False) # Complex representation instead of x/y

P = tuple(zip(*(sp.symbols('%s:%d'%(w,n+1), real=True) for w in 'xy')))
C = tuple(sp.symbols('c:%d'%(n+1), real=False))

# Cubic Bernstein basis functions
BinomialCoefficient = [(1, 0)]
for i in range(1, n+1):
	last = BinomialCoefficient[-1]
	this = tuple(last[j-1]+last[j] for j in range(len(last)))+(0,)
	BinomialCoefficient.append(this)
BinomialCoefficient = tuple(tuple(item[:-1]) for item in BinomialCoefficient)
del last, this

BernsteinPolynomial = tuple(
	tuple(c * t**i * (1-t)**(n-i) for i,c in enumerate(coeffs))
	for n,coeffs in enumerate(BinomialCoefficient))

BezierCurve = tuple(
	tuple(sum(P[i][j]*bernstein for i,bernstein in enumerate(bernsteins))
		for j in range(2))
	for n,bernsteins in enumerate(BernsteinPolynomial))
BezierCurveC = tuple(
	sum(C[i]*bernstein for i,bernstein in enumerate(bernsteins))
	for n,bernsteins in enumerate(BernsteinPolynomial))

def green(f, curveXY, optimize=True):
	f = -sp.integrate(sp.sympify(f), y)
	f = f.subs({x:curveXY[0], y:curveXY[1]})
	f = sp.integrate(f * sp.diff(curveXY[0], t), (t, 0, 1))
	if optimize:
		f = sp.gcd_terms(f.collect(sum(P,())))
	return f

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
			self._bezfuncs[i] = sp.lambdify(args, green(self._symfunc, BezierCurve[i]))
		return self._bezfuncs[i]

_BezierFuncs = {}

def getGreenBezierFuncs(func):
	funcstr = str(func)
	global _BezierFuncs
	if not funcstr in _BezierFuncs:
		_BezierFuncs[funcstr] = BezierFuncs(func)
	return _BezierFuncs[funcstr]

def printCache(func, file=sys.stdout):
	funcstr = str(func)
	print("_BezierFuncs['%s'] = [" % funcstr, file=file)
	for i in range(n+1):
		print('	lambda P:', green(func, BezierCurve[i]), ',')
	print(']', file=file)

def printPen(name, funcs, file=sys.stdout):
	print(
'''from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

from fontTools.pens.basePen import BasePen

class {name}(BasePen):

	def __init__(self, glyphset=None):
		BasePen.__init__(self, glyphset)
'''.format(name=name), file=file)
	for name,f in funcs:
		print('		self.%s = 0' % name, file=file)
	print('''
	def _moveTo(self, p0):
		self.__startPoint = p0

	def _closePath(self):
		p0 = self._getCurrentPoint()
		if p0 != self.__startPoint:
			p1 = self.__startPoint
			self._lineTo(p1)''', file=file)

	for n in (1, 2, 3):

		if n == 1:
			print('''
	def _lineTo(self, p1):
		x0,y0 = self._getCurrentPoint()
		x1,y1 = p1
''', file=file)
		elif n == 2:
			print('''
	def _qCurveToOne(self, p1, p2):
		x0,y0 = self._getCurrentPoint()
		x1,y1 = p1
		x2,y2 = p2
''', file=file)
		elif n == 3:
			print('''
	def _curveToOne(self, p1, p2, p3):
		x0,y0 = self._getCurrentPoint()
		x1,y1 = p1
		x2,y2 = p2
		x3,y3 = p3
''', file=file)
		defs, exprs = sp.cse([green(f, BezierCurve[n]) for name,f in funcs],
				     optimizations='basic',
				     symbols=(sp.Symbol('r%d'%i) for i in count()))
		for name,value in defs:
			print('		%s = %s' % (name, value), file=file)
		print(file=file)
		for name,value in zip([f[0] for f in funcs], exprs):
			print('		self.%s += %s' % (name, value), file=file)

#printPen('MomentsPen',
#	 [('area', 1),
#	  ('momentX', x),
#	  ('momentY', y),
#	  ('momentXX', x*x),
#	  ('momentXY', x*y),
#	  ('momentYY', y*y)])

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

		pen = transformer = PerimeterPen(glyphset=self._glyphset)
		if self._transform:
			transformer = TransformPen(pen, self._transform)
		self._glyph.draw(transformer)
		self.Perimeter = pen.value

		Pen = MomentsPen
		pen = transformer = Pen(glyphset=self._glyphset)
		if self._transform:
			transformer = TransformPen(pen, self._transform)
		self._glyph.draw(transformer)
		self.m = m = pen

		self.Area = area = m.area
		self.Moment1X = m.momentX
		self.Moment1Y = m.momentY
		self.Moment2XX = m.momentXX
		self.Moment2XY = m.momentXY
		self.Moment2YY = m.momentYY

		if not area:
			self.MeanX = 0.
			self.MeanY = 0.
			self.VarianceX = 0.
			self.VarianceY = 0.
			self.StdDevX = 0.
			self.StdDevY = 0.
			self.Covariance = 0.
			self.Correlation = 0.
			self.Slant = 0.
			return

		# Center of mass
		# https://en.wikipedia.org/wiki/Center_of_mass#A_continuous_volume
		self.MeanX = self.Moment1X / area
		self.MeanY = self.Moment1Y / area

		#  Var(X) = E[X^2] - E[X]^2
		self.VarianceX = self.Moment2XX / area - self.MeanX**2
		self.VarianceY = self.Moment2YY / area - self.MeanY**2

		self.StdDevX = math.copysign(abs(self.VarianceX)**.5, self.VarianceX)
		self.StdDevY = math.copysign(abs(self.VarianceY)**.5, self.VarianceY)

		#  Covariance(X,Y) = ( E[X.Y] - E[X]E[Y] )
		self.Covariance = self.Moment2XY / area - self.MeanX*self.MeanY

		#  Correlation(X,Y) = Covariance(X,Y) / ( StdDev(X) * StdDev(Y)) )
		# https://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient
		corr = self.Covariance / (self.StdDevX * self.StdDevY)
		self.Correlation = corr if abs(corr) > 1e-3 else 0

		slant = self.Covariance / self.VarianceY
		self.Slant = slant if abs(slant) > 1e-3 else 0


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
	if not args:
		return
	filename, glyphs = args[0], args[1:]
	if not glyphs:
		glyphs = ['e', 'o', 'I', 'slash', 'E', 'zero', 'eight', 'minus', 'equal']
	from fontTools.ttLib import TTFont
	font = TTFont(filename)
	test(font.getGlyphSet(), font['head'].unitsPerEm, glyphs)

if __name__ == '__main__':
	import sys
	main(sys.argv[1:])
