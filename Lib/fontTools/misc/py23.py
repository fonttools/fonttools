"""Python 2/3 compat layer."""

from __future__ import print_function, division, absolute_import
import sys

try:
	basestring
except NameError:
	basestring = str

try:
	unicode
except NameError:
	unicode = str

try:
	unichr

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

try:
	from StringIO import StringIO
except ImportError:
	from io import BytesIO as StringIO

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


if __name__ == "__main__":
	import doctest, sys
	sys.exit(doctest.testmod().failed)
