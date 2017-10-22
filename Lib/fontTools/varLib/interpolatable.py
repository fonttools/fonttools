"""
Tool to find wrong contour order between different masters, and
other interpolatability (or lack thereof) issues.

Call as:
$ fonttools varLib.interpolatable font1 font2 ...
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

from fontTools.pens.basePen import AbstractPen, BasePen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.statisticsPen import StatisticsPen
import itertools


class PerContourPen(BasePen):
	def __init__(self, Pen, glyphset=None):
		BasePen.__init__(self, glyphset)
		self._glyphset = glyphset
		self._Pen = Pen
		self._pen = None
		self.value = []
	def _moveTo(self, p0):
		self._newItem()
		self._pen.moveTo(p0)
	def _lineTo(self, p1):
		self._pen.lineTo(p1)
	def _qCurveToOne(self, p1, p2):
		self._pen.qCurveTo(p1, p2)
	def _curveToOne(self, p1, p2, p3):
		self._pen.curveTo(p1, p2, p3)
	def _closePath(self):
		self._pen.closePath()
		self._pen = None
	def _endPath(self):
		self._pen.endPath()
		self._pen = None

	def _newItem(self):
		self._pen = pen = self._Pen()
		self.value.append(pen)

class PerContourOrComponentPen(PerContourPen):

	def addComponent(self, glyphName, transformation):
		self._newItem()
		self.value[-1].addComponent(glyphName, transformation)


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
	try:
		from scipy.optimize import linear_sum_assignment
		rows, cols = linear_sum_assignment(G)
		assert (rows == list(range(n))).all()
		return list(cols), _matching_cost(G, cols)
	except ImportError:
		pass

	try:
		from munkres import Munkres
		cols = [None] * n
		for row,col in Munkres().compute(G):
			cols[row] = col
		return cols, _matching_cost(G, cols)
	except ImportError:
		pass

	if n > 6:
		raise Exception("Install Python module 'munkres' or 'scipy >= 0.17.0'")

	# Otherwise just brute-force
	permutations = itertools.permutations(range(n))
	best = list(next(permutations))
	best_cost = _matching_cost(G, best)
	for p in permutations:
		cost = _matching_cost(G, p)
		if cost < best_cost:
			best, best_cost = list(p), cost
	return best, best_cost


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
			for glyphset,name in zip(glyphsets, names):
				#print('.', end='')
				glyph = glyphset[glyph_name]

				perContourPen = PerContourOrComponentPen(RecordingPen, glyphset=glyphset)
				glyph.draw(perContourPen)
				contourPens = perContourPen.value
				del perContourPen

				contourVectors = []
				allVectors.append(contourVectors)
				for contour in contourPens:
					stats = StatisticsPen(glyphset=glyphset)
					contour.replay(stats)
					size = abs(stats.area) ** .5 * .5
					vector = (
						int(size),
						int(stats.meanX),
						int(stats.meanY),
						int(stats.stddevX * 2),
						int(stats.stddevY * 2),
						int(stats.correlation * size),
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
				item_cost = round((matching_cost / len(m0) / len(m0[0])) ** .5 / upem * 100)
				hist.append(item_cost)
				threshold = 7
				if item_cost >= threshold:
					print('%s: %s+%s: Glyph has very high cost: %d%%' % (glyph_name, names[i], names[i+1], item_cost))


		except ValueError as e:
			print('%s: %s: math error %s; skipping glyph.' % (glyph_name, name, e))
			print(contour.value)
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
