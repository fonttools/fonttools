"""fontTools.ttLib -- a package for dealing with TrueType fonts.

This package offers translators to convert TrueType fonts to Python 
objects and vice versa, and additionally from Python to TTX (an XML-based
text format) and vice versa.

Example interactive session:

Python 1.5.2c1 (#43, Mar  9 1999, 13:06:43)  [CW PPC w/GUSI w/MSL]
Copyright 1991-1995 Stichting Mathematisch Centrum, Amsterdam
>>> from fontTools import ttLib
>>> tt = ttLib.TTFont("afont.ttf")
>>> tt['maxp'].numGlyphs
242
>>> tt['OS/2'].achVendID
'B&H\000'
>>> tt['head'].unitsPerEm
2048
>>> tt.saveXML("afont.ttx")
Dumping 'LTSH' table...
Dumping 'OS/2' table...
Dumping 'VDMX' table...
Dumping 'cmap' table...
Dumping 'cvt ' table...
Dumping 'fpgm' table...
Dumping 'glyf' table...
Dumping 'hdmx' table...
Dumping 'head' table...
Dumping 'hhea' table...
Dumping 'hmtx' table...
Dumping 'loca' table...
Dumping 'maxp' table...
Dumping 'name' table...
Dumping 'post' table...
Dumping 'prep' table...
>>> tt2 = ttLib.TTFont()
>>> tt2.importXML("afont.ttx")
>>> tt2['maxp'].numGlyphs
242
>>> 

"""

#
# $Id: __init__.py,v 1.16 2000-10-02 07:51:42 Just Exp $
#

__version__ = "1.0a6"

import os
import string
import types

class TTLibError(Exception): pass


class TTFont:
	
	"""The main font object. It manages file input and output, and offers
	a convenient way of accessing tables. 
	Tables will be only decompiled when neccesary, ie. when they're actually
	accessed. This means that simple operations can be extremely fast.
	"""
	
	def __init__(self, file=None, res_name_or_index=None, 
			sfntVersion="\000\001\000\000", checkchecksums=0, 
			verbose=0, recalcBBoxes=1):
		
		"""The constructor can be called with a few different arguments.
		When reading a font from disk, 'file' should be either a pathname
		pointing to a file, or a readable file object. 
		
		It we're running on a Macintosh, 'res_name_or_index' maybe an sfnt 
		resource name or an sfnt resource index number or zero. The latter 
		case will cause TTLib to autodetect whether the file is a flat file 
		or a suitcase. (If it's a suitcase, only the first 'sfnt' resource
		will be read!)
		
		The 'checkchecksums' argument is used to specify how sfnt
		checksums are treated upon reading a file from disk:
			0: don't check (default)
			1: check, print warnings if a wrong checksum is found (default)
			2: check, raise an exception if a wrong checksum is found.
		
		The TTFont constructor can also be called without a 'file' 
		argument: this is the way to create a new empty font. 
		In this case you can optionally supply the 'sfntVersion' argument.
		
		If the recalcBBoxes argument is false, a number of things will *not*
		be recalculated upon save/compile:
			1) glyph bounding boxes
			2) maxp font bounding box
			3) hhea min/max values
		(1) is needed for certain kinds of CJK fonts (ask Werner Lemberg ;-).
		Additionally, upon importing an TTX file, this option cause glyphs
		to be compiled right away. This should reduce memory consumption 
		greatly, and therefore should have some impact on the time needed 
		to parse/compile large fonts.
		"""
		
		import sfnt
		self.verbose = verbose
		self.recalcBBoxes = recalcBBoxes
		self.tables = {}
		self.reader = None
		if not file:
			self.sfntVersion = sfntVersion
			return
		if type(file) == types.StringType:
			if os.name == "mac" and res_name_or_index is not None:
				# on the mac, we deal with sfnt resources as well as flat files
				import macUtils
				if res_name_or_index == 0:
					if macUtils.getSFNTResIndices(file):
						# get the first available sfnt font.
						file = macUtils.SFNTResourceReader(file, 1)
					else:
						file = open(file, "rb")
				else:
					file = macUtils.SFNTResourceReader(file, res_name_or_index)
			else:
				file = open(file, "rb")
		else:
			pass # assume "file" is a readable file object
		self.reader = sfnt.SFNTReader(file, checkchecksums)
		self.sfntVersion = self.reader.sfntVersion
	
	def close(self):
		"""If we still have a reader object, close it."""
		if self.reader is not None:
			self.reader.close()
	
	def save(self, file, makeSuitcase=0):
		"""Save the font to disk. Similarly to the constructor, 
		the 'file' argument can be either a pathname or a writable
		file object.
		
		On the Mac, if makeSuitcase is true, a suitcase (resource fork)
		file will we made instead of a flat .ttf file. 
		"""
		from fontTools.ttLib import sfnt
		if type(file) == types.StringType:
			closeStream = 1
			if os.name == "mac" and makeSuitcase:
				import macUtils
				file = macUtils.SFNTResourceWriter(file, self)
			else:
				file = open(file, "wb")
				if os.name == "mac":
					import macfs
					fss = macfs.FSSpec(file.name)
					fss.SetCreatorType('mdos', 'BINA')
		else:
			# assume "file" is a writable file object
			closeStream = 0
		
		tags = self.keys()
		numTables = len(tags)
		writer = sfnt.SFNTWriter(file, numTables, self.sfntVersion)
		
		done = []
		for tag in tags:
			self._writeTable(tag, writer, done)
		
		writer.close(closeStream)
	
	def saveXML(self, fileOrPath, progress=None, 
			tables=None, skipTables=None, splitTables=0, disassembleInstructions=1):
		"""Export the font as TTX (an XML-based text file), or as a series of text
		files when splitTables is true. In the latter case, the 'fileOrPath'
		argument should be a path to a directory.
		The 'tables' argument must either be false (dump all tables) or a
		list of tables to dump. The 'skipTables' argument may be a list of tables
		to skip, but only when the 'tables' argument is false.
		"""
		import xmlWriter
		
		self.disassembleInstructions = disassembleInstructions
		if not tables:
			tables = self.keys()
			if skipTables:
				for tag in skipTables:
					if tag in tables:
						tables.remove(tag)
		numTables = len(tables)
		numGlyphs = self['maxp'].numGlyphs
		if progress:
			progress.set(0, numTables * numGlyphs)
		if not splitTables:
			writer = xmlWriter.XMLWriter(fileOrPath)
			writer.begintag("ttFont", sfntVersion=`self.sfntVersion`[1:-1], 
					ttLibVersion=__version__)
			writer.newline()
			writer.newline()
		else:
			# 'fileOrPath' must now be a path (pointing to a directory)
			if not os.path.exists(fileOrPath):
				os.mkdir(fileOrPath)
			fileNameTemplate = os.path.join(fileOrPath, 
					os.path.basename(fileOrPath)) + ".%s.ttx"
		
		for i in range(numTables):
			tag = tables[i]
			if splitTables:
				writer = xmlWriter.XMLWriter(fileNameTemplate % tag2identifier(tag))
				writer.begintag("ttFont", sfntVersion=`self.sfntVersion`[1:-1], 
						ttLibVersion=__version__)
				writer.newline()
				writer.newline()
			table = self[tag]
			report = "Dumping '%s' table..." % tag
			if progress:
				progress.setlabel(report)
			elif self.verbose:
				debugmsg(report)
			else:
				print report
			xmltag = tag2xmltag(tag)
			if hasattr(table, "ERROR"):
				writer.begintag(xmltag, ERROR="decompilation error")
			else:
				writer.begintag(xmltag)
			writer.newline()
			if tag == "glyf":
				table.toXML(writer, self, progress)
			elif tag == "CFF ":
				table.toXML(writer, self, progress)
			else:
				table.toXML(writer, self)
			writer.endtag(xmltag)
			writer.newline()
			writer.newline()
			if splitTables:
				writer.endtag("ttFont")
				writer.newline()
				writer.close()
			if progress:
				progress.set(i * numGlyphs, numTables * numGlyphs)
		if not splitTables:
			writer.endtag("ttFont")
			writer.newline()
			writer.close()
		if self.verbose:
			debugmsg("Done dumping TTX")
	
	def importXML(self, file, progress=None):
		"""Import an TTX file (an XML-based text format), so as to recreate
		a font object.
		"""
		import xmlImport, stat
		from xml.parsers.xmlproc import xmlproc
		builder = xmlImport.XMLApplication(self, progress)
		if progress:
			progress.set(0, os.stat(file)[stat.ST_SIZE] / 100 or 1)
		proc = xmlImport.UnicodeProcessor()
		proc.set_application(builder)
		proc.set_error_handler(xmlImport.XMLErrorHandler(proc))
		dir, filename = os.path.split(file)
		if dir:
			olddir = os.getcwd()
			os.chdir(dir)
		try:
			proc.parse_resource(filename)
			root = builder.root
		finally:
			if dir:
				os.chdir(olddir)
			# remove circular references
			proc.deref()
			del builder.progress
	
	def isLoaded(self, tag):
		"""Return true if the table identified by 'tag' has been 
		decompiled and loaded into memory."""
		return self.tables.has_key(tag)
	
	def has_key(self, tag):
		"""Pretend we're a dictionary."""
		if self.isLoaded(tag):
			return 1
		elif self.reader and self.reader.has_key(tag):
			return 1
		else:
			return 0
	
	def keys(self):
		"""Pretend we're a dictionary."""
		keys = self.tables.keys()
		if self.reader:
			for key in self.reader.keys():
				if key not in keys:
					keys.append(key)
		keys.sort()
		return keys
	
	def __len__(self):
		"""Pretend we're a dictionary."""
		return len(self.keys())
	
	def __getitem__(self, tag):
		"""Pretend we're a dictionary."""
		try:
			return self.tables[tag]
		except KeyError:
			if self.reader is not None:
				import traceback
				if self.verbose:
					debugmsg("reading '%s' table from disk" % tag)
				data = self.reader[tag]
				tableclass = getTableClass(tag)
				table = tableclass(tag)
				self.tables[tag] = table
				if self.verbose:
					debugmsg("decompiling '%s' table" % tag)
				try:
					table.decompile(data, self)
				except "_ _ F O O _ _": # dummy exception to disable exception catching
					print "An exception occurred during the decompilation of the '%s' table" % tag
					from tables.DefaultTable import DefaultTable
					import StringIO
					file = StringIO.StringIO()
					traceback.print_exc(file=file)
					table = DefaultTable(tag)
					table.ERROR = file.getvalue()
					self.tables[tag] = table
					table.decompile(data, self)
				return table
			else:
				raise KeyError, "'%s' table not found" % tag
	
	def __setitem__(self, tag, table):
		"""Pretend we're a dictionary."""
		self.tables[tag] = table
	
	def __delitem__(self, tag):
		"""Pretend we're a dictionary."""
		del self.tables[tag]
	
	def setGlyphOrder(self, glyphOrder):
		self.glyphOrder = glyphOrder
		if self.has_key('CFF '):
			self['CFF '].setGlyphOrder(glyphOrder)
		if self.has_key('glyf'):
			self['glyf'].setGlyphOrder(glyphOrder)
	
	def getGlyphOrder(self):
		if not hasattr(self, "glyphOrder"):
			if self.has_key('CFF '):
				# CFF OpenType font
				self.glyphOrder = self['CFF '].getGlyphOrder()
			elif self.has_key('post'):
				# TrueType font
				glyphOrder = self['post'].getGlyphOrder()
				if glyphOrder is None:
					#
					# No names found in the 'post' table.
					# Try to create glyph names from the unicode cmap (if available) 
					# in combination with the Adobe Glyph List (AGL).
					#
					self._getGlyphNamesFromCmap()
				else:
					self.glyphOrder = glyphOrder
			else:
				self._getGlyphNamesFromCmap()
			# XXX what if a font contains 'glyf'/'post' table *and* CFF?
		return self.glyphOrder
	
	def _getGlyphNamesFromCmap(self):
		# Make up glyph names based on glyphID, which will be used 
		# in case we don't find a unicode cmap.
		numGlyphs = int(self['maxp'].numGlyphs)
		glyphOrder = [None] * numGlyphs
		glyphOrder[0] = ".notdef"
		for i in range(1, numGlyphs):
			glyphOrder[i] = "glyph%.5d" % i
		# Set the glyph order, so the cmap parser has something
		# to work with
		self.glyphOrder = glyphOrder
		# Get the temporary cmap (based on the just invented names)
		tempcmap = self['cmap'].getcmap(3, 1)
		if tempcmap is not None:
			# we have a unicode cmap
			from fontTools import agl
			cmap = tempcmap.cmap
			# create a reverse cmap dict
			reversecmap = {}
			for unicode, name in cmap.items():
				reversecmap[name] = unicode
			for i in range(numGlyphs):
				tempName = glyphOrder[i]
				if reversecmap.has_key(tempName):
					unicode = reversecmap[tempName]
					if agl.UV2AGL.has_key(unicode):
						# get name from the Adobe Glyph List
						glyphOrder[i] = agl.UV2AGL[unicode]
					else:
						# create uni<CODE> name
						glyphOrder[i] = "uni" + string.upper(string.zfill(hex(unicode)[2:], 4))
			# Delete the cmap table from the cache, so it can be 
			# parsed again with the right names.
			del self.tables['cmap']
		else:
			pass # no unicode cmap available, stick with the invented names
		self.glyphOrder = glyphOrder
	
	def getGlyphNames(self):
		"""Get a list of glyph names, sorted alphabetically."""
		glyphNames = self.getGlyphOrder()[:]
		glyphNames.sort()
		return glyphNames
	
	def getGlyphNames2(self):
		"""Get a list of glyph names, sorted alphabetically, 
		but not case sensitive.
		"""
		from fontTools.misc import textTools
		return textTools.caselessSort(self.getGlyphOrder())
	
	def getGlyphName(self, glyphID):
		return self.getGlyphOrder()[glyphID]
	
	def getGlyphID(self, glyphName):
		if not hasattr(self, "_reverseGlyphOrderDict"):
			self._buildReverseGlyphOrderDict()
		glyphOrder = self.getGlyphOrder()
		d = self._reverseGlyphOrderDict
		if not d.has_key(glyphName):
			if glyphName in glyphOrder:
				self._buildReverseGlyphOrderDict()
				return self.getGlyphID(glyphName)
			else:
				raise KeyError, glyphName
		glyphID = d[glyphName]
		if glyphName <> glyphOrder[glyphID]:
			self._buildReverseGlyphOrderDict()
			return self.getGlyphID(glyphName)
		return glyphID
	
	def _buildReverseGlyphOrderDict(self):
		self._reverseGlyphOrderDict = d = {}
		glyphOrder = self.getGlyphOrder()
		for glyphID in range(len(glyphOrder)):
			d[glyphOrder[glyphID]] = glyphID
	
	def _writeTable(self, tag, writer, done):
		"""Internal helper function for self.save(). Keeps track of 
		inter-table dependencies.
		"""
		if tag in done:
			return
		tableclass = getTableClass(tag)
		for masterTable in tableclass.dependencies:
			if masterTable not in done:
				if self.has_key(masterTable):
					self._writeTable(masterTable, writer, done)
				else:
					done.append(masterTable)
		tabledata = self._getTableData(tag)
		if self.verbose:
			debugmsg("writing '%s' table to disk" % tag)
		writer[tag] = tabledata
		done.append(tag)
	
	def _getTableData(self, tag):
		"""Internal helper function. Returns raw table data,
		whether compiled or directly read from disk.
		"""
		if self.isLoaded(tag):
			if self.verbose:
				debugmsg("compiling '%s' table" % tag)
			return self.tables[tag].compile(self)
		elif self.reader and self.reader.has_key(tag):
			if self.verbose:
				debugmsg("reading '%s' table from disk" % tag)
			return self.reader[tag]
		else:
			raise KeyError, tag


def _test_endianness():
	"""Test the endianness of the machine. This is crucial to know
	since TrueType data is always big endian, even on little endian
	machines. There are quite a few situations where we explicitly
	need to swap some bytes.
	"""
	import struct
	data = struct.pack("h", 0x01)
	if data == "\000\001":
		return "big"
	elif data == "\001\000":
		return "little"
	else:
		assert 0, "endian confusion!"

endian = _test_endianness()


def getTableModule(tag):
	"""Fetch the packer/unpacker module for a table. 
	Return None when no module is found.
	"""
	import imp
	import tables
	py_tag = tag2identifier(tag)
	try:
		f, path, kind = imp.find_module(py_tag, tables.__path__)
		if f:
			f.close()
	except ImportError:
		return None
	else:
		module = __import__("fontTools.ttLib.tables." + py_tag)
		return getattr(tables, py_tag)


def getTableClass(tag):
	"""Fetch the packer/unpacker class for a table. 
	Return None when no class is found.
	"""
	module = getTableModule(tag)
	if module is None:
		from tables.DefaultTable import DefaultTable
		return DefaultTable
	py_tag = tag2identifier(tag)
	tableclass = getattr(module, "table_" + py_tag)
	return tableclass


def getNewTable(tag):
	"""Return a new instance of a table."""
	tableclass = getTableClass(tag)
	return tableclass(tag)


def _escapechar(c):
	"""Helper function for tag2identifier()"""
	import re
	if re.match("[a-z0-9]", c):
		return "_" + c
	elif re.match("[A-Z]", c):
		return c + "_"
	else:
		return hex(ord(c))[2:]


def tag2identifier(tag):
	"""Convert a table tag to a valid (but UGLY) python identifier, 
	as well as a filename that's guaranteed to be unique even on a 
	caseless file system. Each character is mapped to two characters.
	Lowercase letters get an underscore before the letter, uppercase
	letters get an underscore after the letter. Trailing spaces are
	trimmed. Illegal characters are escaped as two hex bytes. If the
	result starts with a number (as the result of a hex escape), an
	extra underscore is prepended. Examples: 
		'glyf' -> '_g_l_y_f'
		'cvt ' -> '_c_v_t'
		'OS/2' -> 'O_S_2f_2'
	"""
	import re
	assert len(tag) == 4, "tag should be 4 characters long"
	while len(tag) > 1 and tag[-1] == ' ':
		tag = tag[:-1]
	ident = ""
	for c in tag:
		ident = ident + _escapechar(c)
	if re.match("[0-9]", ident):
		ident = "_" + ident
	return ident


def identifier2tag(ident):
	"""the opposite of tag2identifier()"""
	if len(ident) % 2 and ident[0] == "_":
		ident = ident[1:]
	assert not (len(ident) % 2)
	tag = ""
	for i in range(0, len(ident), 2):
		if ident[i] == "_":
			tag = tag + ident[i+1]
		elif ident[i+1] == "_":
			tag = tag + ident[i]
		else:
			# assume hex
			tag = tag + chr(string.atoi(ident[i:i+2], 16))
	# append trailing spaces
	tag = tag + (4 - len(tag)) * ' '
	return tag


def tag2xmltag(tag):
	"""Similarly to tag2identifier(), this converts a TT tag
	to a valid XML element name. Since XML element names are
	case sensitive, this is a fairly simple/readable translation.
	"""
	import re
	if tag == "OS/2":
		return "OS_2"
	if re.match("[A-Za-z_][A-Za-z_0-9]* *$", tag):
		return string.strip(tag)
	else:
		return tag2identifier(tag)


def xmltag2tag(tag):
	"""The opposite of tag2xmltag()"""
	if tag == "OS_2":
		return "OS/2"
	if len(tag) == 8:
		return identifier2tag(tag)
	else:
		return tag + " " * (4 - len(tag))
	return tag


def debugmsg(msg):
	import time
	print msg + time.strftime("  (%H:%M:%S)", time.localtime(time.time()))


