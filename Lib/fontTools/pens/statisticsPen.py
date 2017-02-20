from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import math
from fontTools.pens.momentsPen import MomentsPen

class StatisticsPen(MomentsPen):

	# Center of mass
	# https://en.wikipedia.org/wiki/Center_of_mass#A_continuous_volume
	@property
	def meanX(self):
		return self.momentX / self.area if self.area else 0
	@property
	def meanY(self):
		return self.momentY / self.area if self.area else 0

	#  Var(X) = E[X^2] - E[X]^2
	@property
	def varianceX(self):
		return self.momentXX / self.area - self.meanX**2 if self.area else 0
	@property
	def varianceY(self):
		return self.momentYY / self.area - self.meanY**2 if self.area else 0

	@property
	def stddevX(self):
		return math.copysign(abs(self.varianceX)**.5, self.varianceX)
	@property
	def stddevY(self):
		return math.copysign(abs(self.varianceY)**.5, self.varianceY)

	#  Covariance(X,Y) = ( E[X.Y] - E[X]E[Y] )
	@property
	def covariance(self):
		return self.momentXY / self.area - self.meanX*self.meanY if self.area else 0

	#  Correlation(X,Y) = Covariance(X,Y) / ( stddev(X) * stddev(Y) )
	# https://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient
	@property
	def correlation(self):
		correlation = self.covariance / (self.stddevX * self.stddevY) if self.area else 0
		return correlation if abs(correlation) > 1e-3 else 0

	@property
	def slant(self):
		slant = self.covariance / self.varianceY if self.area else 0
		return slant if abs(slant) > 1e-3 else 0


def _test(glyphset, upem, glyphs):
	from fontTools.pens.transformPen import TransformPen
	from fontTools.misc.transform import Scale

	print('upem', upem)

	for glyph_name in glyphs:
		print()
		print("glyph:", glyph_name)
		glyph = glyphset[glyph_name]
		pen = StatisticsPen(glyphset=glyphset)
		transformer = TransformPen(pen, Scale(1./upem))
		glyph.draw(transformer)
		for item in ['area', 'momentX', 'momentY', 'momentXX', 'momentYY', 'momentXY', 'meanX', 'meanY', 'varianceX', 'varianceY', 'stddevX', 'stddevY', 'covariance', 'correlation', 'slant']:
			if item[0] == '_': continue
			print ("%s: %g" % (item, getattr(pen, item)))

def main(args):
	if not args:
		return
	filename, glyphs = args[0], args[1:]
	if not glyphs:
		glyphs = ['e', 'o', 'I', 'slash', 'E', 'zero', 'eight', 'minus', 'equal']
	from fontTools.ttLib import TTFont
	font = TTFont(filename)
	_test(font.getGlyphSet(), font['head'].unitsPerEm, glyphs)

if __name__ == '__main__':
	import sys
	main(sys.argv[1:])
