from fontTools import ttLib
from fontTools.misc.textTools import safeEval
from fontTools.ttLib.tables.DefaultTable import DefaultTable
import types
import string
import Numeric, array
from xml.parsers.xmlproc import xmlproc


class TTXParseError(Exception): pass


class ExpatParser:
	
	def __init__(self, ttFont, progress=None):
		from xml.parsers.expat import ParserCreate
		self.ttFont = ttFont
		self.progress = progress
		self.root = None
		self.contentStack = []
		self.lastpos = 0
		self.stackSize = 0
		self.parser = ParserCreate()
		self.parser.returns_unicode = 0
		self.parser.StartElementHandler = self.StartElementHandler
		self.parser.EndElementHandler = self.EndElementHandler
		self.parser.CharacterDataHandler = self.CharacterDataHandler
	
	def ParseFile(self, file):
		self.parser.ParseFile(file)
	
	def StartElementHandler(self, name, attrs):
		if 0 and self.progress:
			# XXX
			pos = self.locator.pos + self.locator.block_offset
			if (pos - self.lastpos) > 4000:
				self.progress.set(pos / 100)
				self.lastpos = pos
		stackSize = self.stackSize
		self.stackSize = self.stackSize + 1
		if not stackSize:
			if name <> "ttFont":
				raise TTXParseError, "illegal root tag: %s" % name
			sfntVersion = attrs.get("sfntVersion", "\000\001\000\000")
			if len(sfntVersion) <> 4:
				sfntVersion = safeEval('"' + sfntVersion + '"')
			self.ttFont.sfntVersion = sfntVersion
			self.contentStack.append([])
		elif stackSize == 1:
			msg = "Parsing '%s' table..." % ttLib.xmltag2tag(name)
			if self.progress:
				self.progress.setlabel(msg)
			elif self.ttFont.verbose:
				ttLib.debugmsg(msg)
			else:
				print msg
			tag = ttLib.xmltag2tag(name)
			if attrs.has_key("ERROR"):
				tableClass = DefaultTable
			else:
				tableClass = ttLib.getTableClass(tag)
				if tableClass is None:
					tableClass = DefaultTable
			if self.ttFont.has_key(tag):
				self.currentTable = self.ttFont[tag]
			else:
				self.currentTable = tableClass(tag)
				self.ttFont[tag] = self.currentTable
			self.contentStack.append([])
		elif stackSize == 2:
			self.contentStack.append([])
			self.root = (name, attrs, self.contentStack[-1])
		else:
			list = []
			self.contentStack[-1].append((name, attrs, list))
			self.contentStack.append(list)
	
	def CharacterDataHandler(self, data):
		if self.stackSize > 1:
			self.contentStack[-1].append(data)
	
	def EndElementHandler(self, name):
		self.stackSize = self.stackSize - 1
		del self.contentStack[-1]
		if self.stackSize == 1:
			self.root = None
		elif self.stackSize == 2:
			self.currentTable.fromXML(self.root, self.ttFont)
			self.root = None


class ProgressPrinter:
	
	def __init__(self, title, maxval=100):
		print title
	
	def set(self, val, maxval=None):
		pass
	
	def increment(self, val=1):
		pass
	
	def setlabel(self, text):
		print text


def importXML(ttFont, fileName, progress=None):
	"""Import a TTX file (an XML-based text format), so as to recreate
	a font object.
	"""
	p = ExpatParser(ttFont, progress)
	file = open(fileName)
	p.ParseFile(file)
	file.close()

