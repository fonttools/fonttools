"""Python 2/3 compat layer."""

from __future__ import print_function, division

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
		return ord(c) if isinstance(c, str) else c

try:
	from cStringIO import StringIO
except ImportError:
	from io import StringIO

if str == bytes:
	class Tag(str):
		def tobytes(self):
			if isinstance(self, bytes):
				return self
			else:
				return self.encode('latin-1')

	def tostr(s):
		if not isinstance(s, str):
			return s.encode('ascii')
		else:
			return s
	tobytes = tostr
else:
	class Tag(str):

		@staticmethod
		def transcode(blob):
			if not isinstance(blob, str):
				blob = blob.decode('latin-1')
			return blob

		def __new__(self, content):
			return str.__new__(self, self.transcode(content))
		def __eq__(self, other):
			return str.__eq__(self, self.transcode(other))

		def __hash__(self):
			return str.__hash__(self)

		def tobytes(self):
			return self.encode('latin-1')

	def tostr(s):
		if not isinstance(s, str):
			return s.decode('ascii')
		else:
			return s
	def tobytes(s):
		if not isinstance(s, bytes):
			return s.encode('ascii')
		else:
			return s
