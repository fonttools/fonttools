"""Variation fonts interpolation models."""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

__all__ = ['normalizeLocation', 'supportScalar', 'VariationModel']

def normalizeLocation(location, axes):
	"""Normalizes location based on axis min/default/max values from axes."""
	out = {}
	for tag,(lower,default,upper) in axes.items():
		v = location.get(tag, default)
		if v == default:
			v = 0
		elif v < default:
			v = (max(v, lower) - default) / (default - lower)
		else:
			v = (min(v, upper) - default) / (upper - default)
		out[tag] = v
	return out

def supportScalar(location, support):
	"""Returns the scalar multiplier at location, for a master
	with support.
	>>> supportScalar({}, {})
	1.0
	>>> supportScalar({'wght':.2}, {})
	1.0
	>>> supportScalar({'wght':.2}, {'wght':(0,2,3)})
	0.1
	>>> supportScalar({'wght':2.5}, {'wght':(0,2,4)})
	0.75
	"""
	scalar = 1.
	for axis,(lower,peak,upper) in support.items():
		if axis not in location:
			scalar = 0.
			break
		v = location[axis]
		if v == peak:
			continue
		if v <= lower or upper <= v:
			scalar = 0.
			break;
		if v < peak:
			scalar *= (v - lower) / (peak - lower)
		else: # v > peak
			scalar *= (v - upper) / (peak - upper)
	return scalar


class VariationModel(object):

	"""
	Locations must be in normalized space.  Ie. base master
	is at origin (0).
	>>> from pprint import pprint
	>>> locations = [ \
	{'wght':100}, \
	{'wght':-100}, \
	{'wght':-180}, \
	{'wdth':+.3}, \
	{'wght':+120,'wdth':.3}, \
	{'wght':+120,'wdth':.2}, \
	{}, \
	{'wght':+180,'wdth':.3}, \
	{'wght':+180}, \
	]
	>>> model = VariationModel(locations, axisOrder=['wght'])
	>>> pprint(model.locations)
	[{},
	 {'wght': -100},
	 {'wght': -180},
	 {'wght': 100},
	 {'wght': 180},
	 {'wdth': 0.3},
	 {'wdth': 0.3, 'wght': 180},
	 {'wdth': 0.3, 'wght': 120},
	 {'wdth': 0.2, 'wght': 120}]
	>>> pprint(model.deltaWeights)
	[{},
	 {0: 1.0},
	 {0: 1.0},
	 {0: 1.0},
	 {0: 1.0},
	 {0: 1.0},
	 {0: 1.0, 4: 1.0, 5: 1.0},
	 {0: 1.0, 3: 0.75, 4: 0.25, 5: 1.0, 6: 0.25},
	 {0: 1.0,
	  3: 0.75,
	  4: 0.25,
	  5: 0.6666666666666667,
	  6: 0.16666666666666669,
	  7: 0.6666666666666667}]
	"""

	def __init__(self, locations, axisOrder=[]):
		locations = [{k:v for k,v in loc.items() if v != 0.} for loc in locations]
		keyFunc = self.getMasterLocationsSortKeyFunc(locations, axisOrder=axisOrder)
		axisPoints = keyFunc.axisPoints
		self.locations = sorted(locations, key=keyFunc)
		# TODO Assert that locations are unique.
		self.mapping = [self.locations.index(l) for l in locations] # Mapping from user's master order to our master order
		self.reverseMapping = [locations.index(l) for l in self.locations] # Reverse of above

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
		locations = self.locations
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

			deltaWeight = {}
			# Walk over previous masters now, populate deltaWeight
			for j,m in enumerate(locations[:i]):
				scalar = supportScalar(loc, supports[j])
				if scalar:
					deltaWeight[j] = scalar
			deltaWeights.append(deltaWeight)

		self.supports = supports
		self.deltaWeights = deltaWeights

	def getDeltas(self, masterValues):
		count = len(self.locations)
		assert len(masterValues) == len(self.deltaWeights)
		mapping = self.reverseMapping
		out = []
		for i,weights in enumerate(self.deltaWeights):
			delta = masterValues[mapping[i]]
			for j,weight in weights.items():
				delta -= out[j] * weight
			out.append(delta)
		return out

	def interpolateFromDeltas(self, loc, deltas):
		v = None
		supports = self.supports
		assert len(deltas) == len(supports)
		for i,(delta,support) in enumerate(zip(deltas, supports)):
			scalar = supportScalar(loc, support)
			if not scalar: continue
			contribution = delta * scalar
			if i == 0:
				v = contribution
			else:
				v += contribution
		return v

	def interpolateFromMasters(self, loc, masterValues):
		deltas = self.getDeltas(masterValues)
		return self.interpolateFromDeltas(loc, deltas)
