# -*- coding: utf-8 -*-
"""
glifLib.py -- Generic module for reading and writing the .glif format.

More info about the .glif format (GLyphInterchangeFormat) can be found here:

	http://unifiedfontobject.org

The main class in this module is GlyphSet. It manages a set of .glif files
in a folder. It offers two ways to read glyph data, and one way to write
glyph data. See the class doc string for details.
"""

from __future__ import unicode_literals
import os
from io import BytesIO, open
from warnings import warn
from fontTools.misc.py23 import tobytes, unicode
from ufoLib.plistlib import PlistWriter, readPlist, writePlist
from ufoLib.plistFromETree import readPlistFromTree
from ufoLib.pointPen import AbstractPointPen, PointToSegmentPen
from ufoLib.filenames import userNameToFileName
from ufoLib.validators import isDictEnough, genericTypeValidator, colorValidator,\
	guidelinesValidator, anchorsValidator, identifierValidator, imageValidator, glyphLibValidator

try:
	basestring
except NameError:
	basestring = str

try:
	from xml.etree import cElementTree as ElementTree
except ImportError:
	from xml.etree import ElementTree

__all__ = [
	"GlyphSet",
	"GlifLibError",
	"readGlyphFromString", "writeGlyphToString",
	"glyphNameToFileName"
]


class GlifLibError(Exception): pass

# ---------
# Constants
# ---------

LAYERINFO_FILENAME = "layerinfo.plist"
supportedUFOFormatVersions = [1, 2, 3]
supportedGLIFFormatVersions = [1, 2]


# ------------
# Simple Glyph
# ------------

class Glyph(object):

	"""
	Minimal glyph object. It has no glyph attributes until either
	the draw() or the drawPoints() method has been called.
	"""

	def __init__(self, glyphName, glyphSet):
		self.glyphName = glyphName
		self.glyphSet = glyphSet

	def draw(self, pen):
		"""
		Draw this glyph onto a *FontTools* Pen.
		"""
		pointPen = PointToSegmentPen(pen)
		self.drawPoints(pointPen)

	def drawPoints(self, pointPen):
		"""
		Draw this glyph onto a PointPen.
		"""
		self.glyphSet.readGlyph(self.glyphName, self, pointPen)


# ---------
# Glyph Set
# ---------

class GlyphSet(object):

	"""
	GlyphSet manages a set of .glif files inside one directory.

	GlyphSet's constructor takes a path to an existing directory as it's
	first argument. Reading glyph data can either be done through the
	readGlyph() method, or by using GlyphSet's dictionary interface, where
	the keys are glyph names and the values are (very) simple glyph objects.

	To write a glyph to the glyph set, you use the writeGlyph() method.
	The simple glyph objects returned through the dict interface do not
	support writing, they are just a convenient way to get at the glyph data.
	"""

	glyphClass = Glyph

	def __init__(self, dirName, glyphNameToFileNameFunc=None, ufoFormatVersion=3):
		"""
		'dirName' should be a path to an existing directory.

		The optional 'glyphNameToFileNameFunc' argument must be a callback
		function that takes two arguments: a glyph name and the GlyphSet
		instance. It should return a file name (including the .glif
		extension). The glyphNameToFileName function is called whenever
		a file name is created for a given glyph name.
		"""
		self.dirName = dirName
		if ufoFormatVersion not in supportedUFOFormatVersions:
			raise GlifLibError("Unsupported UFO format version: %s" % ufoFormatVersion)
		self.ufoFormatVersion = ufoFormatVersion
		if glyphNameToFileNameFunc is None:
			glyphNameToFileNameFunc = glyphNameToFileName
		self.glyphNameToFileName = glyphNameToFileNameFunc
		self.rebuildContents()
		self._reverseContents = None
		self._glifCache = {}

	def rebuildContents(self):
		"""
		Rebuild the contents dict by loading contents.plist.
		"""
		contentsPath = os.path.join(self.dirName, "contents.plist")
		if not os.path.exists(contentsPath):
			# missing, consider the glyphset empty.
			contents = {}
		else:
			contents = self._readPlist(contentsPath)
		# validate the contents
		invalidFormat = False
		if not isinstance(contents, dict):
			invalidFormat = True
		else:
			for name, fileName in list(contents.items()):
				if not isinstance(name, basestring):
					invalidFormat = True
				if not isinstance(fileName, basestring):
					invalidFormat = True
				elif not os.path.exists(os.path.join(self.dirName, fileName)):
					raise GlifLibError("contents.plist references a file that does not exist: %s" % fileName)
		if invalidFormat:
			raise GlifLibError("contents.plist is not properly formatted")
		self.contents = contents
		self._reverseContents = None

	def getReverseContents(self):
		"""
		Return a reversed dict of self.contents, mapping file names to
		glyph names. This is primarily an aid for custom glyph name to file
		name schemes that want to make sure they don't generate duplicate
		file names. The file names are converted to lowercase so we can
		reliably check for duplicates that only differ in case, which is
		important for case-insensitive file systems.
		"""
		if self._reverseContents is None:
			d = {}
			for k, v in self.contents.items():
				d[v.lower()] = k
			self._reverseContents = d
		return self._reverseContents

	def writeContents(self):
		"""
		Write the contents.plist file out to disk. Call this method when
		you're done writing glyphs.
		"""
		contentsPath = os.path.join(self.dirName, "contents.plist")
		with open(contentsPath, "wb") as f:
			writePlist(self.contents, f)

	# layer info

	def readLayerInfo(self, info):
		path = os.path.join(self.dirName, LAYERINFO_FILENAME)
		if not os.path.exists(path):
			return
		infoDict = self._readPlist(path)
		if not isinstance(infoDict, dict):
			raise GlifLibError("layerinfo.plist is not properly formatted.")
		infoDict = validateLayerInfoVersion3Data(infoDict)
		# populate the object
		for attr, value in list(infoDict.items()):
			try:
				setattr(info, attr, value)
			except AttributeError:
				raise GlifLibError("The supplied layer info object does not support setting a necessary attribute (%s)." % attr)

	def writeLayerInfo(self, info):
		if self.ufoFormatVersion < 3:
			raise GlifLibError("layerinfo.plist is not allowed in UFO %d." % self.ufoFormatVersion)
		# gather data
		infoData = {}
		for attr in list(layerInfoVersion3ValueData.keys()):
			if hasattr(info, attr):
				try:
					value = getattr(info, attr)
				except AttributeError:
					raise GlifLibError("The supplied info object does not support getting a necessary attribute (%s)." % attr)
				if value is None or (attr == 'lib' and not value):
					continue
				infoData[attr] = value
		# validate
		infoData = validateLayerInfoVersion3Data(infoData)
		# write file
		path = os.path.join(self.dirName, LAYERINFO_FILENAME)
		with open(path, "wb") as f:
			writePlist(infoData, f)

	# read caching

	def getGLIF(self, glyphName):
		"""
		Get the raw GLIF text for a given glyph name. This only works
		for GLIF files that are already on disk.

		This method is useful in situations when the raw XML needs to be
		read from a glyph set for a particular glyph before fully parsing
		it into an object structure via the readGlyph method.

		Internally, this method will load a GLIF the first time it is
		called and then cache it. The next time this method is called
		the GLIF will be pulled from the cache if the file's modification
		time has not changed since the GLIF was cached. For memory
		efficiency, the cached GLIF will be purged by various other methods
		such as readGlyph.
		"""
		needRead = False
		fileName = self.contents.get(glyphName)
		path = None
		if fileName is not None:
			path = os.path.join(self.dirName, fileName)
		if glyphName not in self._glifCache:
			needRead = True
		elif fileName is not None and os.path.getmtime(path) != self._glifCache[glyphName][1]:
			needRead = True
		if needRead:
			fileName = self.contents[glyphName]
			if not os.path.exists(path):
				raise KeyError(glyphName)
			with open(path, "rb") as f:
				text = f.read()
			self._glifCache[glyphName] = (text, os.path.getmtime(path))
		return self._glifCache[glyphName][0]

	def getGLIFModificationTime(self, glyphName):
		"""
		Get the modification time (as reported by os.path.getmtime)
		of the GLIF with glyphName.
		"""
		self.getGLIF(glyphName)
		return self._glifCache[glyphName][1]

	def _purgeCachedGLIF(self, glyphName):
		if glyphName in self._glifCache:
			del self._glifCache[glyphName]

	# reading/writing API

	def readGlyph(self, glyphName, glyphObject=None, pointPen=None):
		"""
		Read a .glif file for 'glyphName' from the glyph set. The
		'glyphObject' argument can be any kind of object (even None);
		the readGlyph() method will attempt to set the following
		attributes on it:
			"width"      the advance with of the glyph
			"height"     the advance height of the glyph
			"unicodes"   a list of unicode values for this glyph
			"note"       a string
			"lib"        a dictionary containing custom data
			"image"      a dictionary containing image data
			"guidelines" a list of guideline data dictionaries
			"anchors"    a list of anchor data dictionaries

		All attributes are optional, in two ways:
			1) An attribute *won't* be set if the .glif file doesn't
			   contain data for it. 'glyphObject' will have to deal
			   with default values itself.
			2) If setting the attribute fails with an AttributeError
			   (for example if the 'glyphObject' attribute is read-
			   only), readGlyph() will not propagate that exception,
			   but ignore that attribute.

		To retrieve outline information, you need to pass an object
		conforming to the PointPen protocol as the 'pointPen' argument.
		This argument may be None if you don't need the outline data.

		readGlyph() will raise KeyError if the glyph is not present in
		the glyph set.
		"""
		text = self.getGLIF(glyphName)
		self._purgeCachedGLIF(glyphName)
		tree = _glifTreeFromString(text)
		if self.ufoFormatVersion < 3:
			formatVersions = (1,)
		else:
			formatVersions = (1, 2)
		_readGlyphFromTree(tree, glyphObject, pointPen, formatVersions=formatVersions)

	def writeGlyph(self, glyphName, glyphObject=None, drawPointsFunc=None, formatVersion=None):
		"""
		Write a .glif file for 'glyphName' to the glyph set. The
		'glyphObject' argument can be any kind of object (even None);
		the writeGlyph() method will attempt to get the following
		attributes from it:
			"width"      the advance with of the glyph
			"height"     the advance height of the glyph
			"unicodes"   a list of unicode values for this glyph
			"note"       a string
			"lib"        a dictionary containing custom data
			"image"      a dictionary containing image data
			"guidelines" a list of guideline data dictionaries
			"anchors"    a list of anchor data dictionaries

		All attributes are optional: if 'glyphObject' doesn't
		have the attribute, it will simply be skipped.

		To write outline data to the .glif file, writeGlyph() needs
		a function (any callable object actually) that will take one
		argument: an object that conforms to the PointPen protocol.
		The function will be called by writeGlyph(); it has to call the
		proper PointPen methods to transfer the outline to the .glif file.

		The GLIF format version will be chosen based on the ufoFormatVersion
		passed during the creation of this object. If a particular format
		version is desired, it can be passed with the formatVersion argument.
		"""
		if formatVersion is None:
			if self.ufoFormatVersion >= 3:
				formatVersion = 2
			else:
				formatVersion = 1
		else:
			if formatVersion not in supportedGLIFFormatVersions:
				raise GlifLibError("Unsupported GLIF format version: %s" % formatVersion)
			if formatVersion == 2 and self.ufoFormatVersion < 3:
				raise GlifLibError("Unsupported GLIF format version (%d) for UFO format version %d." % (formatVersion, self.ufoFormatVersion))
		self._purgeCachedGLIF(glyphName)
		data = writeGlyphToString(glyphName, glyphObject, drawPointsFunc, formatVersion=formatVersion)
		fileName = self.contents.get(glyphName)
		if fileName is None:
			fileName = self.glyphNameToFileName(glyphName, self)
			self.contents[glyphName] = fileName
			if self._reverseContents is not None:
				self._reverseContents[fileName.lower()] = glyphName
		path = os.path.join(self.dirName, fileName)
		if os.path.exists(path):
			with open(path, "rb") as f:
				oldData = f.read()
			if data == oldData:
				return
		with open(path, "wb") as f:
			f.write(tobytes(data, encoding="utf-8"))

	def deleteGlyph(self, glyphName):
		"""Permanently delete the glyph from the glyph set on disk. Will
		raise KeyError if the glyph is not present in the glyph set.
		"""
		self._purgeCachedGLIF(glyphName)
		fileName = self.contents[glyphName]
		os.remove(os.path.join(self.dirName, fileName))
		if self._reverseContents is not None:
			del self._reverseContents[self.contents[glyphName].lower()]
		del self.contents[glyphName]

	# dict-like support

	def keys(self):
		return list(self.contents.keys())

	def has_key(self, glyphName):
		return glyphName in self.contents

	__contains__ = has_key

	def __len__(self):
		return len(self.contents)

	def __getitem__(self, glyphName):
		if glyphName not in self.contents:
			raise KeyError(glyphName)
		return self.glyphClass(glyphName, self)

	# quickly fetch unicode values

	def getUnicodes(self, glyphNames=None):
		"""
		Return a dictionary that maps glyph names to lists containing
		the unicode value[s] for that glyph, if any. This parses the .glif
		files partially, so it is a lot faster than parsing all files completely.
		By default this checks all glyphs, but a subset can be passed with glyphNames.
		"""
		unicodes = {}
		if glyphNames is None:
			glyphNames = list(self.contents.keys())
		for glyphName in glyphNames:
			text = self.getGLIF(glyphName)
			unicodes[glyphName] = _fetchUnicodes(text)
		return unicodes

	def getComponentReferences(self, glyphNames=None):
		"""
		Return a dictionary that maps glyph names to lists containing the
		base glyph name of components in the glyph. This parses the .glif
		files partially, so it is a lot faster than parsing all files completely.
		By default this checks all glyphs, but a subset can be passed with glyphNames.
		"""
		components = {}
		if glyphNames is None:
			glyphNames = list(self.contents.keys())
		for glyphName in glyphNames:
			text = self.getGLIF(glyphName)
			components[glyphName] = _fetchComponentBases(text)
		return components

	def getImageReferences(self, glyphNames=None):
		"""
		Return a dictionary that maps glyph names to the file name of the image
		referenced by the glyph. This parses the .glif files partially, so it is a
		lot faster than parsing all files completely.
		By default this checks all glyphs, but a subset can be passed with glyphNames.
		"""
		images = {}
		if glyphNames is None:
			glyphNames = list(self.contents.keys())
		for glyphName in glyphNames:
			text = self.getGLIF(glyphName)
			images[glyphName] = _fetchImageFileName(text)
		return images

	# internal methods

	def _readPlist(self, path):
		try:
			with open(path, "rb") as f:
				data = readPlist(f)
			return data
		except:
			raise GlifLibError("The file %s could not be read." % path)


# -----------------------
# Glyph Name to File Name
# -----------------------

def glyphNameToFileName(glyphName, glyphSet):
	"""
	Wrapper around the userNameToFileName function in filenames.py
	"""
	if glyphSet:
		existing = [name.lower() for name in list(glyphSet.contents.values())]
	else:
		existing = []
	if not isinstance(glyphName, unicode):
		try:
			new = unicode(glyphName)
			glyphName = new
		except UnicodeDecodeError:
			pass
	return userNameToFileName(glyphName, existing=existing, suffix=".glif")

# -----------------------
# GLIF To and From String
# -----------------------

def readGlyphFromString(aString, glyphObject=None, pointPen=None, formatVersions=(1, 2)):
	"""
	Read .glif data from a string into a glyph object.

	The 'glyphObject' argument can be any kind of object (even None);
	the readGlyphFromString() method will attempt to set the following
	attributes on it:
		"width"      the advance with of the glyph
		"height"     the advance height of the glyph
		"unicodes"   a list of unicode values for this glyph
		"note"       a string
		"lib"        a dictionary containing custom data
		"image"      a dictionary containing image data
		"guidelines" a list of guideline data dictionaries
		"anchors"    a list of anchor data dictionaries

	All attributes are optional, in two ways:
		1) An attribute *won't* be set if the .glif file doesn't
		   contain data for it. 'glyphObject' will have to deal
		   with default values itself.
		2) If setting the attribute fails with an AttributeError
		   (for example if the 'glyphObject' attribute is read-
		   only), readGlyphFromString() will not propagate that
		   exception, but ignore that attribute.

	To retrieve outline information, you need to pass an object
	conforming to the PointPen protocol as the 'pointPen' argument.
	This argument may be None if you don't need the outline data.

	The formatVersions argument defined the GLIF format versions
	that are allowed to be read.
	"""
	tree = _glifTreeFromString(aString)
	_readGlyphFromTree(tree, glyphObject, pointPen, formatVersions=formatVersions)


def writeGlyphToString(glyphName, glyphObject=None, drawPointsFunc=None, writer=None, formatVersion=2):
	"""
	Return .glif data for a glyph as a UTF-8 encoded string.
	The 'glyphObject' argument can be any kind of object (even None);
	the writeGlyphToString() method will attempt to get the following
	attributes from it:
		"width"      the advance width of the glyph
		"height"     the advance height of the glyph
		"unicodes"   a list of unicode values for this glyph
		"note"       a string
		"lib"        a dictionary containing custom data
		"image"      a dictionary containing image data
		"guidelines" a list of guideline data dictionaries
		"anchors"    a list of anchor data dictionaries

	All attributes are optional: if 'glyphObject' doesn't
	have the attribute, it will simply be skipped.

	To write outline data to the .glif file, writeGlyphToString() needs
	a function (any callable object actually) that will take one
	argument: an object that conforms to the PointPen protocol.
	The function will be called by writeGlyphToString(); it has to call the
	proper PointPen methods to transfer the outline to the .glif file.

	The GLIF format version can be specified with the formatVersion argument.
	"""
	if writer is None:
		try:
			from fontTools.misc.xmlWriter import XMLWriter
		except ImportError:
			# try the other location
			from xmlWriter import XMLWriter
		aFile = BytesIO()
		writer = XMLWriter(aFile, encoding="UTF-8")
	else:
		aFile = None
	identifiers = set()
	# start
	if not isinstance(glyphName, basestring):
		raise GlifLibError("The glyph name is not properly formatted.")
	if len(glyphName) == 0:
		raise GlifLibError("The glyph name is empty.")
	writer.begintag("glyph", [("name", glyphName), ("format", formatVersion)])
	writer.newline()
	# advance
	_writeAdvance(glyphObject, writer)
	# unicodes
	if getattr(glyphObject, "unicodes", None):
		_writeUnicodes(glyphObject, writer)
	# note
	if getattr(glyphObject, "note", None):
		_writeNote(glyphObject, writer)
	# image
	if formatVersion >= 2 and getattr(glyphObject, "image", None):
		_writeImage(glyphObject, writer)
	# guidelines
	if formatVersion >= 2 and getattr(glyphObject, "guidelines", None):
		_writeGuidelines(glyphObject, writer, identifiers)
	# anchors
	anchors = getattr(glyphObject, "anchors", None)
	if formatVersion >= 2 and anchors:
		_writeAnchors(glyphObject, writer, identifiers)
	# outline
	if drawPointsFunc is not None:
		writer.begintag("outline")
		writer.newline()
		pen = GLIFPointPen(writer, identifiers=identifiers)
		drawPointsFunc(pen)
		if formatVersion == 1 and anchors:
			_writeAnchorsFormat1(pen, anchors)
		writer.endtag("outline")
		writer.newline()
	# lib
	if getattr(glyphObject, "lib", None):
		_writeLib(glyphObject, writer)
	# end
	writer.endtag("glyph")
	writer.newline()
	# return the appropriate value
	if aFile is not None:
		return aFile.getvalue().decode("utf-8")
	else:
		return None

def _writeAdvance(glyphObject, writer):
	width = getattr(glyphObject, "width", None)
	if width is not None:
		if not isinstance(width, (int, float)):
			raise GlifLibError("width attribute must be int or float")
		if width == 0:
		    width = None
	height = getattr(glyphObject, "height", None)
	if height is not None:
		if not isinstance(height, (int, float)):
			raise GlifLibError("height attribute must be int or float")
		if height == 0:
		    height = None
	if width is not None and height is not None:
		writer.simpletag("advance", width=repr(width), height=repr(height))
		writer.newline()
	elif width is not None:
		writer.simpletag("advance", width=repr(width))
		writer.newline()
	elif height is not None:
		writer.simpletag("advance", height=repr(height))
		writer.newline()

def _writeUnicodes(glyphObject, writer):
	unicodes = getattr(glyphObject, "unicodes", None)
	if isinstance(unicodes, int):
		unicodes = [unicodes]
	seen = set()
	for code in unicodes:
		if not isinstance(code, int):
			raise GlifLibError("unicode values must be int")
		if code in seen:
			continue
		seen.add(code)
		hexCode = "%04X" % code
		writer.simpletag("unicode", hex=hexCode)
		writer.newline()

def _writeNote(glyphObject, writer):
	note = getattr(glyphObject, "note", None)
	if not isinstance(note, basestring):
		raise GlifLibError("note attribute must be str or unicode")
	note = note.encode("utf-8")
	writer.begintag("note")
	writer.newline()
	for line in note.splitlines():
		writer.write(line.strip())
		writer.newline()
	writer.endtag("note")
	writer.newline()

def _writeImage(glyphObject, writer):
	image = getattr(glyphObject, "image", None)
	if not imageValidator(image):
		raise GlifLibError("image attribute must be a dict or dict-like object with the proper structure.")
	attrs = [
		("fileName", image["fileName"])
	]
	for attr, default in _transformationInfo:
		value = image.get(attr, default)
		if value != default:
			attrs.append((attr, repr(value)))
	color = image.get("color")
	if color is not None:
		attrs.append(("color", color))
	writer.simpletag("image", attrs)
	writer.newline()

def _writeGuidelines(glyphObject, writer, identifiers):
	guidelines = getattr(glyphObject, "guidelines", [])
	if not guidelinesValidator(guidelines):
		raise GlifLibError("guidelines attribute does not have the proper structure.")
	for guideline in guidelines:
		attrs = []
		x = guideline.get("x")
		if x is not None:
			attrs.append(("x", repr(x)))
		y = guideline.get("y")
		if y is not None:
			attrs.append(("y", repr(y)))
		angle = guideline.get("angle")
		if angle is not None:
			attrs.append(("angle", repr(angle)))
		name = guideline.get("name")
		if name is not None:
			attrs.append(("name", name))
		color = guideline.get("color")
		if color is not None:
			attrs.append(("color", color))
		identifier = guideline.get("identifier")
		if identifier is not None:
			if identifier in identifiers:
				raise GlifLibError("identifier used more than once: %s" % identifier)
			attrs.append(("identifier", identifier))
			identifiers.add(identifier)
		writer.simpletag("guideline", attrs)
		writer.newline()

def _writeAnchorsFormat1(pen, anchors):
	if not anchorsValidator(anchors):
		raise GlifLibError("anchors attribute does not have the proper structure.")
	for anchor in anchors:
		attrs = []
		x = anchor["x"]
		attrs.append(("x", repr(x)))
		y = anchor["y"]
		attrs.append(("y", repr(y)))
		name = anchor.get("name")
		if name is not None:
			attrs.append(("name", name))
		pen.beginPath()
		pen.addPoint((x, y), segmentType="move", name=name)
		pen.endPath()

def _writeAnchors(glyphObject, writer, identifiers):
	anchors = getattr(glyphObject, "anchors", [])
	if not anchorsValidator(anchors):
		raise GlifLibError("anchors attribute does not have the proper structure.")
	for anchor in anchors:
		attrs = []
		x = anchor["x"]
		attrs.append(("x", repr(x)))
		y = anchor["y"]
		attrs.append(("y", repr(y)))
		name = anchor.get("name")
		if name is not None:
			attrs.append(("name", name))
		color = anchor.get("color")
		if color is not None:
			attrs.append(("color", color))
		identifier = anchor.get("identifier")
		if identifier is not None:
			if identifier in identifiers:
				raise GlifLibError("identifier used more than once: %s" % identifier)
			attrs.append(("identifier", identifier))
			identifiers.add(identifier)
		writer.simpletag("anchor", attrs)
		writer.newline()

def _writeLib(glyphObject, writer):
	lib = getattr(glyphObject, "lib", None)
	valid, message = glyphLibValidator(lib)
	if not valid:
		raise GlifLibError(message)
	if not isinstance(lib, dict):
		lib = dict(lib)
	writer.begintag("lib")
	writer.newline()
	plistWriter = PlistWriter(writer.file, indentLevel=writer.indentlevel,
			indent=writer.indentwhite, writeHeader=False)
	plistWriter.writeValue(lib)
	writer.endtag("lib")
	writer.newline()

# -----------------------
# layerinfo.plist Support
# -----------------------

layerInfoVersion3ValueData = {
	"color"			: dict(type=basestring, valueValidator=colorValidator),
	"lib"			: dict(type=dict, valueValidator=genericTypeValidator)
}

def validateLayerInfoVersion3ValueForAttribute(attr, value):
	"""
	This performs very basic validation of the value for attribute
	following the UFO 3 fontinfo.plist specification. The results
	of this should not be interpretted as *correct* for the font
	that they are part of. This merely indicates that the value
	is of the proper type and, where the specification defines
	a set range of possible values for an attribute, that the
	value is in the accepted range.
	"""
	if attr not in layerInfoVersion3ValueData:
		return False
	dataValidationDict = layerInfoVersion3ValueData[attr]
	valueType = dataValidationDict.get("type")
	validator = dataValidationDict.get("valueValidator")
	valueOptions = dataValidationDict.get("valueOptions")
	# have specific options for the validator
	if valueOptions is not None:
		isValidValue = validator(value, valueOptions)
	# no specific options
	else:
		if validator == genericTypeValidator:
			isValidValue = validator(value, valueType)
		else:
			isValidValue = validator(value)
	return isValidValue

def validateLayerInfoVersion3Data(infoData):
	"""
	This performs very basic validation of the value for infoData
	following the UFO 3 layerinfo.plist specification. The results
	of this should not be interpretted as *correct* for the font
	that they are part of. This merely indicates that the values
	are of the proper type and, where the specification defines
	a set range of possible values for an attribute, that the
	value is in the accepted range.
	"""
	validInfoData = {}
	for attr, value in list(infoData.items()):
		if attr not in layerInfoVersion3ValueData:
			raise GlifLibError("Unknown attribute %s." % attr)
		isValidValue = validateLayerInfoVersion3ValueForAttribute(attr, value)
		if not isValidValue:
			raise GlifLibError("Invalid value for attribute %s (%s)." % (attr, repr(value)))
		else:
			validInfoData[attr] = value
	return validInfoData

# -----------------
# GLIF Tree Support
# -----------------

def _glifTreeFromFile(aFile):
	root = ElementTree.parse(aFile).getroot()
	if root.tag != "glyph":
		raise GlifLibError("The GLIF is not properly formatted.")
	if root.text and root.text.strip() != '':
		raise GlifLibError("Invalid GLIF structure.")
	return root

def _glifTreeFromString(aString):
	root = ElementTree.fromstring(aString)
	if root.tag != "glyph":
		raise GlifLibError("The GLIF is not properly formatted.")
	if root.text and root.text.strip() != '':
		raise GlifLibError("Invalid GLIF structure.")
	return root

def _readGlyphFromTree(tree, glyphObject=None, pointPen=None, formatVersions=(1, 2)):
	# check the format version
	formatVersion = tree.get("format")
	if formatVersion is None:
		raise GlifLibError("Unspecified format version in GLIF.")
	try:
		v = int(formatVersion)
		formatVersion = v
	except ValueError:
		pass
	if formatVersion not in formatVersions:
		raise GlifLibError("Forbidden GLIF format version: %s" % formatVersion)
	if formatVersion == 1:
		_readGlyphFromTreeFormat1(tree=tree, glyphObject=glyphObject, pointPen=pointPen)
	elif formatVersion == 2:
		_readGlyphFromTreeFormat2(tree=tree, glyphObject=glyphObject, pointPen=pointPen)
	else:
		raise GlifLibError("Unsupported GLIF format version: %s" % formatVersion)


def _readGlyphFromTreeFormat1(tree, glyphObject=None, pointPen=None):
	# get the name
	_readName(glyphObject, tree)
	# populate the sub elements
	unicodes = []
	haveSeenAdvance = haveSeenOutline = haveSeenLib = haveSeenNote = False
	for element in tree:
		if element.tag == "outline":
			if haveSeenOutline:
				raise GlifLibError("The outline element occurs more than once.")
			if element.attrib:
				raise GlifLibError("The outline element contains unknown attributes.")
			if element.text and element.text.strip() != '':
				raise GlifLibError("Invalid outline structure.")
			haveSeenOutline = True
			buildOutlineFormat1(glyphObject, pointPen, element)
		elif glyphObject is None:
			continue
		elif element.tag == "advance":
			if haveSeenAdvance:
				raise GlifLibError("The advance element occurs more than once.")
			haveSeenAdvance = True
			_readAdvance(glyphObject, element)
		elif element.tag == "unicode":
			try:
				v = element.get("hex")
				v = int(v, 16)
				if v not in unicodes:
					unicodes.append(v)
			except ValueError:
				raise GlifLibError("Illegal value for hex attribute of unicode element.")
		elif element.tag == "note":
			if haveSeenNote:
				raise GlifLibError("The note element occurs more than once.")
			haveSeenNote = True
			_readNote(glyphObject, element)
		elif element.tag == "lib":
			if haveSeenLib:
				raise GlifLibError("The lib element occurs more than once.")
			haveSeenLib = True
			_readLib(glyphObject, element)
		else:
			raise GlifLibError("Unknown element in GLIF: %s" % element)
	# set the collected unicodes
	if unicodes:
		_relaxedSetattr(glyphObject, "unicodes", unicodes)

def _readGlyphFromTreeFormat2(tree, glyphObject=None, pointPen=None):
	# get the name
	_readName(glyphObject, tree)
	# populate the sub elements
	unicodes = []
	guidelines = []
	anchors = []
	haveSeenAdvance = haveSeenImage = haveSeenOutline = haveSeenLib = haveSeenNote = False
	identifiers = set()
	for element in tree:
		if element.tag == "outline":
			if haveSeenOutline:
				raise GlifLibError("The outline element occurs more than once.")
			if element.attrib:
				raise GlifLibError("The outline element contains unknown attributes.")
			if element.text and element.text.strip() != '':
				raise GlifLibError("Invalid outline structure.")
			haveSeenOutline = True
			if pointPen is not None:
				buildOutlineFormat2(glyphObject, pointPen, element, identifiers)
		elif glyphObject is None:
			continue
		elif element.tag == "advance":
			if haveSeenAdvance:
				raise GlifLibError("The advance element occurs more than once.")
			haveSeenAdvance = True
			_readAdvance(glyphObject, element)
		elif element.tag == "unicode":
			try:
				v = element.get("hex")
				v = int(v, 16)
				if v not in unicodes:
					unicodes.append(v)
			except ValueError:
				raise GlifLibError("Illegal value for hex attribute of unicode element.")
		elif element.tag == "guideline":
			if len(element):
				raise GlifLibError("Unknown children in guideline element.")
			for attr in ("x", "y", "angle"):
				if attr in element.attrib:
					element.attrib[attr] = _number(element.attrib[attr])
			guidelines.append(element.attrib)
		elif element.tag == "anchor":
			if len(element):
				raise GlifLibError("Unknown children in anchor element.")
			for attr in ("x", "y"):
				if attr in element.attrib:
					element.attrib[attr] = _number(element.attrib[attr])
			anchors.append(element.attrib)
		elif element.tag == "image":
			if haveSeenImage:
				raise GlifLibError("The image element occurs more than once.")
			if len(element):
				raise GlifLibError("Unknown children in image element.")
			haveSeenImage = True
			_readImage(glyphObject, element)
		elif element.tag == "note":
			if haveSeenNote:
				raise GlifLibError("The note element occurs more than once.")
			haveSeenNote = True
			_readNote(glyphObject, element)
		elif element.tag == "lib":
			if haveSeenLib:
				raise GlifLibError("The lib element occurs more than once.")
			haveSeenLib = True
			_readLib(glyphObject, element)
		else:
			raise GlifLibError("Unknown element in GLIF: %s" % element)
	# set the collected unicodes
	if unicodes:
		_relaxedSetattr(glyphObject, "unicodes", unicodes)
	# set the collected guidelines
	if guidelines:
		if not guidelinesValidator(guidelines, identifiers):
			raise GlifLibError("The guidelines are improperly formatted.")
		_relaxedSetattr(glyphObject, "guidelines", guidelines)
	# set the collected anchors
	if anchors:
		if not anchorsValidator(anchors, identifiers):
			raise GlifLibError("The anchors are improperly formatted.")
		_relaxedSetattr(glyphObject, "anchors", anchors)

def _readName(glyphObject, root):
	glyphName = root.get("name")
	if not glyphName:
		raise GlifLibError("Empty glyph name in GLIF.")
	if glyphName and glyphObject is not None:
		_relaxedSetattr(glyphObject, "name", glyphName)

def _readAdvance(glyphObject, advance):
	width = _number(advance.get("width", 0))
	_relaxedSetattr(glyphObject, "width", width)
	height = _number(advance.get("height", 0))
	_relaxedSetattr(glyphObject, "height", height)

def _readNote(glyphObject, note):
	lines = note.text.split("\n")
	note = "\n".join(line.strip() for line in lines if line.strip())
	_relaxedSetattr(glyphObject, "note", note)

def _readLib(glyphObject, lib):
	assert len(lib) == 1
	child = lib[0]
	plist = readPlistFromTree(child)
	valid, message = glyphLibValidator(plist)
	if not valid:
		raise GlifLibError(message)
	_relaxedSetattr(glyphObject, "lib", plist)

def _readImage(glyphObject, image):
	imageData = image.attrib
	for attr, default in _transformationInfo:
		value = imageData.get(attr, default)
		imageData[attr] = _number(value)
	if not imageValidator(imageData):
		raise GlifLibError("The image element is not properly formatted.")
	_relaxedSetattr(glyphObject, "image", imageData)

# ----------------
# GLIF to PointPen
# ----------------

contourAttributesFormat2 = set(["identifier"])
componentAttributesFormat1 = set(["base", "xScale", "xyScale", "yxScale", "yScale", "xOffset", "yOffset"])
componentAttributesFormat2 = componentAttributesFormat1 | set(["identifier"])
pointAttributesFormat1 = set(["x", "y", "type", "smooth", "name"])
pointAttributesFormat2 = pointAttributesFormat1 | set(["identifier"])
pointSmoothOptions = set(("no", "yes"))
pointTypeOptions = set(["move", "line", "offcurve", "curve", "qcurve"])

# format 1

componentAttributesFormat1 = set(["base", "xScale", "xyScale", "yxScale", "yScale", "xOffset", "yOffset"])
pointAttributesFormat1 = set(["x", "y", "type", "smooth", "name"])
pointSmoothOptions = set(("no", "yes"))
pointTypeOptions = set(["move", "line", "offcurve", "curve", "qcurve"])

def buildOutlineFormat1(glyphObject, pen, outline):
	anchors = []
	for element in outline:
		if element.tag == "contour":
			if len(element) == 1:
				point = element[0]
				if point.tag == "point":
					anchor = _buildAnchorFormat1(point)
					if anchor is not None:
						anchors.append(anchor)
						continue
			if pen is not None:
				_buildOutlineContourFormat1(pen, element)
		elif element.tag == "component":
			if pen is not None:
				_buildOutlineComponentFormat1(pen, element)
		else:
			raise GlifLibError("Unknown element in outline element: %s" % element)
	if glyphObject is not None and anchors:
		if not anchorsValidator(anchors):
			raise GlifLibError("GLIF 1 anchors are not properly formatted.")
		_relaxedSetattr(glyphObject, "anchors", anchors)

def _buildAnchorFormat1(point):
	if point.get("type") != "move":
		return None
	x = point.get("x")
	y = point.get("y")
	if x is None:
		raise GlifLibError("Required x attribute is missing in point element.")
	if y is None:
		raise GlifLibError("Required y attribute is missing in point element.")
	x = _number(x)
	y = _number(y)
	name = point.get("name")
	anchor = dict(x=x, y=y, name=name)
	return anchor

def _buildOutlineContourFormat1(pen, contour):
	if contour.attrib:
		raise GlifLibError("Unknown attributes in contour element.")
	pen.beginPath()
	if len(contour):
		_validateAndMassagePointStructures(contour, pointAttributesFormat1, openContourOffCurveLeniency=True)
		_buildOutlinePointsFormat1(pen, contour)
	pen.endPath()

def _buildOutlinePointsFormat1(pen, contour):
	for index, element in enumerate(contour):
		x = element.attrib["x"]
		y = element.attrib["y"]
		segmentType = element.attrib["segmentType"]
		smooth = element.attrib["smooth"]
		name = element.attrib["name"]
		pen.addPoint((x, y), segmentType=segmentType, smooth=smooth, name=name)

def _buildOutlineComponentFormat1(pen, component):
	if len(component):
		raise GlifLibError("Unknown child elements of component element.")
	if set(component.attrib.keys()) - componentAttributesFormat1:
		raise GlifLibError("Unknown attributes in component element.")
	baseGlyphName = component.get("base")
	if baseGlyphName is None:
		raise GlifLibError("The base attribute is not defined in the component.")
	transformation = []
	for attr, default in _transformationInfo:
		value = component.get(attr)
		if value is None:
			value = default
		else:
			value = _number(value)
		transformation.append(value)
	pen.addComponent(baseGlyphName, tuple(transformation))

# format 2

def buildOutlineFormat2(glyphObject, pen, outline, identifiers):
	for element in outline:
		if element.tag == "contour":
			_buildOutlineContourFormat2(pen, element, identifiers)
		elif element.tag == "component":
			_buildOutlineComponentFormat2(pen, element, identifiers)
		else:
			raise GlifLibError("Unknown element in outline element: %s" % element.tag)

def _buildOutlineContourFormat2(pen, contour, identifiers):
	if set(contour.attrib.keys()) - contourAttributesFormat2:
		raise GlifLibError("Unknown attributes in contour element.")
	identifier = contour.get("identifier")
	if identifier is not None:
		if identifier in identifiers:
			raise GlifLibError("The identifier %s is used more than once." % identifier)
		if not identifierValidator(identifier):
			raise GlifLibError("The contour identifier %s is not valid." % identifier)
		identifiers.add(identifier)
	try:
		pen.beginPath(identifier=identifier)
	except TypeError:
		pen.beginPath()
		warn("The beginPath method needs an identifier kwarg. The contour's identifier value has been discarded.", DeprecationWarning)
	if len(contour):
		_validateAndMassagePointStructures(contour, pointAttributesFormat2)
		_buildOutlinePointsFormat2(pen, contour, identifiers)
	pen.endPath()

def _buildOutlinePointsFormat2(pen, contour, identifiers):
	for index, element in enumerate(contour):
		x = element.attrib["x"]
		y = element.attrib["y"]
		segmentType = element.attrib["segmentType"]
		smooth = element.attrib["smooth"]
		name = element.attrib["name"]
		identifier = element.get("identifier")
		if identifier is not None:
			if identifier in identifiers:
				raise GlifLibError("The identifier %s is used more than once." % identifier)
			if not identifierValidator(identifier):
				raise GlifLibError("The identifier %s is not valid." % identifier)
			identifiers.add(identifier)
		try:
			pen.addPoint((x, y), segmentType=segmentType, smooth=smooth, name=name, identifier=identifier)
		except TypeError:
			pen.addPoint((x, y), segmentType=segmentType, smooth=smooth, name=name)
			warn("The addPoint method needs an identifier kwarg. The point's identifier value has been discarded.", DeprecationWarning)

def _buildOutlineComponentFormat2(pen, component, identifiers):
	if len(component):
		raise GlifLibError("Unknown child elements of component element.")
	if set(component.attrib.keys()) - componentAttributesFormat2:
		raise GlifLibError("Unknown attributes in component element.")
	baseGlyphName = component.get("base")
	if baseGlyphName is None:
		raise GlifLibError("The base attribute is not defined in the component.")
	transformation = []
	for attr, default in _transformationInfo:
		value = component.get(attr)
		if value is None:
			value = default
		else:
			value = _number(value)
		transformation.append(value)
	identifier = component.get("identifier")
	if identifier is not None:
		if identifier in identifiers:
			raise GlifLibError("The identifier %s is used more than once." % identifier)
		if not identifierValidator(identifier):
			raise GlifLibError("The identifier %s is not valid." % identifier)
		identifiers.add(identifier)
	try:
		pen.addComponent(baseGlyphName, tuple(transformation), identifier=identifier)
	except TypeError:
		pen.addComponent(baseGlyphName, tuple(transformation))
		warn("The addComponent method needs an identifier kwarg. The component's identifier value has been discarded.", DeprecationWarning)

# all formats

def _validateAndMassagePointStructures(contour, pointAttributes, openContourOffCurveLeniency=False):
	if not len(contour):
		return
	# store some data for later validation
	lastOnCurvePoint = None
	haveOffCurvePoint = False
	# validate and massage the individual point elements
	for index, element in enumerate(contour):
		# not <point>
		if element.tag != "point":
			raise GlifLibError("Unknown child element (%s) of contour element." % element.tag)
		# unknown attributes
		unknownAttributes = [attr for attr in list(element.attrib.keys()) if attr not in pointAttributes]
		if unknownAttributes:
			raise GlifLibError("Unknown attributes in point element.")
		# search for unknown children
		if len(element):
			raise GlifLibError("Unknown child elements in point element.")
		# x and y are required
		x = element.get("x")
		y = element.get("y")
		if x is None:
			raise GlifLibError("Required x attribute is missing in point element.")
		if y is None:
			raise GlifLibError("Required y attribute is missing in point element.")
		element.attrib["x"] = _number(x)
		element.attrib["y"] = _number(y)
		# segment type
		pointType = element.attrib.pop("type", "offcurve")
		if pointType not in pointTypeOptions:
			raise GlifLibError("Unknown point type: %s" % pointType)
		if pointType == "offcurve":
			pointType = None
		element.attrib["segmentType"] = pointType
		if pointType is None:
			haveOffCurvePoint = True
		else:
			lastOnCurvePoint = index
		# move can only occur as the first point
		if pointType == "move" and index != 0:
			raise GlifLibError("A move point occurs after the first point in the contour.")
		# smooth is optional
		smooth = element.get("smooth", "no")
		if smooth is not None:
			if smooth not in pointSmoothOptions:
				raise GlifLibError("Unknown point smooth value: %s" % smooth)
		smooth = smooth == "yes"
		element.attrib["smooth"] = smooth
		# smooth can only be applied to curve and qcurve
		if smooth and pointType is None:
			raise GlifLibError("smooth attribute set in an offcurve point.")
		# name is optional
		if "name" not in element.attrib:
			element.attrib["name"] = None
	if openContourOffCurveLeniency:
		# remove offcurves that precede a move. this is technically illegal,
		# but we let it slide because there are fonts out there in the wild like this.
		if contour[0].attrib["segmentType"] == "move":
			for element in reversed(contour):
				if element.attrib["segmentType"] is None:
					contour.remove(element)
				else:
					break
	# validate the off-curves in the segments
	if haveOffCurvePoint and lastOnCurvePoint is not None:
		# we only care about how many offCurves there are before an onCurve
		# filter out the trailing offCurves
		offCurvesCount = len(contour) - 1 - lastOnCurvePoint
		stripedContour = contour[:-offCurvesCount] if offCurvesCount else contour
		for element in stripedContour:
			segmentType = element.attrib["segmentType"]
			if segmentType is None:
				offCurvesCount += 1
			else:
				if offCurvesCount:
					# move and line can't be preceded by off-curves
					if segmentType == "move":
						# this will have been filtered out already
						raise GlifLibError("move can not have an offcurve.")
					elif segmentType == "line":
						raise GlifLibError("line can not have an offcurve.")
					elif segmentType == "curve":
						if offCurvesCount > 2:
							raise GlifLibError("Too many offcurves defined for curve.")
					elif segmentType == "qcurve":
						pass
					else:
						# unknown segment type. it'll be caught later.
						pass
				offCurvesCount = 0

# ---------------------
# Misc Helper Functions
# ---------------------

def _relaxedSetattr(object, attr, value):
	try:
		setattr(object, attr, value)
	except AttributeError:
		pass

def _number(s):
	"""
	Given a numeric string, return an integer or a float, whichever
	the string indicates. _number("1") will return the integer 1,
	_number("1.0") will return the float 1.0.

	>>> _number("1")
	1
	>>> _number("1.0")
	1.0
	>>> _number("a")  # doctest: +IGNORE_EXCEPTION_DETAIL
	Traceback (most recent call last):
	    ...
	GlifLibError: Could not convert a to an int or float.
	"""
	try:
		n = int(s)
		return n
	except ValueError:
		pass
	try:
		n = float(s)
		return n
	except ValueError:
		raise GlifLibError("Could not convert %s to an int or float." % s)

# --------------------
# Rapid Value Fetching
# --------------------

# base

class _DoneParsing(Exception): pass

class _BaseParser(object):

	def __init__(self):
		self._elementStack = []

	def parse(self, text):
		from xml.parsers.expat import ParserCreate
		parser = ParserCreate()
		parser.StartElementHandler = self.startElementHandler
		parser.EndElementHandler = self.endElementHandler
		parser.Parse(text)

	def startElementHandler(self, name, attrs):
		self._elementStack.append(name)

	def endElementHandler(self, name):
		other = self._elementStack.pop(-1)
		assert other == name


# unicodes

def _fetchUnicodes(glif):
	"""
	Get a list of unicodes listed in glif.
	"""
	parser = _FetchUnicodesParser()
	parser.parse(glif)
	return parser.unicodes

class _FetchUnicodesParser(_BaseParser):

	def __init__(self):
		self.unicodes = []
		super(_FetchUnicodesParser, self).__init__()

	def startElementHandler(self, name, attrs):
		if name == "unicode" and self._elementStack and self._elementStack[-1] == "glyph":
			value = attrs.get("hex")
			if value is not None:
				try:
					value = int(value, 16)
					if value not in self.unicodes:
						self.unicodes.append(value)
				except ValueError:
					pass
		super(_FetchUnicodesParser, self).startElementHandler(name, attrs)

# image

def _fetchImageFileName(glif):
	"""
	The image file name (if any) from glif.
	"""
	parser = _FetchImageFileNameParser()
	try:
		parser.parse(glif)
	except _DoneParsing:
		pass
	return parser.fileName

class _FetchImageFileNameParser(_BaseParser):

	def __init__(self):
		self.fileName = None
		super(_FetchImageFileNameParser, self).__init__()

	def startElementHandler(self, name, attrs):
		if name == "image" and self._elementStack and self._elementStack[-1] == "glyph":
			self.fileName = attrs.get("fileName")
			raise _DoneParsing
		super(_FetchImageFileNameParser, self).startElementHandler(name, attrs)

# component references

def _fetchComponentBases(glif):
	"""
	Get a list of component base glyphs listed in glif.
	"""
	parser = _FetchComponentBasesParser()
	try:
		parser.parse(glif)
	except _DoneParsing:
		pass
	return list(parser.bases)

class _FetchComponentBasesParser(_BaseParser):

	def __init__(self):
		self.bases = []
		super(_FetchComponentBasesParser, self).__init__()

	def startElementHandler(self, name, attrs):
		if name == "component" and self._elementStack and self._elementStack[-1] == "outline":
			base = attrs.get("base")
			if base is not None:
				self.bases.append(base)
		super(_FetchComponentBasesParser, self).startElementHandler(name, attrs)

	def endElementHandler(self, name):
		if name == "outline":
			raise _DoneParsing
		super(_FetchComponentBasesParser, self).endElementHandler(name)

# --------------
# GLIF Point Pen
# --------------

_transformationInfo = [
	# field name, default value
	("xScale",    1),
	("xyScale",   0),
	("yxScale",   0),
	("yScale",    1),
	("xOffset",   0),
	("yOffset",   0),
]

class GLIFPointPen(AbstractPointPen):

	"""
	Helper class using the PointPen protocol to write the <outline>
	part of .glif files.
	"""

	def __init__(self, xmlWriter, formatVersion=2, identifiers=None):
		if identifiers is None:
			identifiers = set()
		self.formatVersion = formatVersion
		self.identifiers = identifiers
		self.writer = xmlWriter
		self.prevOffCurveCount = 0
		self.prevPointTypes = []

	def beginPath(self, identifier=None, **kwargs):
		attrs = []
		if identifier is not None and self.formatVersion >= 2:
			if identifier in self.identifiers:
				raise GlifLibError("identifier used more than once: %s" % identifier)
			if not identifierValidator(identifier):
				raise GlifLibError("identifier not formatted properly: %s" % identifier)
			attrs.append(("identifier", identifier))
			self.identifiers.add(identifier)
		self.writer.begintag("contour", attrs)
		self.writer.newline()
		self.prevOffCurveCount = 0

	def endPath(self):
		if self.prevPointTypes and self.prevPointTypes[0] == "move":
			if self.prevPointTypes[-1] == "offcurve":
				raise GlifLibError("open contour has loose offcurve point")
		self.writer.endtag("contour")
		self.writer.newline()
		self.prevPointType = None
		self.prevOffCurveCount = 0
		self.prevPointTypes = []

	def addPoint(self, pt, segmentType=None, smooth=None, name=None, identifier=None, **kwargs):
		attrs = []
		# coordinates
		if pt is not None:
			for coord in pt:
				if not isinstance(coord, (int, float)):
					raise GlifLibError("coordinates must be int or float")
			attrs.append(("x", repr(pt[0])))
			attrs.append(("y", repr(pt[1])))
		# segment type
		if segmentType == "offcurve":
			segmentType = None
		if segmentType == "move" and self.prevPointTypes:
			raise GlifLibError("move occurs after a point has already been added to the contour.")
		if segmentType in ("move", "line") and self.prevPointTypes and self.prevPointTypes[-1] == "offcurve":
			raise GlifLibError("offcurve occurs before %s point." % segmentType)
		if segmentType == "curve" and self.prevOffCurveCount > 2:
			raise GlifLibError("too many offcurve points before curve point.")
		if segmentType is not None:
			attrs.append(("type", segmentType))
		else:
			segmentType = "offcurve"
		if segmentType == "offcurve":
			self.prevOffCurveCount += 1
		else:
			self.prevOffCurveCount = 0
		self.prevPointTypes.append(segmentType)
		# smooth
		if smooth:
			if segmentType == "offcurve":
				raise GlifLibError("can't set smooth in an offcurve point.")
			attrs.append(("smooth", "yes"))
		# name
		if name is not None:
			attrs.append(("name", name))
		# identifier
		if identifier is not None and self.formatVersion >= 2:
			if identifier in self.identifiers:
				raise GlifLibError("identifier used more than once: %s" % identifier)
			if not identifierValidator(identifier):
				raise GlifLibError("identifier not formatted properly: %s" % identifier)
			attrs.append(("identifier", identifier))
			self.identifiers.add(identifier)
		self.writer.simpletag("point", attrs)
		self.writer.newline()

	def addComponent(self, glyphName, transformation, identifier=None, **kwargs):
		attrs = [("base", glyphName)]
		for (attr, default), value in zip(_transformationInfo, transformation):
			if not isinstance(value, (int, float)):
				raise GlifLibError("transformation values must be int or float")
			if value != default:
				attrs.append((attr, repr(value)))
		if identifier is not None and self.formatVersion >= 2:
			if identifier in self.identifiers:
				raise GlifLibError("identifier used more than once: %s" % identifier)
			if not identifierValidator(identifier):
				raise GlifLibError("identifier not formatted properly: %s" % identifier)
			attrs.append(("identifier", identifier))
			self.identifiers.add(identifier)
		self.writer.simpletag("component", attrs)
		self.writer.newline()

if __name__ == "__main__":
	import doctest
	doctest.testmod()
