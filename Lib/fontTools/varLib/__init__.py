"""Module for dealing with 'gvar'-style font variations,
also known as run-time interpolation."""

from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.ttLib.tables import _g_l_y_f as glyf


class MutatorModel(object):

	"""
	Locations must be in normalized space.  Ie. base master
	is at origin (0).
	"""

	def __init__(self, locations, axisOrder=[]):
		locations = [{k:v for k,v in loc.items() if v != 0.} for loc in locations]
		keyFunc = self.getMasterLocationsSortKeyFunc(locations, axisOrder=axisOrder)
		axisPoints = keyFunc.axisPoints
		self.locations = locations
		self.sortedLocations = sorted(locations, key=keyFunc)
		self.mapping = [locations.index(l) for l in self.sortedLocations]
		self.reverseMapping = [self.sortedLocations.index(l) for l in locations]

		self._computeMasterSupports(axisPoints)

	@staticmethod
	def getMasterLocationsSortKeyFunc(locations, axisOrder=[]):
		assert {} in locations, "Base master not found."
		axisPoints = {}
		for loc in locations:
			if len(loc) != 1:
				continue
			axis = next(iter(loc))
			value = loc[axis]
			if axis not in axisPoints:
				axisPoints[axis] = {0}
			assert value not in axisPoints[axis]
			axisPoints[axis].add(value)

		def getKey(axisPoints, axisOrder):
			def sign(v):
				return -1 if v < 0 else +1 if v > 0 else 0
			def key(loc):
				rank = len(loc)
				onPointAxes = [axis for axis,value in loc.items() if value in axisPoints[axis]]
				orderedAxes = [axis for axis in axisOrder if axis in loc]
				orderedAxes.extend([axis for axis in sorted(loc.keys()) if axis not in axisOrder])
				return (
					rank, # First, order by increasing rank
					-len(onPointAxes), # Next, by decreasing number of onPoint axes
					tuple(axisOrder.index(axis) if axis in axisOrder else 0x10000 for axis in orderedAxes), # Next, by known axes
					tuple(orderedAxes), # Next, by all axes
					tuple(sign(loc[axis]) for axis in orderedAxes), # Next, by signs of axis values
					tuple(abs(loc[axis]) for axis in orderedAxes), # Next, by absolute value of axis values
				)
			return key

		ret = getKey(axisPoints, axisOrder)
		ret.axisPoints = axisPoints
		return ret

	@staticmethod
	def lowerBound(value, lst):
		if any(v < value for v in lst):
			return max(v for v in lst if v < value)
		else:
			return value
	@staticmethod
	def upperBound(value, lst):
		if any(v > value for v in lst):
			return min(v for v in lst if v > value)
		else:
			return value

	def _computeMasterSupports(self, axisPoints):
		supports = []
		deltaWeights = []
		locations = self.sortedLocations
		for i,loc in enumerate(locations):
			box = {}

			# Account for axisPoints first
			for axis,values in axisPoints.items():
				if not axis in loc:
					continue
				locV = loc[axis]
				box[axis] = (self.lowerBound(locV, values), locV, self.upperBound(locV, values))

			locAxes = set(loc.keys())
			# Walk over previous masters now
			for j,m in enumerate(locations[:i]):
				# Master with extra axes do not participte
				if not set(m.keys()).issubset(locAxes):
					continue
				# If it's NOT in the current box, it does not participate
				relevant = True
				for axis, (lower,_,upper) in box.items():
					if axis in m and not (lower < m[axis] < upper):
						relevant = False
						break
				if not relevant:
					continue
				# Split the box for new master
				for axis,val in m.items():
					assert axis in box
					lower,locV,upper = box[axis]
					if val < locV:
						lower = val
					elif locV < val:
						upper = val
					box[axis] = (lower,locV,upper)
			supports.append(box)

			deltaWeight = []
			# Walk over previous masters now, populate deltaWeight
			for j,m in enumerate(locations[:i]):
				scalar = 1.
				support = supports[j]
				for axis,v in m.items():
					lower, peak, upper = support[axis]
					if axis not in loc:
						scalar = 0.
						break
					v = loc[axis]
					if v == peak:
						continue
					if v <= lower or upper <= v:
						scalar = 0.
						break;
					if v < peak:
						scalar *= (v - peak) / (lower - peak)
					else: # v > peak
						scalar *= (v - peak) / (upper - peak)
				deltaWeight.append(-scalar)
			deltaWeight.append(+1.)
			deltaWeights.append(deltaWeight)

		mapping = self.reverseMapping
		self.supports = [supports[mapped] for mapped in mapping]
		mapping = self.mapping
		self.deltaWeights = {mapping[i]:{mapping[i]:off for i,off in enumerate(deltaWeight) if off != 0.}
				     for i,deltaWeight in enumerate(deltaWeights)}

	def deltas(self, deltas):
		return


locations = [
{'wght':100},
{'wght':-100},
{'wght':-180},
{'wdth':+.3},
{'wght':+120,'wdth':.3},
{'wght':+120,'wdth':.2},
{},
{'wght':+180,'wdth':.3},
{'wght':+180},
]
model = MutatorModel(locations, axisOrder=['wght'])
assert model.sortedLocations == \
[{},
 {u'wght': -100},
 {u'wght': -180},
 {u'wght': 100},
 {u'wght': 180},
 {u'wdth': 0.3},
 {u'wdth': 0.3, u'wght': 180},
 {u'wdth': 0.3, u'wght': 120},
 {u'wdth': 0.2, u'wght': 120},
]
from pprint import pprint
pprint(model.locations)
pprint(model.supports)
pprint(model.deltaWeights)
