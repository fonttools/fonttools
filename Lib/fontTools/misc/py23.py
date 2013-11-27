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
