""""
A library for importing .ufo files and their descendants.
Refer to http://unifiedfontobject.com for the UFO specification.

The UFOReader and UFOWriter classes support versions 1 and 2
of the specification. Up and down conversion functions are also
supplied in this library. These conversion functions are only
necessary if conversion without loading the UFO data into
a set of objects is desired. These functions are:
	convertUFOFormatVersion1ToFormatVersion2
	convertUFOFormatVersion2ToFormatVersion1

Two sets that list the font info attribute names for the two
fontinfo.plist formats are available for external use. These are:
	fontInfoAttributesVersion1
	fontInfoAttributesVersion2

A set listing the fontinfo.plist attributes that were deprecated
in version 2 is available for external use:
	deprecatedFontInfoAttributesVersion2

A function, validateFontInfoVersion2ValueForAttribute, that does
some basic validation on values for a fontinfo.plist value is
available for external use.

Two value conversion functions are availble for converting
fontinfo.plist values between the possible format versions.
	convertFontInfoValueForAttributeFromVersion1ToVersion2
	convertFontInfoValueForAttributeFromVersion2ToVersion1
"""


import os
import shutil
from cStringIO import StringIO
import codecs
from copy import deepcopy
from plistlib import readPlist, writePlist
from glifLib import GlyphSet, READ_MODE, WRITE_MODE
from validators import *
from filenames import userNameToFileName
from converters import convertUFO1OrUFO2KerningToUFO3Kerning

try:
	set
except NameError:
	from sets import Set as set

__all__ = [
	"makeUFOPath"
	"UFOLibError",
	"UFOReader",
	"UFOWriter",
	"convertUFOFormatVersion1ToFormatVersion2",
	"convertUFOFormatVersion2ToFormatVersion1",
	"fontInfoAttributesVersion1",
	"fontInfoAttributesVersion2",
	"deprecatedFontInfoAttributesVersion2",
	"validateFontInfoVersion2ValueForAttribute",
	"convertFontInfoValueForAttributeFromVersion1ToVersion2",
	"convertFontInfoValueForAttributeFromVersion2ToVersion1"
]


class UFOLibError(Exception): pass


# ----------
# File Names
# ----------

DEFAULT_GLYPHS_DIRNAME = "glyphs"
DATA_DIRNAME = "data"
IMAGES_DIRNAME = "images"
METAINFO_FILENAME = "metainfo.plist"
FONTINFO_FILENAME = "fontinfo.plist"
LIB_FILENAME = "lib.plist"	
GROUPS_FILENAME = "groups.plist"
KERNING_FILENAME = "kerning.plist"
FEATURES_FILENAME = "features.fea"
LAYERCONTENTS_FILENAME = "layercontents.plist"
LAYERINFO_FILENAME = "layerinfo.plist"

DEFAULT_LAYER_NAME = "public.default"

DEFAULT_FIRST_KERNING_PREFIX = "@KERN_1_"
DEFAULT_SECOND_KERNING_PREFIX = "@KERN_2_"

supportedUFOFormatVersions = [1, 2, 3]


# ----------
# UFO Reader
# ----------

class UFOReader(object):

	"""Read the various components of the .ufo."""

	def __init__(self, path):
		if not os.path.exists(path):
			raise UFOLibError("The specified UFO doesn't exist.")
		self._path = path
		self.readMetaInfo()
		self._upConvertedKerningData = None

	# properties

	def _get_formatVersion(self):
		return self._formatVersion

	formatVersion = property(_get_formatVersion, doc="The format version of the UFO. This is determined by reading metainfo.plist during __init__.")

	# up conversion

	def _upConvertKerning(self):
		"""
		Up convert kerning, groups and font info in UFO 1 and 2.
		The data will be held internally until each bit of data
		has been retrieved. The conversion of all three must
		be done at once, so the raw data is cached and an error
		is raised if one bit of data becomes obsolete before
		it is called.
		"""
		if self._upConvertedKerningData:
			testKerning = self._readKerning()
			if testKerning != self._upConvertedKerningData["originalKerning"]:
				raise UFOLibError("The data in kerning.plist has been modified since it was converted to UFO 3 format.")
			testGroups = self._readGroups()
			if testGroups != self._upConvertedKerningData["originalGroups"]:
				raise UFOLibError("The data in groups.plist has been modified since it was converted to UFO 3 format.")
			testFontInfo = self._readInfo()
			if testFontInfo != self._upConvertedKerningData["originalFontInfo"]:
				raise UFOLibError("The data in fontinfo.plist has been modified since it was converted to UFO 3 format.")
		else:
			self._upConvertedKerningData = dict(
				kerning={},
				originalKerning=self._readKerning(),
				groups={},
				originalGroups=self._readGroups(),
				fontInfo={},
				originalFontInfo=self._readInfo()
			)
			# convert kerning and groups
			kerning, groups = convertUFO1OrUFO2KerningToUFO3Kerning(
				self._upConvertedKerningData["originalKerning"],
				deepcopy(self._upConvertedKerningData["originalGroups"]),
				firstKerningGroupPrefix=DEFAULT_FIRST_KERNING_PREFIX,
				secondKerningGroupPrefix=DEFAULT_SECOND_KERNING_PREFIX
			)
			# update the font info
			fontInfo = deepcopy(self._upConvertedKerningData["originalFontInfo"])
			fontInfo["firstKerningGroupPrefix"] = DEFAULT_FIRST_KERNING_PREFIX
			fontInfo["secondKerningGroupPrefix"] = DEFAULT_SECOND_KERNING_PREFIX
			# store
			self._upConvertedKerningData["kerning"] = kerning
			self._upConvertedKerningData["groups"] = groups
			self._upConvertedKerningData["fontInfo"] = fontInfo

	# support methods

	def _checkForFile(self, path):
		if not os.path.exists(path):
			return False
		else:
			return True

	def _readPlist(self, path):
		"""
		XXX make all readers in this object use this method.

		Read a property list. The errors that
		could be raised during the reading of
		a plist are unpredictable and/or too
		large to list, so, a blind try: except:
		is done. If an exception occurs, a
		UFOLibError will be raised.
		"""
		originalPath = path
		path = os.path.join(self._path, path)
		try:
			data = readPlist(path)
			return data
		except:
			raise UFOLibError("The file %s could not be read." % originalPath)

	def readBytesFromPath(self, path, encoding=None):
		"""
		Returns the bytes in the file at the given path.
		The path must be relative to the UFO path.
		Returns None if the file does not exist.
		An encoding may be passed if needed.
		"""
		path = os.path.join(self._path, path)
		if not self._checkForFile(path):
			return None
		f = codecs.open(path, READ_MODE, encoding=encoding)
		data = f.read()
		f.close()
		return data

	def getReadFileForPath(self, path, encoding=None):
		"""
		Returns a file (or file-like) object for the
		file at the given path. The path must be relative
		to the UFO path. Returns None if the file does not exist.
		An encoding may be passed if needed.

		Note: The caller is responsible for closing the open file.
		"""
		path = os.path.join(self._path, path)
		if not self._checkForFile(path):
			return None
		f = codecs.open(path, READ_MODE, encoding=encoding)
		return f

	# metainfo.plist

	def readMetaInfo(self):
		"""
		Read metainfo.plist. Only used for internal operations.
		"""
		path = os.path.join(self._path, METAINFO_FILENAME)
		if not self._checkForFile(path):
			raise UFOLibError("metainfo.plist is missing in %s. This file is required." % self._path)
		# should there be a blind try/except with a UFOLibError
		# raised in except here (and elsewhere)? It would be nice to
		# provide external callers with a single exception to catch.
		data = readPlist(path)
		formatVersion = data["formatVersion"]
		if formatVersion not in supportedUFOFormatVersions:
			raise UFOLibError("Unsupported UFO format (%d) in %s." % (formatVersion, self._path))
		self._formatVersion = formatVersion

	# groups.plist

	def _readGroups(self):
		path = os.path.join(self._path, GROUPS_FILENAME)
		if not self._checkForFile(path):
			return {}
		return readPlist(path)

	def readGroups(self):
		"""
		Read groups.plist. Returns a dict.
		"""
		# handle up conversion
		if self._formatVersion < 3:
			self._upConvertKerning()
			return self._upConvertedKerningData["groups"]
		# normal
		else:
			return self._readGroups()

	# fontinfo.plist

	def _readInfo(self):
		path = os.path.join(self._path, FONTINFO_FILENAME)
		if not self._checkForFile(path):
			return {}
		return readPlist(path)

	def readInfo(self, info):
		"""
		Read fontinfo.plist. It requires an object that allows
		setting attributes with names that follow the fontinfo.plist
		version 3 specification. This will write the attributes
		defined in the file into the object.
		"""
		# handle up conversion
		if self._formatVersion < 3:
			self._upConvertKerning()
			infoDict = self._upConvertedKerningData["fontInfo"]
		# normal
		else:
			infoDict = self._readInfo()
		infoDataToSet = {}
		# version 1
		if self._formatVersion == 1:
			for attr in fontInfoAttributesVersion1:
				value = infoDict.get(attr)
				if value is not None:
					infoDataToSet[attr] = value
			infoDataToSet = _convertFontInfoDataVersion1ToVersion2(infoDataToSet)
		# version 2
		elif self._formatVersion == 2:
			for attr, dataValidationDict in fontInfoAttributesVersion2ValueData.items():
				value = infoDict.get(attr)
				if value is None:
					continue
				infoDataToSet[attr] = value
		# version 3
		elif self._formatVersion == 3:
			for attr, dataValidationDict in fontInfoAttributesVersion3ValueData.items():
				value = infoDict.get(attr)
				if value is None:
					continue
				infoDataToSet[attr] = value
		# unsupported version
		else:
			raise NotImplementedError
		# validate data
		if self._formatVersion < 3:
			infoDataToSet = validateInfoVersion2Data(infoDataToSet)
		elif self._formatVersion == 3:
			infoDataToSet = validateInfoVersion3Data(infoDataToSet)
		# populate the object
		for attr, value in infoDataToSet.items():
			try:
				setattr(info, attr, value)
			except AttributeError:
				raise UFOLibError("The supplied info object does not support setting a necessary attribute (%s)." % attr)
		# set the kenring prefixes for older formats
		if self._formatVersion < 3 and self._upConvertedKerningData:
			info.firstKerningGroupPrefix = self._upConvertedKerningData["fontInfo"]["firstKerningGroupPrefix"]
			info.secondKerningGroupPrefix = self._upConvertedKerningData["fontInfo"]["secondKerningGroupPrefix"]

	# kerning.plist

	def _readKerning(self):
		path = os.path.join(self._path, KERNING_FILENAME)
		if not self._checkForFile(path):
			return {}
		return readPlist(path)

	def readKerning(self):
		"""
		Read kerning.plist. Returns a dict.
		"""
		# handle up conversion
		if self._formatVersion < 3:
			self._upConvertKerning()
			kerningNested = self._upConvertedKerningData["kerning"]
		# normal
		else:
			kerningNested = self._readKerning()
		# flatten
		kerning = {}
		for left in kerningNested:
			for right in kerningNested[left]:
				value = kerningNested[left][right]
				kerning[left, right] = value
		return kerning

	# lib.plist

	def readLib(self):
		"""
		Read lib.plist. Returns a dict.
		"""
		path = os.path.join(self._path, LIB_FILENAME)
		if not self._checkForFile(path):
			return {}
		return readPlist(path)

	# features.fea

	def readFeatures(self):
		"""
		Read features.fea. Returns a string.
		"""
		path = os.path.join(self._path, FEATURES_FILENAME)
		if not self._checkForFile(path):
			return ""
		f = open(path, READ_MODE)
		text = f.read()
		f.close()
		return text

	# glyph sets & layers

	def _readLayerContents(self):
		"""
		Rebuild the layer contents list by checking what glyphsets
		are available on disk.
		"""
		if self._formatVersion < 3:
			return [(DEFAULT_LAYER_NAME, DEFAULT_GLYPHS_DIRNAME)]
		# read the file on disk
		path = os.path.join(self._path, LAYERCONTENTS_FILENAME)
		if not os.path.exists(path):
			raise UFOLibError("layercontents.plist is missing.")
		bogusFileMessage = "layercontents.plist in not in the correct format."
		if os.path.exists(path):
			contents = self._readPlist(path)
			valid, error = layerContentsValidator(contents, self._path)
			if not valid:
				raise UFOLibError(error)
		return contents

	def getLayerNames(self):
		"""
		Get the ordered layer names from layercontents.plist.
		"""
		layerContents = self._readLayerContents()
		layerNames = [layerName for layerName, directoryName in layerContents]
		return layerNames

	def getDefaultLayerName(self):
		"""
		Get the default layer name from layercontents.plist.
		"""
		layerContents = self._readLayerContents()
		for layerName, layerDirectory in layerContents:
			if layerDirectory == DEFAULT_GLYPHS_DIRNAME:
				return layerName
		# this will already have been raised during __init__
		raise UFOLibError("The default layer is not defined in layercontents.plist.")

	def getGlyphSet(self, layerName=None):
		"""
		Return the GlyphSet associated with the
		glyphs directory mapped to layerName
		in the UFO. If layerName is not provided,
		the name retrieved with getDefaultLayerName
		will be used.
		"""
		if layerName is None:
			layerName = self.getDefaultLayerName()
		directory = None
		layerContents = self._readLayerContents()
		for storedLayerName, storedLayerDirectory in layerContents:
			if layerName == storedLayerName:
				directory = storedLayerDirectory
				break
		if directory is None:
			raise UFOLibError("No glyphs directory is mapped to \"%s\"." % layerName)
		glyphsPath = os.path.join(self._path, directory)
		return GlyphSet(glyphsPath)

	def getCharacterMapping(self):
		"""
		Return a dictionary that maps unicode values (ints) to
		lists of glyph names.
		"""
		glyphsPath = os.path.join(self._path, DEFAULT_GLYPHS_DIRNAME)
		glyphSet = GlyphSet(glyphsPath)
		allUnicodes = glyphSet.getUnicodes()
		cmap = {}
		for glyphName, unicodes in allUnicodes.iteritems():
			for code in unicodes:
				if code in cmap:
					cmap[code].append(glyphName)
				else:
					cmap[code] = [glyphName]
		return cmap

	# /data

	def getDataDirectoryListing(self, maxDepth=100):
		"""
		Returns a list of all files and directories
		in the data directory. The returned paths will
		be relative to the UFO. This will not list
		directory names, only file names. Thus, empty
		directories will be skipped.

		The maxDepth argument sets the maximum number
		of sub-directories that are allowed.
		"""
		path = os.path.join(self._path, DATA_DIRNAME)
		if not self._checkForFile(path):
			return []
		listing = self._getDirectoryListing(path, maxDepth=maxDepth)
		return listing

	def _getDirectoryListing(self, path, depth=0, maxDepth=100):
		if depth > maxDepth:
			raise UFOLibError("Maximum recusion depth reached.")
		result = []
		for fileName in os.listdir(path):
			p = os.path.join(path, fileName)
			if os.path.isdir(p):
				result += self._getDirectoryListing(p, depth=depth+1, maxDepth=maxDepth)
			else:
				p = os.path.relpath(p, self._path)
				result.append(p)
		return result


# ----------
# UFO Writer
# ----------


class UFOWriter(object):

	"""Write the various components of the .ufo."""

	def __init__(self, path, formatVersion=3, fileCreator="org.robofab.ufoLib"):
		if formatVersion not in supportedUFOFormatVersions:
			raise UFOLibError("Unsupported UFO format (%d)." % formatVersion)
		# establish some basic stuff
		self._path = path
		self._formatVersion = formatVersion
		self._fileCreator = fileCreator
		# if the file already exists, get the format version.
		# this will be needed for up and down conversion.
		previousFormatVersion = None
		if os.path.exists(path):
			p = os.path.join(path, METAINFO_FILENAME)
			if not os.path.exists(p):
				raise UFOLibError("The metainfo.plist file is not in the existing UFO.")
			metaInfo = self._readPlist(METAINFO_FILENAME)
			previousFormatVersion = metaInfo.get("formatVersion")
			try:
				previousFormatVersion = int(previousFormatVersion)
			except:
				raise UFOLibError("The existing metainfo.plist is not properly formatted.")
			if previousFormatVersion not in supportedUFOFormatVersions:
				raise UFOLibError("Unsupported UFO format (%d)." % formatVersion)
		# handle the layer contents
		self.layerContents = {}
		self.layerOrder = []
		if previousFormatVersion >= 3:
			# already exists
			self._readLayerContents()
		else:
			# previous < 3
			# imply the layer contents
			p = os.path.join(path, DEFAULT_GLYPHS_DIRNAME)
			if os.path.exists(p):
				self.layerContents = {DEFAULT_LAYER_NAME : DEFAULT_GLYPHS_DIRNAME}
				self.layerOrder = [DEFAULT_LAYER_NAME]
		# write the new metainfo
		self._writeMetaInfo()
		# handle up conversion
		# < 3 to >= 3
		if previousFormatVersion < 3 and formatVersion >= 3:
			self._writeLayerContents()
		# handle down conversion
		# >= 3 to 2
		if formatVersion < 3 and previousFormatVersion >= 3:
			# remove all glyph sets except the default
			for layerName, directoryName in self.layerContents.items():
				if directoryName != DEFAULT_GLYPHS_DIRNAME:
					self._removeFileForPath(directoryName)
			# remove layercontents.plist
			self._removeFileForPath(LAYERCONTENTS_FILENAME)
			# remove glyphs/layerinfo.plist
			p = os.path.join(DEFAULT_GLYPHS_DIRNAME, LAYERINFO_FILENAME)
			self._removeFileForPath(p)
			# remove /images
			self._removeFileForPath(IMAGES_DIRNAME)
			# remove /data
			self._removeFileForPath(DATA_DIRNAME)
		# 2 to 1
		if formatVersion < 2:
			# remove features.fea
			self._removeFileForPath(FEATURES_FILENAME)

	# properties

	def _get_formatVersion(self):
		return self._formatVersion

	formatVersion = property(_get_formatVersion, doc="The format version of the UFO. This is set into metainfo.plist during __init__.")

	def _get_fileCreator(self):
		return self._fileCreator

	fileCreator = property(_get_fileCreator, doc="The file creator of the UFO. This is set into metainfo.plist during __init__.")

	# support methods

	def _readPlist(self, path):
		"""
		Read a property list. The errors that
		could be raised during the reading of
		a plist are unpredictable and/or too
		large to list, so, a blind try: except:
		is done. If an exception occurs, a
		UFOLibError will be raised.
		"""
		originalPath = path
		path = os.path.join(self._path, path)
		try:
			data = readPlist(path)
			return data
		except:
			raise UFOLibError("The file %s could not be read." % originalPath)

	def _writePlist(self, data, path):
		"""
		Write a property list. The errors that
		could be raised during the writing of
		a plist are unpredictable and/or too
		large to list, so, a blind try: except:
		is done. If an exception occurs, a
		UFOLibError will be raised.
		"""
		originalPath = path
		path = os.path.join(self._path, path)
		try:
			data = writePlistAtomically(data, path)
		except:
			raise UFOLibError("The data for the file %s could not be written because it is not properly formatted." % originalPath)

	def _makeDirectory(self, subDirectory=None):
		path = self._path
		if subDirectory:
			path = os.path.join(self._path, subDirectory)
		if not os.path.exists(path):
			os.makedirs(path)
		return path

	def _buildDirectoryTree(self, path):
		directory, fileName = os.path.split(path)
		directoryTree = []
		while directory:
			directory, d = os.path.split(directory)
			directoryTree.append(d)
		directoryTree.reverse()
		built = ""
		for d in directoryTree:
			d = os.path.join(built, d)
			p = os.path.join(self._path, d)
			if not os.path.exists(p):
				os.mkdir(p)
			built = d

	def _removeFileForPath(self, path, raiseErrorIfMissing=False):
		originalPath = path
		path = os.path.join(self._path, path)
		if not os.path.exists(path):
			if raiseErrorIfMissing:
				raise UFOLibError("The file %s does not exist." % path)
		else:
			if os.path.isdir(path):
				shutil.rmtree(path)
			else:
				os.remove(path)
		# remove any directories that are now empty
		self._removeEmptyDirectoriesForPath(os.path.dirname(originalPath))

	def _removeEmptyDirectoriesForPath(self, directory):
		absoluteDirectory = os.path.join(self._path, directory)
		if not os.path.exists(absoluteDirectory):
			return
		if not len(os.listdir(absoluteDirectory)):
			shutil.rmtree(absoluteDirectory)
		else:
			return
		directory = os.path.dirname(directory)
		if directory:
			self._removeEmptyDirectoriesForPath(directory)

	# file system interaction

	def writeBytesToPath(self, path, bytes, encoding=None):
		"""
		Write bytes to path. If needed, the directory tree
		for the given path will be built. The path must be
		relative to the UFO. An encoding may be passed if needed.
		"""
		if self._formatVersion < 2:
			raise UFOLibError("The data directory is not allowed in UFO Format Version %d." % self.formatVersion)
		self._buildDirectoryTree(path)
		path = os.path.join(self._path, path)
		writeFileAtomically(bytes, path, encoding=encoding)

	def getFileObjectForPath(self, path, encoding=None):
		"""
		Creates a write mode file object at path. If needed,
		the directory tree for the given path will be built.
		The path must be relative to the UFO. An encoding may
		be passed if needed.

		Note: The caller is responsible for closing the open file.
		"""
		if self._formatVersion < 2:
			raise UFOLibError("The data directory is not allowed in UFO Format Version %d." % self.formatVersion)
		self._buildDirectoryTree(path)
		path = os.path.join(self._path, path)
		return codecs.open(path, WRITE_MODE, encoding=encoding)

	def removeFileForPath(self, path):
		"""
		Remove the file (or directory) at path. The path
		must be relative to the UFO. This is only allowed
		for files in the data and image directories.
		"""
		# make sure that only data or images is being changed
		d = path
		parts = []
		while d:
			d, p = os.path.split(d)
			if p:
				parts.append(p)
		if parts[-1] not in ("images", "data"):
			raise UFOLibError("Removing \"%s\" is not legal." % path)
		# remove the file
		self._removeFileForPath(path, raiseErrorIfMissing=True)

	# metainfo.plist

	def _writeMetaInfo(self):
		self._makeDirectory()
		path = os.path.join(self._path, METAINFO_FILENAME)
		metaInfo = dict(
			creator=self._fileCreator,
			formatVersion=self._formatVersion
		)
		self._writePlist(metaInfo, path)

	# groups.plist

	def writeGroups(self, groups):
		"""
		Write groups.plist. This method requires a
		dict of glyph groups as an argument.
		"""
		self._makeDirectory()
		path = os.path.join(self._path, GROUPS_FILENAME)
		groupsNew = {}
		for key, value in groups.items():
			groupsNew[key] = list(value)
		if groupsNew:
			self._writePlist(groupsNew, path)
		elif os.path.exists(path):
			os.remove(path)

	# fontinfo.plist

	def writeInfo(self, info):
		"""
		Write info.plist. This method requires an object
		that supports getting attributes that follow the
		fontinfo.plist version 2 specification. Attributes
		will be taken from the given object and written
		into the file.
		"""
		self._makeDirectory()
		path = os.path.join(self._path, FONTINFO_FILENAME)
		# gather version 3 data
		infoData = {}
		for attr in fontInfoAttributesVersion3ValueData.keys():
			if hasattr(info, attr):
				try:
					value = getattr(info, attr)
				except AttributeError:
					raise UFOLibError("The supplied info object does not support getting a necessary attribute (%s)." % attr)
				if value is None:
					continue
				infoData[attr] = value
		# down convert data if necessary and validate
		if self._formatVersion == 3:
			infoData = validateInfoVersion3Data(infoData)
		elif self._formatVersion == 2:
			infoData = _convertFontInfoDataVersion3ToVersion2(infoData)
			infoData = validateInfoVersion2Data(infoData)
		elif self._formatVersion == 1:
			infoData = _convertFontInfoDataVersion3ToVersion2(infoData)
			infoData = validateInfoVersion2Data(infoData)
			infoData = _convertFontInfoDataVersion2ToVersion1(infoData)
		# write file
		self._writePlist(infoData, path)

	# kerning.plist

	def writeKerning(self, kerning):
		"""
		Write kerning.plist. This method requires a
		dict of kerning pairs as an argument.
		"""
		self._makeDirectory()
		path = os.path.join(self._path, KERNING_FILENAME)
		kerningDict = {}
		for left, right in kerning.keys():
			value = kerning[left, right]
			if not left in kerningDict:
				kerningDict[left] = {}
			kerningDict[left][right] = value
		if kerningDict:
			self._writePlist(kerningDict, path)
		elif os.path.exists(path):
			os.remove(path)

	# lib.plist

	def writeLib(self, libDict):
		"""
		Write lib.plist. This method requires a
		lib dict as an argument.
		"""
		self._makeDirectory()
		path = os.path.join(self._path, LIB_FILENAME)
		if libDict:
			self._writePlist(libDict, path)
		elif os.path.exists(path):
			os.remove(path)

	# features.fea

	def writeFeatures(self, features):
		"""
		Write features.fea. This method requires a
		features string as an argument.
		"""
		if self._formatVersion == 1:
			raise UFOLibError("features.fea is not allowed in UFO Format Version 1.")
		self._makeDirectory()
		path = os.path.join(self._path, FEATURES_FILENAME)
		writeFileAtomically(features, path)

	# glyph sets & layers

	def _readLayerContents(self):
		"""
		Rebuild the layer contents list by checking what glyph sets
		are available on disk.
		"""
		# read the file on disk
		path = os.path.join(self._path, LAYERCONTENTS_FILENAME)
		if not os.path.exists(path):
			raise UFOLibError("layercontents.plist is missing.")
		contents = {}
		order = []
		bogusFileMessage = "layercontents.plist in not in the correct format."
		if os.path.exists(path):
			raw = self._readPlist(path)
			valid, error = layerContentsValidator(raw, self._path)
			if not valid:
				raise UFOLibError(error)
			for entry in raw:
				layerName, directoryName = entry
				contents[layerName] = directoryName
				order.append(layerName)
		self.layerContents = contents
		self.layerOrder = order

	def _writeLayerContents(self):
		self._makeDirectory()
		path = os.path.join(self._path, LAYERCONTENTS_FILENAME)
		layerContents = [(layerName, self.layerContents[layerName]) for layerName in self.layerOrder]
		self._writePlist(layerContents, path)

	def _findDirectoryForLayerName(self, layerName):
		foundDirectory = None
		for existingLayerName, directoryName in self.layerContents.items():
			if layerName is None and directoryName == DEFAULT_GLYPHS_DIRNAME:
				foundDirectory = directoryName
				break
			elif existingLayerName == layerName:
				foundDirectory = directoryName
				break
		if not foundDirectory:
			raise UFOLibError("Could not locate a glyph set directory for the layer named %s." % layerName)
		return foundDirectory

	def getGlyphSet(self, layerName=None, glyphNameToFileNameFunc=None):
		"""
		Return the GlyphSet object associated with the
		appropriate glyph directory in the .ufo.
		If layerName is None, the default glyph set
		will be used.

		This method also establishes the layer order.
		Each time this method is called, the layer for
		which it is called is placed at the top of the
		stored layer order. To ensure that the order in
		the UFO is properly stored, this method should be
		called for each layer each time the UFO is written.
		If not, any layers that are not called with this
		method will be ordered below the called layers.
		"""
		if layerName is not None and self._formatVersion < 3:
			raise UFOLibError("Layer names are not supported in UFO %d." % self._formatVersion)
		# try to find an existing directory
		foundDirectory = None
		if layerName is None:
			for existingLayerName, directory in self.layerContents.items():
				if directory == DEFAULT_GLYPHS_DIRNAME:
					foundDirectory = directory
					layerName = existingLayerName
		else:
			foundDirectory = self.layerContents.get(layerName)
		directory = foundDirectory
		# make a new directory name
		if not directory:
			# use the default if no name is given.
			# this won't cause an overwrite since the
			# default would have been found in the
			# previous search.
			if layerName is None:
				layerName = DEFAULT_LAYER_NAME
				directory = DEFAULT_GLYPHS_DIRNAME
			else:
				# not caching this could be slightly expensive,
				# but caching it will be cumbersome
				existing = [d.lower() for d in self.layerContents.values()]
				if not isinstance(layerName, unicode):
					try:
						layerName = unicode(layerName)
					except UnicodeDecodeError:
						raise UFOLibError("The specified layer name is not a Unicode string.")
				directory = userNameToFileName(layerName, existing=existing, prefix="glyphs.")
		# make the directory
		path = os.path.join(self._path, directory)
		if not os.path.exists(path):
			self._makeDirectory(subDirectory=directory)
		# store the mapping and position
		self.layerContents[layerName] = directory
		if layerName in self.layerOrder:
			self.layerOrder.remove(layerName)
		self.layerOrder.insert(0, layerName)
		# write the layer contents file
		self._writeLayerContents()
		# load the glyph set
		return GlyphSet(path, glyphNameToFileNameFunc=glyphNameToFileNameFunc)

	def renameGlyphSet(self, layerName, newLayerName):
		"""
		Rename a glyph set.

		Note: if a GlyphSet object has already been retrieved for
		layerName, it is up to the caller to inform that object that
		the directory it represents has changed.
		"""
		if layerName is not None and self._formatVersion < 3:
			raise UFOLibError("Renaming a glyph set is not allowed in UFO %d." % self._formatVersion)
		# make sure the new layer name doesn't already exist
		if newLayerName is None:
			newLayerName = DEFAULT_LAYER_NAME
		if newLayerName in self.layerContents:
			raise UFOLibError("A layer named %s already exists." % newLayerName)
		# get the paths
		oldDirectory = self._findDirectoryForLayerName(layerName)
		newDirectory = userNameToFileName(newLayerName, existing=self.layerContents.values(), prefix="glyphs.", )
		# update the internal mapping
		del self.layerContents[layerName]
		self.layerContents[newLayerName] = newDirectory
		layerOrder = []
		for otherLayerName in self.layerOrder:
			if otherLayerName == layerName:
				otherLayerName = newLayerName
			layerOrder.append(otherLayerName)
		self.layerOrder = layerOrder
		# do the file system copy
		oldDirectory = os.path.join(self._path, oldDirectory)
		newDirectory = os.path.join(self._path, newDirectory)
		shutil.move(oldDirectory, newDirectory)
		# write the layer contents file
		self._writeLayerContents()

	def deleteGlyphSet(self, layerName):
		"""
		Remove the glyph set matching layerName.
		"""
		if layerName is not None and self._formatVersion < 3:
			raise UFOLibError("Deleting a glyph set is not allowed in UFO %d." % self._formatVersion)
		foundDirectory = self._findDirectoryForLayerName(layerName)
		self._removeFileForPath(foundDirectory)
		del self.layerContents[layerName]
		self.layerOrder.remove(layerName)
		# write the layer contents file
		self._writeLayerContents()

# ----------------
# Helper Functions
# ----------------

def makeUFOPath(path):
	"""
	Return a .ufo pathname.

	>>> makeUFOPath("/directory/something.ext")
	'/directory/something.ufo'
	>>> makeUFOPath("/directory/something.another.thing.ext")
	'/directory/something.another.thing.ufo'
	"""
	dir, name = os.path.split(path)
	name = ".".join([".".join(name.split(".")[:-1]), "ufo"])
	return os.path.join(dir, name)

def writePlistAtomically(obj, path):
	"""
	Write a plist for "obj" to "path". Do this sort of atomically,
	making it harder to cause corrupt files, for example when writePlist
	encounters an error halfway during write. This also checks to see
	if text matches the text that is already in the file at path.
	If so, the file is not rewritten so that the modification date
	is preserved.
	"""
	f = StringIO()
	writePlist(obj, f)
	data = f.getvalue()
	writeFileAtomically(data, path)

def writeFileAtomically(text, path, encoding=None):
	"""
	Write text into a file at path. Do this sort of atomically
	making it harder to cause corrupt files. This also checks to see
	if text matches the text that is already in the file at path.
	If so, the file is not rewritten so that the modification date
	is preserved. An encoding may be passed if needed.
	"""
	if os.path.exists(path):
		f = codecs.open(path, READ_MODE, encoding=encoding)
		oldText = f.read()
		f.close()
		if text == oldText:
			return
		# if the text is empty, remove the existing file
		if not text:
			os.remove(path)
	if text:
		f = codecs.open(path, WRITE_MODE, encoding=encoding)
		f.write(text)
		f.close()

# ---------------------------
# Format Conversion Functions
# ---------------------------

def convertUFOFormatVersion1ToFormatVersion2(inPath, outPath=None):
	"""
	Function for converting a version format 1 UFO
	to version format 2. inPath should be a path
	to a UFO. outPath is the path where the new UFO
	should be written. If outPath is not given, the
	inPath will be used and, therefore, the UFO will
	be converted in place. Otherwise, if outPath is
	specified, nothing must exist at that path.
	"""
	if outPath is None:
		outPath = inPath
	if inPath != outPath and os.path.exists(outPath):
		raise UFOLibError("A file already exists at %s." % outPath)
	# use a reader for loading most of the data
	reader = UFOReader(inPath)
	if reader.formatVersion == 2:
		raise UFOLibError("The UFO at %s is already format version 2." % inPath)
	groups = reader.readGroups()
	kerning = reader.readKerning()
	libData = reader.readLib()
	# read the info data manually and convert
	infoPath = os.path.join(inPath, FONTINFO_FILENAME)
	if not os.path.exists(infoPath):
		infoData = {}
	else:
		infoData = readPlist(infoPath)
	infoData = _convertFontInfoDataVersion1ToVersion2(infoData)
	# if the paths are the same, only need to change the
	# fontinfo and meta info files.
	infoPath = os.path.join(outPath, FONTINFO_FILENAME)
	if inPath == outPath:
		metaInfoPath = os.path.join(inPath, METAINFO_FILENAME)
		metaInfo = dict(
			creator="org.robofab.ufoLib",
			formatVersion=2
		)
		writePlistAtomically(metaInfo, metaInfoPath)
		writePlistAtomically(infoData, infoPath)
	# otherwise write everything.
	else:
		writer = UFOWriter(outPath, formatVersion=2)
		writer.writeGroups(groups)
		writer.writeKerning(kerning)
		writer.writeLib(libData)
		# write the info manually
		writePlistAtomically(infoData, infoPath)
		# copy the glyph tree
		inGlyphs = os.path.join(inPath, DEFAULT_GLYPHS_DIRNAME)
		outGlyphs = os.path.join(outPath, DEFAULT_GLYPHS_DIRNAME)
		if os.path.exists(inGlyphs):
			shutil.copytree(inGlyphs, outGlyphs)

def convertUFOFormatVersion2ToFormatVersion1(inPath, outPath=None):
	"""
	Function for converting a version format 2 UFO
	to version format 1. inPath should be a path
	to a UFO. outPath is the path where the new UFO
	should be written. If outPath is not given, the
	inPath will be used and, therefore, the UFO will
	be converted in place. Otherwise, if outPath is
	specified, nothing must exist at that path.
	"""
	if outPath is None:
		outPath = inPath
	if inPath != outPath and os.path.exists(outPath):
		raise UFOLibError("A file already exists at %s." % outPath)
	# use a reader for loading most of the data
	reader = UFOReader(inPath)
	if reader.formatVersion == 1:
		raise UFOLibError("The UFO at %s is already format version 1." % inPath)
	groups = reader.readGroups()
	kerning = reader.readKerning()
	libData = reader.readLib()
	# read the info data manually and convert
	infoPath = os.path.join(inPath, FONTINFO_FILENAME)
	if not os.path.exists(infoPath):
		infoData = {}
	else:
		infoData = readPlist(infoPath)
	infoData = _convertFontInfoDataVersion2ToVersion1(infoData)
	# if the paths are the same, only need to change the
	# fontinfo, metainfo and feature files.
	infoPath = os.path.join(outPath, FONTINFO_FILENAME)
	if inPath == outPath:
		metaInfoPath = os.path.join(inPath, METAINFO_FILENAME)
		metaInfo = dict(
			creator="org.robofab.ufoLib",
			formatVersion=1
		)
		writePlistAtomically(metaInfo, metaInfoPath)
		writePlistAtomically(infoData, infoPath)
		featuresPath = os.path.join(inPath, FEATURES_FILENAME)
		if os.path.exists(featuresPath):
			os.remove(featuresPath)
	# otherwise write everything.
	else:
		writer = UFOWriter(outPath, formatVersion=1)
		writer.writeGroups(groups)
		writer.writeKerning(kerning)
		writer.writeLib(libData)
		# write the info manually
		writePlistAtomically(infoData, infoPath)
		# copy the glyph tree
		inGlyphs = os.path.join(inPath, DEFAULT_GLYPHS_DIRNAME)
		outGlyphs = os.path.join(outPath, DEFAULT_GLYPHS_DIRNAME)
		if os.path.exists(inGlyphs):
			shutil.copytree(inGlyphs, outGlyphs)

# ----------------------
# fontinfo.plist Support
# ----------------------

# Version Validators

# There is no version 1 validator and there shouldn't be.
# The version 1 spec was very loose and there were numerous
# cases of invalid values.

def validateFontInfoVersion2ValueForAttribute(attr, value):
	"""
	This performs very basic validation of the value for attribute
	following the UFO 2 fontinfo.plist specification. The results
	of this should not be interpretted as *correct* for the font
	that they are part of. This merely indicates that the value
	is of the proper type and, where the specification defines
	a set range of possible values for an attribute, that the
	value is in the accepted range.
	"""
	dataValidationDict = fontInfoAttributesVersion2ValueData[attr]
	valueType = dataValidationDict.get("type")
	validator = dataValidationDict.get("valueValidator")
	valueOptions = dataValidationDict.get("valueOptions")
	# have specific options for the validator
	if valueOptions is not None:
		isValidValue = validator(value, valueOptions)
	# no specific options
	else:
		if validator == fontInfoTypeValidator:
			isValidValue = validator(value, valueType)
		else:
			isValidValue = validator(value)
	return isValidValue

def validateInfoVersion2Data(infoData):
	"""
	This performs very basic validation of the value for infoData
	following the UFO 2 fontinfo.plist specification. The results
	of this should not be interpretted as *correct* for the font
	that they are part of. This merely indicates that the values
	are of the proper type and, where the specification defines
	a set range of possible values for an attribute, that the
	value is in the accepted range.
	"""
	validInfoData = {}
	for attr, value in infoData.items():
		isValidValue = validateFontInfoVersion2ValueForAttribute(attr, value)
		if not isValidValue:
			raise UFOLibError("Invalid value for attribute %s (%s)." % (attr, repr(value)))
		else:
			validInfoData[attr] = value
	return infoData

def validateFontInfoVersion3ValueForAttribute(attr, value):
	"""
	This performs very basic validation of the value for attribute
	following the UFO 3 fontinfo.plist specification. The results
	of this should not be interpretted as *correct* for the font
	that they are part of. This merely indicates that the value
	is of the proper type and, where the specification defines
	a set range of possible values for an attribute, that the
	value is in the accepted range.
	"""
	dataValidationDict = fontInfoAttributesVersion3ValueData[attr]
	valueType = dataValidationDict.get("type")
	validator = dataValidationDict.get("valueValidator")
	valueOptions = dataValidationDict.get("valueOptions")
	# have specific options for the validator
	if valueOptions is not None:
		isValidValue = validator(value, valueOptions)
	# no specific options
	else:
		if validator == fontInfoTypeValidator:
			isValidValue = validator(value, valueType)
		else:
			isValidValue = validator(value)
	return isValidValue

def validateInfoVersion3Data(infoData):
	"""
	This performs very basic validation of the value for infoData
	following the UFO 3 fontinfo.plist specification. The results
	of this should not be interpretted as *correct* for the font
	that they are part of. This merely indicates that the values
	are of the proper type and, where the specification defines
	a set range of possible values for an attribute, that the
	value is in the accepted range.
	"""
	validInfoData = {}
	for attr, value in infoData.items():
		isValidValue = validateFontInfoVersion3ValueForAttribute(attr, value)
		if not isValidValue:
			raise UFOLibError("Invalid value for attribute %s (%s)." % (attr, repr(value)))
		else:
			validInfoData[attr] = value
	# handle the kerning prefixes specially
	if not fontInfoKerningPrefixesValidator(infoData):
		raise UFOLibError("Invalid kerning prefixes.")
	return infoData

# Value Options

fontInfoOpenTypeHeadFlagsOptions = range(0, 14)
fontInfoOpenTypeOS2SelectionOptions = [1, 2, 3, 4]
fontInfoOpenTypeOS2UnicodeRangesOptions = range(0, 128)
fontInfoOpenTypeOS2CodePageRangesOptions = range(0, 64)
fontInfoOpenTypeOS2TypeOptions = [0, 1, 2, 3, 8, 9]

# Version Attribute Definitions
# This defines the attributes, types and, in some
# cases the possible values, that can exist is
# fontinfo.plist.

fontInfoAttributesVersion1 = set([
	"familyName",
	"styleName",
	"fullName",
	"fontName",
	"menuName",
	"fontStyle",
	"note",
	"versionMajor",
	"versionMinor",
	"year",
	"copyright",
	"notice",
	"trademark",
	"license",
	"licenseURL",
	"createdBy",
	"designer",
	"designerURL",
	"vendorURL",
	"unitsPerEm",
	"ascender",
	"descender",
	"capHeight",
	"xHeight",
	"defaultWidth",
	"slantAngle",
	"italicAngle",
	"widthName",
	"weightName",
	"weightValue",
	"fondName",
	"otFamilyName",
	"otStyleName",
	"otMacName",
	"msCharSet",
	"fondID",
	"uniqueID",
	"ttVendor",
	"ttUniqueID",
	"ttVersion",
])

fontInfoAttributesVersion2ValueData = {
	"familyName"							: dict(type=basestring),
	"styleName"								: dict(type=basestring),
	"styleMapFamilyName"					: dict(type=basestring),
	"styleMapStyleName"						: dict(type=basestring, valueValidator=fontInfoStyleMapStyleNameValidator),
	"versionMajor"							: dict(type=int),
	"versionMinor"							: dict(type=int),
	"year"									: dict(type=int),
	"copyright"								: dict(type=basestring),
	"trademark"								: dict(type=basestring),
	"unitsPerEm"							: dict(type=(int, float)),
	"descender"								: dict(type=(int, float)),
	"xHeight"								: dict(type=(int, float)),
	"capHeight"								: dict(type=(int, float)),
	"ascender"								: dict(type=(int, float)),
	"italicAngle"							: dict(type=(float, int)),
	"note"									: dict(type=basestring),
	"openTypeHeadCreated"					: dict(type=basestring, valueValidator=fontInfoOpenTypeHeadCreatedValidator),
	"openTypeHeadLowestRecPPEM"				: dict(type=(int, float)),
	"openTypeHeadFlags"						: dict(type="integerList", valueValidator=fontInfoIntListValidator, valueOptions=fontInfoOpenTypeHeadFlagsOptions),
	"openTypeHheaAscender"					: dict(type=(int, float)),
	"openTypeHheaDescender"					: dict(type=(int, float)),
	"openTypeHheaLineGap"					: dict(type=(int, float)),
	"openTypeHheaCaretSlopeRise"			: dict(type=int),
	"openTypeHheaCaretSlopeRun"				: dict(type=int),
	"openTypeHheaCaretOffset"				: dict(type=(int, float)),
	"openTypeNameDesigner"					: dict(type=basestring),
	"openTypeNameDesignerURL"				: dict(type=basestring),
	"openTypeNameManufacturer"				: dict(type=basestring),
	"openTypeNameManufacturerURL"			: dict(type=basestring),
	"openTypeNameLicense"					: dict(type=basestring),
	"openTypeNameLicenseURL"				: dict(type=basestring),
	"openTypeNameVersion"					: dict(type=basestring),
	"openTypeNameUniqueID"					: dict(type=basestring),
	"openTypeNameDescription"				: dict(type=basestring),
	"openTypeNamePreferredFamilyName"		: dict(type=basestring),
	"openTypeNamePreferredSubfamilyName"	: dict(type=basestring),
	"openTypeNameCompatibleFullName"		: dict(type=basestring),
	"openTypeNameSampleText"				: dict(type=basestring),
	"openTypeNameWWSFamilyName"				: dict(type=basestring),
	"openTypeNameWWSSubfamilyName"			: dict(type=basestring),
	"openTypeOS2WidthClass"					: dict(type=int, valueValidator=fontInfoOpenTypeOS2WidthClassValidator),
	"openTypeOS2WeightClass"				: dict(type=int, valueValidator=fontInfoOpenTypeOS2WeightClassValidator),
	"openTypeOS2Selection"					: dict(type="integerList", valueValidator=fontInfoIntListValidator, valueOptions=fontInfoOpenTypeOS2SelectionOptions),
	"openTypeOS2VendorID"					: dict(type=basestring),
	"openTypeOS2Panose"						: dict(type="integerList", valueValidator=fontInfoVersion2OpenTypeOS2PanoseValidator),
	"openTypeOS2FamilyClass"				: dict(type="integerList", valueValidator=fontInfoOpenTypeOS2FamilyClassValidator),
	"openTypeOS2UnicodeRanges"				: dict(type="integerList", valueValidator=fontInfoIntListValidator, valueOptions=fontInfoOpenTypeOS2UnicodeRangesOptions),
	"openTypeOS2CodePageRanges"				: dict(type="integerList", valueValidator=fontInfoIntListValidator, valueOptions=fontInfoOpenTypeOS2CodePageRangesOptions),
	"openTypeOS2TypoAscender"				: dict(type=(int, float)),
	"openTypeOS2TypoDescender"				: dict(type=(int, float)),
	"openTypeOS2TypoLineGap"				: dict(type=(int, float)),
	"openTypeOS2WinAscent"					: dict(type=(int, float)),
	"openTypeOS2WinDescent"					: dict(type=(int, float)),
	"openTypeOS2Type"						: dict(type="integerList", valueValidator=fontInfoIntListValidator, valueOptions=fontInfoOpenTypeOS2TypeOptions),
	"openTypeOS2SubscriptXSize"				: dict(type=(int, float)),
	"openTypeOS2SubscriptYSize"				: dict(type=(int, float)),
	"openTypeOS2SubscriptXOffset"			: dict(type=(int, float)),
	"openTypeOS2SubscriptYOffset"			: dict(type=(int, float)),
	"openTypeOS2SuperscriptXSize"			: dict(type=(int, float)),
	"openTypeOS2SuperscriptYSize"			: dict(type=(int, float)),
	"openTypeOS2SuperscriptXOffset"			: dict(type=(int, float)),
	"openTypeOS2SuperscriptYOffset"			: dict(type=(int, float)),
	"openTypeOS2StrikeoutSize"				: dict(type=(int, float)),
	"openTypeOS2StrikeoutPosition"			: dict(type=(int, float)),
	"openTypeVheaVertTypoAscender"			: dict(type=(int, float)),
	"openTypeVheaVertTypoDescender"			: dict(type=(int, float)),
	"openTypeVheaVertTypoLineGap"			: dict(type=(int, float)),
	"openTypeVheaCaretSlopeRise"			: dict(type=int),
	"openTypeVheaCaretSlopeRun"				: dict(type=int),
	"openTypeVheaCaretOffset"				: dict(type=(int, float)),
	"postscriptFontName"					: dict(type=basestring),
	"postscriptFullName"					: dict(type=basestring),
	"postscriptSlantAngle"					: dict(type=(float, int)),
	"postscriptUniqueID"					: dict(type=int),
	"postscriptUnderlineThickness"			: dict(type=(int, float)),
	"postscriptUnderlinePosition"			: dict(type=(int, float)),
	"postscriptIsFixedPitch"				: dict(type=bool),
	"postscriptBlueValues"					: dict(type="integerList", valueValidator=fontInfoPostscriptBluesValidator),
	"postscriptOtherBlues"					: dict(type="integerList", valueValidator=fontInfoPostscriptOtherBluesValidator),
	"postscriptFamilyBlues"					: dict(type="integerList", valueValidator=fontInfoPostscriptBluesValidator),
	"postscriptFamilyOtherBlues"			: dict(type="integerList", valueValidator=fontInfoPostscriptOtherBluesValidator),
	"postscriptStemSnapH"					: dict(type="integerList", valueValidator=fontInfoPostscriptStemsValidator),
	"postscriptStemSnapV"					: dict(type="integerList", valueValidator=fontInfoPostscriptStemsValidator),
	"postscriptBlueFuzz"					: dict(type=(int, float)),
	"postscriptBlueShift"					: dict(type=(int, float)),
	"postscriptBlueScale"					: dict(type=(float, int)),
	"postscriptForceBold"					: dict(type=bool),
	"postscriptDefaultWidthX"				: dict(type=(int, float)),
	"postscriptNominalWidthX"				: dict(type=(int, float)),
	"postscriptWeightName"					: dict(type=basestring),
	"postscriptDefaultCharacter"			: dict(type=basestring),
	"postscriptWindowsCharacterSet"			: dict(type=int, valueValidator=fontInfoPostscriptWindowsCharacterSetValidator),
	"macintoshFONDFamilyID"					: dict(type=int),
	"macintoshFONDName"						: dict(type=basestring),
}
fontInfoAttributesVersion2 = set(fontInfoAttributesVersion2ValueData.keys())

fontInfoAttributesVersion3ValueData = deepcopy(fontInfoAttributesVersion2ValueData)
fontInfoAttributesVersion3ValueData.update({
	"versionMinor"							: dict(type=int, valueValidator=fontInfoNonNegativeIntValidator),
	"unitsPerEm"							: dict(type=(int, float), valueValidator=fontInfoNonNegativeNumberValidator),
	"openTypeHeadLowestRecPPEM"				: dict(type=(int, float), valueValidator=fontInfoNonNegativeNumberValidator),
	"openTypeOS2Panose"						: dict(type="integerList", valueValidator=fontInfoVersion3OpenTypeOS2PanoseValidator),
	"openTypeOS2WinAscent"					: dict(type=(int, float), valueValidator=fontInfoNonNegativeNumberValidator),
	"openTypeOS2WinDescent"					: dict(type=(int, float), valueValidator=fontInfoNonNegativeNumberValidator),
	"openTypeGaspRangeRecords"				: dict(type="dictList", valueValidator=fontInfoOpenTypeGaspRangeRecordsValidator),
	"openTypeNameRecords"					: dict(type="dictList", valueValidator=fontInfoOpenTypeNameRecordsValidator),
	"woffMajorVersion"						: dict(type=int, valueValidator=fontInfoNonNegativeIntValidator),
	"woffMinorVersion"						: dict(type=int, valueValidator=fontInfoNonNegativeIntValidator),
	"woffMetadataUniqueID"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataUniqueIDValidator),
	"woffMetadataVendor"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataVendorValidator),
	"woffMetadataCredits"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataCreditsValidator),
	"woffMetadataDescription"				: dict(type=dict, valueValidator=fontInfoWOFFMetadataDescriptionValidator),
	"woffMetadataLicense"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataLicenseValidator),
	"woffMetadataCopyright"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataCopyrightValidator),
	"woffMetadataTrademark"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataTrademarkValidator),
	"woffMetadataLicensee"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataLicenseeValidator),
	"woffMetadataExtensions"				: dict(type=list, valueValidator=fontInfoWOFFMetadataExtensionsValidator),
	"firstKerningGroupPrefix" 				: dict(type=basestring, valueValidator=fontInfoKerningPrefixValidator),
	"secondKerningGroupPrefix" 				: dict(type=basestring, valueValidator=fontInfoKerningPrefixValidator),
	"guidelines"							: dict(type=list, valueValidator=fontInfoGuidelinesValidator)
})

# insert the type validator for all attrs that
# have no defined validator.
for attr, dataDict in fontInfoAttributesVersion2ValueData.items():
	if "valueValidator" not in dataDict:
		dataDict["valueValidator"] = fontInfoTypeValidator

for attr, dataDict in fontInfoAttributesVersion3ValueData.items():
	if "valueValidator" not in dataDict:
		dataDict["valueValidator"] = fontInfoTypeValidator

# Version Conversion Support
# These are used from converting from version 1
# to version 2 or vice-versa.

def _flipDict(d):
	flipped = {}
	for key, value in d.items():
		flipped[value] = key
	return flipped

fontInfoAttributesVersion1To2 = {
	"menuName"		: "styleMapFamilyName",
	"designer"		: "openTypeNameDesigner",
	"designerURL"	: "openTypeNameDesignerURL",
	"createdBy"		: "openTypeNameManufacturer",
	"vendorURL"		: "openTypeNameManufacturerURL",
	"license"		: "openTypeNameLicense",
	"licenseURL"	: "openTypeNameLicenseURL",
	"ttVersion"		: "openTypeNameVersion",
	"ttUniqueID"	: "openTypeNameUniqueID",
	"notice"		: "openTypeNameDescription",
	"otFamilyName"	: "openTypeNamePreferredFamilyName",
	"otStyleName"	: "openTypeNamePreferredSubfamilyName",
	"otMacName"		: "openTypeNameCompatibleFullName",
	"weightName"	: "postscriptWeightName",
	"weightValue"	: "openTypeOS2WeightClass",
	"ttVendor"		: "openTypeOS2VendorID",
	"uniqueID"		: "postscriptUniqueID",
	"fontName"		: "postscriptFontName",
	"fondID"		: "macintoshFONDFamilyID",
	"fondName"		: "macintoshFONDName",
	"defaultWidth"	: "postscriptDefaultWidthX",
	"slantAngle"	: "postscriptSlantAngle",
	"fullName"		: "postscriptFullName",
	# require special value conversion
	"fontStyle"		: "styleMapStyleName",
	"widthName"		: "openTypeOS2WidthClass",
	"msCharSet"		: "postscriptWindowsCharacterSet"
}
fontInfoAttributesVersion2To1 = _flipDict(fontInfoAttributesVersion1To2)
deprecatedFontInfoAttributesVersion2 = set(fontInfoAttributesVersion1To2.keys())

_fontStyle1To2 = {
	64 : "regular",
	1  : "italic",
	32 : "bold",
	33 : "bold italic"
}
_fontStyle2To1 = _flipDict(_fontStyle1To2)
# Some UFO 1 files have 0
_fontStyle1To2[0] = "regular"

_widthName1To2 = {
	"Ultra-condensed" : 1,
	"Extra-condensed" : 2,
	"Condensed"		  : 3,
	"Semi-condensed"  : 4,
	"Medium (normal)" : 5,
	"Semi-expanded"	  : 6,
	"Expanded"		  : 7,
	"Extra-expanded"  : 8,
	"Ultra-expanded"  : 9
}
_widthName2To1 = _flipDict(_widthName1To2)
# FontLab's default width value is "Normal".
# Many format version 1 UFOs will have this.
_widthName1To2["Normal"] = 5
# FontLab has an "All" width value. In UFO 1
# move this up to "Normal".
_widthName1To2["All"] = 5
# "medium" appears in a lot of UFO 1 files.
_widthName1To2["medium"] = 5
# "Medium" appears in a lot of UFO 1 files.
_widthName1To2["Medium"] = 5

_msCharSet1To2 = {
	0	: 1,
	1	: 2,
	2	: 3,
	77	: 4,
	128 : 5,
	129 : 6,
	130 : 7,
	134 : 8,
	136 : 9,
	161 : 10,
	162 : 11,
	163 : 12,
	177 : 13,
	178 : 14,
	186 : 15,
	200 : 16,
	204 : 17,
	222 : 18,
	238 : 19,
	255 : 20
}
_msCharSet2To1 = _flipDict(_msCharSet1To2)

def convertFontInfoValueForAttributeFromVersion1ToVersion2(attr, value):
	"""
	Convert value from version 1 to version 2 format.
	Returns the new attribute name and the converted value.
	If the value is None, None will be returned for the new value.
	"""
	# convert floats to ints if possible
	if isinstance(value, float):
		if int(value) == value:
			value = int(value)
	if value is not None:
		if attr == "fontStyle":
			v = _fontStyle1To2.get(value)
			if v is None:
				raise UFOLibError("Cannot convert value (%s) for attribute %s." % (repr(value), attr))
			value = v
		elif attr == "widthName":
			v = _widthName1To2.get(value)
			if v is None:
				raise UFOLibError("Cannot convert value (%s) for attribute %s." % (repr(value), attr))
			value = v
		elif attr == "msCharSet":
			v = _msCharSet1To2.get(value)
			if v is None:
				raise UFOLibError("Cannot convert value (%s) for attribute %s." % (repr(value), attr))
			value = v
	attr = fontInfoAttributesVersion1To2.get(attr, attr)
	return attr, value

def convertFontInfoValueForAttributeFromVersion2ToVersion1(attr, value):
	"""
	Convert value from version 2 to version 1 format.
	Returns the new attribute name and the converted value.
	If the value is None, None will be returned for the new value.
	"""
	if value is not None:
		if attr == "styleMapStyleName":
			value = _fontStyle2To1.get(value)
		elif attr == "openTypeOS2WidthClass":
			value = _widthName2To1.get(value)
		elif attr == "postscriptWindowsCharacterSet":
			value = _msCharSet2To1.get(value)
	attr = fontInfoAttributesVersion2To1.get(attr, attr)
	return attr, value

def _convertFontInfoDataVersion1ToVersion2(data):
	converted = {}
	for attr, value in data.items():
		# FontLab gives -1 for the weightValue
		# for fonts wil no defined value. Many
		# format version 1 UFOs will have this.
		if attr == "weightValue" and value == -1:
			continue
		newAttr, newValue = convertFontInfoValueForAttributeFromVersion1ToVersion2(attr, value)
		# skip if the attribute is not part of version 2
		if newAttr not in fontInfoAttributesVersion2:
			continue
		# catch values that can't be converted
		if value is None:
			raise UFOLibError("Cannot convert value (%s) for attribute %s." % (repr(value), newAttr))
		# store
		converted[newAttr] = newValue
	return converted

def _convertFontInfoDataVersion2ToVersion1(data):
	converted = {}
	for attr, value in data.items():
		newAttr, newValue = convertFontInfoValueForAttributeFromVersion2ToVersion1(attr, value)
		# only take attributes that are registered for version 1
		if newAttr not in fontInfoAttributesVersion1:
			continue
		# catch values that can't be converted
		if value is None:
			raise UFOLibError("Cannot convert value (%s) for attribute %s." % (repr(value), newAttr))
		# store
		converted[newAttr] = newValue
	return converted

def _convertFontInfoDataVersion3ToVersion2(data):
	converted = {}
	for attr, value in data.items():
		# only take attributes that are registered for version 2
		if attr not in fontInfoAttributesVersion2:
			continue
		# store
		converted[attr] = value
	return converted

if __name__ == "__main__":
	import doctest
	doctest.testmod()
