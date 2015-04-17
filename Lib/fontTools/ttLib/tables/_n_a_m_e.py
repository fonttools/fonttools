from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
import fontTools.encodings.codecs
from . import DefaultTable
import struct

nameRecordFormat = """
		>	# big endian
		platformID:	H
		platEncID:	H
		langID:		H
		nameID:		H
		length:		H
		offset:		H
"""

nameRecordSize = sstruct.calcsize(nameRecordFormat)


class table__n_a_m_e(DefaultTable.DefaultTable):
	
	def decompile(self, data, ttFont):
		format, n, stringOffset = struct.unpack(">HHH", data[:6])
		expectedStringOffset = 6 + n * nameRecordSize
		if stringOffset != expectedStringOffset:
			# XXX we need a warn function
			print("Warning: 'name' table stringOffset incorrect. Expected: %s; Actual: %s" % (expectedStringOffset, stringOffset))
		stringData = data[stringOffset:]
		data = data[6:]
		self.names = []
		for i in range(n):
			if len(data) < 12:
				# compensate for buggy font
				break
			name, data = sstruct.unpack2(nameRecordFormat, data, NameRecord())
			name.string = stringData[name.offset:name.offset+name.length]
			assert len(name.string) == name.length
			#if (name.platEncID, name.platformID) in ((0, 0), (1, 3)):
			#	if len(name.string) % 2:
			#		print "2-byte string doesn't have even length!"
			#		print name.__dict__
			del name.offset, name.length
			self.names.append(name)
	
	def compile(self, ttFont):
		if not hasattr(self, "names"):
			# only happens when there are NO name table entries read
			# from the TTX file
			self.names = []
		names = self.names
		names.sort() # sort according to the spec; see NameRecord.__lt__()
		stringData = b""
		format = 0
		n = len(names)
		stringOffset = 6 + n * sstruct.calcsize(nameRecordFormat)
		data = struct.pack(">HHH", format, n, stringOffset)
		lastoffset = 0
		done = {}  # remember the data so we can reuse the "pointers"
		for name in names:
			string = name.toBytes()
			if string in done:
				name.offset, name.length = done[string]
			else:
				name.offset, name.length = done[string] = len(stringData), len(string)
				stringData = bytesjoin([stringData, string])
			data = data + sstruct.pack(nameRecordFormat, name)
		return data + stringData
	
	def toXML(self, writer, ttFont):
		for name in self.names:
			name.toXML(writer, ttFont)
	
	def fromXML(self, name, attrs, content, ttFont):
		if name != "namerecord":
			return # ignore unknown tags
		if not hasattr(self, "names"):
			self.names = []
		name = NameRecord()
		self.names.append(name)
		name.fromXML(name, attrs, content, ttFont)
	
	def getName(self, nameID, platformID, platEncID, langID=None):
		for namerecord in self.names:
			if (	namerecord.nameID == nameID and 
					namerecord.platformID == platformID and 
					namerecord.platEncID == platEncID):
				if langID is None or namerecord.langID == langID:
					return namerecord
		return None # not found


class NameRecord(object):

	# Map keyed by platformID, then platEncID, then possibly langID
	_encodingMap =	{
		0: { # Unicode
			0: 'utf-16be',
			1: 'utf-16be',
			2: 'utf-16be',
			3: 'utf-16be',
			4: 'utf-16be',
			5: 'utf-16be',
			6: 'utf-16be',
		},
		1: { # Macintosh
			# See
			# https://github.com/behdad/fonttools/issues/236
			0: { # Macintosh, platEncID==0, keyed by langID
				15: "mac-iceland",
				17: "mac-turkish",
				18: None,
				24: "mac-latin2",
				25: "mac-latin2",
				26: "mac-latin2",
				27: "mac-latin2",
				28: "mac-latin2",
				36: "mac-latin2",
				37: None,
				38: "mac-latin2",
				39: "mac-latin2",
				40: "mac-latin2",
				Ellipsis: 'mac-roman', # Other
			},
			1: 'x-mac-japanese-ttx',
			2: 'x-mac-chinesetrad-ttx',
			3: 'x-mac-korean-ttx',
			6: 'mac-greek',
			7: 'mac-cyrillic',
			25: 'x-mac-chinesesimp-ttx',
			29: 'mac-latin2',
			35: 'mac-turkish',
			37: 'mac-iceland',
		},
		2: { # ISO
			0: 'ascii',
			1: 'utf-16be',
			2: 'latin1',
		},
		3: { # Microsoft
			0: 'utf-16be',
			1: 'utf-16be',
			2: 'shift-jis',
			3: 'gb2312',
			4: 'big5',
			5: 'wansung',
			6: 'johab',
			10: 'utf-16be',
		},
	}

	def getEncoding(self, default='ascii'):
		"""Returns the Python encoding name for this name entry based on its platformID,
		platEncID, and langID.  If encoding for these values is not known, by default
		'ascii' is returned.  That can be overriden by passing a value to the default
		argument.
		"""
		encoding = self._encodingMap.get(self.platformID, {}).get(self.platEncID, default)
		if isinstance(encoding, dict):
			encoding = encoding.get(self.langID, encoding[Ellipsis])
		return encoding

	def encodingIsUnicodeCompatible(self):
		return self.getEncoding(None) in ['utf-16be', 'ucs2be', 'ascii', 'latin1']

	def __str__(self):
		try:
			return self.toUnicode()
		except UnicodeDecodeError:
			return str(self.string)

	def isUnicode(self):
		return (self.platformID == 0 or
			(self.platformID == 3 and self.platEncID in [0, 1, 10]))

	def toUnicode(self, errors='strict'):
		"""
		If self.string is a Unicode string, return it; otherwise try decoding the
		bytes in self.string to a Unicode string using the encoding of this
		entry as returned by self.getEncoding(); Note that  self.getEncoding()
		returns 'ascii' if the encoding is unknown to the library.

		If the bytes are ill-formed in that chosen encoding, the error is handled
		according to the errors parameter to this function, which is passed to the
		underlying decode() function; by default it throws a UnicodeDecodeError exception.
		"""
		return tounicode(self.string, encoding=self.getEncoding(), errors=errors)

	def toBytes(self, errors='strict'):
		""" If self.string is a bytes object, return it; otherwise try encoding
		the Unicode string in self.string to bytes using the encoding of this
		entry as returned by self.getEncoding(); Note that self.getEncoding()
		returns 'ascii' if the encoding is unknown to the library.

		If the Unicode string cannot be encoded to bytes in the chosen encoding,
		the error is handled according to the errors parameter to this function,
		which is passed to the underlying encode() function; by default it throws a
		UnicodeEncodeError exception.
		"""
		return tobytes(self.string, encoding=self.getEncoding(), errors=errors)

	def toXML(self, writer, ttFont):
		try:
			unistr = self.toUnicode()
		except UnicodeDecodeError:
			unistr = None
		attrs = [
				("nameID", self.nameID),
				("platformID", self.platformID),
				("platEncID", self.platEncID),
				("langID", hex(self.langID)),
			]

		if not self.encodingIsUnicodeCompatible():
			attrs.append(("unicode", unistr is not None))

		writer.begintag("namerecord", attrs)
		writer.newline()
		if unistr is not None:
			writer.write(unistr)
		else:
			writer.write8bit(self.string)
		writer.newline()
		writer.endtag("namerecord")
		writer.newline()
	
	def fromXML(self, name, attrs, content, ttFont):
		self.nameID = safeEval(attrs["nameID"])
		self.platformID = safeEval(attrs["platformID"])
		self.platEncID = safeEval(attrs["platEncID"])
		self.langID =  safeEval(attrs["langID"])
		s = strjoin(content).strip()
		encoding = self.getEncoding()
		if self.encodingIsUnicodeCompatible() or safeEval(attrs.get("unicode", "False")):
			self.string = s.encode(encoding)
		else:
			# This is the inverse of write8bit...
			self.string = s.encode("latin1")
	
	def __lt__(self, other):
		if type(self) != type(other):
			return NotImplemented

		# implemented so that list.sort() sorts according to the spec.
		selfTuple = (
			getattr(self, "platformID", None),
			getattr(self, "platEncID", None),
			getattr(self, "langID", None),
			getattr(self, "nameID", None),
			getattr(self, "string", None),
		)
		otherTuple = (
			getattr(other, "platformID", None),
			getattr(other, "platEncID", None),
			getattr(other, "langID", None),
			getattr(other, "nameID", None),
			getattr(other, "string", None),
		)
		return selfTuple < otherTuple
	
	def __repr__(self):
		return "<NameRecord NameID=%d; PlatformID=%d; LanguageID=%d>" % (
				self.nameID, self.platformID, self.langID)
