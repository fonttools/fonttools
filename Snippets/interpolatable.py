#! /usr/bin/env python

"""
Tool to find wront contour order between different masters, and
other interpolatability (or lack thereof) issues.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

from fontTools.pens.basePen import BasePen
from symfont import GlyphStatistics
from itertools import product

class PerContourOrComponentPen(BasePen):
	def __init__(self, Pen, glyphset=None):
		BasePen.__init__(self, glyphset)
		self._glyphset = glyphset
		self._Pen = Pen
		self.value = []
	def _moveTo(self, p0):
		self._newItem()
		self.value[-1].moveTo(p0)
	def _lineTo(self, p1):
		self.value[-1].lineTo(p1)
	def _qCurveToOne(self, p1, p2):
		self.value[-1].qCurveTo(p1, p2)
	def _curveToOne(self, p1, p2, p3):
		self.value[-1].curveTo(p1, p2, p3)
	def _closePath(self):
		self.value[-1].closePath()
	def _endPath(self):
		self.value[-1].endPath()
	def addComponent(self, glyphName, transformation):
		self._newItem()
		self.value[-1].addComponent(glyphName, transformation)

	def _newItem(self):
		self.value.append(self._Pen(glyphset=self._glyphset))

class RecordingPen(BasePen):
	def __init__(self, glyphset):
		BasePen.__init__(self, glyphset)
		self._glyphset = glyphset
		self.value = []
	def _moveTo(self, p0):
		self.value.append(('moveTo', (p0,)))
	def _lineTo(self, p1):
		self.value.append(('lineTo', (p1,)))
	def _qCurveToOne(self, p1, p2):
		self.value.append(('qCurveTo', (p1,p2)))
	def _curveToOne(self, p1, p2, p3):
		self.value.append(('curveTo', (p1,p2,p3)))
	def _closePath(self):
		self.value.append(('closePath', ()))
	def _endPath(self):
		self.value.append(('endPath', ()))
	# Humm, adding the following method slows things down some 20%.
	# We don't have as much control as we like currently.
	#def addComponent(self, glyphName, transformation):
	#	self.value.append(('addComponent', (glyphName, transformation)))

	def draw(self, pen):
		for operator,operands in self.value:
			getattr(pen, operator)(*operands)

def _dot(v0, v1):
	v = 0
	for p,q in zip(v0,v1):
		v += p*q
	return v

def test(glyphsets, glyphs=None):

	if glyphs is None:
		glyphs = glyphsets[0].keys()

	for glyph_name in glyphs:
		#print()
		#print("glyph:", glyph_name, end='')

		try:
			allVectors = []
			for glyphset in glyphsets:
				#print('.', end='')
				glyph = glyphset[glyph_name]

				perContourPen = PerContourOrComponentPen(RecordingPen, glyphset=glyphset)
				glyph.draw(perContourPen)
				contourPens = perContourPen.value
				del perContourPen

				contourVectors = []
				allVectors.append(contourVectors)
				for contour in contourPens:
					stats = GlyphStatistics(contour, glyphset=glyphset)
					vector = (
						#int(stats.Perimeter * .125),
						int(abs(stats.Area) ** .5 * .5),
						int(stats.MeanX),
						int(stats.MeanY),
						#int(stats.StdDevX * 2),
						#int(stats.StdDevY * 2),
						#int(stats.Covariance/(stats.StdDevX*stats.StdDevY)**.5),
					)
					contourVectors.append(vector)
					#print(vector)

			# Check each master against the next one in the list.
			for m0,m1 in zip(allVectors[:-1],allVectors[1:]):
				assert len(m0) == len(m1)
				# TODO Implement proper weighted bipartite matching
				while m0:
					n = len(m0)
					weights = [_dot(v0,v1) for v0,v1 in product(m0,m1)]
					maxWeight = max(weights)
					arg = weights.index(maxWeight)
					# Expect it to be on the diagonal
					row, col = arg // n, arg % n
					if row != col:
						print('Glyph has wrong contour/component order', glyph_name)#, m0, m1)
						break
					del m0[row], m1[col]


		except ValueError as e:
			print(' math error; skipping glyph', e)

def main(args):
	filenames = args
	glyphs = None
	#glyphs = ['uni08DB', 'uniFD76']
	from fontTools.ttLib import TTFont
	fonts = [TTFont(filename) for filename in filenames]
	glyphsets = [font.getGlyphSet() for font in fonts]
	test(glyphsets, glyphs=glyphs)

if __name__ == '__main__':
	import sys
	main(sys.argv[1:])
