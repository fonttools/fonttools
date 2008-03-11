"""This module has been deprecated."""

from warnings import warn
warn("family.py is deprecated.", DeprecationWarning)

"""
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 

W A R N I N G

This is work in progress, a fast moving target.

XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX 
"""

import os
from robofab import RoboFabError
from robofab.plistlib import readPlist, writePlist
from robofab.objects.objectsRF import RInfo, RFont, RLib, RGlyph, OpenFont
from robofab.ufoLib import UFOReader, writePlistAtomically, fontInfoAttrs
from robofab.objects.objectsBase import RBaseObject, BaseGroups
from robofab.glifLib import GlyphSet
import weakref

"""
RoboFab family planning

A font family is a group of UFO fonts that are related when
	- they share a common source
	- they are masters in various interpolations
	- they are weights in a section of design space

Some family infrastructure is needed because there is some
information that transcends font or glyph. It is also a tool
to track fonts which are part of a larger structure, make sure
all resources needed for a project are present, up to date etc.

Structure:
	MyFamilyProjectName.uff/
	# the file and folder structure of the extended UFO family.

		lib.plist
		# a lib for the family

		fonts/
		# a folder with ufo's
			masterA.ufo/
			masterB.ufo/
			# any number of fonts
			...
			contents.plist
			# a contents.plist to track resources 

		shared/
		# a .ufo containing capable of containing all
		# data that a .ufo can contain. this data is 
		# shared with all members of the family
			metainfo.plist
			fontinfo.plist
			lib.plist
			groups.plist
			kerning.plist
			glyphs/
				# any number of common or sharable glifs.
				foundryLogo.glif
				genericStuff.glif

				# location for inbetween masters, interpolation exceptions:
				# glyphs that don't fit in any specific font
				a_lightBold_028.glif
				a_lightBold_102.glif
				a_lightBold_103.glif
				...
				contents.plist
"""


FONTS_DIRNAME = 'fonts'
FONTSCONTENTS_FILENAME = "contents.plist"
METAINFO_FILENAME = 'metainfo.plist'
LIB_FILENAME = 'lib.plist'	
FAMILY_EXTENSION = ".uff"
FONT_EXTENSION = ".ufo"
SHARED_DIRNAME = "shared"

			
def makeUFFName(familyName):
	return ''.join([familyName, FAMILY_EXTENSION])
	
def _scanContentsDirectory(path, forceRebuild=False):
	contentsPath = os.path.join(path, FONTSCONTENTS_FILENAME)
	if forceRebuild or not os.path.exists(contentsPath):
		ext = FONT_EXTENSION
		fileNames = os.listdir(path)
		fileNames = [n for n in fileNames if n.endswith(ext)]
		contents = {}
		for n in fileNames:
			contents[n[:-len(ext)]] = n
	else:
		contents = readPlist(contentsPath)
	return contents


class FamilyReader(object):
	
	"""A reader that reads all info from a .uff"""
	
	def __init__(self, path):
		self._path = path
	
	def _checkForFile(self, path):
		if not os.path.exists(path):
			return False
		else:
			return True
			
	def readMetaInfo(self):
		path = os.path.join(self._path, METAINFO_FILENAME)
		if not self._checkForFile(path):
			return
	
	def readLib(self):
		path = os.path.join(self._path, LIB_FILENAME)
		if not self._checkForFile(path):
			return {}
		return readPlist(path)
	
	def readFontsContents(self):
		contentsPath = os.path.join(self._path, FONTS_DIRNAME)
		contents = _scanContentsDirectory(contentsPath)
		return contents
	
	def getSharedPath(self):
		"""Return the path of all shared values in the family,
		rather then create a new instance for it."""
		return os.path.join(self._path, SHARED_DIRNAME)


class FamilyWriter(object):
	
	"""a writer that builds all the necessary family stuff."""

	
	fileCreator = 'org.robofab.uffLib'
	formatVersion = 1
	
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
	
	def writeLib(self, libDict):
		self._makeDirectory()
		path = os.path.join(self._path, LIB_FILENAME)
		if libDict:
			writePlistAtomically(libDict, path)
		elif os.path.exists(path):
			os.remove(path)
	
	def writeFontsContents(self):
		path = self.makeFontsPath()
		contents = _scanContentsDirectory(path)
		contentsPath = os.path.join(path, FONTSCONTENTS_FILENAME)
		writePlistAtomically(contents, contentsPath)
	
	def makeFontsPath(self):
		fontDir = self._makeDirectory(FONTS_DIRNAME)
		return fontDir
	
	def makeSharedPath(self):
		sharedDir = self._makeDirectory(SHARED_DIRNAME)
		return sharedDir
	
	def getSharedGlyphSet(self):
		path = self.makeSharedGlyphsPath()
		return GlyphSet(path)


class RFamily(RBaseObject):
	
	"""
	Sketch for Family, the font superstructure.
	This should ultimately move to objectsRF
	
	The shared fontinfo and glyphset is just another font, named 'shared',
	this avoids duplication of a lot of  functionality in maintaining
	the shared glyphset, reading, writing etc.
	"""
		
	def __init__(self, path=None):
		self._path = path
		self.info = RInfo()		# this should go away. it is part of shared.info.
		self.lib = RLib()
		self.shared = RFont()
		self._fontsContents = {}	# font name: path
		self._fonts = {}		# fontName: object
		self.lib.setParent(self)
		if self._path:
			self._loadData()
	
	def __repr__(self):
		if self.info.familyName:
			name = self.info.familyName
		else:
			name = 'UnnamedFamily'
		return "<RFont family for %s>" %(name)
	
	def __len__(self):
		return len(self._fontsContents.keys())
	
	def __getitem__(self, fontKey):
		if self._fontsContents.has_key(fontKey):
			if not self._fonts.has_key(fontKey):
				fontPath = os.path.join(self._path, FONTS_DIRNAME, self._fontsContents[fontKey])
				font = RFont(fontPath)
				font.setParent(self)
				self._fonts[fontKey] = font
			# uh, is returning a proxy the right thing to do here?
			return weakref.proxy(self._fonts[fontKey])
		raise IndexError
	
	def __setitem__(self, key, fontObject):
		if not key:
			key = 'None'
		key = self._makeKey(key)
		self._fontsContents[key] = None
		self._fonts[key] = fontObject
		fontObject._path = None
	
	def keys(self):
		return self._fontsContents.keys()
		
	def has_key(self, key):
		return self._fontsContents.has_key(key)
		
	__contains__ = has_key
		
	def _loadData(self):
		fr = FamilyReader(self._path)
		self._fontsContents = fr.readFontsContents()
		self.shared = RFont(fr.getSharedPath())
		self.lib.update(fr.readLib())
		
	def _hasChanged(self):
		#mark the object as changed
		self.setChanged(True)
	
	def _makeKey(self, key):
		# add a numerical extension to the key if it already exists
		if self._fontsContents.has_key(key):
			if key[-2] == '.':
				try:
					key = key[:-1] + `int(key[-1]) + 1`
				except ValueError:
					key = key + '.1'
			else:
				key = key + 1
			self_makeKey(key)
		return key
	
	def save(self, destDir=None, doProgress=False):
		if not destDir:
			saveAs = False
			destDir = self._path
		else:
			saveAs = True
		fw = FamilyWriter(destDir)
		for fontName, fontPath in self._fontsContents.items():
			if saveAs and not self._fonts.has_key(fontName):
				font = self[fontName]
			if self._fonts.has_key(fontName):
				if not fontPath or saveAs:
					fontPath = os.path.join(path, fw.makeFontsPath(), ''.join([fontName, FONT_EXTENSION]))
					self._fontsContents[fontName] = fontPath
				self._fonts[fontName].save(fontPath, doProgress=False)
		fw.writeFontsContents()
		fw.writeLib(self.lib)
		sharedPath = fw.makeSharedPath()
		self.shared.save(sharedPath, doProgress=False)
		self._path = destDir
		
	#def sharedGlyphNames(self):
	#	"""a list of all shared glyphs"""
	#	keys = self.sharedGlyphs.keys()
	#	if self.sharedGlyphSet is not None:
	#		keys.extend(self.sharedGlyphSet.keys())
	#	d = dict.fromkeys(keys)
	#	return d.keys()
	#
	#def getGlyph(self, glyphName, fontName=None):
	#	"""retrieve a glyph from fontName, or from shared if no font is given."""
	#	if fontName is None or fontName =="shared":
	#		# ask for a shared glyph
	#		return self.shared[glyphName]
	#	if self.has_key(fontName):
	#		return self[fontName].getGlyph(glyphName)
	#	return None
	#
	#def newGlyph(self, glyphName):
	#	"""add a new shared glyph"""
	#	return self.shared.newGlyph(glyphName)
	#
	#def removeGlyph(self, glyphName):
	#	"""remove a shared glyph"""
	#	self.shared.removeGlyph(glyphName)
		
	
if __name__ == "__main__":

	from robofab.world import OpenFont
	from robofab.interface.all.dialogs import GetFolder
	from PyBrowser import Browser

	#open and test
	font = OpenFont()
	family = RFamily()
	family['aFont'] = font
	family.lib['org.robofab.uffLibTest'] = 'TestOneTwo!'
	family.shared.info.familyName = 'ThisIsAFamilyName'
	family.shared.newGlyph('xxx')
	path = GetFolder('where do you want to store this new .uff?')
	path = os.path.join(path, makeUFFName('MyBigFamily'))
	family.save(path)
	#family = RFamily(path)
	#Browser(family.getGlyph('ASharedGlyph_Yay'))
	
	## save as test
	#path = GetFolder('select a .uff directory')
	#family = RFamily(path)
	#family.newGlyph('xxx')
	#family.name = 'YeOldFamily'
	#newPath = os.path.join(os.path.split(path)[0], 'xxx'+os.path.split(path)[1])
	#family.save(newPath)

