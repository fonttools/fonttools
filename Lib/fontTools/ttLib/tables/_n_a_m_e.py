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

class table__n_a_m_e(DefaultTable.DefaultTable):
	
	def decompile(self, data, ttFont):
		format, n, stringoffset = struct.unpack(">HHH", data[:6])
		stringoffset = int(stringoffset)
		stringData = data[stringoffset:]
		data = data[6:stringoffset]
		self.names = []
		for i in range(n):
			name, data = sstruct.unpack2(nameRecordFormat, data, NameRecord())
			name.fixlongs()
			name.string = stringData[name.offset:name.offset+name.length]
			del name.offset, name.length
			self.names.append(name)
	
	def compile(self, ttFont):
		self.names.sort()  # sort according to the spec; see NameRecord.__cmp__()
		stringData = ""
		format = 0
		n = len(self.names)
		stringoffset = 6 + n * sstruct.calcsize(nameRecordFormat)
		data = struct.pack(">HHH", format, n, stringoffset)
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
	
	def getname(self, nameID, platformID, platEncID, langID=None):
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
		if self.platformID == 0 or (self.platformID == 3 and self.platEncID == 1):
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
			from fontTools.ttLib.xmlImport import UnicodeString
			str = UnicodeString("")
			for element in content:
				str = str + element
			self.string = str.stripped().tostring()
		else:
			self.string = string.strip(string.join(content, ""))
	
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
	
	def fixlongs(self):
		"""correct effects from bug in Python 1.5.1, where "H" 
		returns a Python Long int. 
		This has been fixed in Python 1.5.2.
		"""
		for attr in dir(self):
			val = getattr(self, attr)
			if type(val) == types.LongType:
				setattr(self, attr, int(val))

