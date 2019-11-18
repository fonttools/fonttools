"""fontTools.misc.fixedTools.py -- tools for working with fixed numbers.
"""

from fontTools.misc.py23 import *
import math
import logging

log = logging.getLogger(__name__)

__all__ = [
	"otRound",
	"fixedToFloat",
	"floatToFixed",
	"floatToFixedToFloat",
	"floatToFixedToStr",
	"fixedToStr",
	"strToFixed",
	"strToFixedToFloat",
	"ensureVersionIsLong",
	"versionToFixed",
]


# the max value that can still fit in an F2Dot14:
# 1.99993896484375
MAX_F2DOT14 = 0x7FFF / (1 << 14)


def otRound(value):
	"""Round float value to nearest integer towards +Infinity.
	For fractional values of 0.5 and higher, take the next higher integer;
	for other fractional values, truncate.

	https://docs.microsoft.com/en-us/typography/opentype/spec/otvaroverview
	https://github.com/fonttools/fonttools/issues/1248#issuecomment-383198166
	"""
	return int(math.floor(value + 0.5))


def fixedToFloat(value, precisionBits):
	"""Converts a fixed-point number to a float given the number of
	precisionBits.  Ie. value / (1 << precisionBits)

	>>> import math
	>>> f = fixedToFloat(-10139, precisionBits=14)
	>>> math.isclose(f, -0.61883544921875)
	True
	"""
	return value / (1 << precisionBits)


def floatToFixed(value, precisionBits):
	"""Converts a float to a fixed-point number given the number of
	precisionBits.  Ie. round(value * (1 << precisionBits)).

	>>> floatToFixed(-0.61883544921875, precisionBits=14)
	-10139
	>>> floatToFixed(-0.61884, precisionBits=14)
	-10139
	"""
	return otRound(value * (1 << precisionBits))


def floatToFixedToFloat(value, precisionBits):
	"""Converts a float to a fixed-point number given the number of
	precisionBits, round it, then convert it back to float again.
	Ie. round(value * (1<<precisionBits)) / (1<<precisionBits)
	Note: this **is** equivalent to fixedToFloat(floatToFixed(value)).

	>>> import math
	>>> f1 = -0.61884
	>>> f2 = floatToFixedToFloat(-0.61884, precisionBits=14)
	>>> f1 != f2
	True
	>>> math.isclose(f2, -0.61883544921875)
	True
	"""
	scale = 1 << precisionBits
	return otRound(value * scale) / scale


def fixedToStr(value, precisionBits):
	"""Converts a fixed-point number with 'precisionBits' number of fractional binary
	digits to a string representing a decimal float, choosing the float that has the
	shortest decimal representation (the least number of fractional decimal digits).
	Eg. to convert a fixed-point number in a 2.14 format, use precisionBits=14:

	>>> fixedToStr(-10139, precisionBits=14)
	'-0.61884'

	This is pretty slow compared to the simple division used in fixedToFloat.
	Use sporadically when you need to serialize or print the fixed-point number in
	a human-readable form.

	NOTE: precisionBits is only supported up to 16.
	"""
	if not value: return "0.0"

	scale = 1 << precisionBits
	value /= scale
	eps = .5 / scale
	lo = value - eps
	hi = value + eps
	# If the range of valid choices spans an integer, return the integer.
	if int(lo) != int(hi):
		return str(float(round(value)))
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
	return fmt % value


def strToFixed(string, precisionBits):
	"""Convert the string representation of a decimal float number to a fixed-point
	number with 'precisionBits' fractional binary digits.
	E.g. to convert a float string to a 2.14 fixed-point number:

	>>> strToFixed('-0.61884', precisionBits=14)
	-10139
	"""
	value = float(string)
	return otRound(value * (1 << precisionBits))


def strToFixedToFloat(string, precisionBits):
	"""Convert a string to a decimal float, by first converting the float to a
	fixed-point number with precisionBits fractional binary digits.
	This is simply a shorthand for fixedToFloat(floatToFixed(float(s))).

	>>> import math
	>>> s = '-0.61884'
	>>> bits = 14
	>>> f = strToFixedToFloat(s, precisionBits=bits)
	>>> math.isclose(f, -0.61883544921875)
	True
	>>> f == fixedToFloat(floatToFixed(float(s), precisionBits=bits), precisionBits=bits)
	True
	"""
	value = float(string)
	scale = 1 << precisionBits
	return otRound(value * scale) / scale


def floatToFixedToStr(value, precisionBits):
	"""Convert float to string using the shortest decimal representation (ie. the least
	number of fractional decimal digits) to represent the equivalent fixed-point number
	with 'precisionBits' fractional binary digits.
	It uses fixedToStr under the hood.

	>>> floatToFixedToStr(-0.61883544921875, precisionBits=14)
	'-0.61884'
	"""
	fixed = otRound(value * (1 << precisionBits))
	return fixedToStr(fixed, precisionBits)


def ensureVersionIsLong(value):
	"""Ensure a table version is an unsigned long (unsigned short major,
	unsigned short minor) instead of a float."""
	if value < 0x10000:
		newValue = floatToFixed(value, 16)
		log.warning(
			"Table version value is a float: %.4f; "
			"fix to use hex instead: 0x%08x", value, newValue)
		value = newValue
	return value


def versionToFixed(value):
	"""Converts a table version to a fixed"""
	value = int(value, 0) if value.startswith("0") else float(value)
	value = ensureVersionIsLong(value)
	return value
