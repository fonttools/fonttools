"""xmlWriter.py -- Simple XML authoring class"""

import string
import struct
import os

INDENT = "  "


class XMLWriter:
	
	def __init__(self, fileOrPath, indentwhite=INDENT, idlefunc=None, encoding="ISO-8859-1"):
		if not hasattr(fileOrPath, "write"):
			self.file = open(fileOrPath, "w")
			if os.name == "mac":
				import macfs
				macfs.FSSpec(fileOrPath).SetCreatorType('R*ch', 'TEXT')
		else:
			# assume writable file object
			self.file = fileOrPath
		self.indentwhite = indentwhite
		self.indentlevel = 0
		self.stack = []
		self.needindent = 1
		self.idlefunc = idlefunc
		self.idlecounter = 0
		if encoding:
			self.writeraw('<?xml version="1.0" encoding="%s"?>' % encoding)
		else:
			self.writeraw('<?xml version="1.0"?>')
		self.newline()
	
	def close(self):
		self.file.close()
	
	def write(self, data):
		self.writeraw(escape(data))
	
	def write_noindent(self, data):
		self.file.write(escape(data))
	
	def write8bit(self, data):
		self.writeraw(escape8bit(data))
	
	def write16bit(self, data):
		self.writeraw(escape16bit(data))
	
	def writeraw(self, data):
		if self.needindent:
			self.file.write(self.indentlevel * self.indentwhite)
			self.needindent = 0
		self.file.write(data)
	
	def newline(self):
		self.file.write("\n")
		self.needindent = 1
		idlecounter = self.idlecounter
		if not idlecounter % 100 and self.idlefunc is not None:
			self.idlefunc()
		self.idlecounter = idlecounter + 1
	
	def comment(self, data):
		data = escape(data)
		lines = string.split(data, "\n")
		self.writeraw("<!-- " + lines[0])
		for line in lines[1:]:
			self.newline()
			self.writeraw("     " + line)
		self.writeraw(" -->")
	
	def simpletag(self, _TAG_, *args, **kwargs):
		attrdata = apply(self.stringifyattrs, args, kwargs)
		data = "<%s%s/>" % (_TAG_, attrdata)
		self.writeraw(data)
	
	def begintag(self, _TAG_, *args, **kwargs):
		attrdata = apply(self.stringifyattrs, args, kwargs)
		data = "<%s%s>" % (_TAG_, attrdata)
		self.writeraw(data)
		self.stack.append(_TAG_)
		self.indent()
	
	def endtag(self, _TAG_):
		assert self.stack and self.stack[-1] == _TAG_, "nonmatching endtag"
		del self.stack[-1]
		self.dedent()
		data = "</%s>" % _TAG_
		self.writeraw(data)
	
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
			self.writeraw(line)
			self.newline()
	
	def indent(self):
		self.indentlevel = self.indentlevel + 1
	
	def dedent(self):
		assert self.indentlevel > 0
		self.indentlevel = self.indentlevel - 1
	
	def stringifyattrs(self, *args, **kwargs):
		if kwargs:
			assert not args
			attributes = kwargs.items()
			attributes.sort()
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
	data = string.replace(data, "&", "&amp;")
	data = string.replace(data, "<", "&lt;")
	return data

def escapeattr(data):
	data = string.replace(data, "&", "&amp;")
	data = string.replace(data, "<", "&lt;")
	data = string.replace(data, '"', "&quot;")
	return data

def escape8bit(data):
	def escapechar(c):
		n = ord(c)
		if c in "<&":
			if c == "&":
				return "&amp;"
			else:
				return "&lt;"
		elif 32 <= n <= 127:
			return c
		else:
			return "&#" + `n` + ";"
	return string.join(map(escapechar, data), "")

needswap = struct.pack("h", 1) == "\001\000"

def escape16bit(data):
	import array
	a = array.array("H")
	a.fromstring(data)
	if needswap:
		a.byteswap()
	def escapenum(n, amp=ord("&"), lt=ord("<")):
		if n == amp:
			return "&amp;"
		elif n == lt:
			return "&lt;"
		elif 32 <= n <= 127:
			return chr(n)
		else:
			return "&#" + `n` + ";"
	return string.join(map(escapenum, a), "")


def hexStr(s):
	h = string.hexdigits
	r = ''
	for c in s:
		i = ord(c)
		r = r + h[(i >> 4) & 0xF] + h[i & 0xF]
	return r

