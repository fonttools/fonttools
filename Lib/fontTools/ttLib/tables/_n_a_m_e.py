import DefaultTable
import struct, sstruct
from fontTools.misc.textTools import safeEval
import string
import types

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
			print "Warning: 'name' table stringOffset incorrect.",
			print "Expected: %s; Actual: %s" % (expectedStringOffset, stringOffset)
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
		self.names.sort()  # sort according to the spec; see NameRecord.__cmp__()
		stringData = ""
		format = 0
		n = len(self.names)
		stringOffset = 6 + n * sstruct.calcsize(nameRecordFormat)
		data = struct.pack(">HHH", format, n, stringOffset)
		lastoffset = 0
		done = {}  # remember the data so we can reuse the "pointers"
		for name in self.names:
			if done.has_key(name.string):
				name.offset, name.length = done[name.string]
			else:
				name.offset, name.length = done[name.string] = len(stringData), len(name.string)
				stringData = stringData + name.string
			data = data + sstruct.pack(nameRecordFormat, name)
		return data + stringData
	
	def toXML(self, writer, ttFont):
		for name in self.names:
			name.toXML(writer, ttFont)
	
	def fromXML(self, (name, attrs, content), ttFont):
		if name <> "namerecord":
			return # ignore unknown tags
		if not hasattr(self, "names"):
			self.names = []
		name = NameRecord()
		self.names.append(name)
		name.fromXML((name, attrs, content), ttFont)
	
	def getName(self, nameID, platformID, platEncID, langID=None):
		for namerecord in self.names:
			if (	namerecord.nameID == nameID and 
					namerecord.platformID == platformID and 
					namerecord.platEncID == platEncID):
				if langID is None or namerecord.langID == langID:
					return namerecord
		return None # not found
	
	def __cmp__(self, other):
		return cmp(self.names, other.names)
	

class NameRecord:
	
	def toXML(self, writer, ttFont):
		writer.begintag("namerecord", [
				("nameID", self.nameID),
				("platformID", self.platformID),
				("platEncID", self.platEncID),
				("langID", hex(self.langID)),
						])
		writer.newline()
		if self.platformID == 0 or (self.platformID == 3 and self.platEncID in (0, 1)):
			if len(self.string) % 2:
				# no, shouldn't happen, but some of the Apple
				# tools cause this anyway :-(
				writer.write16bit(self.string + "\0")
			else:
				writer.write16bit(self.string)
		else:
			writer.write8bit(self.string)
		writer.newline()
		writer.endtag("namerecord")
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.nameID = safeEval(attrs["nameID"])
		self.platformID = safeEval(attrs["platformID"])
		self.platEncID = safeEval(attrs["platEncID"])
		self.langID =  safeEval(attrs["langID"])
		if self.platformID == 0 or (self.platformID == 3 and self.platEncID in (0, 1)):
			s = ""
			for element in content:
				s = s + element
			s = unicode(s, "utf8")
			s = s.strip()
			self.string = s.encode("utf_16_be")
		else:
			s = string.strip(string.join(content, ""))
			self.string = unicode(s, "utf8").encode("latin1")
	
	def __cmp__(self, other):
		"""Compare method, so a list of NameRecords can be sorted
		according to the spec by just sorting it..."""
		selftuple = (self.platformID,
				self.platEncID,
				self.langID,
				self.nameID,
				self.string)
		othertuple = (other.platformID,
				other.platEncID,
				other.langID,
				other.nameID,
				other.string)
		return cmp(selftuple, othertuple)
	
	def __repr__(self):
		return "<NameRecord NameID=%d; PlatformID=%d; LanguageID=%d>" % (
				self.nameID, self.platformID, self.langID)
