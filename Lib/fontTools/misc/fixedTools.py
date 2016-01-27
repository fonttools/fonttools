"""fontTools.misc.fixedTools.py -- tools for working with fixed numbers.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

__all__ = [
	"fixedToFloat",
	"floatToFixed",
]

def fixedToFloat(value, precisionBits):
	"""Converts a fixed-point number to a float, choosing the float
	that has the shortest decimal reprentation.  Eg. to convert a
	fixed number in a 2.14 format, use precisionBits=14.  This is
	pretty slow compared to a simple division.  Use sporadically.

	precisionBits is only supported up to 16.
	"""
	if not value: return 0.0

	scale = 1 << precisionBits
	value /= scale
	eps = .5 / scale
	lo = value - eps
	hi = value + eps
	# If the range of valid choices spans an integer, return the integer.
	if int(lo) != int(hi):
		return float(round(value))
	fmt = "%.8f"
	lo = fmt % lo
	hi = fmt % hi
	assert len(lo) == len(hi) and lo != hi
	for i in range(len(lo)):
		if lo[i] != hi[i]:
			break
	period = lo.find('.')
	assert period < i
	fmt = "%%.%df" % (i - period)
	value = fmt % value
	return float(value)

def floatToFixed(value, precisionBits):
	"""Converts a float to a fixed-point number given the number of
	precisionBits.  Ie. int(round(value * (1<<precisionBits))).
	"""
	return int(round(value * (1<<precisionBits)))

