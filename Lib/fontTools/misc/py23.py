"""Python 2/3 compat layer."""

from __future__ import print_function, division, absolute_import

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
	bytechr = chr
	byteord = ord
except:
	unichr = chr
	def bytechr(n):
		return bytes([n])
	def byteord(c):
		return c if isinstance(c, int) else ord(c)

try:
	from StringIO import StringIO
except ImportError:
	from io import BytesIO as StringIO

def strjoin(iterable):
	return ''.join(iterable)
if str == bytes:
	class Tag(str):
		def tobytes(self):
			if isinstance(self, bytes):
				return self
			else:
				return self.encode('latin1')

	def tostr(s, encoding='ascii'):
		if not isinstance(s, str):
			return s.encode(encoding)
		else:
			return s
	tobytes = tostr

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

	def tostr(s, encoding='ascii'):
		if not isinstance(s, str):
			return s.decode(encoding)
		else:
			return s
	def tobytes(s, encoding='ascii'):
		if not isinstance(s, bytes):
			return s.encode(encoding)
		else:
			return s

	def bytesjoin(iterable):
		return b''.join(tobytes(item) for item in iterable)
