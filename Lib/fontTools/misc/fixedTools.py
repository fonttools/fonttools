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
	"""
	if not value: return 0.0

	scale = 1 << precisionBits
	value /= scale
	eps = .5 / scale
	lo = value - eps
	hi = value + eps
	# If the range of valid choices spans an integer, return the integer.
	if int(lo) != int(hi):
		return round(value)
	fmt = "%.8f"
	lo = fmt % lo
	hi = fmt % hi
	i = 0
	length = min(len(lo), len(hi))
	while i < length and lo[i] == hi[i]:
		i += 1
	out = lo[:i]
	assert -1 != out.find('.') # Both ends should be the same past decimal point
	if i < length:
		fmt = "%%.%df" % (i - out.find('.'))
		value = fmt % value
		out += value[-1]
	return float(out)

def floatToFixed(value, precisionBits):
	"""Converts a float to a fixed-point number given the number of
	precisionBits.  Ie. int(round(value * (1<<precisionBits))).
	"""
	return int(round(value * (1<<precisionBits)))
