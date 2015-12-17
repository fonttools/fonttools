from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from fontTools.misc.encodingTools import getEncoding
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

	def getDebugName(self, nameID):
		englishName = someName = None
		for name in self.names:
			if name.nameID != nameID:
				continue
			try:
				unistr = name.toUnicode()
			except UnicodeDecodeError:
				continue

			someName = unistr
			if (name.platformID, name.langID) in ((1, 0), (3, 0x409)):
				englishName = unistr
				break
		if englishName:
			return englishName
		elif someName:
			return someName
		else:
			return None

	def setName(self, string, nameID, platformID, platEncID, langID):
		if not hasattr(self, 'names'):
			self.names = []
		namerecord = self.getName(nameID, platformID, platEncID, langID)
		exists = False if namerecord is None else True
		if not exists:
			namerecord = NameRecord()
			namerecord.nameID = nameID
			namerecord.platformID = platformID
			namerecord.platEncID = platEncID
			namerecord.langID = langID
		encoding = namerecord.getEncoding()
		namerecord.string = string.encode(encoding)
		if not exists:
			self.names.append(namerecord)


class NameRecord(object):

	def getEncoding(self, default='ascii'):
		"""Returns the Python encoding name for this name entry based on its platformID,
		platEncID, and langID.  If encoding for these values is not known, by default
		'ascii' is returned.  That can be overriden by passing a value to the default
		argument.
		"""
		return getEncoding(self.platformID, self.platEncID, self.langID, default)

	def encodingIsUnicodeCompatible(self):
		return self.getEncoding(None) in ['utf_16_be', 'ucs2be', 'ascii', 'latin1']

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

		Certain heuristics are performed to recover data from bytes that are
		ill-formed in the chosen encoding, or that otherwise look misencoded
		(mostly around bad UTF-16BE encoded bytes, or bytes that look like UTF-16BE
		but marked otherwise).  If the bytes are ill-formed and the heuristics fail,
		the error is handled according to the errors parameter to this function, which is
		passed to the underlying decode() function; by default it throws a
		UnicodeDecodeError exception.

		Note: The mentioned heuristics mean that roundtripping a font to XML and back
		to binary might recover some misencoded data whereas just loading the font
		and saving it back will not change them.
		"""
		def isascii(b):
			return (b >= 0x20 and b <= 0x7E) or b in [0x09, 0x0A, 0x0D]
		encoding = self.getEncoding()
		string = self.string

		if encoding == 'utf_16_be' and len(string) % 2 == 1:
			# Recover badly encoded UTF-16 strings that have an odd number of bytes:
			# - If the last byte is zero, drop it.  Otherwise,
			# - If all the odd bytes are zero and all the even bytes are ASCII,
			#   prepend one zero byte.  Otherwise,
			# - If first byte is zero and all other bytes are ASCII, insert zero
			#   bytes between consecutive ASCII bytes.
			#
			# (Yes, I've seen all of these in the wild... sigh)
			if byteord(string[-1]) == 0:
				string = string[:-1]
			elif all(byteord(b) == 0 if i % 2 else isascii(byteord(b)) for i,b in enumerate(string)):
				string = b'\0' + string
			elif byteord(string[0]) == 0 and all(isascii(byteord(b)) for b in string[1:]):
				string = bytesjoin(b'\0'+bytechr(byteord(b)) for b in string[1:])

		string = tounicode(string, encoding=encoding, errors=errors)

		# If decoded strings still looks like UTF-16BE, it suggests a double-encoding.
		# Fix it up.
		if all(ord(c) == 0 if i % 2 == 0 else isascii(ord(c)) for i,c in enumerate(string)):
			# If string claims to be Mac encoding, but looks like UTF-16BE with ASCII text,
			# narrow it down.
			string = ''.join(c for c in string[1::2])

		return string

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

		if unistr is None or not self.encodingIsUnicodeCompatible():
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
