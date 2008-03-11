""""
A library for importing .ufo files and their descendants.
This library works with robofab objects. Using the magic of the
U.F.O., common attributes are exported to and read from .plist files.

It contains two very simple classes for reading and writing the
various components of the .ufo. Currently, the .ufo supports the
files detailed below. But, these files are not absolutely required.
If the a file is not included in the .ufo, it is implied that the data
of that file is empty.

FontName.ufo/
	metainfo.plist      # meta info about the .ufo bundle, most impartantly the
	                    # format version number.
	glyphs/
		contents.plist  # a plist mapping all glyph names to file names
		a.glif          # a glif file
		...etc...
	fontinfo.plist      # font names, versions, copyright, dimentions, etc.
	kerning.plist       # kerning
	lib.plist           # user definable data
	groups.plist        # glyph group definitions
"""


import os
from cStringIO import StringIO
from robofab.plistlib import readPlist, writePlist
from robofab.glifLib import GlyphSet, READ_MODE, WRITE_MODE


def writePlistAtomically(obj, path):
	"""Write a plist for 'obj' to 'path'. Do this sort of atomically,
	making it harder to cause corrupt files, for example when writePlist
	encounters an error halfway during write. Also: don't write out the
	file if it would be identical to what's already there, meaning the
	modification date won't get stomped when writing the same data.
	"""
	f = StringIO()
	writePlist(obj, f)
	data = f.getvalue()
	if os.path.exists(path):
		f = open(path, READ_MODE)
		oldData = f.read()
		f.close()
		if data == oldData:
			return
	f = open(path, WRITE_MODE)
	f.write(data)
	f.close()


GLYPHS_DIRNAME = 'glyphs'
METAINFO_FILENAME = 'metainfo.plist'
FONTINFO_FILENAME = 'fontinfo.plist'
LIB_FILENAME = 'lib.plist'	
GROUPS_FILENAME = 'groups.plist'
KERNING_FILENAME = 'kerning.plist'


fontInfoAttrs = [
	# XXX we need to document how these map to OTF 'name' table fields
	'familyName',
	'styleName',
	'fullName',
	'fontName',
	'menuName',
	'fontStyle',
	'note',
	'versionMajor',
	'versionMinor',
	'year',
	'copyright',
	'notice',
	'trademark',
	'license',
	'licenseURL',
	'createdBy',
	'designer',
	'designerURL',
	'vendorURL',
	'unitsPerEm',
	'ascender',
	'descender',
	'capHeight',
	'xHeight',
	'defaultWidth',
	'slantAngle',
	'italicAngle',
	'widthName',
	'weightName',
	'weightValue',

	# dubious format-specific fields
	'fondName',
	'otFamilyName',
	'otStyleName',
	'otMacName',
	'msCharSet',
	'fondID',
	'uniqueID',
	'ttVendor',
	'ttUniqueID',
	'ttVersion',
]


def makeUFOPath(fontPath):
	"""return a .ufo pathname based on a .vfb pathname"""
	dir, name = os.path.split(fontPath)
	name = '.'.join([name.split('.')[0], 'ufo'])
	return os.path.join(dir, name)


class UFOReader(object):
	
	"""read the various components of the .ufo"""
	
	def __init__(self, path):
		self._path = path
		
	def _checkForFile(self, path):
		if not os.path.exists(path):
			#print "missing file: %s" % path
			return False
		else:
			return True
			
	def readMetaInfo(self):
		"""read metainfo.plist. mostly used
		for internal operations"""
		path = os.path.join(self._path, METAINFO_FILENAME)
		if not self._checkForFile(path):
			return
	
	def readGroups(self):
		"""read groups.plist. returns a dict that should
		be applied to a font.groups object."""
		path = os.path.join(self._path, GROUPS_FILENAME)
		if not self._checkForFile(path):
			return {}
		return readPlist(path)
	
	def readInfo(self, info):
		"""read info.plist. it requires a font.info object
		as an argument. this will write the attributes
		defined in the file into the info object."""
		path = os.path.join(self._path, FONTINFO_FILENAME)
		if not self._checkForFile(path):
			return {}
		infoDict = readPlist(path)
		for key, value in infoDict.items():
			try:
				setattr(info, key, value)
			except AttributeError:
				# object doesn't support setting this attribute
				pass
	
	def readKerning(self):
		"""read kerning.plist. returns a dict that should
		be applied to a font.kerning object."""
		path = os.path.join(self._path, KERNING_FILENAME)
		if not self._checkForFile(path):
			return {}
		kerningNested = readPlist(path)
		kerning = {}
		for left in kerningNested:
			for right in kerningNested[left]:
				value = kerningNested[left][right]
				kerning[left, right] = value
		return kerning
	
	def readLib(self):
		"""read lib.plist. returns a dict that should
		be applied to a font.lib object."""
		path = os.path.join(self._path, LIB_FILENAME)
		if not self._checkForFile(path):
			return {}
		return readPlist(path)
	
	def getGlyphSet(self):
		"""return the GlyphSet associated with the
		glyphs directory in the .ufo"""
		glyphsPath = os.path.join(self._path, GLYPHS_DIRNAME)
		return GlyphSet(glyphsPath)

	def getCharacterMapping(self):
		"""Return a dictionary that maps unicode values (ints) to
		lists of glyph names.
		"""
		glyphsPath = os.path.join(self._path, GLYPHS_DIRNAME)
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


class UFOWriter(object):
	
	"""write the various components of the .ufo"""
	
	fileCreator = 'org.robofab.ufoLib'
	formatVersion = 1  # the format version is an int, the next version will be 2.
	
	def __init__(self, path):
		self._path = path
		
	def _makeDirectory(self, subDirectory=None):
		path = self._path
		if subDirectory:
			path = os.path.join(self._path, subDirectory)
		if not os.path.exists(path):
			os.makedirs(path)
		if not os.path.exists(os.path.join(path, METAINFO_FILENAME)):
			self._writeMetaInfo()
		return path
	
	def _writeMetaInfo(self):
		path = os.path.join(self._path, METAINFO_FILENAME)
		metaInfo = {
			'creator': self.fileCreator,
			'formatVersion': self.formatVersion,
		}
		writePlistAtomically(metaInfo, path)
	
	def writeGroups(self, groups):
		"""write groups.plist. this method requires a
		dict of glyph groups as an argument."""
		self._makeDirectory()
		path = os.path.join(self._path, GROUPS_FILENAME)
		groupsNew = {}
		for key, value in groups.items():
			groupsNew[key] = list(value)
		if groupsNew:
			writePlistAtomically(groupsNew, path)
		elif os.path.exists(path):
			os.remove(path)
	
	def writeInfo(self, info):
		"""write info.plist. this method requires a
		font.info object. attributes will be taken from
		the given object and written into the file"""
		self._makeDirectory()
		path = os.path.join(self._path, FONTINFO_FILENAME)
		infoDict = {}
		for name in fontInfoAttrs:
			value = getattr(info, name, None)
			if value is not None:
				infoDict[name] = value
		writePlistAtomically(infoDict, path)
	
	def writeKerning(self, kerning):
		"""write kerning.plist. this method requires a
		dict of kerning pairs as an argument"""
		self._makeDirectory()
		path = os.path.join(self._path, KERNING_FILENAME)
		kerningDict = {}
		for left, right in kerning.keys():
			value = kerning[left, right]
			if not left in kerningDict:
				kerningDict[left] = {}
			kerningDict[left][right] = value
		if kerningDict:
			writePlistAtomically(kerningDict, path)
		elif os.path.exists(path):
			os.remove(path)
	
	def writeLib(self, libDict):
		"""write lib.plist. this method requires a
		lib dict as an argument"""
		self._makeDirectory()
		path = os.path.join(self._path, LIB_FILENAME)
		if libDict:
			writePlistAtomically(libDict, path)
		elif os.path.exists(path):
			os.remove(path)

	def makeGlyphPath(self):
		"""make the glyphs directory in the .ufo
		returns the path of the directory created"""
		glyphDir = self._makeDirectory(GLYPHS_DIRNAME)
		return glyphDir

	def getGlyphSet(self, glyphNameToFileNameFunc=None):
		"""return the GlyphSet associated with the
		glyphs directory in the .ufo"""
		return GlyphSet(self.makeGlyphPath(), glyphNameToFileNameFunc)
