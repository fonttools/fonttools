import DefaultTable
import struct
from fontTools.ttLib import sfnt
from fontTools.misc.textTools import safeEval, readHex
from types import TupleType, StringType


class table_V_O_R_G_(DefaultTable.DefaultTable):

	""" This table is structured so that you can treat it like a dictionary keyed by glyph name.
	ttFont['VORG'][<glyphName>] will return the vertical origin for any glyph
	ttFont['VORG'][<glyphName>] = <value> will set the vertical origin for any glyph.
	"""

	def decompile(self, data, ttFont):
		self.majorVersion, self.minorVersion, self.defaultVertOriginY, self.numVertOriginYMetrics = struct.unpack(">HHhH", data[:8])
		assert (self.majorVersion <= 1), "Major version of VORG table is higher than I knwo how to handle"
		data = data[8:]
		self.VOriginRecords = {}
		for i in range(self.numVertOriginYMetrics):
			gid, vOrigin = struct.unpack(">Hh", data[:4])
			glyphName = ttFont.getGlyphName(gid)
			self.VOriginRecords[glyphName] = vOrigin
			data = data[4:]

	def compile(self, ttFont):
		glyphNames = self.VOriginRecords.keys()
		self.numVertOriginYMetrics = len(glyphNames)
		data = struct.pack(">HHhH", self.majorVersion, self.minorVersion, self.defaultVertOriginY, self.numVertOriginYMetrics)
		vOriginTable = []
		for glyphName in glyphNames:
			try:
				gid = ttFont.getGlyphID(glyphName)
			except:
				assert 0, "VORG table contains a glyph name not in ttFont.getGlyphNames(): " + str(glyphName)
			vOriginTable.append([gid, self.VOriginRecords[glyphName]])
		vOriginTable.sort()
		for entry in vOriginTable:
			data = data + struct.pack(">Hh", entry[0], entry[1])
		return data

	def toXML(self, writer, ttFont):
		writer.simpletag("majorVersion", value=self.majorVersion)
		writer.newline()
		writer.simpletag("minorVersion", value=self.minorVersion)
		writer.newline()
		writer.simpletag("defaultVertOriginY", value=self.defaultVertOriginY)
		writer.newline()
		writer.simpletag("numVertOriginYMetrics", value=self.numVertOriginYMetrics)
		writer.newline()
		vOriginTable = []
		glyphNames = self.VOriginRecords.keys()
		for glyphName in glyphNames:
			try:
				gid = ttFont.getGlyphID(glyphName)
			except:
				assert 0, "VORG table contains a glyph name not in ttFont.getGlyphNames(): " + str(glyphName)
			vOriginTable.append([gid, glyphName, self.VOriginRecords[glyphName]])
		vOriginTable.sort()
		for entry in vOriginTable:
			vOriginRec = VOriginRecord(entry[1], entry[2])
			vOriginRec.toXML(writer, ttFont)

	def fromXML(self, (name, attrs, content), ttFont):
		if name == "VOriginRecord":
			for element in content:
				if isinstance(element, StringType):
					continue
			if not hasattr(self, "VOriginRecords"):
				self.VOriginRecords = {}
			vOriginRec = VOriginRecord()
			for element in content:
				if isinstance(element, StringType):
					continue
				vOriginRec.fromXML(element, ttFont)
			self.VOriginRecords[vOriginRec.glyphName] = vOriginRec.vOrigin
		elif attrs.has_key("value"):
			value =  safeEval(attrs["value"])
			setattr(self, name, value)

	def __getitem__(self, name):
		if not self.VOriginRecords.has_key(name):
			return self.defaultVertOriginY
			
		return self.VOriginRecords[name]

	def __setitem__(self, name, value):
		if  value != self.defaultVertOriginY:
			self.VOriginRecords[name] = value
		elif self.VOriginRecords.has_key(name):
			del self.VOriginRecords[name]


class VOriginRecord:

	def __init__(self, name = None, vOrigin = None):
		self.glyphName = name
		self.vOrigin = vOrigin

	def toXML(self, writer, ttFont):
		writer.begintag("VOriginRecord")
		writer.newline()
		writer.simpletag("glyphName", value=self.glyphName)
		writer.newline()
		writer.simpletag("vOrigin", value=self.vOrigin)
		writer.newline()
		writer.endtag("VOriginRecord")
		writer.newline()

	def fromXML(self, (name, attrs, content), ttFont):
		value = attrs["value"]
		if name == "glyphName":
			setattr(self, name, value)
		else:
			try:
				value = safeEval(value)
			except OverflowError:
				value = long(value)
			setattr(self, name, value)
