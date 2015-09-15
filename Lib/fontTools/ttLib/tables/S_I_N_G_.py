from . import DefaultTable
from fontTools.misc import sstruct
import struct
import time
from fontTools.misc.textTools import safeEval, num2binary, binary2num

SINGFormat = """
		>	# big endian
		tableVersionMajor:	H
		tableVersionMinor: 	H
		glyphletVersion:	H
		permissions:		h
		mainGID:			H
		unitsPerEm:			H
		vertAdvance:		h
		vertOrigin:			h
		uniqueName:			28s
		METAMD5:			16s
		nameLength:			1s
"""
# baseGlyphName is a byte string which follows the record above.
		


class table_S_I_N_G_(DefaultTable.DefaultTable):
	
	dependencies = []
	
	def decompile(self, data, ttFont):
		dummy, rest = sstruct.unpack2(SINGFormat, data, self)
		self.uniqueName = self.decompileUniqueName(self.uniqueName)
		self.nameLength = ord(self.nameLength)
		assert len(rest) == self.nameLength
		self.baseGlyphName = rest
		
		rawMETAMD5 = self.METAMD5
		self.METAMD5 = "[" + hex(ord(self.METAMD5[0]))
		for char in rawMETAMD5[1:]:
			self.METAMD5 = self.METAMD5 + ", " + hex(ord(char))
		self.METAMD5 = self.METAMD5 + "]"
		
	def decompileUniqueName(self, data):
		name = ""
		for char in data:
			val = ord(char)
			if val == 0:
				break
			if (val > 31) or (val < 128):
				name = name + char
			else:
				octString = oct(val)
				if len(octString) > 3:
					octString = octString[1:] # chop off that leading zero.
				elif len(octString) < 3:
					octString.zfill(3)
				name = name + "\\" + octString
		return name
		
		
	def compile(self, ttFont):
		self.nameLength = chr(len(self.baseGlyphName))
		self.uniqueName = self.compilecompileUniqueName(self.uniqueName, 28)
		METAMD5List = eval(self.METAMD5)
		self.METAMD5 = ""
		for val in METAMD5List:
			self.METAMD5 = self.METAMD5 + chr(val)
		assert (len(self.METAMD5) == 16), "Failed to pack 16 byte MD5 hash in SING table"
		data = sstruct.pack(SINGFormat, self)
		data = data + self.baseGlyphName
		return data
	
	def compilecompileUniqueName(self, name, length):
		nameLen = len(name)
		if length <= nameLen:
			name[:length-1] + "\000"
		else:
			name.join( (nameLen - length)* "\000")
		return name


	def toXML(self, writer, ttFont):
		writer.comment("Most of this table will be recalculated by the compiler")
		writer.newline()
		formatstring, names, fixes = sstruct.getformat(SINGFormat)
		for name in names:
			value = getattr(self, name)
			writer.simpletag(name, value=value)
			writer.newline()
		writer.simpletag("baseGlyphName", value=self.baseGlyphName)
		writer.newline()
		
	def fromXML(self, name, attrs, content, ttFont):
		value = attrs["value"]
		if name in ["uniqueName", "METAMD5", "baseGlyphName"]:
			setattr(self, name, value)
		else:
			setattr(self, name, safeEval(value))
