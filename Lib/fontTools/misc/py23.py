"""Python 2/3 compat layer."""

from __future__ import print_function, division, absolute_import
import sys


__all__ = ['basestring', 'unicode', 'unichr', 'byteord', 'bytechr', 'BytesIO',
		'StringIO', 'UnicodeIO', 'strjoin', 'bytesjoin', 'tobytes', 'tostr',
		'tounicode', 'Tag', 'open', 'range', 'xrange', 'round', 'Py23Error',
		'SimpleNamespace', 'zip']


class Py23Error(NotImplementedError):
	pass


PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2


try:
	basestring = basestring
except NameError:
	basestring = str

try:
	unicode = unicode
except NameError:
	unicode = str

try:
	unichr = unichr

	if sys.maxunicode < 0x10FFFF:
		# workarounds for Python 2 "narrow" builds with UCS2-only support.

		_narrow_unichr = unichr

		def unichr(i):
			"""
			Return the unicode character whose Unicode code is the integer 'i'.
			The valid range is 0 to 0x10FFFF inclusive.

			>>> _narrow_unichr(0xFFFF + 1)
			Traceback (most recent call last):
			  File "<stdin>", line 1, in ?
			ValueError: unichr() arg not in range(0x10000) (narrow Python build)
			>>> unichr(0xFFFF + 1) == u'\U00010000'
			True
			>>> unichr(1114111) == u'\U0010FFFF'
			True
			>>> unichr(0x10FFFF + 1)
			Traceback (most recent call last):
			  File "<stdin>", line 1, in ?
			ValueError: unichr() arg not in range(0x110000)
			"""
			try:
				return _narrow_unichr(i)
			except ValueError:
				try:
					padded_hex_str = hex(i)[2:].zfill(8)
					escape_str = "\\U" + padded_hex_str
					return escape_str.decode("unicode-escape")
				except UnicodeDecodeError:
					raise ValueError('unichr() arg not in range(0x110000)')

		import re
		_unicode_escape_RE = re.compile(r'\\U[A-Fa-f0-9]{8}')

		def byteord(c):
			"""
			Given a 8-bit or unicode character, return an integer representing the
			Unicode code point of the character. If a unicode argument is given, the
			character's code point must be in the range 0 to 0x10FFFF inclusive.

			>>> ord(u'\U00010000')
			Traceback (most recent call last):
			  File "<stdin>", line 1, in ?
			TypeError: ord() expected a character, but string of length 2 found
			>>> byteord(u'\U00010000') == 0xFFFF + 1
			True
			>>> byteord(u'\U0010FFFF') == 1114111
			True
			"""
			try:
				return ord(c)
			except TypeError as e:
				try:
					escape_str = c.encode('unicode-escape')
					if not _unicode_escape_RE.match(escape_str):
						raise
					hex_str = escape_str[3:]
					return int(hex_str, 16)
				except:
					raise TypeError(e)

	else:
		byteord = ord
	bytechr = chr

except NameError:
	unichr = chr
	def bytechr(n):
		return bytes([n])
	def byteord(c):
		return c if isinstance(c, int) else ord(c)


# the 'io' module provides the same I/O interface on both 2 and 3.
# here we define an alias of io.StringIO to disambiguate it eternally...
from io import BytesIO
from io import StringIO as UnicodeIO
try:
	# in python 2, by 'StringIO' we still mean a stream of *byte* strings
	from StringIO import StringIO
except ImportError:
	# in Python 3, we mean instead a stream of *unicode* strings
	StringIO = UnicodeIO


def strjoin(iterable, joiner=''):
	return tostr(joiner).join(iterable)

def tobytes(s, encoding='ascii', errors='strict'):
	if not isinstance(s, bytes):
		return s.encode(encoding, errors)
	else:
		return s
def tounicode(s, encoding='ascii', errors='strict'):
	if not isinstance(s, unicode):
		return s.decode(encoding, errors)
	else:
		return s

if str == bytes:
	class Tag(str):
		def tobytes(self):
			if isinstance(self, bytes):
				return self
			else:
				return self.encode('latin1')

	tostr = tobytes

	bytesjoin = strjoin
else:
	class Tag(str):

		@staticmethod
		def transcode(blob):
			if isinstance(blob, bytes):
				blob = blob.decode('latin-1')
			return blob

		def __new__(self, content):
			return str.__new__(self, self.transcode(content))
		def __ne__(self, other):
			return not self.__eq__(other)
		def __eq__(self, other):
			return str.__eq__(self, self.transcode(other))

		def __hash__(self):
			return str.__hash__(self)

		def tobytes(self):
			return self.encode('latin-1')

	tostr = tounicode

	def bytesjoin(iterable, joiner=b''):
		return tobytes(joiner).join(tobytes(item) for item in iterable)


import os
import io as _io

try:
	from msvcrt import setmode as _setmode
except ImportError:
	_setmode = None  # only available on the Windows platform


def open(file, mode='r', buffering=-1, encoding=None, errors=None,
		 newline=None, closefd=True, opener=None):
	""" Wrapper around `io.open` that bridges the differences between Python 2
	and Python 3's built-in `open` functions. In Python 2, `io.open` is a
	backport of Python 3's `open`, whereas in Python 3, it is an alias of the
	built-in `open` function.

	One difference is that the 'opener' keyword argument is only supported in
	Python 3. Here we pass the value of 'opener' only when it is not None.
	This causes Python 2 to raise TypeError, complaining about the number of
	expected arguments, so it must be avoided in py2 or py2-3 contexts.

	Another difference between 2 and 3, this time on Windows, has to do with
	opening files by name or by file descriptor.

	On the Windows C runtime, the 'O_BINARY' flag is defined which disables
	the newlines translation ('\r\n' <=> '\n') when reading/writing files.
	On both Python 2 and 3 this flag is always set when opening files by name.
	This way, the newlines translation at the MSVCRT level doesn't interfere
	with the Python io module's own newlines translation.

	However, when opening files via fd, on Python 2 the fd is simply copied,
	regardless of whether it has the 'O_BINARY' flag set or not.
	This becomes a problem in the case of stdout, stdin, and stderr, because on
	Windows these are opened in text mode by default (ie. don't have the
	O_BINARY flag set).

	On Python 3, this issue has been fixed, and all fds are now opened in
	binary mode on Windows, including standard streams. Similarly here, I use
	the `_setmode` function to ensure that integer file descriptors are
	O_BINARY'ed before I pass them on to io.open.

	For more info, see: https://bugs.python.org/issue10841
	"""
	if isinstance(file, int):
		# the 'file' argument is an integer file descriptor
		fd = file
		if fd < 0:
			raise ValueError('negative file descriptor')
		if _setmode:
			# `_setmode` function sets the line-end translation and returns the
			# value of the previous mode. AFAIK there's no `_getmode`, so to
			# check if the previous mode already had the bit set, I fist need
			# to duplicate the file descriptor, set the binary flag on the copy
			# and check the returned value.
			fdcopy = os.dup(fd)
			current_mode = _setmode(fdcopy, os.O_BINARY)
			if not (current_mode & os.O_BINARY):
				# the binary mode was not set: use the file descriptor's copy
				file = fdcopy
				if closefd:
					# close the original file descriptor
					os.close(fd)
				else:
					# ensure the copy is closed when the file object is closed
					closefd = True
			else:
				# original file descriptor already had binary flag, close copy
				os.close(fdcopy)

	if opener is not None:
		# "opener" is not supported on Python 2, use it at your own risk!
		return _io.open(
			file, mode, buffering, encoding, errors, newline, closefd,
			opener=opener)
	else:
		return _io.open(
			file, mode, buffering, encoding, errors, newline, closefd)


# always use iterator for 'range' and 'zip' on both py 2 and 3
try:
	range = xrange
except NameError:
	range = range

def xrange(*args, **kwargs):
	raise Py23Error("'xrange' is not defined. Use 'range' instead.")

try:
	from itertools import izip as zip
except ImportError:
	zip = zip


import math as _math

try:
	isclose = _math.isclose
except AttributeError:
	# math.isclose() was only added in Python 3.5

	_isinf = _math.isinf
	_fabs = _math.fabs

	def isclose(a, b, rel_tol=1e-09, abs_tol=0):
		"""
		Python 2 implementation of Python 3.5 math.isclose()
		https://hg.python.org/cpython/file/v3.5.2/Modules/mathmodule.c#l1993
		"""
		# sanity check on the inputs
		if rel_tol < 0 or abs_tol < 0:
			raise ValueError("tolerances must be non-negative")
		# short circuit exact equality -- needed to catch two infinities of
		# the same sign. And perhaps speeds things up a bit sometimes.
		if a == b:
			return True
		# This catches the case of two infinities of opposite sign, or
		# one infinity and one finite number. Two infinities of opposite
		# sign would otherwise have an infinite relative tolerance.
		# Two infinities of the same sign are caught by the equality check
		# above.
		if _isinf(a) or _isinf(b):
			return False
		# Cast to float to allow decimal.Decimal arguments
		if not isinstance(a, float):
			a = float(a)
		if not isinstance(b, float):
			b = float(b)
		# now do the regular computation
		# this is essentially the "weak" test from the Boost library
		diff = _fabs(b - a)
		result = ((diff <= _fabs(rel_tol * a)) or
				  (diff <= _fabs(rel_tol * b)) or
				  (diff <= abs_tol))
		return result


import decimal as _decimal

if PY3:
	def round2(number, ndigits=None):
		"""
		Implementation of Python 2 built-in round() function.

		Rounds a number to a given precision in decimal digits (default
		0 digits). The result is a floating point number. Values are rounded
		to the closest multiple of 10 to the power minus ndigits; if two
		multiples are equally close, rounding is done away from 0.

		ndigits may be negative.

		See Python 2 documentation:
		https://docs.python.org/2/library/functions.html?highlight=round#round
		"""
		if ndigits is None:
			ndigits = 0

		if ndigits < 0:
			exponent = 10 ** (-ndigits)
			quotient, remainder = divmod(number, exponent)
			if remainder >= exponent//2 and number >= 0:
				quotient += 1
			return float(quotient * exponent)
		else:
			exponent = _decimal.Decimal('10') ** (-ndigits)

			d = _decimal.Decimal.from_float(number).quantize(
				exponent, rounding=_decimal.ROUND_HALF_UP)

			return float(d)

	if sys.version_info[:2] >= (3, 6):
		# in Python 3.6, 'round3' is an alias to the built-in 'round'
		round = round3 = round
	else:
		# in Python3 < 3.6 we need work around the inconsistent behavior of
		# built-in round(), whereby floats accept a second None argument,
		# while integers raise TypeError. See https://bugs.python.org/issue27936
		_round = round

		def round3(number, ndigits=None):
			return _round(number) if ndigits is None else _round(number, ndigits)

		round = round3

else:
	# in Python 2, 'round2' is an alias to the built-in 'round' and
	# 'round' is shadowed by 'round3'
	round2 = round

	def round3(number, ndigits=None):
		"""
		Implementation of Python 3 built-in round() function.

		Rounds a number to a given precision in decimal digits (default
		0 digits). This returns an int when ndigits is omitted or is None,
		otherwise the same type as the number.

		Values are rounded to the closest multiple of 10 to the power minus
		ndigits; if two multiples are equally close, rounding is done toward
		the even choice (aka "Banker's Rounding"). For example, both round(0.5)
		and round(-0.5) are 0, and round(1.5) is 2.

		ndigits may be negative.

		See Python 3 documentation:
		https://docs.python.org/3/library/functions.html?highlight=round#round

		Derived from python-future:
		https://github.com/PythonCharmers/python-future/blob/master/src/future/builtins/newround.py
		"""
		if ndigits is None:
			ndigits = 0
			# return an int when called with one argument
			totype = int
			# shortcut if already an integer, or a float with no decimal digits
			inumber = totype(number)
			if inumber == number:
				return inumber
		else:
			# return the same type as the number, when called with two arguments
			totype = type(number)

		m = number * (10 ** ndigits)
		# if number is half-way between two multiples, and the mutliple that is
		# closer to zero is even, we use the (slow) pure-Python implementation
		if isclose(m % 1, .5) and int(m) % 2 == 0:
			if ndigits < 0:
				exponent = 10 ** (-ndigits)
				quotient, remainder = divmod(number, exponent)
				half = exponent//2
				if remainder > half or (remainder == half and quotient % 2 != 0):
					quotient += 1
				d = quotient * exponent
			else:
				exponent = _decimal.Decimal('10') ** (-ndigits) if ndigits != 0 else 1

				d = _decimal.Decimal.from_float(number).quantize(
					exponent, rounding=_decimal.ROUND_HALF_EVEN)
		else:
			# else we use the built-in round() as it produces the same results
			d = round2(number, ndigits)

		return totype(d)

	round = round3


try:
	from types import SimpleNamespace
except ImportError:
	class SimpleNamespace(object):
		"""
		A backport of Python 3.3's ``types.SimpleNamespace``.
		"""
		def __init__(self, **kwargs):
			self.__dict__.update(kwargs)

		def __repr__(self):
			keys = sorted(self.__dict__)
			items = ("{0}={1!r}".format(k, self.__dict__[k]) for k in keys)
			return "{0}({1})".format(type(self).__name__, ", ".join(items))

		def __eq__(self, other):
			return self.__dict__ == other.__dict__


if sys.version_info[:2] > (3, 4):
	from contextlib import redirect_stdout, redirect_stderr
else:
	# `redirect_stdout` was added with python3.4, while `redirect_stderr`
	# with python3.5. For simplicity, I redefine both for any versions
	# less than or equal to 3.4.
	# The code below is copied from:
	# https://github.com/python/cpython/blob/57161aa/Lib/contextlib.py

	class _RedirectStream(object):

		_stream = None

		def __init__(self, new_target):
			self._new_target = new_target
			# We use a list of old targets to make this CM re-entrant
			self._old_targets = []

		def __enter__(self):
			self._old_targets.append(getattr(sys, self._stream))
			setattr(sys, self._stream, self._new_target)
			return self._new_target

		def __exit__(self, exctype, excinst, exctb):
			setattr(sys, self._stream, self._old_targets.pop())


	class redirect_stdout(_RedirectStream):
		"""Context manager for temporarily redirecting stdout to another file.
			# How to send help() to stderr
			with redirect_stdout(sys.stderr):
				help(dir)
			# How to write help() to a file
			with open('help.txt', 'w') as f:
				with redirect_stdout(f):
					help(pow)
		"""

		_stream = "stdout"


	class redirect_stderr(_RedirectStream):
		"""Context manager for temporarily redirecting stderr to another file."""

		_stream = "stderr"


if __name__ == "__main__":
	import doctest, sys
	sys.exit(doctest.testmod().failed)
