import string
import sys

class DefaultTable:
	
	dependencies = []
	
	def __init__(self, tag):
		self.tableTag = tag
	
	def decompile(self, data, ttFont):
		self.data = data
	
	def compile(self, ttFont):
		return self.data
	
	def toXML(self, writer, ttFont):
		if hasattr(self, "ERROR"):
			writer.comment("An error occurred during the decompilation of this table")
			writer.newline()
			writer.comment(self.ERROR)
			writer.newline()
		writer.begintag("hexdata")
		writer.newline()
		writer.dumphex(self.compile(ttFont))
		writer.endtag("hexdata")
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		from fontTools.misc.textTools import readHex
		from fontTools import ttLib
		if name <> "hexdata":
			raise ttLib.TTLibError, "can't handle '%s' element" % name
		self.decompile(readHex(content), ttFont)
	
	def __repr__(self):
		return "<'%s' table at %x>" % (self.tableTag, id(self))
	
	def __cmp__(self, other):
		return cmp(self.__dict__, other.__dict__)

