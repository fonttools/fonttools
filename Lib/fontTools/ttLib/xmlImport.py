from fontTools import ttLib
from fontTools.misc.textTools import safeEval
from fontTools.ttLib.tables.DefaultTable import DefaultTable
import os


class TTXParseError(Exception): pass

BUFSIZE = 0x4000


class ExpatParser:
	
	def __init__(self, ttFont, fileName, progress=None):
		self.ttFont = ttFont
		self.fileName = fileName
		self.progress = progress
		self.root = None
		self.contentStack = []
		self.stackSize = 0
	
	def parse(self):
		file = open(self.fileName)
		self.parseFile(file)
		file.close()
	
	def parseFile(self, file):
		from xml.parsers.expat import ParserCreate
		parser = ParserCreate("latin1")
		parser.returns_unicode = 0
		parser.StartElementHandler = self.startElementHandler
		parser.EndElementHandler = self.endElementHandler
		parser.CharacterDataHandler = self.characterDataHandler
		
		pos = 0
		while 1:
			chunk = file.read(BUFSIZE)
			if not chunk:
				parser.Parse(chunk, 1)
				break
			pos = pos + len(chunk)
			if self.progress:
				self.progress.set(pos / 100)
			parser.Parse(chunk, 0)
	
	def startElementHandler(self, name, attrs):
		stackSize = self.stackSize
		self.stackSize = stackSize + 1
		if not stackSize:
			if name <> "ttFont":
				raise TTXParseError, "illegal root tag: %s" % name
			sfntVersion = attrs.get("sfntVersion")
			if sfntVersion is not None:
				if len(sfntVersion) <> 4:
					sfntVersion = safeEval('"' + sfntVersion + '"')
				self.ttFont.sfntVersion = sfntVersion
			self.contentStack.append([])
		elif stackSize == 1:
			subFile = attrs.get("src")
			if subFile is not None:
				subFile = os.path.join(os.path.dirname(self.fileName), subFile)
				importXML(self.ttFont, subFile, self.progress)
				self.contentStack.append([])
				return
			tag = ttLib.xmlToTag(name)
			msg = "Parsing '%s' table..." % tag
			if self.progress:
				self.progress.setlabel(msg)
			elif self.ttFont.verbose:
				ttLib.debugmsg(msg)
			else:
				print msg
			if tag == "GlyphOrder":
				tableClass = ttLib.GlyphOrder
			elif attrs.has_key("ERROR"):
				tableClass = DefaultTable
			else:
				tableClass = ttLib.getTableClass(tag)
				if tableClass is None:
					tableClass = DefaultTable
			if tag == 'loca' and self.ttFont.has_key(tag):
				# Special-case the 'loca' table as we need the
				#    original if the 'glyf' table isn't recompiled.
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
	
	def characterDataHandler(self, data):
		if self.stackSize > 1:
			self.contentStack[-1].append(data)
	
	def endElementHandler(self, name):
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
	
	def setLabel(self, text):
		print text


def importXML(ttFont, fileName, progress=None):
	"""Import a TTX file (an XML-based text format), so as to recreate
	a font object.
	"""
	if progress:
		import stat
		progress.set(0, os.stat(fileName)[stat.ST_SIZE] / 100 or 1)
	p = ExpatParser(ttFont, fileName, progress)
	p.parse()

