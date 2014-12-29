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
	
	# Note: Python 3 prints 1.0 as "1", while Python 2 prints as "1.0".
	# As such we avoid depending on that in the tests below.
	>>> fixedToFloat(13107, 14)
	0.8
	>>> fixedToFloat(0, 14)
	0.0
	>>> fixedToFloat(0x4000, 14) == 1
	True
	>>> fixedToFloat(-16384, 14) == -1
	True
	>>> fixedToFloat(-16383, 14)
	-0.99994
	>>> fixedToFloat(16384, 14) == 1
	True
	>>> fixedToFloat(16383, 14)
	0.99994
	>>> fixedToFloat(-639, 6)
	-9.99
	>>> fixedToFloat(-640, 6) == -10
	True
	>>> fixedToFloat(639, 6)
	9.99
	>>> fixedToFloat(640, 6) == 10
	True
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
	fmt = "%%.%df" % ((precisionBits + 2) // 3)
	lo = fmt % lo
	hi = fmt % hi
	i = 0
	length = min(len(lo), len(hi))
	while i < length and lo[i] == hi[i]:
		i += 1
	out = lo[:i]
	assert -1 != out.find('.') # Both ends should be the same past decimal point
	if i < length:
		# Append mid-point digit of half-open range (l,h].
		out = out + str((int(lo[i]) + int(hi[i]) + 1) // 2)
	return float(out)

def floatToFixed(value, precisionBits):
	"""Converts a float to a fixed-point number given the number of
	precisionBits.  Ie. int(round(value * (1<<precisionBits))).

	>>> floatToFixed(0.8, 14)
	13107
	>>> floatToFixed(1.0, 14)
	16384
	>>> floatToFixed(1, 14)
	16384
	>>> floatToFixed(-1.0, 14)
	-16384
	>>> floatToFixed(-1, 14)
	-16384
	>>> floatToFixed(0, 14)
	0
	"""

	return int(round(value * (1<<precisionBits)))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
