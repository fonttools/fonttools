from __future__ import absolute_import, unicode_literals
import os
import shutil
from io import StringIO, BytesIO, open
from copy import deepcopy
from fontTools.misc.py23 import basestring, unicode, tounicode
from ufoLib.filesystem import FileSystem
from ufoLib.glifLib import GlyphSet
from ufoLib.validators import *
from ufoLib.filenames import userNameToFileName
from ufoLib.converters import convertUFO1OrUFO2KerningToUFO3Kerning
from ufoLib.errors import UFOLibError

"""
A library for importing .ufo files and their descendants.
Refer to http://unifiedfontobject.com for the UFO specification.

The UFOReader and UFOWriter classes support versions 1, 2 and 3
of the specification.

Sets that list the font info attribute names for the fontinfo.plist
formats are available for external use. These are:
	fontInfoAttributesVersion1
	fontInfoAttributesVersion2
	fontInfoAttributesVersion3

A set listing the fontinfo.plist attributes that were deprecated
in version 2 is available for external use:
	deprecatedFontInfoAttributesVersion2

Functions that do basic validation on values for fontinfo.plist
are available for external use. These are
	validateFontInfoVersion2ValueForAttribute
	validateFontInfoVersion3ValueForAttribute

Value conversion functions are available for converting
fontinfo.plist values between the possible format versions.
	convertFontInfoValueForAttributeFromVersion1ToVersion2
	convertFontInfoValueForAttributeFromVersion2ToVersion1
	convertFontInfoValueForAttributeFromVersion2ToVersion3
	convertFontInfoValueForAttributeFromVersion3ToVersion2
"""

__all__ = [
	"makeUFOPath",
	"UFOLibError",
	"UFOReader",
	"UFOWriter",
	"fontInfoAttributesVersion1",
	"fontInfoAttributesVersion2",
	"fontInfoAttributesVersion3",
	"deprecatedFontInfoAttributesVersion2",
	"validateFontInfoVersion2ValueForAttribute",
	"validateFontInfoVersion3ValueForAttribute",
	"convertFontInfoValueForAttributeFromVersion1ToVersion2",
	"convertFontInfoValueForAttributeFromVersion2ToVersion1"
]

__version__ = "2.3.2"





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

supportedUFOFormatVersions = [1, 2, 3]


# ----------
# UFO Reader
# ----------

class UFOReader(object):

	"""
	Read the various components of the .ufo.

	By default read data is validated. Set ``validate`` to
	``False`` to not validate the data.
	"""

	def __init__(self, path, validate=True):
		self.fileSystem = FileSystem(path)
		self._path = path
		self._validate = validate
		self.readMetaInfo(validate=validate)
		self._upConvertedKerningData = None

	# properties

	def _get_formatVersion(self):
		return self._formatVersion

	formatVersion = property(_get_formatVersion, doc="The format version of the UFO. This is determined by reading metainfo.plist during __init__.")

	def readBytesFromPath(self, path, encoding=None):
		"""
		Returns the bytes in the file at the given path.
		The path must be relative to the UFO path.
		Returns None if the file does not exist.
		An encoding may be passed if needed.
		"""
		return self.fileSystem.readBytesFromPath(path, encoding=encoding)

	def getReadFileForPath(self, path, encoding=None):
		"""
		Returns a file (or file-like) object for the
		file at the given path. The path must be relative
		to the UFO path. Returns None if the file does
		not exist An encoding may be passed if needed.

		Note: The caller is responsible for closing the open file.
		"""
		return self.fileSystem.open(path, mode="rb", encoding=encoding)

	# up conversion

	def _upConvertKerning(self, validate):
		"""
		Up convert kerning and groups in UFO 1 and 2.
		The data will be held internally until each bit of data
		has been retrieved. The conversion of both must be done
		at once, so the raw data is cached and an error is raised
		if one bit of data becomes obsolete before it is called.

		``validate`` will validate the data.
		"""
		if self._upConvertedKerningData:
			testKerning = self._readKerning()
			if testKerning != self._upConvertedKerningData["originalKerning"]:
				raise UFOLibError("The data in kerning.plist has been modified since it was converted to UFO 3 format.")
			testGroups = self._readGroups()
			if testGroups != self._upConvertedKerningData["originalGroups"]:
				raise UFOLibError("The data in groups.plist has been modified since it was converted to UFO 3 format.")
		else:
			groups = self._readGroups()
			if validate:
				invalidFormatMessage = "groups.plist is not properly formatted."
				if not isinstance(groups, dict):
					raise UFOLibError(invalidFormatMessage)
				for groupName, glyphList in groups.items():
					if not isinstance(groupName, basestring):
						raise UFOLibError(invalidFormatMessage)
					elif not isinstance(glyphList, list):
						raise UFOLibError(invalidFormatMessage)
					for glyphName in glyphList:
						if not isinstance(glyphName, basestring):
							raise UFOLibError(invalidFormatMessage)
			self._upConvertedKerningData = dict(
				kerning={},
				originalKerning=self._readKerning(),
				groups={},
				originalGroups=groups
			)
			# convert kerning and groups
			kerning, groups, conversionMaps = convertUFO1OrUFO2KerningToUFO3Kerning(
				self._upConvertedKerningData["originalKerning"],
				deepcopy(self._upConvertedKerningData["originalGroups"])
			)
			# store
			self._upConvertedKerningData["kerning"] = kerning
			self._upConvertedKerningData["groups"] = groups
			self._upConvertedKerningData["groupRenameMaps"] = conversionMaps

	# support methods

	def getFileModificationTime(self, path):
		return self.fileSystem.getFileModificationTime(path)

	# metainfo.plist

	def readMetaInfo(self, validate=None):
		"""
		Read metainfo.plist. Only used for internal operations.

		``validate`` will validate the read data, by default it is set
		to the class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		data = self.fileSystem.readPlist(METAINFO_FILENAME)
		if validate and not isinstance(data, dict):
			raise UFOLibError("metainfo.plist is not properly formatted.")
		formatVersion = data["formatVersion"]
		if validate:
			if not isinstance(formatVersion, int):
				metaplist_path = os.path.join(self._path, METAINFO_FILENAME)
				raise UFOLibError("formatVersion must be specified as an integer in " + metaplist_path)
			if formatVersion not in supportedUFOFormatVersions:
				raise UFOLibError("Unsupported UFO format (%d) in %s." % (formatVersion, self._path))
		self._formatVersion = formatVersion

	# groups.plist

	def _readGroups(self):
		return self.fileSystem.readPlist(GROUPS_FILENAME, {})

	def readGroups(self, validate=None):
		"""
		Read groups.plist. Returns a dict.
		``validate`` will validate the read data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		# handle up conversion
		if self._formatVersion < 3:
			self._upConvertKerning(validate)
			groups = self._upConvertedKerningData["groups"]
		# normal
		else:
			groups = self._readGroups()
		if validate:
			valid, message = groupsValidator(groups)
			if not valid:
				raise UFOLibError(message)
		return groups

	def getKerningGroupConversionRenameMaps(self, validate=None):
		"""
		Get maps defining the renaming that was done during any
		needed kerning group conversion. This method returns a
		dictionary of this form:

			{
				"side1" : {"old group name" : "new group name"},
				"side2" : {"old group name" : "new group name"}
			}

		When no conversion has been performed, the side1 and side2
		dictionaries will be empty.

		``validate`` will validate the groups, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		if self._formatVersion >= 3:
			return dict(side1={}, side2={})
		# use the public group reader to force the load and
		# conversion of the data if it hasn't happened yet.
		self.readGroups(validate=validate)
		return self._upConvertedKerningData["groupRenameMaps"]

	# fontinfo.plist

	def _readInfo(self, validate):
		data = self.fileSystem.readPlist(FONTINFO_FILENAME, {})
		if validate and not isinstance(data, dict):
			raise UFOLibError("fontinfo.plist is not properly formatted.")
		return data

	def readInfo(self, info, validate=None):
		"""
		Read fontinfo.plist. It requires an object that allows
		setting attributes with names that follow the fontinfo.plist
		version 3 specification. This will write the attributes
		defined in the file into the object.

		``validate`` will validate the read data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		infoDict = self._readInfo(validate)
		infoDataToSet = {}
		# version 1
		if self._formatVersion == 1:
			for attr in fontInfoAttributesVersion1:
				value = infoDict.get(attr)
				if value is not None:
					infoDataToSet[attr] = value
			infoDataToSet = _convertFontInfoDataVersion1ToVersion2(infoDataToSet)
			infoDataToSet = _convertFontInfoDataVersion2ToVersion3(infoDataToSet)
		# version 2
		elif self._formatVersion == 2:
			for attr, dataValidationDict in list(fontInfoAttributesVersion2ValueData.items()):
				value = infoDict.get(attr)
				if value is None:
					continue
				infoDataToSet[attr] = value
			infoDataToSet = _convertFontInfoDataVersion2ToVersion3(infoDataToSet)
		# version 3
		elif self._formatVersion == 3:
			for attr, dataValidationDict in list(fontInfoAttributesVersion3ValueData.items()):
				value = infoDict.get(attr)
				if value is None:
					continue
				infoDataToSet[attr] = value
		# unsupported version
		else:
			raise NotImplementedError
		# validate data
		if validate:
			infoDataToSet = validateInfoVersion3Data(infoDataToSet)
		# populate the object
		for attr, value in list(infoDataToSet.items()):
			try:
				setattr(info, attr, value)
			except AttributeError:
				raise UFOLibError("The supplied info object does not support setting a necessary attribute (%s)." % attr)

	# kerning.plist

	def _readKerning(self):
		data = self.fileSystem.readPlist(KERNING_FILENAME, {})
		return data

	def readKerning(self, validate=None):
		"""
		Read kerning.plist. Returns a dict.

		``validate`` will validate the kerning data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		# handle up conversion
		if self._formatVersion < 3:
			self._upConvertKerning(validate)
			kerningNested = self._upConvertedKerningData["kerning"]
		# normal
		else:
			kerningNested = self._readKerning()
		if validate:
			valid, message = kerningValidator(kerningNested)
			if not valid:
				raise UFOLibError(message)
		# flatten
		kerning = {}
		for left in kerningNested:
			for right in kerningNested[left]:
				value = kerningNested[left][right]
				kerning[left, right] = value
		return kerning

	# lib.plist

	def readLib(self, validate=None):
		"""
		Read lib.plist. Returns a dict.

		``validate`` will validate the data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		data = self.fileSystem.readPlist(LIB_FILENAME, {})
		if validate:
			valid, message = fontLibValidator(data)
			if not valid:
				raise UFOLibError(message)
		return data

	# features.fea

	def readFeatures(self):
		"""
		Read features.fea. Returns a string.
		"""
		if not self.fileSystem.exists(FEATURES_FILENAME):
			return ""
		with self.fileSystem.open(FEATURES_FILENAME, "r", encoding="utf-8") as f:
			text = f.read()
		return text

	# glyph sets & layers

	def _readLayerContents(self, validate):
		"""
		Rebuild the layer contents list by checking what glyphsets
		are available on disk.

		``validate`` will validate the layer contents.
		"""
		if self._formatVersion < 3:
			return [(DEFAULT_LAYER_NAME, DEFAULT_GLYPHS_DIRNAME)]
		contents = self.fileSystem.readPlist(LAYERCONTENTS_FILENAME)
		if validate:
			valid, error = layerContentsValidator(contents, self.fileSystem)
			if not valid:
				raise UFOLibError(error)
		return contents

	def getLayerNames(self, validate=None):
		"""
		Get the ordered layer names from layercontents.plist.

		``validate`` will validate the data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		layerContents = self._readLayerContents(validate)
		layerNames = [layerName for layerName, directoryName in layerContents]
		return layerNames

	def getDefaultLayerName(self, validate=None):
		"""
		Get the default layer name from layercontents.plist.

		``validate`` will validate the data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		layerContents = self._readLayerContents(validate)
		for layerName, layerDirectory in layerContents:
			if layerDirectory == DEFAULT_GLYPHS_DIRNAME:
				return layerName
		# this will already have been raised during __init__
		raise UFOLibError("The default layer is not defined in layercontents.plist.")

	def getGlyphSet(self, layerName=None, validateRead=None, validateWrite=None):
		"""
		Return the GlyphSet associated with the
		glyphs directory mapped to layerName
		in the UFO. If layerName is not provided,
		the name retrieved with getDefaultLayerName
		will be used.

		``validateRead`` will validate the read data, by default it is set to the
		class's validate value, can be overridden.
		``validateWrte`` will validate the written data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validateRead is None:
			validateRead = self._validate
		if validateWrite is None:
			validateWrite = self._validate
		if layerName is None:
			layerName = self.getDefaultLayerName(validate=validateRead)
		directory = None
		layerContents = self._readLayerContents(validateRead)
		for storedLayerName, storedLayerDirectory in layerContents:
			if layerName == storedLayerName:
				directory = storedLayerDirectory
				break
		if directory is None:
			raise UFOLibError("No glyphs directory is mapped to \"%s\"." % layerName)
		return GlyphSet(
			directory,
			fileSystem=self.fileSystem,
			ufoFormatVersion=self._formatVersion,
			validateRead=validateRead,
			validateWrite=validateWrite,
		)

	def getCharacterMapping(self, layerName=None, validate=None):
		"""
		Return a dictionary that maps unicode values (ints) to
		lists of glyph names.
		"""
		if validate is None:
			validate = self._validate
		glyphSet = self.getGlyphSet(layerName, validateRead=validate, validateWrite=True)
		allUnicodes = glyphSet.getUnicodes()
		cmap = {}
		for glyphName, unicodes in allUnicodes.items():
			for code in unicodes:
				if code in cmap:
					cmap[code].append(glyphName)
				else:
					cmap[code] = [glyphName]
		return cmap

	# /data

	def getDataDirectoryListing(self):
		"""
		Returns a list of all files in the data directory.
		The returned paths will be relative to the UFO.
		This will not list directory names, only file names.
		Thus, empty directories will be skipped.
		"""
		if not self.fileSystem.exists(DATA_DIRNAME):
			return []
		listing = self.fileSystem.listDirectory(DATA_DIRNAME, recurse=True)
		return listing

	def getImageDirectoryListing(self, validate=None):
		"""
		Returns a list of all image file names in
		the images directory. Each of the images will
		have been verified to have the PNG signature.

		``validate`` will validate the data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if self._formatVersion < 3:
			return []
		if validate is None:
			validate = self._validate
		if not self.fileSystem.exists(IMAGES_DIRNAME):
			return []
		if not self.fileSystem.isDirectory(IMAGES_DIRNAME):
			raise UFOLibError("The UFO contains an \"images\" file instead of a directory.")
		result = []
		for fileName in self.fileSystem.listDirectory(IMAGES_DIRNAME):
			path = self.fileSystem.joinPath(IMAGES_DIRNAME, fileName)
			if self.fileSystem.isDirectory(path):
				# silently skip this as version control
				# systems often have hidden directories
				continue
			if validate:
				with self.fileSystem.open(path, mode='rb') as fp:
					valid, error = pngValidator(fileObj=fp)
				if valid:
					result.append(fileName)
			else:
				result.append(fileName)
		return result

	def readImage(self, fileName, validate=None):
		"""
		Return image data for the file named fileName.

		``validate`` will validate the data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		if self._formatVersion < 3:
			raise UFOLibError("Reading images is not allowed in UFO %d." % self._formatVersion)
		path = self.fileSystem.joinPath(IMAGES_DIRNAME, fileName)
		data = self.fileSystem.readBytesFromPath(path)
		if data is None:
			raise UFOLibError("No image file named %s." % fileName)
		if validate:
			valid, error = pngValidator(data=data)
			if not valid:
				raise UFOLibError(error)
		return data


# ----------
# UFO Writer
# ----------

class UFOWriter(object):

	"""
	Write the various components of the .ufo.

	By default, the written data will be validated before writing. Set ``validate`` to
	``False`` if you do not want to validate the data. Validation can also be overriden
	on a per method level if desired.
	"""

	def __init__(
		self,
		path,
		formatVersion=3,
		fileCreator="org.robofab.ufoLib",
		structure=None,
		validate=True,
	):
		# XXX
		# for testing only
		if isinstance(path, basestring) and structure is None:
			ext = os.path.splitext(path)[-1].lower()
			if ext == ".ufo":
				structure = "package"
			elif ext == ".ufoz":
				structure = "zip"
			else:
				structure = "zip"

		if isinstance(structure, basestring) and structure == "zip":
			file, ext = os.path.splitext(path)
			ext.lower()
			if ext != ".ufoz":
				path = file + '.ufoz'
		# /XXX

		if formatVersion not in supportedUFOFormatVersions:
			raise UFOLibError("Unsupported UFO format (%d)." % formatVersion)
		# establish some basic stuff
		self._path = path
		self._formatVersion = formatVersion
		self._fileCreator = fileCreator
		self._downConversionKerningData = None
		self._validate = validate
		# if the file already exists, get the format version.
		# this will be needed for up and down conversion.
		havePreviousFile = False
		if isinstance(path, basestring) and os.path.exists(path):
			havePreviousFile = True
		self.fileSystem = FileSystem(path, mode="w", structure=structure)
		previousFormatVersion = None
		if havePreviousFile:
			metaInfo = self.fileSystem.readPlist(METAINFO_FILENAME)
			previousFormatVersion = metaInfo.get("formatVersion")
			try:
				previousFormatVersion = int(previousFormatVersion)
			except:
				self.fileSystem.close()
				raise UFOLibError("The existing metainfo.plist is not properly formatted.")
			if previousFormatVersion not in supportedUFOFormatVersions:
				self.fileSystem.close()
				raise UFOLibError("Unsupported UFO format (%d)." % formatVersion)
		# catch down conversion
		if previousFormatVersion is not None and previousFormatVersion > formatVersion:
			raise UFOLibError("The UFO located at this path is a higher version (%d) than the version (%d) that is trying to be written. This is not supported." % (previousFormatVersion, formatVersion))
		# handle the layer contents
		self.layerContents = {}
		if previousFormatVersion is not None and previousFormatVersion >= 3:
			# already exists
			self._readLayerContents(validate=validate)
		else:
			# previous < 3
			# imply the layer contents
			if self.fileSystem.exists(DEFAULT_GLYPHS_DIRNAME):
				self.layerContents = {DEFAULT_LAYER_NAME : DEFAULT_GLYPHS_DIRNAME}
		# write the new metainfo
		self._writeMetaInfo()

	# properties

	def _get_path(self):
		return self._path

	path = property(_get_path, doc="The path the UFO is being written to.")

	def _get_formatVersion(self):
		return self._formatVersion

	formatVersion = property(_get_formatVersion, doc="The format version of the UFO. This is set into metainfo.plist during __init__.")

	def _get_fileCreator(self):
		return self._fileCreator

	fileCreator = property(_get_fileCreator, doc="The file creator of the UFO. This is set into metainfo.plist during __init__.")

	def copyFromReader(self, reader, sourcePath, destPath):
		"""
		Copy the sourcePath in the provided UFOReader to destPath
		in this writer. The paths must be relative. This only
		works with individual files, not directories.
		"""
		if not isinstance(reader, UFOReader):
			raise UFOLibError("The reader must be an instance of UFOReader.")
		if not reader.fileSystem.exists(sourcePath):
			raise UFOLibError("The reader does not have data located at \"%s\"." % sourcePath)
		if self.fileSystem.exists(destPath):
			raise UFOLibError("A file named \"%s\" already exists." % destPath)
		if reader.fileSystem.isDirectory(sourcePath):
			self._copyDirectoryFromReader(reader, sourcePath, destPath)
		else:
			data = reader.fileSystem.readBytesFromPath(sourcePath)
			self.fileSystem.writeBytesToPath(destPath, data)

	def _copyDirectoryFromReader(self, reader, sourcePath, destPath):
		# create the destination directory if it doesn't exist
		if not self.fileSystem.exists(destPath):
			destDirectory = destPath
			destTree = []
			while destDirectory:
				destDirectory, b = self.fileSystem.splitPath(destDirectory)
				destTree.insert(0, b)
			for i, d in enumerate(destTree):
				p = self.fileSystem.joinPath(*(destTree[:i] + [d]))
				if not self.fileSystem.exists(p):
					self.fileSystem.makeDirectory(p)
		# copy everything in the source directory
		for fileName in reader.fileSystem.listDirectory(sourcePath):
			fullSourcePath = self.fileSystem.joinPath(sourcePath, fileName)
			fullDestPath = self.fileSystem.joinPath(destPath, fileName)
			self.copyFromReader(reader, fullSourcePath, fullDestPath)


	def writeBytesToPath(self, path, data, encoding=None):
		"""
		Write bytes to path. If needed, the directory tree
		for the given path will be built. The path must be
		relative to the UFO. An encoding may be passed if needed.
		"""
		self.fileSystem.writeBytesToPath(path, data, encoding=encoding)

	def readBytesFromPath(self, path, encoding=None):
		"""
		Returns the bytes in the file at the given path.
		The path must be relative to the UFO path.
		Returns None if the file does not exist.
		An encoding may be passed if needed.
		"""
		return self.fileSystem.readBytesFromPath(path, encoding=encoding)

	def getFileObjectForPath(self, path, mode="w", encoding=None):
		"""
		Returns a file (or file-like) object for the
		file at the given path. The path must be relative
		to the UFO path. Returns None if the file does
		not exist and the mode is "r" or "rb. An encoding
		may be passed if needed.

		Note: The caller is responsible for closing the open file.
		"""
		return self.fileSystem.open(path, mode=mode, encoding=encoding)

	def removeFileForPath(self, path):
		"""
		Remove the file (or directory) at path. The path
		must be relative to the UFO.
		"""
		if not self.fileSystem.exists(path):
			raise UFOLibError("%s does not exist." % path)
		self.fileSystem.remove(path)

	# UFO mod time

	def setModificationTime(self):
		"""
		Set the UFO modification time to the current time.
		This is never called automatically. It is up to the
		caller to call this when finished working on the UFO.
		"""
		path = self.path
		if path is not None:
			os.utime(path, None)

	# metainfo.plist

	def _writeMetaInfo(self):
		metaInfo = dict(
			creator=self._fileCreator,
			formatVersion=self._formatVersion
		)
		self.fileSystem.writePlist(METAINFO_FILENAME, metaInfo)

	# groups.plist

	def setKerningGroupConversionRenameMaps(self, maps):
		"""
		Set maps defining the renaming that should be done
		when writing groups and kerning in UFO 1 and UFO 2.
		This will effectively undo the conversion done when
		UFOReader reads this data. The dictionary should have
		this form:

			{
				"side1" : {"group name to use when writing" : "group name in data"},
				"side2" : {"group name to use when writing" : "group name in data"}
			}

		This is the same form returned by UFOReader's
		getKerningGroupConversionRenameMaps method.
		"""
		if self._formatVersion >= 3:
			return # XXX raise an error here
		# flip the dictionaries
		remap = {}
		for side in ("side1", "side2"):
			for writeName, dataName in list(maps[side].items()):
				remap[dataName] = writeName
		self._downConversionKerningData = dict(groupRenameMap=remap)

	def writeGroups(self, groups, validate=None):
		"""
		Write groups.plist. This method requires a
		dict of glyph groups as an argument.

		``validate`` will validate the data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		# validate the data structure
		if validate:
			valid, message = groupsValidator(groups)
			if not valid:
				raise UFOLibError(message)
		# down convert
		if self._formatVersion < 3 and self._downConversionKerningData is not None:
			remap = self._downConversionKerningData["groupRenameMap"]
			remappedGroups = {}
			# there are some edge cases here that are ignored:
			# 1. if a group is being renamed to a name that
			#    already exists, the existing group is always
			#    overwritten. (this is why there are two loops
			#    below.) there doesn't seem to be a logical
			#    solution to groups mismatching and overwriting
			#    with the specifiecd group seems like a better
			#    solution than throwing an error.
			# 2. if side 1 and side 2 groups are being renamed
			#    to the same group name there is no check to
			#    ensure that the contents are identical. that
			#    is left up to the caller.
			for name, contents in list(groups.items()):
				if name in remap:
					continue
				remappedGroups[name] = contents
			for name, contents in list(groups.items()):
				if name not in remap:
					continue
				name = remap[name]
				remappedGroups[name] = contents
			groups = remappedGroups
		# pack and write
		groupsNew = {}
		for key, value in list(groups.items()):
			groupsNew[key] = list(value)
		if groupsNew:
			self.fileSystem.writePlist(GROUPS_FILENAME, groupsNew)
		else:
			self.fileSystem.remove(GROUPS_FILENAME)

	# fontinfo.plist

	def writeInfo(self, info, validate=None):
		"""
		Write info.plist. This method requires an object
		that supports getting attributes that follow the
		fontinfo.plist version 2 specification. Attributes
		will be taken from the given object and written
		into the file.

		``validate`` will validate the data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		# gather version 3 data
		infoData = {}
		for attr in list(fontInfoAttributesVersion3ValueData.keys()):
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
			if validate:
				infoData = validateInfoVersion3Data(infoData)
		elif self._formatVersion == 2:
			infoData = _convertFontInfoDataVersion3ToVersion2(infoData)
			if validate:
				infoData = validateInfoVersion2Data(infoData)
		elif self._formatVersion == 1:
			infoData = _convertFontInfoDataVersion3ToVersion2(infoData)
			if validate:
				infoData = validateInfoVersion2Data(infoData)
			infoData = _convertFontInfoDataVersion2ToVersion1(infoData)
		# write file
		self.fileSystem.writePlist(FONTINFO_FILENAME, infoData)

	# kerning.plist

	def writeKerning(self, kerning, validate=None):
		"""
		Write kerning.plist. This method requires a
		dict of kerning pairs as an argument.

		This performs basic structural validation of the kerning,
		but it does not check for compliance with the spec in
		regards to conflicting pairs. The assumption is that the
		kerning data being passed is standards compliant.

		``validate`` will validate the data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		# validate the data structure
		if validate:
			invalidFormatMessage = "The kerning is not properly formatted."
			if not isDictEnough(kerning):
				raise UFOLibError(invalidFormatMessage)
			for pair, value in list(kerning.items()):
				if not isinstance(pair, (list, tuple)):
					raise UFOLibError(invalidFormatMessage)
				if not len(pair) == 2:
					raise UFOLibError(invalidFormatMessage)
				if not isinstance(pair[0], basestring):
					raise UFOLibError(invalidFormatMessage)
				if not isinstance(pair[1], basestring):
					raise UFOLibError(invalidFormatMessage)
				if not isinstance(value, (int, float)):
					raise UFOLibError(invalidFormatMessage)
		# down convert
		if self._formatVersion < 3 and self._downConversionKerningData is not None:
			remap = self._downConversionKerningData["groupRenameMap"]
			remappedKerning = {}
			for (side1, side2), value in list(kerning.items()):
				side1 = remap.get(side1, side1)
				side2 = remap.get(side2, side2)
				remappedKerning[side1, side2] = value
			kerning = remappedKerning
		# pack and write
		kerningDict = {}
		for left, right in list(kerning.keys()):
			value = kerning[left, right]
			if left not in kerningDict:
				kerningDict[left] = {}
			kerningDict[left][right] = value
		if kerningDict:
			self.fileSystem.writePlist(KERNING_FILENAME, kerningDict)
		else:
			self.fileSystem.remove(KERNING_FILENAME)

	# lib.plist

	def writeLib(self, libDict, validate=None):
		"""
		Write lib.plist. This method requires a
		lib dict as an argument.

		``validate`` will validate the data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validate is None:
			validate = self._validate
		if validate:
			valid, message = fontLibValidator(libDict)
			if not valid:
				raise UFOLibError(message)
		if libDict:
			self.fileSystem.writePlist(LIB_FILENAME, libDict)
		else:
			self.fileSystem.remove(LIB_FILENAME)

	# features.fea

	def writeFeatures(self, features, validate=None):
		"""
		Write features.fea. This method requires a
		features string as an argument.
		"""
		if validate is None:
			validate = self._validate
		if self._formatVersion == 1:
			raise UFOLibError("features.fea is not allowed in UFO Format Version 1.")
		if validate:
			if not isinstance(features, basestring):
				raise UFOLibError("The features are not text.")
		self.fileSystem.writeBytesToPath(FEATURES_FILENAME, features.encode("utf8"))

	# glyph sets & layers

	def _readLayerContents(self, validate):
		"""
		Rebuild the layer contents list by checking what glyph sets
		are available on disk.

		``validate`` will validate the data.
		"""
		# read the file on disk
		raw = self.fileSystem.readPlist(LAYERCONTENTS_FILENAME)
		contents = {}
		if validate:
			valid, error = layerContentsValidator(raw, self.fileSystem)
			if not valid:
				raise UFOLibError(error)
		for entry in raw:
			layerName, directoryName = entry
			contents[layerName] = directoryName
		self.layerContents = contents

	def writeLayerContents(self, layerOrder=None, validate=None):
		"""
		Write the layercontents.plist file. This method  *must* be called
		after all glyph sets have been written.
		"""
		if validate is None:
			validate = self._validate
		if self.formatVersion < 3:
			return
		if layerOrder is not None:
			newOrder = []
			for layerName in layerOrder:
				if layerName is None:
					layerName = DEFAULT_LAYER_NAME
				else:
					layerName = tounicode(layerName)
				newOrder.append(layerName)
			layerOrder = newOrder
		else:
			layerOrder = list(self.layerContents.keys())
		if validate and set(layerOrder) != set(self.layerContents.keys()):
			raise UFOLibError("The layer order content does not match the glyph sets that have been created.")
		layerContents = [(layerName, self.layerContents[layerName]) for layerName in layerOrder]
		self.fileSystem.writePlist(LAYERCONTENTS_FILENAME, layerContents)

	def _findDirectoryForLayerName(self, layerName):
		foundDirectory = None
		for existingLayerName, directoryName in list(self.layerContents.items()):
			if layerName is None and directoryName == DEFAULT_GLYPHS_DIRNAME:
				foundDirectory = directoryName
				break
			elif existingLayerName == layerName:
				foundDirectory = directoryName
				break
		if not foundDirectory:
			raise UFOLibError("Could not locate a glyph set directory for the layer named %s." % layerName)
		return foundDirectory

	def getGlyphSet(self, layerName=None, defaultLayer=True, glyphNameToFileNameFunc=None, validateRead=None, validateWrite=None):
		"""
		Return the GlyphSet object associated with the
		appropriate glyph directory in the .ufo.
		If layerName is None, the default glyph set
		will be used. The defaultLayer flag indictes
		that the layer should be saved into the default
		glyphs directory.

		``validateRead`` will validate the read data, by default it is set to the
		class's validate value, can be overridden.
		``validateWrte`` will validate the written data, by default it is set to the
		class's validate value, can be overridden.
		"""
		if validateRead is None:
			validateRead = self._validate
		if validateWrite is None:
			validateWrite = self._validate
		# only default can be written in < 3
		if self._formatVersion < 3 and (not defaultLayer or layerName is not None):
			raise UFOLibError("Only the default layer can be writen in UFO %d." % self.formatVersion)
		# locate a layer name when None has been given
		if layerName is None and defaultLayer:
			for existingLayerName, directory in list(self.layerContents.items()):
				if directory == DEFAULT_GLYPHS_DIRNAME:
					layerName = existingLayerName
			if layerName is None:
				layerName = DEFAULT_LAYER_NAME
		elif layerName is None and not defaultLayer:
			raise UFOLibError("A layer name must be provided for non-default layers.")
		# move along to format specific writing
		if self.formatVersion == 1:
			return self._getGlyphSetFormatVersion1(validateRead, validateWrite, glyphNameToFileNameFunc=glyphNameToFileNameFunc)
		elif self.formatVersion == 2:
			return self._getGlyphSetFormatVersion2(validateRead, validateWrite, glyphNameToFileNameFunc=glyphNameToFileNameFunc)
		elif self.formatVersion == 3:
			return self._getGlyphSetFormatVersion3(validateRead, validateWrite, layerName=layerName, defaultLayer=defaultLayer, glyphNameToFileNameFunc=glyphNameToFileNameFunc)

	def _getGlyphSetFormatVersion1(self, validateRead, validateWrite, glyphNameToFileNameFunc=None):
		return GlyphSet(
			DEFAULT_GLYPHS_DIRNAME,
			fileSystem=self.fileSystem,
			glyphNameToFileNameFunc=glyphNameToFileNameFunc,
			ufoFormatVersion=1,
			validateRead=validateRead,
			validateWrite=validateWrite,
		)

	def _getGlyphSetFormatVersion2(self, validateRead, validateWrite, glyphNameToFileNameFunc=None):
		return GlyphSet(
			DEFAULT_GLYPHS_DIRNAME,
			fileSystem=self.fileSystem,
			glyphNameToFileNameFunc=glyphNameToFileNameFunc,
			ufoFormatVersion=2,
			validateRead=validateRead,
			validateWrite=validateWrite,
		)

	def _getGlyphSetFormatVersion3(self, validateRead, validateWrite, layerName=None, defaultLayer=True, glyphNameToFileNameFunc=None):
		# if the default flag is on, make sure that the default in the file
		# matches the default being written. also make sure that this layer
		# name is not already linked to a non-default layer.
		if defaultLayer:
			for existingLayerName, directory in list(self.layerContents.items()):
				if directory == DEFAULT_GLYPHS_DIRNAME:
					if existingLayerName != layerName:
						raise UFOLibError("Another layer is already mapped to the default directory.")
				elif existingLayerName == layerName:
					raise UFOLibError("The layer name is already mapped to a non-default layer.")
		# get an existing directory name
		if layerName in self.layerContents:
			directory = self.layerContents[layerName]
		# get a  new directory name
		else:
			if defaultLayer:
				directory = DEFAULT_GLYPHS_DIRNAME
			else:
				# not caching this could be slightly expensive,
				# but caching it will be cumbersome
				existing = [d.lower() for d in list(self.layerContents.values())]
				if not isinstance(layerName, unicode):
					try:
						layerName = unicode(layerName)
					except UnicodeDecodeError:
						raise UFOLibError("The specified layer name is not a Unicode string.")
				directory = userNameToFileName(layerName, existing=existing, prefix="glyphs.")
		# make the directory
		self.fileSystem.makeDirectory(directory)
		# store the mapping
		self.layerContents[layerName] = directory
		# load the glyph set
		return GlyphSet(
			directory,
			fileSystem=self.fileSystem,
			glyphNameToFileNameFunc=glyphNameToFileNameFunc,
			ufoFormatVersion=3,
			validateRead=validateRead,
			validateWrite=validateWrite,
		)

	def renameGlyphSet(self, layerName, newLayerName, defaultLayer=False):
		"""
		Rename a glyph set.

		Note: if a GlyphSet object has already been retrieved for
		layerName, it is up to the caller to inform that object that
		the directory it represents has changed.
		"""
		if self._formatVersion < 3:
			# ignore renaming glyph sets for UFO1 UFO2
			# just write the data from the default layer
			return
		# the new and old names can be the same
		# as long as the default is being switched
		if layerName == newLayerName:
			# if the default is off and the layer is already not the default, skip
			if self.layerContents[layerName] != DEFAULT_GLYPHS_DIRNAME and not defaultLayer:
				return
			# if the default is on and the layer is already the default, skip
			if self.layerContents[layerName] == DEFAULT_GLYPHS_DIRNAME and defaultLayer:
				return
		else:
			# make sure the new layer name doesn't already exist
			if newLayerName is None:
				newLayerName = DEFAULT_LAYER_NAME
			if newLayerName in self.layerContents:
				raise UFOLibError("A layer named %s already exists." % newLayerName)
			# make sure the default layer doesn't already exist
			if defaultLayer and DEFAULT_GLYPHS_DIRNAME in list(self.layerContents.values()):
				raise UFOLibError("A default layer already exists.")
		# get the paths
		oldDirectory = self._findDirectoryForLayerName(layerName)
		if defaultLayer:
			newDirectory = DEFAULT_GLYPHS_DIRNAME
		else:
			existing = [name.lower() for name in list(self.layerContents.values())]
			newDirectory = userNameToFileName(newLayerName, existing=existing, prefix="glyphs.")
		# update the internal mapping
		del self.layerContents[layerName]
		self.layerContents[newLayerName] = newDirectory
		# do the file system copy
		self.fileSystem.move(oldDirectory, newDirectory)

	def deleteGlyphSet(self, layerName):
		"""
		Remove the glyph set matching layerName.
		"""
		if self._formatVersion < 3:
			# ignore deleting glyph sets for UFO1 UFO2 as there are no layers
			# just write the data from the default layer
			return
		foundDirectory = self._findDirectoryForLayerName(layerName)
		self.fileSystem.remove(foundDirectory)
		del self.layerContents[layerName]

	# /images

	def writeImage(self, fileName, data, validate=None):
		"""
		Write data to fileName in the images directory.
		The data must be a valid PNG.
		"""
		if validate is None:
			validate = self._validate
		if self._formatVersion < 3:
			raise UFOLibError("Images are not allowed in UFO %d." % self._formatVersion)
		if validate:
			valid, error = pngValidator(data=data)
			if not valid:
				raise UFOLibError(error)
		path = self.fileSystem.joinPath(IMAGES_DIRNAME, fileName)
		self.fileSystem.writeBytesToPath(path, data)

	def removeImage(self, fileName, validate=None):
		"""
		Remove the file named fileName from the
		images directory.
		"""
		if validate is None:
			validate = self._validate
		if self._formatVersion < 3:
			raise UFOLibError("Images are not allowed in UFO %d." % self._formatVersion)
		path = self.fileSystem.joinPath(IMAGES_DIRNAME, fileName)
		self.fileSystem.remove(path)

	def copyImageFromReader(self, reader, sourceFileName, destFileName, validate=None):
		"""
		Copy the sourceFileName in the provided UFOReader to destFileName
		in this writer. This uses the most memory efficient method possible
		for copying the data possible.
		"""
		if validate is None:
			validate = self._validate
		if self._formatVersion < 3:
			raise UFOLibError("Images are not allowed in UFO %d." % self._formatVersion)
		sourcePath = self.fileSystem.joinPath(IMAGES_DIRNAME, sourceFileName)
		destPath = self.fileSystem.joinPath(IMAGES_DIRNAME, destFileName)
		self.copyFromReader(reader, sourcePath, destPath)


# ----------------
# Helper Functions
# ----------------

def makeUFOPath(path):
	"""
	Return a .ufo pathname.

	>>> makeUFOPath("directory/something.ext") == (
	... 	os.path.join('directory', 'something.ufo'))
	True
	>>> makeUFOPath("directory/something.another.thing.ext") == (
	... 	os.path.join('directory', 'something.another.thing.ufo'))
	True
	"""
	dir, name = os.path.split(path)
	name = ".".join([".".join(name.split(".")[:-1]), "ufo"])
	return os.path.join(dir, name)

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
		if validator == genericTypeValidator:
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
	for attr, value in list(infoData.items()):
		isValidValue = validateFontInfoVersion2ValueForAttribute(attr, value)
		if not isValidValue:
			raise UFOLibError("Invalid value for attribute %s (%s)." % (attr, repr(value)))
		else:
			validInfoData[attr] = value
	return validInfoData

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
		if validator == genericTypeValidator:
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
	for attr, value in list(infoData.items()):
		isValidValue = validateFontInfoVersion3ValueForAttribute(attr, value)
		if not isValidValue:
			raise UFOLibError("Invalid value for attribute %s (%s)." % (attr, repr(value)))
		else:
			validInfoData[attr] = value
	return validInfoData

# Value Options

fontInfoOpenTypeHeadFlagsOptions = list(range(0, 15))
fontInfoOpenTypeOS2SelectionOptions = [1, 2, 3, 4, 7, 8, 9]
fontInfoOpenTypeOS2UnicodeRangesOptions = list(range(0, 128))
fontInfoOpenTypeOS2CodePageRangesOptions = list(range(0, 64))
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
	"openTypeHeadFlags"						: dict(type="integerList", valueValidator=genericIntListValidator, valueOptions=fontInfoOpenTypeHeadFlagsOptions),
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
	"openTypeOS2Selection"					: dict(type="integerList", valueValidator=genericIntListValidator, valueOptions=fontInfoOpenTypeOS2SelectionOptions),
	"openTypeOS2VendorID"					: dict(type=basestring),
	"openTypeOS2Panose"						: dict(type="integerList", valueValidator=fontInfoVersion2OpenTypeOS2PanoseValidator),
	"openTypeOS2FamilyClass"				: dict(type="integerList", valueValidator=fontInfoOpenTypeOS2FamilyClassValidator),
	"openTypeOS2UnicodeRanges"				: dict(type="integerList", valueValidator=genericIntListValidator, valueOptions=fontInfoOpenTypeOS2UnicodeRangesOptions),
	"openTypeOS2CodePageRanges"				: dict(type="integerList", valueValidator=genericIntListValidator, valueOptions=fontInfoOpenTypeOS2CodePageRangesOptions),
	"openTypeOS2TypoAscender"				: dict(type=(int, float)),
	"openTypeOS2TypoDescender"				: dict(type=(int, float)),
	"openTypeOS2TypoLineGap"				: dict(type=(int, float)),
	"openTypeOS2WinAscent"					: dict(type=(int, float)),
	"openTypeOS2WinDescent"					: dict(type=(int, float)),
	"openTypeOS2Type"						: dict(type="integerList", valueValidator=genericIntListValidator, valueOptions=fontInfoOpenTypeOS2TypeOptions),
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
	"versionMinor"							: dict(type=int, valueValidator=genericNonNegativeIntValidator),
	"unitsPerEm"							: dict(type=(int, float), valueValidator=genericNonNegativeNumberValidator),
	"openTypeHeadLowestRecPPEM"				: dict(type=int, valueValidator=genericNonNegativeNumberValidator),
	"openTypeHheaAscender"					: dict(type=int),
	"openTypeHheaDescender"					: dict(type=int),
	"openTypeHheaLineGap"					: dict(type=int),
	"openTypeHheaCaretOffset"				: dict(type=int),
	"openTypeOS2Panose"						: dict(type="integerList", valueValidator=fontInfoVersion3OpenTypeOS2PanoseValidator),
	"openTypeOS2TypoAscender"				: dict(type=int),
	"openTypeOS2TypoDescender"				: dict(type=int),
	"openTypeOS2TypoLineGap"				: dict(type=int),
	"openTypeOS2WinAscent"					: dict(type=int, valueValidator=genericNonNegativeNumberValidator),
	"openTypeOS2WinDescent"					: dict(type=int, valueValidator=genericNonNegativeNumberValidator),
	"openTypeOS2SubscriptXSize"				: dict(type=int),
	"openTypeOS2SubscriptYSize"				: dict(type=int),
	"openTypeOS2SubscriptXOffset"			: dict(type=int),
	"openTypeOS2SubscriptYOffset"			: dict(type=int),
	"openTypeOS2SuperscriptXSize"			: dict(type=int),
	"openTypeOS2SuperscriptYSize"			: dict(type=int),
	"openTypeOS2SuperscriptXOffset"			: dict(type=int),
	"openTypeOS2SuperscriptYOffset"			: dict(type=int),
	"openTypeOS2StrikeoutSize"				: dict(type=int),
	"openTypeOS2StrikeoutPosition"			: dict(type=int),
	"openTypeGaspRangeRecords"				: dict(type="dictList", valueValidator=fontInfoOpenTypeGaspRangeRecordsValidator),
	"openTypeNameRecords"					: dict(type="dictList", valueValidator=fontInfoOpenTypeNameRecordsValidator),
	"openTypeVheaVertTypoAscender"			: dict(type=int),
	"openTypeVheaVertTypoDescender"			: dict(type=int),
	"openTypeVheaVertTypoLineGap"			: dict(type=int),
	"openTypeVheaCaretOffset"				: dict(type=int),
	"woffMajorVersion"						: dict(type=int, valueValidator=genericNonNegativeIntValidator),
	"woffMinorVersion"						: dict(type=int, valueValidator=genericNonNegativeIntValidator),
	"woffMetadataUniqueID"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataUniqueIDValidator),
	"woffMetadataVendor"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataVendorValidator),
	"woffMetadataCredits"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataCreditsValidator),
	"woffMetadataDescription"				: dict(type=dict, valueValidator=fontInfoWOFFMetadataDescriptionValidator),
	"woffMetadataLicense"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataLicenseValidator),
	"woffMetadataCopyright"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataCopyrightValidator),
	"woffMetadataTrademark"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataTrademarkValidator),
	"woffMetadataLicensee"					: dict(type=dict, valueValidator=fontInfoWOFFMetadataLicenseeValidator),
	"woffMetadataExtensions"				: dict(type=list, valueValidator=fontInfoWOFFMetadataExtensionsValidator),
	"guidelines"							: dict(type=list, valueValidator=guidelinesValidator)
})
fontInfoAttributesVersion3 = set(fontInfoAttributesVersion3ValueData.keys())

# insert the type validator for all attrs that
# have no defined validator.
for attr, dataDict in list(fontInfoAttributesVersion2ValueData.items()):
	if "valueValidator" not in dataDict:
		dataDict["valueValidator"] = genericTypeValidator

for attr, dataDict in list(fontInfoAttributesVersion3ValueData.items()):
	if "valueValidator" not in dataDict:
		dataDict["valueValidator"] = genericTypeValidator

# Version Conversion Support
# These are used from converting from version 1
# to version 2 or vice-versa.

def _flipDict(d):
	flipped = {}
	for key, value in list(d.items()):
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

# 1 <-> 2

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
	for attr, value in list(data.items()):
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
	for attr, value in list(data.items()):
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

# 2 <-> 3

_ufo2To3NonNegativeInt = set((
	"versionMinor",
	"openTypeHeadLowestRecPPEM",
	"openTypeOS2WinAscent",
	"openTypeOS2WinDescent"
))
_ufo2To3NonNegativeIntOrFloat = set((
	"unitsPerEm"
))
_ufo2To3FloatToInt = set(((
	"openTypeHeadLowestRecPPEM",
	"openTypeHheaAscender",
	"openTypeHheaDescender",
	"openTypeHheaLineGap",
	"openTypeHheaCaretOffset",
	"openTypeOS2TypoAscender",
	"openTypeOS2TypoDescender",
	"openTypeOS2TypoLineGap",
	"openTypeOS2WinAscent",
	"openTypeOS2WinDescent",
	"openTypeOS2SubscriptXSize",
	"openTypeOS2SubscriptYSize",
	"openTypeOS2SubscriptXOffset",
	"openTypeOS2SubscriptYOffset",
	"openTypeOS2SuperscriptXSize",
	"openTypeOS2SuperscriptYSize",
	"openTypeOS2SuperscriptXOffset",
	"openTypeOS2SuperscriptYOffset",
	"openTypeOS2StrikeoutSize",
	"openTypeOS2StrikeoutPosition",
	"openTypeVheaVertTypoAscender",
	"openTypeVheaVertTypoDescender",
	"openTypeVheaVertTypoLineGap",
	"openTypeVheaCaretOffset"
)))

def convertFontInfoValueForAttributeFromVersion2ToVersion3(attr, value):
	"""
	Convert value from version 2 to version 3 format.
	Returns the new attribute name and the converted value.
	If the value is None, None will be returned for the new value.
	"""
	if attr in _ufo2To3FloatToInt:
		try:
			v = int(round(value))
		except (ValueError, TypeError):
			raise UFOLibError("Could not convert value for %s." % attr)
		if v != value:
			value = v
	if attr in _ufo2To3NonNegativeInt:
		try:
			v = int(abs(value))
		except (ValueError, TypeError):
			raise UFOLibError("Could not convert value for %s." % attr)
		if v != value:
			value = v
	elif attr in _ufo2To3NonNegativeIntOrFloat:
		try:
			v = float(abs(value))
		except (ValueError, TypeError):
			raise UFOLibError("Could not convert value for %s." % attr)
		if v == int(v):
			v = int(v)
		if v != value:
			value = v
	return attr, value

def convertFontInfoValueForAttributeFromVersion3ToVersion2(attr, value):
	"""
	Convert value from version 3 to version 2 format.
	Returns the new attribute name and the converted value.
	If the value is None, None will be returned for the new value.
	"""
	return attr, value

def _convertFontInfoDataVersion3ToVersion2(data):
	converted = {}
	for attr, value in list(data.items()):
		newAttr, newValue = convertFontInfoValueForAttributeFromVersion3ToVersion2(attr, value)
		if newAttr not in fontInfoAttributesVersion2:
			continue
		converted[newAttr] = newValue
	return converted

def _convertFontInfoDataVersion2ToVersion3(data):
	converted = {}
	for attr, value in list(data.items()):
		attr, value = convertFontInfoValueForAttributeFromVersion2ToVersion3(attr, value)
		converted[attr] = value
	return converted

if __name__ == "__main__":
	import doctest
	doctest.testmod()
