#! /usr/bin/env python

"""
Tool to find wront contour order between different masters, and
other interpolatability (or lack thereof) issues.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

from fontTools.pens.basePen import BasePen
from symfont import GlyphStatistics
import itertools

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

def _vdiff(v0, v1):
	return tuple(b-a for a,b in zip(v0,v1))
def _vlen(vec):
	v = 0
	for x in vec:
		v += x*x
	return v

def _matching_cost(G, matching):
	return sum(G[i][j] for i,j in enumerate(matching))

def min_cost_perfect_bipartite_matching(G):
	n = len(G)
	if n <= 8:
		# brute-force
		permutations = itertools.permutations(range(n))
		best = list(next(permutations))
		best_cost = _matching_cost(G, best)
		for p in permutations:
			cost = _matching_cost(G, p)
			if cost < best_cost:
				best, best_cost = list(p), cost
		return best, best_cost
	else:

		# Set up current matching and inverse
		matching = list(range(n)) # identity matching
		matching_cost = _matching_cost(G, matching)
		reverse = list(matching)

		return matching, matching_cost
		# TODO implement real matching here

		# Set up cover
		cover0 = [max(c for c in row) for row in G]
		cover1 = [0] * n
		cover_weight = sum(cover0)

		while cover_weight < matching_cost:
			break
			NotImplemented

		return matching, matching_cost


def test(glyphsets, glyphs=None, names=None):

	if names is None:
		names = glyphsets
	if glyphs is None:
		glyphs = glyphsets[0].keys()

	hist = []
	for glyph_name in glyphs:
		#print()
		#print(glyph_name)

		try:
			allVectors = []
			for glyphset in glyphsets:
				#print('.', end='')
				#print()
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
						int(stats.Perimeter * .125),
						int(abs(stats.Area) ** .5 * .5),
						int(stats.MeanX),
						int(stats.MeanY),
						int(stats.StdDevX * 2),
						int(stats.StdDevY * 2),
						int(stats.Covariance/(stats.StdDevX*stats.StdDevY)**.5),
					)
					contourVectors.append(vector)
					#print(vector)

			# Check each master against the next one in the list.
			for i,(m0,m1) in enumerate(zip(allVectors[:-1],allVectors[1:])):
				if len(m0) != len(m1):
					print('%s: %s+%s: Glyphs not compatible!!!!!' % (glyph_name, names[i], names[i+1]))
					continue
				if not m0:
					continue
				costs = [[_vlen(_vdiff(v0,v1)) for v1 in m1] for v0 in m0]
				matching, matching_cost = min_cost_perfect_bipartite_matching(costs)
				if matching != list(range(len(m0))):
					print('%s: %s+%s: Glyph has wrong contour/component order: %s' % (glyph_name, names[i], names[i+1], matching)) #, m0, m1)
					break
				upem = 2048
				item_cost = int(round((matching_cost / len(m0) / len(m0[0])) ** .5 / upem * 100))
				hist.append(item_cost)
				threshold = 7
				if item_cost >= threshold:
					print('%s: %s+%s: Glyph has very high cost: %d%%' % (glyph_name, names[i], names[i+1], item_cost))


		except ValueError as e:
			print('%s: math error %s; skipping glyph' % (glyph_name, e))
			#raise
	#for x in hist:
	#	print(x)

def main(args):
	filenames = args
	glyphs = None
	#glyphs = ['uni08DB', 'uniFD76']
	#glyphs = ['uni08DE', 'uni0034']
	#glyphs = ['uni08DE', 'uni0034', 'uni0751', 'uni0753', 'uni0754', 'uni08A4', 'uni08A4.fina', 'uni08A5.fina']

	from os.path import basename
	names = [basename(filename).rsplit('.', 1)[0] for filename in filenames]

	from fontTools.ttLib import TTFont
	fonts = [TTFont(filename) for filename in filenames]

	glyphsets = [font.getGlyphSet() for font in fonts]
	test(glyphsets, glyphs=glyphs, names=names)

if __name__ == '__main__':
	import sys
	main(sys.argv[1:])
