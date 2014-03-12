from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
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
		self.names.sort()  # sort according to the spec; see NameRecord.__lt__()
		stringData = b""
		format = 0
		n = len(self.names)
		stringOffset = 6 + n * sstruct.calcsize(nameRecordFormat)
		data = struct.pack(">HHH", format, n, stringOffset)
		lastoffset = 0
		done = {}  # remember the data so we can reuse the "pointers"
		for name in self.names:
			if name.string in done:
				name.offset, name.length = done[name.string]
			else:
				name.offset, name.length = done[name.string] = len(stringData), len(name.string)
				stringData = stringData + name.string
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
	
	def isUnicode(self):
		return (self.platformID == 0 or
			(self.platformID == 3 and self.platEncID in [0, 1, 10]))

	def toXML(self, writer, ttFont):
		writer.begintag("namerecord", [
				("nameID", self.nameID),
				("platformID", self.platformID),
				("platEncID", self.platEncID),
				("langID", hex(self.langID)),
						])
		writer.newline()
		if self.isUnicode():
			if len(self.string) % 2:
				# no, shouldn't happen, but some of the Apple
				# tools cause this anyway :-(
				writer.write16bit(self.string + b"\0", strip=True)
			else:
				writer.write16bit(self.string, strip=True)
		else:
			writer.write8bit(self.string, strip=True)
		writer.newline()
		writer.endtag("namerecord")
		writer.newline()
	
	def fromXML(self, name, attrs, content, ttFont):
		self.nameID = safeEval(attrs["nameID"])
		self.platformID = safeEval(attrs["platformID"])
		self.platEncID = safeEval(attrs["platEncID"])
		self.langID =  safeEval(attrs["langID"])
		s = strjoin(content).strip()
		if self.isUnicode():
			self.string = s.encode("utf_16_be")
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
