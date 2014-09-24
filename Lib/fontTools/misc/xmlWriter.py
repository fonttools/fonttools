"""xmlWriter.py -- Simple XML authoring class"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import sys
import string

INDENT = "  "


class XMLWriter(object):
	
	def __init__(self, fileOrPath, indentwhite=INDENT, idlefunc=None):
		if not hasattr(fileOrPath, "write"):
			try:
				# Python3 has encoding support.
				self.file = open(fileOrPath, "w", encoding="utf-8")
			except TypeError:
				self.file = open(fileOrPath, "w")
		else:
			# assume writable file object
			self.file = fileOrPath
		self.indentwhite = indentwhite
		self.indentlevel = 0
		self.stack = []
		self.needindent = 1
		self.idlefunc = idlefunc
		self.idlecounter = 0
		self._writeraw('<?xml version="1.0" encoding="utf-8"?>')
		self.newline()
	
	def close(self):
		self.file.close()
	
	def write(self, string, indent=True):
		"""Writes text."""
		self._writeraw(escape(string), indent=indent)

	def writecdata(self, string):
		"""Writes text in a CDATA section."""
		self._writeraw("<![CDATA[" + string + "]]>")

	def write8bit(self, data, strip=False):
		"""Writes a bytes() sequence into the XML, escaping
		non-ASCII bytes.  When this is read in xmlReader,
		the original bytes can be recovered by encoding to
		'latin-1'."""
		self._writeraw(escape8bit(data), strip=strip)

	def write16bit(self, data, strip=False):
		self._writeraw(escape16bit(data), strip=strip)
	
	def write_noindent(self, string):
		"""Writes text without indentation."""
		self._writeraw(escape(string), indent=False)
	
	def _writeraw(self, data, indent=True, strip=False):
		"""Writes bytes, possibly indented."""
		if indent and self.needindent:
			self.file.write(self.indentlevel * self.indentwhite)
			self.needindent = 0
		s = tostr(data, encoding="utf-8")
		if (strip):
			s = s.strip()
		self.file.write(s)
	
	def newline(self):
		self.file.write("\n")
		self.needindent = 1
		idlecounter = self.idlecounter
		if not idlecounter % 100 and self.idlefunc is not None:
			self.idlefunc()
		self.idlecounter = idlecounter + 1
	
	def comment(self, data):
		data = escape(data)
		lines = data.split("\n")
		self._writeraw("<!-- " + lines[0])
		for line in lines[1:]:
			self.newline()
			self._writeraw("     " + line)
		self._writeraw(" -->")
	
	def simpletag(self, _TAG_, *args, **kwargs):
		attrdata = self.stringifyattrs(*args, **kwargs)
		data = "<%s%s/>" % (_TAG_, attrdata)
		self._writeraw(data)
	
	def begintag(self, _TAG_, *args, **kwargs):
		attrdata = self.stringifyattrs(*args, **kwargs)
		data = "<%s%s>" % (_TAG_, attrdata)
		self._writeraw(data)
		self.stack.append(_TAG_)
		self.indent()
	
	def endtag(self, _TAG_):
		assert self.stack and self.stack[-1] == _TAG_, "nonmatching endtag"
		del self.stack[-1]
		self.dedent()
		data = "</%s>" % _TAG_
		self._writeraw(data)
	
	def dumphex(self, data):
		linelength = 16
		hexlinelength = linelength * 2
		chunksize = 8
		for i in range(0, len(data), linelength):
			hexline = hexStr(data[i:i+linelength])
			line = ""
			white = ""
			for j in range(0, hexlinelength, chunksize):
				line = line + white + hexline[j:j+chunksize]
				white = " "
			self._writeraw(line)
			self.newline()
	
	def indent(self):
		self.indentlevel = self.indentlevel + 1
	
	def dedent(self):
		assert self.indentlevel > 0
		self.indentlevel = self.indentlevel - 1
	
	def stringifyattrs(self, *args, **kwargs):
		if kwargs:
			assert not args
			attributes = sorted(kwargs.items())
		elif args:
			assert len(args) == 1
			attributes = args[0]
		else:
			return ""
		data = ""
		for attr, value in attributes:
			data = data + ' %s="%s"' % (attr, escapeattr(str(value)))
		return data
	

def escape(data):
	data = tostr(data, 'utf-8')
	data = data.replace("&", "&amp;")
	data = data.replace("<", "&lt;")
	data = data.replace(">", "&gt;")
	return data

def escapeattr(data):
	data = escape(data)
	data = data.replace('"', "&quot;")
	return data

def escape8bit(data):
	"""Input is Unicode string."""
	def escapechar(c):
		n = ord(c)
		if 32 <= n <= 127 and c not in "<&>":
			return c
		else:
			return "&#" + repr(n) + ";"
	return strjoin(map(escapechar, data.decode('latin-1')))

def escape16bit(data):
	import array
	a = array.array("H")
	a.fromstring(data)
	if sys.byteorder != "big":
		a.byteswap()
	def escapenum(n, amp=byteord("&"), lt=byteord("<")):
		if n == amp:
			return "&amp;"
		elif n == lt:
			return "&lt;"
		elif 32 <= n <= 127:
			return chr(n)
		else:
			return "&#" + repr(n) + ";"
	return strjoin(map(escapenum, a))


def hexStr(s):
	h = string.hexdigits
	r = ''
	for c in s:
		i = byteord(c)
		r = r + h[(i >> 4) & 0xF] + h[i & 0xF]
	return r
