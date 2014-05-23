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

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import os
import sys

haveMacSupport = 0
if sys.platform == "mac":
	haveMacSupport = 1
elif sys.platform == "darwin" and sys.version_info[:3] != (2, 2, 0):
	# Python 2.2's Mac support is broken, so don't enable it there.
	haveMacSupport = 1


class TTLibError(Exception): pass


class TTFont(object):
	
	"""The main font object. It manages file input and output, and offers
	a convenient way of accessing tables. 
	Tables will be only decompiled when necessary, ie. when they're actually
	accessed. This means that simple operations can be extremely fast.
	"""
	
	def __init__(self, file=None, res_name_or_index=None,
			sfntVersion="\000\001\000\000", flavor=None, checkChecksums=False,
			verbose=False, recalcBBoxes=True, allowVID=False, ignoreDecompileErrors=False,
			recalcTimestamp=True, fontNumber=-1, lazy=False, quiet=False):
		
		"""The constructor can be called with a few different arguments.
		When reading a font from disk, 'file' should be either a pathname
		pointing to a file, or a readable file object. 
		
		It we're running on a Macintosh, 'res_name_or_index' maybe an sfnt 
		resource name or an sfnt resource index number or zero. The latter 
		case will cause TTLib to autodetect whether the file is a flat file 
		or a suitcase. (If it's a suitcase, only the first 'sfnt' resource
		will be read!)
		
		The 'checkChecksums' argument is used to specify how sfnt
		checksums are treated upon reading a file from disk:
			0: don't check (default)
			1: check, print warnings if a wrong checksum is found
			2: check, raise an exception if a wrong checksum is found.
		
		The TTFont constructor can also be called without a 'file' 
		argument: this is the way to create a new empty font. 
		In this case you can optionally supply the 'sfntVersion' argument,
		and a 'flavor' which can be None, or 'woff'.
		
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

		If the recalcTimestamp argument is false, the modified timestamp in the
		'head' table will *not* be recalculated upon save/compile.

		If the allowVID argument is set to true, then virtual GID's are
		supported. Asking for a glyph ID with a glyph name or GID that is not in
		the font will return a virtual GID.   This is valid for GSUB and cmap
		tables. For SING glyphlets, the cmap table is used to specify Unicode
		values for virtual GI's used in GSUB/GPOS rules. If the gid N is requested
		and does not exist in the font, or the glyphname has the form glyphN
		and does not exist in the font, then N is used as the virtual GID.
		Else, the first virtual GID is assigned as 0x1000 -1; for subsequent new
		virtual GIDs, the next is one less than the previous.

		If ignoreDecompileErrors is set to True, exceptions raised in
		individual tables during decompilation will be ignored, falling
		back to the DefaultTable implementation, which simply keeps the
		binary data.

		If lazy is set to True, many data structures are loaded lazily, upon
		access only.
		"""
		
		from fontTools.ttLib import sfnt
		self.verbose = verbose
		self.quiet = quiet
		self.lazy = lazy
		self.recalcBBoxes = recalcBBoxes
		self.recalcTimestamp = recalcTimestamp
		self.tables = {}
		self.reader = None

		# Permit the user to reference glyphs that are not int the font.
		self.last_vid = 0xFFFE # Can't make it be 0xFFFF, as the world is full unsigned short integer counters that get incremented after the last seen GID value.
		self.reverseVIDDict = {}
		self.VIDDict = {}
		self.allowVID = allowVID
		self.ignoreDecompileErrors = ignoreDecompileErrors

		if not file:
			self.sfntVersion = sfntVersion
			self.flavor = flavor
			self.flavorData = None
			return
		if not hasattr(file, "read"):
			# assume file is a string
			if haveMacSupport and res_name_or_index is not None:
				# on the mac, we deal with sfnt resources as well as flat files
				from . import macUtils
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
		self.reader = sfnt.SFNTReader(file, checkChecksums, fontNumber=fontNumber)
		self.sfntVersion = self.reader.sfntVersion
		self.flavor = self.reader.flavor
		self.flavorData = self.reader.flavorData
	
	def close(self):
		"""If we still have a reader object, close it."""
		if self.reader is not None:
			self.reader.close()
	
	def save(self, file, makeSuitcase=False, reorderTables=True):
		"""Save the font to disk. Similarly to the constructor, 
		the 'file' argument can be either a pathname or a writable
		file object.
		
		On the Mac, if makeSuitcase is true, a suitcase (resource fork)
		file will we made instead of a flat .ttf file. 
		"""
		from fontTools.ttLib import sfnt
		if not hasattr(file, "write"):
			closeStream = 1
			if os.name == "mac" and makeSuitcase:
				from . import macUtils
				file = macUtils.SFNTResourceWriter(file, self)
			else:
				file = open(file, "wb")
				if os.name == "mac":
					from fontTools.misc.macCreator import setMacCreatorAndType
					setMacCreatorAndType(file.name, 'mdos', 'BINA')
		else:
			# assume "file" is a writable file object
			closeStream = 0
		
		tags = list(self.keys())
		if "GlyphOrder" in tags:
			tags.remove("GlyphOrder")
		numTables = len(tags)
		if reorderTables:
			import tempfile
			tmp = tempfile.TemporaryFile(prefix="ttx-fonttools")
		else:
			tmp = file
		writer = sfnt.SFNTWriter(tmp, numTables, self.sfntVersion, self.flavor, self.flavorData)
		
		done = []
		for tag in tags:
			self._writeTable(tag, writer, done)
		
		writer.close()

		if reorderTables:
			tmp.flush()
			tmp.seek(0)
			reorderFontTables(tmp, file)
			tmp.close()

		if closeStream:
			file.close()
	
	def saveXML(self, fileOrPath, progress=None, quiet=False,
			tables=None, skipTables=None, splitTables=False, disassembleInstructions=True,
			bitmapGlyphDataFormat='raw'):
		"""Export the font as TTX (an XML-based text file), or as a series of text
		files when splitTables is true. In the latter case, the 'fileOrPath'
		argument should be a path to a directory.
		The 'tables' argument must either be false (dump all tables) or a
		list of tables to dump. The 'skipTables' argument may be a list of tables
		to skip, but only when the 'tables' argument is false.
		"""
		from fontTools import version
		from fontTools.misc import xmlWriter
		
		self.disassembleInstructions = disassembleInstructions
		self.bitmapGlyphDataFormat = bitmapGlyphDataFormat
		if not tables:
			tables = list(self.keys())
			if "GlyphOrder" not in tables:
				tables = ["GlyphOrder"] + tables
			if skipTables:
				for tag in skipTables:
					if tag in tables:
						tables.remove(tag)
		numTables = len(tables)
		if progress:
			progress.set(0, numTables)
			idlefunc = getattr(progress, "idle", None)
		else:
			idlefunc = None
		
		writer = xmlWriter.XMLWriter(fileOrPath, idlefunc=idlefunc)
		writer.begintag("ttFont", sfntVersion=repr(self.sfntVersion)[1:-1], 
				ttLibVersion=version)
		writer.newline()
		
		if not splitTables:
			writer.newline()
		else:
			# 'fileOrPath' must now be a path
			path, ext = os.path.splitext(fileOrPath)
			fileNameTemplate = path + ".%s" + ext
		
		for i in range(numTables):
			if progress:
				progress.set(i)
			tag = tables[i]
			if splitTables:
				tablePath = fileNameTemplate % tagToIdentifier(tag)
				tableWriter = xmlWriter.XMLWriter(tablePath, idlefunc=idlefunc)
				tableWriter.begintag("ttFont", ttLibVersion=version)
				tableWriter.newline()
				tableWriter.newline()
				writer.simpletag(tagToXML(tag), src=os.path.basename(tablePath))
				writer.newline()
			else:
				tableWriter = writer
			self._tableToXML(tableWriter, tag, progress, quiet)
			if splitTables:
				tableWriter.endtag("ttFont")
				tableWriter.newline()
				tableWriter.close()
		if progress:
			progress.set((i + 1))
		writer.endtag("ttFont")
		writer.newline()
		writer.close()
		if self.verbose:
			debugmsg("Done dumping TTX")
	
	def _tableToXML(self, writer, tag, progress, quiet):
		if tag in self:
			table = self[tag]
			report = "Dumping '%s' table..." % tag
		else:
			report = "No '%s' table found." % tag
		if progress:
			progress.setLabel(report)
		elif self.verbose:
			debugmsg(report)
		else:
			if not quiet:
				print(report)
		if tag not in self:
			return
		xmlTag = tagToXML(tag)
		if hasattr(table, "ERROR"):
			writer.begintag(xmlTag, ERROR="decompilation error")
		else:
			writer.begintag(xmlTag)
		writer.newline()
		if tag in ("glyf", "CFF "):
			table.toXML(writer, self, progress)
		else:
			table.toXML(writer, self)
		writer.endtag(xmlTag)
		writer.newline()
		writer.newline()
	
	def importXML(self, file, progress=None, quiet=False):
		"""Import a TTX file (an XML-based text format), so as to recreate
		a font object.
		"""
		if "maxp" in self and "post" in self:
			# Make sure the glyph order is loaded, as it otherwise gets
			# lost if the XML doesn't contain the glyph order, yet does
			# contain the table which was originally used to extract the
			# glyph names from (ie. 'post', 'cmap' or 'CFF ').
			self.getGlyphOrder()

		from fontTools.misc import xmlReader

		reader = xmlReader.XMLReader(file, self, progress, quiet)
		reader.read()
	
	def isLoaded(self, tag):
		"""Return true if the table identified by 'tag' has been 
		decompiled and loaded into memory."""
		return tag in self.tables
	
	def has_key(self, tag):
		if self.isLoaded(tag):
			return True
		elif self.reader and tag in self.reader:
			return True
		elif tag == "GlyphOrder":
			return True
		else:
			return False
	
	__contains__ = has_key
	
	def keys(self):
		keys = list(self.tables.keys())
		if self.reader:
			for key in list(self.reader.keys()):
				if key not in keys:
					keys.append(key)

		if "GlyphOrder" in keys:
			keys.remove("GlyphOrder")
		keys = sortedTagList(keys)
		return ["GlyphOrder"] + keys
	
	def __len__(self):
		return len(list(self.keys()))
	
	def __getitem__(self, tag):
		tag = Tag(tag)
		try:
			return self.tables[tag]
		except KeyError:
			if tag == "GlyphOrder":
				table = GlyphOrder(tag)
				self.tables[tag] = table
				return table
			if self.reader is not None:
				import traceback
				if self.verbose:
					debugmsg("Reading '%s' table from disk" % tag)
				data = self.reader[tag]
				tableClass = getTableClass(tag)
				table = tableClass(tag)
				self.tables[tag] = table
				if self.verbose:
					debugmsg("Decompiling '%s' table" % tag)
				try:
					table.decompile(data, self)
				except:
					if not self.ignoreDecompileErrors:
						raise
					# fall back to DefaultTable, retaining the binary table data
					print("An exception occurred during the decompilation of the '%s' table" % tag)
					from .tables.DefaultTable import DefaultTable
					file = StringIO()
					traceback.print_exc(file=file)
					table = DefaultTable(tag)
					table.ERROR = file.getvalue()
					self.tables[tag] = table
					table.decompile(data, self)
				return table
			else:
				raise KeyError("'%s' table not found" % tag)
	
	def __setitem__(self, tag, table):
		self.tables[Tag(tag)] = table
	
	def __delitem__(self, tag):
		if tag not in self:
			raise KeyError("'%s' table not found" % tag)
		if tag in self.tables:
			del self.tables[tag]
		if self.reader and tag in self.reader:
			del self.reader[tag]

	def get(self, tag, default=None):
		try:
			return self[tag]
		except KeyError:
			return default
	
	def setGlyphOrder(self, glyphOrder):
		self.glyphOrder = glyphOrder
	
	def getGlyphOrder(self):
		try:
			return self.glyphOrder
		except AttributeError:
			pass
		if 'CFF ' in self:
			cff = self['CFF ']
			self.glyphOrder = cff.getGlyphOrder()
		elif 'post' in self:
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
		return self.glyphOrder
	
	def _getGlyphNamesFromCmap(self):
		#
		# This is rather convoluted, but then again, it's an interesting problem:
		# - we need to use the unicode values found in the cmap table to
		#   build glyph names (eg. because there is only a minimal post table,
		#   or none at all).
		# - but the cmap parser also needs glyph names to work with...
		# So here's what we do:
		# - make up glyph names based on glyphID
		# - load a temporary cmap table based on those names
		# - extract the unicode values, build the "real" glyph names
		# - unload the temporary cmap table
		#
		if self.isLoaded("cmap"):
			# Bootstrapping: we're getting called by the cmap parser
			# itself. This means self.tables['cmap'] contains a partially
			# loaded cmap, making it impossible to get at a unicode
			# subtable here. We remove the partially loaded cmap and
			# restore it later.
			# This only happens if the cmap table is loaded before any
			# other table that does f.getGlyphOrder()  or f.getGlyphName().
			cmapLoading = self.tables['cmap']
			del self.tables['cmap']
		else:
			cmapLoading = None
		# Make up glyph names based on glyphID, which will be used by the
		# temporary cmap and by the real cmap in case we don't find a unicode
		# cmap.
		numGlyphs = int(self['maxp'].numGlyphs)
		glyphOrder = [None] * numGlyphs
		glyphOrder[0] = ".notdef"
		for i in range(1, numGlyphs):
			glyphOrder[i] = "glyph%.5d" % i
		# Set the glyph order, so the cmap parser has something
		# to work with (so we don't get called recursively).
		self.glyphOrder = glyphOrder
		# Get a (new) temporary cmap (based on the just invented names)
		tempcmap = self['cmap'].getcmap(3, 1)
		if tempcmap is not None:
			# we have a unicode cmap
			from fontTools import agl
			cmap = tempcmap.cmap
			# create a reverse cmap dict
			reversecmap = {}
			for unicode, name in list(cmap.items()):
				reversecmap[name] = unicode
			allNames = {}
			for i in range(numGlyphs):
				tempName = glyphOrder[i]
				if tempName in reversecmap:
					unicode = reversecmap[tempName]
					if unicode in agl.UV2AGL:
						# get name from the Adobe Glyph List
						glyphName = agl.UV2AGL[unicode]
					else:
						# create uni<CODE> name
						glyphName = "uni%04X" % unicode
					tempName = glyphName
					n = 1
					while tempName in allNames:
						tempName = glyphName + "#" + repr(n)
						n = n + 1
					glyphOrder[i] = tempName
					allNames[tempName] = 1
			# Delete the temporary cmap table from the cache, so it can
			# be parsed again with the right names.
			del self.tables['cmap']
		else:
			pass # no unicode cmap available, stick with the invented names
		self.glyphOrder = glyphOrder
		if cmapLoading:
			# restore partially loaded cmap, so it can continue loading
			# using the proper names.
			self.tables['cmap'] = cmapLoading
	
	def getGlyphNames(self):
		"""Get a list of glyph names, sorted alphabetically."""
		glyphNames = sorted(self.getGlyphOrder()[:])
		return glyphNames
	
	def getGlyphNames2(self):
		"""Get a list of glyph names, sorted alphabetically, 
		but not case sensitive.
		"""
		from fontTools.misc import textTools
		return textTools.caselessSort(self.getGlyphOrder())
	
	def getGlyphName(self, glyphID, requireReal=False):
		try:
			return self.getGlyphOrder()[glyphID]
		except IndexError:
			if requireReal or not self.allowVID:
				# XXX The ??.W8.otf font that ships with OSX uses higher glyphIDs in
				# the cmap table than there are glyphs. I don't think it's legal...
				return "glyph%.5d" % glyphID
			else:
				# user intends virtual GID support 	
				try:
					glyphName = self.VIDDict[glyphID]
				except KeyError:
					glyphName  ="glyph%.5d" % glyphID
					self.last_vid = min(glyphID, self.last_vid )
					self.reverseVIDDict[glyphName] = glyphID
					self.VIDDict[glyphID] = glyphName
				return glyphName

	def getGlyphID(self, glyphName, requireReal=False):
		if not hasattr(self, "_reverseGlyphOrderDict"):
			self._buildReverseGlyphOrderDict()
		glyphOrder = self.getGlyphOrder()
		d = self._reverseGlyphOrderDict
		if glyphName not in d:
			if glyphName in glyphOrder:
				self._buildReverseGlyphOrderDict()
				return self.getGlyphID(glyphName)
			else:
				if requireReal:
					raise KeyError(glyphName)
				elif not self.allowVID:
					# Handle glyphXXX only
					if glyphName[:5] == "glyph":
						try:
							return int(glyphName[5:])
						except (NameError, ValueError):
							raise KeyError(glyphName)
				else:
					# user intends virtual GID support 	
					try:
						glyphID = self.reverseVIDDict[glyphName]
					except KeyError:
						# if name is in glyphXXX format, use the specified name.
						if glyphName[:5] == "glyph":
							try:
								glyphID = int(glyphName[5:])
							except (NameError, ValueError):
								glyphID = None
						if glyphID is None:
							glyphID = self.last_vid -1
							self.last_vid = glyphID
						self.reverseVIDDict[glyphName] = glyphID
						self.VIDDict[glyphID] = glyphName
					return glyphID

		glyphID = d[glyphName]
		if glyphName != glyphOrder[glyphID]:
			self._buildReverseGlyphOrderDict()
			return self.getGlyphID(glyphName)
		return glyphID

	def getReverseGlyphMap(self, rebuild=False):
		if rebuild or not hasattr(self, "_reverseGlyphOrderDict"):
			self._buildReverseGlyphOrderDict()
		return self._reverseGlyphOrderDict

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
		tableClass = getTableClass(tag)
		for masterTable in tableClass.dependencies:
			if masterTable not in done:
				if masterTable in self:
					self._writeTable(masterTable, writer, done)
				else:
					done.append(masterTable)
		tabledata = self.getTableData(tag)
		if self.verbose:
			debugmsg("writing '%s' table to disk" % tag)
		writer[tag] = tabledata
		done.append(tag)
	
	def getTableData(self, tag):
		"""Returns raw table data, whether compiled or directly read from disk.
		"""
		tag = Tag(tag)
		if self.isLoaded(tag):
			if self.verbose:
				debugmsg("compiling '%s' table" % tag)
			return self.tables[tag].compile(self)
		elif self.reader and tag in self.reader:
			if self.verbose:
				debugmsg("Reading '%s' table from disk" % tag)
			return self.reader[tag]
		else:
			raise KeyError(tag)
	
	def getGlyphSet(self, preferCFF=True):
		"""Return a generic GlyphSet, which is a dict-like object
		mapping glyph names to glyph objects. The returned glyph objects
		have a .draw() method that supports the Pen protocol, and will
		have an attribute named 'width', but only *after* the .draw() method
		has been called.
		
		If the font is CFF-based, the outlines will be taken from the 'CFF '
		table. Otherwise the outlines will be taken from the 'glyf' table.
		If the font contains both a 'CFF ' and a 'glyf' table, you can use
		the 'preferCFF' argument to specify which one should be taken.
		"""
		if preferCFF and "CFF " in self:
			return list(self["CFF "].cff.values())[0].CharStrings
		if "glyf" in self:
			return _TTGlyphSet(self)
		if "CFF " in self:
			return list(self["CFF "].cff.values())[0].CharStrings
		raise TTLibError("Font contains no outlines")


class _TTGlyphSet(object):
	
	"""Generic dict-like GlyphSet class, meant as a TrueType counterpart
	to CFF's CharString dict. See TTFont.getGlyphSet().
	"""
	
	# This class is distinct from the 'glyf' table itself because we need
	# access to the 'hmtx' table, which could cause a dependency problem
	# there when reading from XML.
	
	def __init__(self, ttFont):
		self._ttFont = ttFont
	
	def keys(self):
		return list(self._ttFont["glyf"].keys())
	
	def has_key(self, glyphName):
		return glyphName in self._ttFont["glyf"]
	
	__contains__ = has_key

	def __getitem__(self, glyphName):
		return _TTGlyph(glyphName, self._ttFont)

	def get(self, glyphName, default=None):
		try:
			return self[glyphName]
		except KeyError:
			return default


class _TTGlyph(object):
	
	"""Wrapper for a TrueType glyph that supports the Pen protocol, meaning
	that it has a .draw() method that takes a pen object as its only
	argument. Additionally there is a 'width' attribute.
	"""
	
	def __init__(self, glyphName, ttFont):
		self._glyphName = glyphName
		self._ttFont = ttFont
		self.width, self.lsb = self._ttFont['hmtx'][self._glyphName]
	
	def draw(self, pen):
		"""Draw the glyph onto Pen. See fontTools.pens.basePen for details
		how that works.
		"""
		glyfTable = self._ttFont['glyf']
		glyph = glyfTable[self._glyphName]
		if hasattr(glyph, "xMin"):
			offset = self.lsb - glyph.xMin
		else:
			offset = 0
		if glyph.isComposite():
			for component in glyph:
				glyphName, transform = component.getComponentInfo()
				pen.addComponent(glyphName, transform)
		else:
			coordinates, endPts, flags = glyph.getCoordinates(glyfTable)
			if offset:
				coordinates = coordinates + (offset, 0)
			start = 0
			for end in endPts:
				end = end + 1
				contour = coordinates[start:end].tolist()
				cFlags = flags[start:end].tolist()
				start = end
				if 1 not in cFlags:
					# There is not a single on-curve point on the curve,
					# use pen.qCurveTo's special case by specifying None
					# as the on-curve point.
					contour.append(None)
					pen.qCurveTo(*contour)
				else:
					# Shuffle the points so that contour the is guaranteed
					# to *end* in an on-curve point, which we'll use for
					# the moveTo.
					firstOnCurve = cFlags.index(1) + 1
					contour = contour[firstOnCurve:] + contour[:firstOnCurve]
					cFlags = cFlags[firstOnCurve:] + cFlags[:firstOnCurve]
					pen.moveTo(contour[-1])
					while contour:
						nextOnCurve = cFlags.index(1) + 1
						if nextOnCurve == 1:
							pen.lineTo(contour[0])
						else:
							pen.qCurveTo(*contour[:nextOnCurve])
						contour = contour[nextOnCurve:]
						cFlags = cFlags[nextOnCurve:]
				pen.closePath()


class GlyphOrder(object):
	
	"""A pseudo table. The glyph order isn't in the font as a separate
	table, but it's nice to present it as such in the TTX format.
	"""
	
	def __init__(self, tag=None):
		pass
	
	def toXML(self, writer, ttFont):
		glyphOrder = ttFont.getGlyphOrder()
		writer.comment("The 'id' attribute is only for humans; "
				"it is ignored when parsed.")
		writer.newline()
		for i in range(len(glyphOrder)):
			glyphName = glyphOrder[i]
			writer.simpletag("GlyphID", id=i, name=glyphName)
			writer.newline()
	
	def fromXML(self, name, attrs, content, ttFont):
		if not hasattr(self, "glyphOrder"):
			self.glyphOrder = []
			ttFont.setGlyphOrder(self.glyphOrder)
		if name == "GlyphID":
			self.glyphOrder.append(attrs["name"])


def getTableModule(tag):
	"""Fetch the packer/unpacker module for a table. 
	Return None when no module is found.
	"""
	from . import tables
	pyTag = tagToIdentifier(tag)
	try:
		__import__("fontTools.ttLib.tables." + pyTag)
	except ImportError as err:
		# If pyTag is found in the ImportError message,
		# means table is not implemented.  If it's not
		# there, then some other module is missing, don't
		# suppress the error.
		if str(err).find(pyTag) >= 0:
			return None
		else:
			raise err
	else:
		return getattr(tables, pyTag)


def getTableClass(tag):
	"""Fetch the packer/unpacker class for a table. 
	Return None when no class is found.
	"""
	module = getTableModule(tag)
	if module is None:
		from .tables.DefaultTable import DefaultTable
		return DefaultTable
	pyTag = tagToIdentifier(tag)
	tableClass = getattr(module, "table_" + pyTag)
	return tableClass


def getClassTag(klass):
	"""Fetch the table tag for a class object."""
	name = klass.__name__
	assert name[:6] == 'table_'
	name = name[6:] # Chop 'table_'
	return identifierToTag(name)



def newTable(tag):
	"""Return a new instance of a table."""
	tableClass = getTableClass(tag)
	return tableClass(tag)


def _escapechar(c):
	"""Helper function for tagToIdentifier()"""
	import re
	if re.match("[a-z0-9]", c):
		return "_" + c
	elif re.match("[A-Z]", c):
		return c + "_"
	else:
		return hex(byteord(c))[2:]


def tagToIdentifier(tag):
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
	tag = Tag(tag)
	if tag == "GlyphOrder":
		return tag
	assert len(tag) == 4, "tag should be 4 characters long"
	while len(tag) > 1 and tag[-1] == ' ':
		tag = tag[:-1]
	ident = ""
	for c in tag:
		ident = ident + _escapechar(c)
	if re.match("[0-9]", ident):
		ident = "_" + ident
	return ident


def identifierToTag(ident):
	"""the opposite of tagToIdentifier()"""
	if ident == "GlyphOrder":
		return ident
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
			tag = tag + chr(int(ident[i:i+2], 16))
	# append trailing spaces
	tag = tag + (4 - len(tag)) * ' '
	return Tag(tag)


def tagToXML(tag):
	"""Similarly to tagToIdentifier(), this converts a TT tag
	to a valid XML element name. Since XML element names are
	case sensitive, this is a fairly simple/readable translation.
	"""
	import re
	tag = Tag(tag)
	if tag == "OS/2":
		return "OS_2"
	elif tag == "GlyphOrder":
		return tag
	if re.match("[A-Za-z_][A-Za-z_0-9]* *$", tag):
		return tag.strip()
	else:
		return tagToIdentifier(tag)


def xmlToTag(tag):
	"""The opposite of tagToXML()"""
	if tag == "OS_2":
		return Tag("OS/2")
	if len(tag) == 8:
		return identifierToTag(tag)
	else:
		return Tag(tag + " " * (4 - len(tag)))


def debugmsg(msg):
	import time
	print(msg + time.strftime("  (%H:%M:%S)", time.localtime(time.time())))


# Table order as recommended in the OpenType specification 1.4
TTFTableOrder = ["head", "hhea", "maxp", "OS/2", "hmtx", "LTSH", "VDMX",
                  "hdmx", "cmap", "fpgm", "prep", "cvt ", "loca", "glyf",
                  "kern", "name", "post", "gasp", "PCLT"]

OTFTableOrder = ["head", "hhea", "maxp", "OS/2", "name", "cmap", "post",
                  "CFF "]

def sortedTagList(tagList, tableOrder=None):
	"""Return a sorted copy of tagList, sorted according to the OpenType
	specification, or according to a custom tableOrder. If given and not
	None, tableOrder needs to be a list of tag names.
	"""
	tagList = sorted(tagList)
	if tableOrder is None:
		if "DSIG" in tagList:
			# DSIG should be last (XXX spec reference?)
			tagList.remove("DSIG")
			tagList.append("DSIG")
		if "CFF " in tagList:
			tableOrder = OTFTableOrder
		else:
			tableOrder = TTFTableOrder
	orderedTables = []
	for tag in tableOrder:
		if tag in tagList:
			orderedTables.append(tag)
			tagList.remove(tag)
	orderedTables.extend(tagList)
	return orderedTables


def reorderFontTables(inFile, outFile, tableOrder=None, checkChecksums=False):
	"""Rewrite a font file, ordering the tables as recommended by the
	OpenType specification 1.4.
	"""
	from fontTools.ttLib.sfnt import SFNTReader, SFNTWriter
	reader = SFNTReader(inFile, checkChecksums=checkChecksums)
	writer = SFNTWriter(outFile, len(reader.tables), reader.sfntVersion, reader.flavor, reader.flavorData)
	tables = list(reader.keys())
	for tag in sortedTagList(tables, tableOrder):
		writer[tag] = reader[tag]
	writer.close()
