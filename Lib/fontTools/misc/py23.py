"""Python 2/3 compat layer."""

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
except:
	unichr = chr
	def bytechr(n):
		return bytes([n])

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
