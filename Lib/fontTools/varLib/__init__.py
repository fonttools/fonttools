"""Module for dealing with 'gvar'-style font variations,
also known as run-time interpolation."""

from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *


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


def sortMasterLocations(locations, axisOrder=[]):
	"""
	Sort masters.
	Locations must be in normalized space.  Ie. base master
	is at origin (0).
	"""

	return sorted(locations, key=getMasterLocationsSortKeyFunc(locations, axisOrder=axisOrder))

locations = [
{'wght':100},
{'wght':-100},
{'wght':-180},
{'wdth':+.3},
{'wght':+120,'wdth':.3},
{'wght':+120,'wdth':.2},
{'wght':+180,'wdth':.3},
{'wght':+180},
{},
]
from pprint import pprint
assert sortMasterLocations(locations, axisOrder=['wght']) == \
[{},
 {u'wght': -100},
 {u'wght': -180},
 {u'wght': 100},
 {u'wght': 180},
 {u'wdth': 0.3},
 {u'wdth': 0.3, u'wght': 180},
 {u'wdth': 0.3, u'wght': 120},
 {u'wdth': 0.2, u'wght': 120}]
