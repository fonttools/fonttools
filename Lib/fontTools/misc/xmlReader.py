from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.misc.textTools import safeEval
from fontTools.ttLib.tables.DefaultTable import DefaultTable
import os


class TTXParseError(Exception): pass

BUFSIZE = 0x4000


class XMLReader(object):
	
	def __init__(self, fileName, ttFont, progress=None, quiet=False):
		self.ttFont = ttFont
		self.fileName = fileName
		self.progress = progress
		self.quiet = quiet
		self.root = None
		self.contentStack = []
		self.stackSize = 0
	
	def read(self):
		if self.progress:
			import stat
			self.progress.set(0, os.stat(self.fileName)[stat.ST_SIZE] // 100 or 1)
		file = open(self.fileName)
		self._parseFile(file)
		file.close()
	
	def _parseFile(self, file):
		from xml.parsers.expat import ParserCreate
		parser = ParserCreate()
		parser.StartElementHandler = self._startElementHandler
		parser.EndElementHandler = self._endElementHandler
		parser.CharacterDataHandler = self._characterDataHandler
		
		pos = 0
		while True:
			chunk = file.read(BUFSIZE)
			if not chunk:
				parser.Parse(chunk, 1)
				break
			pos = pos + len(chunk)
			if self.progress:
				self.progress.set(pos // 100)
			parser.Parse(chunk, 0)
	
	def _startElementHandler(self, name, attrs):
		stackSize = self.stackSize
		self.stackSize = stackSize + 1
		if not stackSize:
			if name != "ttFont":
				raise TTXParseError("illegal root tag: %s" % name)
			sfntVersion = attrs.get("sfntVersion")
			if sfntVersion is not None:
				if len(sfntVersion) != 4:
					sfntVersion = safeEval('"' + sfntVersion + '"')
				self.ttFont.sfntVersion = sfntVersion
			self.contentStack.append([])
		elif stackSize == 1:
			subFile = attrs.get("src")
			if subFile is not None:
				subFile = os.path.join(os.path.dirname(self.fileName), subFile)
				subReader = XMLReader(subFile, self.ttFont, self.progress, self.quiet)
				subReader.read()
				self.contentStack.append([])
				return
			tag = ttLib.xmlToTag(name)
			msg = "Parsing '%s' table..." % tag
			if self.progress:
				self.progress.setlabel(msg)
			elif self.ttFont.verbose:
				ttLib.debugmsg(msg)
			else:
				if not self.quiet:
					print(msg)
			if tag == "GlyphOrder":
				tableClass = ttLib.GlyphOrder
			elif "ERROR" in attrs or ('raw' in attrs and safeEval(attrs['raw'])):
				tableClass = DefaultTable
			else:
				tableClass = ttLib.getTableClass(tag)
				if tableClass is None:
					tableClass = DefaultTable
			if tag == 'loca' and tag in self.ttFont:
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
			l = []
			self.contentStack[-1].append((name, attrs, l))
			self.contentStack.append(l)
	
	def _characterDataHandler(self, data):
		if self.stackSize > 1:
			self.contentStack[-1].append(data)
	
	def _endElementHandler(self, name):
		self.stackSize = self.stackSize - 1
		del self.contentStack[-1]
		if self.stackSize == 1:
			self.root = None
		elif self.stackSize == 2:
			name, attrs, content = self.root
			self.currentTable.fromXML(name, attrs, content, self.ttFont)
			self.root = None


class ProgressPrinter(object):
	
	def __init__(self, title, maxval=100):
		print(title)
	
	def set(self, val, maxval=None):
		pass
	
	def increment(self, val=1):
		pass
	
	def setLabel(self, text):
		print(text)

