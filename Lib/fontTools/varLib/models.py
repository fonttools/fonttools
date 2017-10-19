"""Variation fonts interpolation models."""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

__all__ = ['normalizeValue', 'normalizeLocation', 'supportScalar', 'VariationModel']

def normalizeValue(v, triple):
	"""Normalizes value based on a min/default/max triple.
	>>> normalizeValue(400, (100, 400, 900))
	0.0
	>>> normalizeValue(100, (100, 400, 900))
	-1.0
	>>> normalizeValue(650, (100, 400, 900))
	0.5
	"""
	lower, default, upper = triple
	assert lower <= default <= upper, "invalid axis values: %3.3f, %3.3f %3.3f"%(lower, default, upper)
	v = max(min(v, upper), lower)
	if v == default:
		v = 0.
	elif v < default:
		v = (v - default) / (default - lower)
	else:
		v = (v - default) / (upper - default)
	return v

def normalizeLocation(location, axes):
	"""Normalizes location based on axis min/default/max values from axes.
	>>> axes = {"wght": (100, 400, 900)}
	>>> normalizeLocation({"wght": 400}, axes)
	{'wght': 0.0}
	>>> normalizeLocation({"wght": 100}, axes)
	{'wght': -1.0}
	>>> normalizeLocation({"wght": 900}, axes)
	{'wght': 1.0}
	>>> normalizeLocation({"wght": 650}, axes)
	{'wght': 0.5}
	>>> normalizeLocation({"wght": 1000}, axes)
	{'wght': 1.0}
	>>> normalizeLocation({"wght": 0}, axes)
	{'wght': -1.0}
	>>> axes = {"wght": (0, 0, 1000)}
	>>> normalizeLocation({"wght": 0}, axes)
	{'wght': 0.0}
	>>> normalizeLocation({"wght": -1}, axes)
	{'wght': 0.0}
	>>> normalizeLocation({"wght": 1000}, axes)
	{'wght': 1.0}
	>>> normalizeLocation({"wght": 500}, axes)
	{'wght': 0.5}
	>>> normalizeLocation({"wght": 1001}, axes)
	{'wght': 1.0}
	>>> axes = {"wght": (0, 1000, 1000)}
	>>> normalizeLocation({"wght": 0}, axes)
	{'wght': -1.0}
	>>> normalizeLocation({"wght": -1}, axes)
	{'wght': -1.0}
	>>> normalizeLocation({"wght": 500}, axes)
	{'wght': -0.5}
	>>> normalizeLocation({"wght": 1000}, axes)
	{'wght': 0.0}
	>>> normalizeLocation({"wght": 1001}, axes)
	{'wght': 0.0}
	"""
	out = {}
	for tag,triple in axes.items():
		v = location.get(tag, triple[1])
		out[tag] = normalizeValue(v, triple)
	return out

def supportScalar(location, support, ot=True):
	"""Returns the scalar multiplier at location, for a master
	with support.  If ot is True, then a peak value of zero
	for support of an axis means "axis does not participate".  That
	is how OpenType Variation Font technology works.
	>>> supportScalar({}, {})
	1.0
	>>> supportScalar({'wght':.2}, {})
	1.0
	>>> supportScalar({'wght':.2}, {'wght':(0,2,3)})
	0.1
	>>> supportScalar({'wght':2.5}, {'wght':(0,2,4)})
	0.75
	>>> supportScalar({'wght':2.5, 'wdth':0}, {'wght':(0,2,4), 'wdth':(-1,0,+1)})
	0.75
	>>> supportScalar({'wght':2.5, 'wdth':.5}, {'wght':(0,2,4), 'wdth':(-1,0,+1)}, ot=False)
	0.375
	>>> supportScalar({'wght':2.5, 'wdth':0}, {'wght':(0,2,4), 'wdth':(-1,0,+1)})
	0.75
	>>> supportScalar({'wght':2.5, 'wdth':.5}, {'wght':(0,2,4), 'wdth':(-1,0,+1)})
	0.75
	"""
	scalar = 1.
	for axis,(lower,peak,upper) in support.items():
		if ot:
			# OpenType-specific case handling
			if peak == 0.:
				continue
			if lower > peak or peak > upper:
				continue
			if lower < 0. and upper > 0.:
				continue
			v = location.get(axis, 0.)
		else:
			assert axis in location
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
				axisPoints[axis] = {0.}
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
		assert len(masterValues) == len(self.deltaWeights)
		mapping = self.reverseMapping
		out = []
		for i,weights in enumerate(self.deltaWeights):
			delta = masterValues[mapping[i]]
			for j,weight in weights.items():
				delta -= out[j] * weight
			out.append(delta)
		return out

	def getScalars(self, loc):
		return [supportScalar(loc, support) for support in self.supports]

	@staticmethod
	def interpolateFromDeltasAndScalars(deltas, scalars):
		v = None
		assert len(deltas) == len(scalars)
		for i,(delta,scalar) in enumerate(zip(deltas, scalars)):
			if not scalar: continue
			contribution = delta * scalar
			if v is None:
				v = contribution
			else:
				v += contribution
		return v

	def interpolateFromDeltas(self, loc, deltas):
		scalars = self.getScalars(loc)
		return self.interpolateFromDeltasAndScalars(deltas, scalars)

	def interpolateFromMasters(self, loc, masterValues):
		deltas = self.getDeltas(masterValues)
		return self.interpolateFromDeltas(loc, deltas)

	def interpolateFromMastersAndScalars(self, masterValues, scalars):
		deltas = self.getDeltas(masterValues)
		return self.interpolateFromDeltasAndScalars(deltas, scalars)


if __name__ == "__main__":
	import doctest, sys
	sys.exit(doctest.testmod().failed)
