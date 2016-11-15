"""Python 2/3 compat layer."""

from __future__ import print_function, division, absolute_import
import sys


__all__ = ['basestring', 'unicode', 'unichr', 'byteord', 'bytechr', 'BytesIO',
		'StringIO', 'UnicodeIO', 'strjoin', 'bytesjoin', 'tobytes', 'tostr',
		'tounicode', 'Tag', 'open', 'range', 'xrange', 'round', 'Py23Error']


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
			if not isinstance(blob, str):
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
	expected arguments, so it must be avoided if py2 or py2-3 contexts.

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


# always use iterator for 'range' on both py 2 and 3
try:
	range = xrange
except NameError:
	range = range

def xrange(*args, **kwargs):
	raise Py23Error("'xrange' is not defined. Use 'range' instead.")


import decimal as _decimal


def round2(number, ndigits=None):
	"""
	See Python 2 documentation.

	Rounds a number to a given precision in decimal digits (default
	0 digits). The result is a floating point number. Values are rounded
	to the closest multiple of 10 to the power minus ndigits; if two
	multiples are equally close, rounding is done away from 0.

	ndigits may be negative.
	"""
	if ndigits is None:
		ndigits = 0
	elif hasattr(ndigits, '__index__'):
		# any type with an __index__ method should be permitted as
		# a second argument
		ndigits = ndigits.__index__()

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


def round3(number, ndigits=None):
	"""
	See Python 3 documentation: uses Banker's Rounding.

	Delegates to the __round__ method if for some reason this exists.

	If not, rounds a number to a given precision in decimal digits (default
	0 digits). This returns an int when called with one argument,
	otherwise the same type as the number. ndigits may be negative.

	ndigits may be negative.

	Derived from python-future:
	https://github.com/PythonCharmers/python-future/blob/master/src/future/builtins/newround.py
	"""
	return_int = False
	if ndigits is None:
		return_int = True
		ndigits = 0

	if hasattr(number, '__round__'):
		d = number.__round__(ndigits)
		return int(d) if return_int else float(d)

	if hasattr(ndigits, '__index__'):
		# any type with an __index__ method should be permitted as
		# a second argument
		ndigits = ndigits.__index__()

	if ndigits < 0:
		exponent = 10 ** (-ndigits)
		quotient, remainder = divmod(number, exponent)
		half = exponent//2
		if remainder > half or (remainder == half and quotient % 2 != 0):
			quotient += 1
		d = quotient * exponent
	else:
		exponent = _decimal.Decimal('10') ** (-ndigits)

		d = _decimal.Decimal.from_float(number).quantize(
			exponent, rounding=_decimal.ROUND_HALF_EVEN)

	return int(d) if return_int else float(d)


if PY2:
	round = round3
else:
	import builtins
	round = builtins.round


import logging


class _Logger(logging.Logger):
	""" Add support for 'lastResort' handler introduced in Python 3.2. """

	def callHandlers(self, record):
		# this is the same as Python 3.5's logging.Logger.callHandlers
		c = self
		found = 0
		while c:
			for hdlr in c.handlers:
				found = found + 1
				if record.levelno >= hdlr.level:
					hdlr.handle(record)
			if not c.propagate:
				c = None  # break out
			else:
				c = c.parent
		if (found == 0):
			if logging.lastResort:
				if record.levelno >= logging.lastResort.level:
					logging.lastResort.handle(record)
			elif logging.raiseExceptions and not self.manager.emittedNoHandlerWarning:
				sys.stderr.write("No handlers could be found for logger"
								 " \"%s\"\n" % self.name)
				self.manager.emittedNoHandlerWarning = True


class _StderrHandler(logging.StreamHandler):
	""" This class is like a StreamHandler using sys.stderr, but always uses
	whatever sys.stderr is currently set to rather than the value of
	sys.stderr at handler construction time.
	"""
	def __init__(self, level=logging.NOTSET):
		"""
		Initialize the handler.
		"""
		logging.Handler.__init__(self, level)

	@property
	def stream(self):
		return sys.stderr


if not hasattr(logging, 'lastResort'):
	# for Python pre-3.2, we need to define the "last resort" handler used when
	# clients don't explicitly configure logging (in Python 3.2 and above this is
	# already defined). The handler prints the bare message to sys.stderr, only
	# for events of severity WARNING or greater.
	# To obtain the pre-3.2 behaviour, you can set logging.lastResort to None.
	# https://docs.python.org/3.5/howto/logging.html#what-happens-if-no-configuration-is-provided
	logging.lastResort = _StderrHandler(logging.WARNING)
	# Also, we need to set the Logger class to one which supports the last resort
	# handler. All new loggers instantiated after this call will use the custom
	# logger class (the already existing ones, like the 'root' logger, will not)
	logging.setLoggerClass(_Logger)


if __name__ == "__main__":
	import doctest, sys
	sys.exit(doctest.testmod().failed)
