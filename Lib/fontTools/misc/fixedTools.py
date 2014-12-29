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
	
	>>> fixedToFloat(13107, 14)
	0.8
	>>> fixedToFloat(0, 14)
	0.0
	>>> fixedToFloat(0x4000, 14)
	1.0
	>>> fixedToFloat(-16384, 14)
	-1.0
	>>> fixedToFloat(-16383, 14)
	-0.99994
	>>> fixedToFloat(16384, 14)
	1.0
	>>> fixedToFloat(16383, 14)
	0.99994
	>>> fixedToFloat(-639, 6)
	-9.99
	>>> fixedToFloat(-640, 6)
	-10.0
	>>> fixedToFloat(639, 6)
	9.99
	>>> fixedToFloat(640, 6)
	10.0
	"""

	if not value: return 0.0

	scale = 1 << precisionBits
	value /= scale
	eps = .5 / scale
	digits = (precisionBits + 2) // 3
	fmt = "%%.%df" % digits
	lo = fmt % (value - eps)
	hi = fmt % (value + eps)
	assert (lo[0] != '-') == (hi[0] != '-') # Both should result in same sign
	out = []
	length = min(len(lo), len(hi))
	for i in range(length):
		if lo[i] != hi[i]:
			break;
		out.append(lo[i])
	outlen = len(out)
	if outlen < length:
		l = lo[outlen]
		h = hi[outlen]
		out.append(str((int(l) + int(h) + 1) // 2))
	return float(strjoin(out))

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
