"""UFO implementation for the objects as used by FontLab 4.5 and higher"""

from FL import *	

from robofab.tools.toolsFL import GlyphIndexTable,\
		AllFonts, NewGlyph
from robofab.objects.objectsBase import BaseFont, BaseGlyph, BaseContour, BaseSegment,\
		BasePoint, BaseBPoint, BaseAnchor, BaseGuide, BaseComponent, BaseKerning, BaseInfo, BaseGroups, BaseLib,\
		roundPt, addPt, _box,\
		MOVE, LINE, CORNER, CURVE, QCURVE, OFFCURVE,\
		relativeBCPIn, relativeBCPOut, absoluteBCPIn, absoluteBCPOut,\
		BasePostScriptFontHintValues, postScriptHintDataLibKey, BasePostScriptGlyphHintValues
from fontTools.misc import arrayTools
from robofab.pens.flPen import FLPointPen
from robofab import RoboFabError
import os
from robofab.plistlib import Data, Dict, readPlist, writePlist
from StringIO import StringIO

# local encoding
if os.name in ["mac", "posix"]:
	LOCAL_ENCODING = "macroman"
else:
	LOCAL_ENCODING = "latin-1"

# a list of attributes that are to be copied when copying a glyph.
# this is used by glyph.copy and font.insertGlyph
GLYPH_COPY_ATTRS = [
	"name",
	"width",
	"unicodes",
	"note",
	"lib",
	]

# Generate Types
PC_TYPE1 = 'pctype1'
PC_MM = 'pcmm'
PC_TYPE1_ASCII = 'pctype1ascii'
PC_MM_ASCII = 'pcmmascii'
UNIX_ASCII = 'unixascii'
MAC_TYPE1 = 'mactype1'
OTF_CFF = 'otfcff'
OTF_TT = 'otfttf'
MAC_TT = 'macttf'
MAC_TT_DFONT = 'macttdfont'

# doc for these functions taken from: http://dev.fontlab.net/flpydoc/
#			internal name			(FontLab name,		extension)
_flGenerateTypes ={	PC_TYPE1		:	(ftTYPE1,			'pfb'),		# PC Type 1 font (binary/PFB)
			PC_MM		:	(ftTYPE1_MM,		'mm'),		# PC MultipleMaster font (PFB)
			PC_TYPE1_ASCII	:	(ftTYPE1ASCII,		'pfa'),		# PC Type 1 font (ASCII/PFA)
			PC_MM_ASCII		:	(ftTYPE1ASCII_MM,		'mm'),		# PC MultipleMaster font (ASCII/PFA)
			UNIX_ASCII		:	(ftTYPE1ASCII,		'pfa'),		# UNIX ASCII font (ASCII/PFA)
			OTF_TT		:	(ftTRUETYPE,			'ttf'),		# PC TrueType/TT OpenType font (TTF)
			OTF_CFF		:	(ftOPENTYPE,			'otf'),		# PS OpenType (CFF-based) font (OTF)
			MAC_TYPE1		:	(ftMACTYPE1,			'suit'),		# Mac Type 1 font (generates suitcase  and LWFN file, optionally AFM)
			MAC_TT		:	(ftMACTRUETYPE,		'ttf'),		# Mac TrueType font (generates suitcase)
			MAC_TT_DFONT	:	(ftMACTRUETYPE_DFONT,	'dfont'),	# Mac TrueType font (generates suitcase with resources in data fork) 
			}

## FL Hint stuff
# this should not be referenced outside of this module
# since we may be changing the way this works in the future.


"""

	FontLab implementation of psHints objects
	
	Most of the FL methods relating to ps hints return a list of 16 items.
	These values are for the 16 corners of a 4 axis multiple master.
	The odd thing is that even single masters get these 16 values.
	RoboFab doesn't access the MM masters, so by default, the psHints
	object only works with the first element. If you want to access the other
	values in the list, give a value between 0 and 15 for impliedMasterIndex
	when creating the object.

	From the FontLab docs:
	http://dev.fontlab.net/flpydoc/

	blue_fuzz
	blue_scale
	blue_shift

	blue_values_num(integer)             - number of defined blue values
	blue_values[integer[integer]]        - two-dimentional array of BlueValues
                                         master index is top-level index

	other_blues_num(integer)             - number of defined OtherBlues values
	other_blues[integer[integer]]        - two-dimentional array of OtherBlues
	                                       master index is top-level index

	family_blues_num(integer)            - number of FamilyBlues records
	family_blues[integer[integer]]       - two-dimentional array of FamilyBlues
	                                       master index is top-level index

	family_other_blues_num(integer)      - number of FamilyOtherBlues records
	family_other_blues[integer[integer]] - two-dimentional array of FamilyOtherBlues
	                                       master index is top-level index

	force_bold[integer]                  - list of Force Bold values, one for 
	                                       each master
	stem_snap_h_num(integer)
	stem_snap_h
	stem_snap_v_num(integer)
	stem_snap_v
 """

class PostScriptFontHintValues(BasePostScriptFontHintValues):
	"""	Wrapper for font-level PostScript hinting information for FontLab.
		Blues values, stem values. 
	"""
	def __init__(self, font=None, impliedMasterIndex=0):
		self._object = font.naked()
		self._masterIndex = impliedMasterIndex
	
	def copy(self):
		from robofab.objects.objectsRF import PostScriptFontHintValues as _PostScriptFontHintValues
		return _PostScriptFontHintValues(data=self.asDict())
			
	def _getBlueFuzz(self):
		return self._object.blue_fuzz[self._masterIndex]
	def _setBlueFuzz(self, value):
		self._object.blue_fuzz[self._masterIndex] = value

	def _getBlueScale(self):
		return self._object.blue_scale[self._masterIndex]
	def _setBlueScale(self, value):
		self._object.blue_scale[self._masterIndex] = float(value)

	def _getBlueShift(self):
		return self._object.blue_shift[self._masterIndex]
	def _setBlueShift(self, value):
		self._object.blue_shift[self._masterIndex] = value

	def _getForceBold(self):
		return self._object.force_bold[self._masterIndex] == 1
		
	def _setForceBold(self, value):
		if value:
			value = 1
		else:
			value = 0
		self._object.force_bold[self._masterIndex] = value
	
	# Note: these attributes are wrapppers for lists,
	# but regular list operatons won't have any effect.
	# you really have to _get_ and _set_ a list.
	
	def _asPairs(self, l):
		"""Split a list of numbers into a list of pairs"""
		assert len(l)%2 == 0, "Even number of values required: %s"%(`l`)
		n = [[l[i], l[i+1]] for i in range(0, len(l), 2)]
		n.sort()
		return n
	
	def _flattenPairs(self, l):
		"""The reverse of _asPairs"""
		n = []
		l.sort()
		for i in l:
			assert len(i) == 2, "Each entry must consist of two numbers"
			n.append(i[0])
			n.append(i[1])
		return n
	
	def _getBlueValues(self):
			return self._asPairs(self._object.blue_values[self._masterIndex])
	def _setBlueValues(self, values):
		values = self._flattenPairs(values)
		self._object.blue_values_num = min(self._attributeNames['blueValues']['max']*2, len(values))
		for i in range(self._object.blue_values_num):
			self._object.blue_values[self._masterIndex][i] = values[i]

	def _getOtherBlues(self):
			return self._asPairs(self._object.other_blues[self._masterIndex])
	def _setOtherBlues(self, values):
		values = self._flattenPairs(values)
		self._object.other_blues_num = min(self._attributeNames['otherBlues']['max']*2, len(values))
		for i in range(self._object.other_blues_num):
			self._object.other_blues[self._masterIndex][i] = values[i]

	def _getFamilyBlues(self):
			return self._asPairs(self._object.family_blues[self._masterIndex])
	def _setFamilyBlues(self, values):
		values = self._flattenPairs(values)
		self._object.family_blues_num = min(self._attributeNames['familyBlues']['max']*2, len(values))
		for i in range(self._object.family_blues_num):
			self._object.family_blues[self._masterIndex][i] = values[i]

	def _getFamilyOtherBlues(self):
			return self._asPairs(self._object.family_other_blues[self._masterIndex])
	def _setFamilyOtherBlues(self, values):
		values = self._flattenPairs(values)
		self._object.family_other_blues_num = min(self._attributeNames['familyOtherBlues']['max']*2, len(values))
		for i in range(self._object.family_other_blues_num):
			self._object.family_other_blues[self._masterIndex][i] = values[i]

	def _getVStems(self):
			return list(self._object.stem_snap_v[self._masterIndex])
	def _setVStems(self, values):
		self._object.stem_snap_v_num = min(self._attributeNames['vStems']['max'], len(values))
		for i in range(self._object.stem_snap_v_num):
			self._object.stem_snap_v[self._masterIndex][i] = values[i]

	def _getHStems(self):
			return list(self._object.stem_snap_h[self._masterIndex])
	def _setHStems(self, values):
		self._object.stem_snap_h_num = min(self._attributeNames['hStems']['max'], len(values))
		for i in range(self._object.stem_snap_h_num):
			self._object.stem_snap_h[self._masterIndex][i] = values[i]

	blueFuzz = property(_getBlueFuzz, _setBlueFuzz, doc="postscript hints: bluefuzz value")
	blueScale = property(_getBlueScale, _setBlueScale, doc="postscript hints: bluescale value")
	blueShift = property(_getBlueShift, _setBlueShift, doc="postscript hints: blueshift value")
	forceBold = property(_getForceBold, _setForceBold, doc="postscript hints: force bold value")
	blueValues = property(_getBlueValues, _setBlueValues, doc="postscript hints: blue values")
	otherBlues = property(_getOtherBlues, _setOtherBlues, doc="postscript hints: other blue values")
	familyBlues = property(_getFamilyBlues, _setFamilyBlues, doc="postscript hints: family blue values")
	familyOtherBlues = property(_getFamilyOtherBlues, _setFamilyOtherBlues, doc="postscript hints: family other blue values")
	vStems = property(_getVStems, _setVStems, doc="postscript hints: vertical stem values")
	hStems = property(_getHStems, _setHStems, doc="postscript hints: horizontal stem values")
			

class PostScriptGlyphHintValues(BasePostScriptGlyphHintValues):
	"""	Wrapper for glyph-level PostScript hinting information for FontLab.
		vStems, hStems
	"""
	def __init__(self, glyph=None):
		self._object = glyph.naked()

	def copy(self):
		from robofab.objects.objectsRF import PostScriptGlyphHintValues as _PostScriptGlyphHintValues
		return _PostScriptGlyphHintValues(data=self.asDict())

	def _hintObjectsToList(self, item):
		data = []
		done = []
		for hint in item:
			p = (hint.position, hint.width)
			if p in done:
				continue
			data.append(p)
			done.append(p)
		data.sort()
		return data
		
	def _listToHintObjects(self, item):
		hints = []
		done = []
		for pos, width in item:
			if (pos, width) in done:
				# we don't want to set duplicates
				continue
			hints.append(Hint(pos, width))
			done.append((pos,width))
		return hints

	def _getVHints(self):
		return self._hintObjectsToList(self._object.vhints)

	def _setVHints(self, values):
		# 1 = horizontal hints and links,
		# 2 = vertical hints and links
		# 3 = all hints and links
		self._object.RemoveHints(2)
		if values is None:
			# just clearing it then
			return
		values.sort()
		for hint in self._listToHintObjects(values):
			self._object.vhints.append(hint)

	def _getHHints(self):
		return self._hintObjectsToList(self._object.hhints)

	def _setHHints(self, values):
		# 1 = horizontal hints and links,
		# 2 = vertical hints and links
		# 3 = all hints and links
		self._object.RemoveHints(1)
		if values is None:
			# just clearing it then
			return
		values.sort()
		for hint in self._listToHintObjects(values):
			self._object.hhints.append(hint)

	vHints = property(_getVHints, _setVHints, doc="postscript hints: vertical hint zones")
	hHints = property(_getHHints, _setHHints, doc="postscript hints: horizontal hint zones")



def _glyphHintsToDict(glyph):
	data = {}
	##
	## horizontal and vertical hints
	##
	# glyph.hhints and glyph.vhints returns a list of Hint objects.
	# Hint objects have position and width attributes.
	data['hHints'] = []
	for index in xrange(len(glyph.hhints)):
		hint = glyph.hhints[index]
		data['hHints'].append((hint.position, hint.width))
	if not data['hHints']:
		del data['hHints']
	data['vHints'] = []
	for index in xrange(len(glyph.vhints)):
		hint = glyph.vhints[index]
		data['vHints'].append((hint.position, hint.width))
	if not data['vHints']:
		del data['vHints']
	##
	## horizontal and vertical links
	##
	# glyph.hlinks and glyph.vlinks returns a list of Link objects.
	# Link objects have node1 and node2 attributes.
	data['hLinks'] = []
	for index in xrange(len(glyph.hlinks)):
		link = glyph.hlinks[index]
		d = {	'node1' : link.node1,
			'node2' : link.node2,
			}
		data['hLinks'].append(d)
	if not data['hLinks']:
		del data['hLinks']
	data['vLinks'] = []
	for index in xrange(len(glyph.vlinks)):
		link = glyph.vlinks[index]
		d = {	'node1' : link.node1,
			'node2' : link.node2,
			}
		data['vLinks'].append(d)
	if not data['vLinks']:
		del data['vLinks']
	##
	## replacement table
	##
	# glyph.replace_table returns a list of Replace objects.
	# Replace objects have type and index attributes.
	data['replaceTable'] = []
	for index in xrange(len(glyph.replace_table)):
		replace = glyph.replace_table[index]
		d = {	'type' : replace.type,
			'index' : replace.index,
			}
		data['replaceTable'].append(d)
	if not data['replaceTable']:
		del data['replaceTable']
	# XXX
	# need to support glyph.instructions and glyph.hdmx?
	# they are not documented very well.
	return data

def _dictHintsToGlyph(glyph, aDict):
	# clear existing hints first
	# RemoveHints requires an "integer mode" argument
	# but it is not documented. from some simple experiments
	# i deduced that
	# 1 = horizontal hints and links,
	# 2 = vertical hints and links
	# 3 = all hints and links
	glyph.RemoveHints(3)
	##
	## horizontal and vertical hints
	##
	if aDict.has_key('hHints'):
		for d in aDict['hHints']:
			glyph.hhints.append(Hint(d[0], d[1]))
	if aDict.has_key('vHints'):
		for d in aDict['vHints']:
			glyph.vhints.append(Hint(d[0], d[1]))
	##
	## horizontal and vertical links
	##
	if aDict.has_key('hLinks'):
		for d in aDict['hLinks']:
			glyph.hlinks.append(Link(d['node1'], d['node2']))
	if aDict.has_key('vLinks'):
		for d in aDict['vLinks']:
			glyph.vlinks.append(Link(d['node1'], d['node2']))
	##
	## replacement table
	##
	if aDict.has_key('replaceTable'):
		for d in aDict['replaceTable']:
			glyph.replace_table.append(Replace(d['type'], d['index']))
	
# FL Node Types
flMOVE = 17			
flLINE = 1
flCURVE = 35
flOFFCURVE = 65
flSHARP = 0
# I have no idea what the difference between
# "smooth" and "fixed" is, but booth values
# are returned by FL
flSMOOTH = 4096
flFIXED = 12288


_flToRFSegmentDict = {	flMOVE		:	MOVE,
				flLINE		:	LINE,
				flCURVE	:	CURVE,
				flOFFCURVE	:	OFFCURVE
			}

_rfToFLSegmentDict = {}
for k, v in _flToRFSegmentDict.items():
	_rfToFLSegmentDict[v] = k
		
def _flToRFSegmentType(segmentType):
	return _flToRFSegmentDict[segmentType]

def _rfToFLSegmentType(segmentType):
	return _rfToFLSegmentDict[segmentType]
		
def _scalePointFromCenter((pointX, pointY), (scaleX, scaleY), (centerX, centerY)):
	ogCenter = (centerX, centerY)
	scaledCenter = (centerX * scaleX, centerY * scaleY)
	shiftVal = (scaledCenter[0] - ogCenter[0], scaledCenter[1] - ogCenter[1])
	scaledPointX = (pointX * scaleX) - shiftVal[0]
	scaledPointY = (pointY * scaleY) - shiftVal[1]
	return (scaledPointX, scaledPointY)

# Nostalgia code:
def CurrentFont():
	"""Return a RoboFab font object for the currently selected font."""
	f = fl.font
	if f is not None:
		return RFont(fl.font)
	return None
	
def CurrentGlyph():
	"""Return a RoboFab glyph object for the currently selected glyph."""
	from robofab.world import AllFonts
	currentPath = fl.font.file_name
	if fl.glyph is None:
		return None
	glyphName = fl.glyph.name
	currentFont = None
	# is this font already loaded as an RFont?
	for font in AllFonts():
		# ugh this won't work because AllFonts sees non RFonts as well....
		if font.path == currentPath:
			currentFont = font
			break
	xx =  currentFont[glyphName]
	#print "objectsFL.CurrentGlyph parent for %d"% id(xx), xx.getParent()
 	return xx
	
def OpenFont(path=None, note=None):
	"""Open a font from a path."""
	if path == None:
		from robofab.interface.all.dialogs import GetFile
		path = GetFile(note)
	if path:
		if path[-4:].lower() in ['.vfb', '.VFB', '.bak', '.BAK']:
			f = Font(path)
			fl.Add(f)
			return RFont(f)
	return None
	
def NewFont(familyName=None, styleName=None):
	"""Make a new font"""
	from FL import fl, Font
	f = Font()
	fl.Add(f)
	rf = RFont(f)
	rf.info.familyName = familyName
	rf.info.styleName = styleName
	return rf

def AllFonts():
	"""Return a list of all open fonts."""
	fontCount = len(fl)
	all = []
	for index in xrange(fontCount):
		naked = fl[index]
		all.append(RFont(naked))
	return all

# the lib getter and setter are shared by RFont and RGlyph	
def _get_lib(self):
	data = self._object.customdata
	if data:
		f = StringIO(data)
		try:
			pList = readPlist(f)
		except: # XXX ugh, plistlib can raise lots of things
			# Anyway, customdata does not contain valid plist data,
			# but we don't need to toss it!
			pList = {"org.robofab.fontlab.customdata": Data(data)}
	else:
		pList = {}
	# pass it along to the lib object
	l = RLib(pList)
	l.setParent(self)
	return l
		
def _set_lib(self, aDict):
	l = RLib({})
	l.setParent(self)
	l.update(aDict)


def _normalizeLineEndings(s):
	return s.replace("\r\n", "\n").replace("\r", "\n")


class RFont(BaseFont):
	"""RoboFab UFO wrapper for FL Font object"""

	_title = "FLFont"

	def __init__(self, font=None):
		BaseFont.__init__(self)
		if font is None:
			from FL import fl, Font
			# rather than raise an error we could just start a new font.
			font = Font()
			fl.Add(font)
			#raise RoboFabError, "RFont: there's nothing to wrap!?"
		self._object = font
		self._lib = {}
		self._supportHints = True

	def keys(self):
		keys = {}
		for glyph in self._object.glyphs:
			glyphName = glyph.name
			if glyphName in keys:
				n = 1
				while ("%s#%s" % (glyphName, n)) in keys:
					n += 1
				newGlyphName = "%s#%s" % (glyphName, n)
				print "RoboFab encountered a duplicate glyph name, renaming %r to %r" % (glyphName, newGlyphName)
				glyphName = newGlyphName
				glyph.name = glyphName
			keys[glyphName] = None
		return keys.keys()

	def has_key(self, glyphName):
		glyph = self._object[glyphName]
		if glyph is None:
			return False
		else:
			return True

	__contains__ = has_key

	def __setitem__(self, glyphName, glyph):
		self._object[glyphName] = glyph.naked()
		
	def __cmp__(self, other):
		if not hasattr(other, '_object'):
			return -1
		return self._compare(other)
	#	if self._object.file_name == other._object.file_name:
	#		# so, names match.
	#		# this will falsely identify two distinct "Untitled"
	#		# let's check some more
	#		return 0
	#	else:
	#		return -1
	

	def _get_psHints(self):
		return PostScriptFontHintValues(self)

	psHints = property(_get_psHints, doc="font level postscript hint data")

	def _get_info(self):
		return RInfo(self._object)
	
	info = property(_get_info, doc="font info object")
	
	def _get_kerning(self):
		kerning = {}
		f = self._object
		for g in f.glyphs:
			for p in g.kerning:
				try:
					key = (g.name, f[p.key].name)
					kerning[key] = p.value
				except AttributeError: pass #catch for TT exception
		rk = RKerning(kerning)
		rk.setParent(self)
		return rk
		
	kerning = property(_get_kerning, doc="a kerning object")
	
	def _set_groups(self, aDict):
		g = RGroups({})
		g.setParent(self)
		g.update(aDict)
	
	def _get_groups(self):
		groups = {}
		for i in self._object.classes:
			# test to make sure that the class is properly formatted
			if i.find(':') == -1:
				continue
			key = i.split(':')[0]
			value = i.split(':')[1].lstrip().split(' ')
			groups[key] = value
		rg = RGroups(groups)
		rg.setParent(self)
		return rg
		
	groups = property(_get_groups, _set_groups, doc="a group object")
	
	lib = property(_get_lib, _set_lib, doc="font lib object")
	
	#
	# attributes
	#
	
	def _get_fontIndex(self):
		# find the index of the font
		# by comparing the file_name
		# to all open fonts. if the
		# font has no file_name, meaning
		# it is a new, unsaved font,
		# return the index of the first
		# font with no file_name.
		selfFileName = self._object.file_name
		fontCount = len(fl)
		for index in xrange(fontCount):
			other = fl[index]
			if other.file_name == selfFileName:
				return index
	
	fontIndex = property(_get_fontIndex, doc="the fontindex for this font")
	
	def _get_path(self):
		return self._object.file_name

	path = property(_get_path, doc="path to the font")
	
	def _get_fileName(self):
		if self.path is None:
			return None
		return os.path.split(self.path)
	
	fileName = property(_get_fileName, doc="the font's file name")
	
	def _get_selection(self):
		# return a list of glyph names for glyphs selected in the font window
		l=[]
		for i in range(len(self._object.glyphs)):
			if fl.Selected(i) == 1:
				l.append(self._object[i].name)
		return l
		
	def _set_selection(self, list):
		fl.Unselect()
		for i in list:
			fl.Select(i)
	
	selection = property(_get_selection, _set_selection, doc="the glyph selection in the font window")
	
		
	def _makeGlyphlist(self):
		# To allow iterations through Font.glyphs. Should become really big in fonts with lotsa letters.
		gl = []
		for c in self:
			gl.append(c)
		return gl
	
	def _get_glyphs(self):
		return self._makeGlyphlist()
	
	glyphs = property(_get_glyphs, doc="A list of all glyphs in the font, to allow iterations through Font.glyphs")
			
	def update(self):
		"""Don't forget to update the font when you are done."""
		fl.UpdateFont(self.fontIndex)

	def save(self, path=None):
		"""Save the font, path is required."""
		if not path:
			if not self._object.file_name:
				raise RoboFabError, "No destination path specified."
			else:
				path = self._object.file_name
		fl.Save(self.fontIndex, path)
	
	def close(self, save=False):
		"""Close the font, saving is optional."""
		if save:
			self.save()
		else:
			self._object.modified = 0
		fl.Close(self.fontIndex)
	
	def getGlyph(self, glyphName):
		# XXX may need to become private
		flGlyph = self._object[glyphName]
		if flGlyph is not None:
			glyph = RGlyph(flGlyph)
			glyph.setParent(self)
			return glyph
		return self.newGlyph(glyphName)

	def newGlyph(self, glyphName, clear=True):
		"""Make a new glyph"""
		#if generate:
		#	g = GenerateGlyph(self._object, glyphName, replace=clear)
		#else:
		g = NewGlyph(self._object, glyphName, clear)
		return RGlyph(g)
	
	def insertGlyph(self, glyph, as=None):
		"""Returns a new glyph that has been inserted into the font.
		as = another glyphname if you want to insert as with that."""
		from robofab.objects.objectsRF import RFont as _RFont
		from robofab.objects.objectsRF import RGlyph as _RGlyph
		oldGlyph = glyph
		if as is None:
			name = oldGlyph.name
		else:
			name = as
		# clear the destination glyph if it exists.
		if self.has_key(name):
			self[name].clear()
		# get the parent for the glyph
		otherFont = oldGlyph.getParent()
		# in some cases we will use the native
		# FL method for appending a glyph.
		useNative = True
		testingNative = True
		while testingNative:
			# but, maybe it is an orphan glyph.
			# in that case we should not use the native method.
			if otherFont is None:
				useNative = False
				testingNative = False
			# or maybe the glyph is coming from a NoneLab font
			if otherFont is not None:
				if isinstance(otherFont, _RFont):
					useNative = False
					testingNative = False
				# but, it could be a copied FL glyph
				# which is a NoneLab glyph that
				# has a FontLab font as the parent
				elif isinstance(otherFont, RFont):
					useNative = False
					testingNative = False
			# or, maybe the glyph is being replaced, in which
			# case the native method should not be used
			# since FL will destroy any references to the glyph
			if self.has_key(name):
				useNative = False
				testingNative = False
			# if the glyph contains components the native
			# method should not be used since FL does
			# not reference glyphs in components by
			# name, but by index (!!!).
			if len(oldGlyph.components) != 0:
				useNative = False
				testingNative = False
			testingNative = False
		# finally, insert the glyph.
		if useNative:
			font = self.naked()
			otherFont = oldGlyph.getParent().naked()
			self.naked().glyphs.append(otherFont[name])
			newGlyph = self.getGlyph(name)
		else:	
			newGlyph = self.newGlyph(name)
			newGlyph.appendGlyph(oldGlyph)
			for attr in GLYPH_COPY_ATTRS:
				if attr == "name":
					value = name
				else:
					value = getattr(oldGlyph, attr)
				setattr(newGlyph, attr, value)
		if self._supportHints:
			# now we need to transfer the hints from
			# the old glyph to the new glyph. we'll do this
			# via the dict to hint functions.
			hintDict = {}
			# if the glyph is a NoneLab glyph, then we need
			# to extract the ps hints from the lib
			if isinstance(oldGlyph, _RGlyph):
				hintDict = oldGlyph.lib.get(postScriptHintDataLibKey, {})
			# otherwise we need to extract the hint dict from the glyph
			else:
				hintDict = _glyphHintsToDict(oldGlyph.naked())
			# now apply the hint data
			if hintDict:
				_dictHintsToGlyph(newGlyph.naked(), hintDict)
			# delete any remaining hint data from the glyph lib
			if newGlyph.lib.has_key(postScriptHintDataLibKey):
				del newGlyph.lib[postScriptHintDataLibKey]
		return newGlyph
	
	def removeGlyph(self, glyphName):
		"""remove a glyph from the font"""
		index = self._object.FindGlyph(glyphName)
		if index != -1:
			del self._object.glyphs[index]

	#
	# opentype
	#

	def getOTClasses(self):
		"""Return all OpenType classes as a dict. Relies on properly formatted classes."""
		classes = {}
		c = self._object.ot_classes
		if c is None:
			return classes
		c = c.replace('\r', '').replace('\n', '').split(';')
		for i in c:
			if i.find('=') != -1:
				value = []
				i = i.replace(' = ', '=')
				name = i.split('=')[0]
				v = i.split('=')[1].replace('[', '').replace(']', '').split(' ')
				#catch double spaces?
				for j in v:
					if len(j) > 0:
						value.append(j)
				classes[name] = value
		return classes
		
	def setOTClasses(self, dict):
		"""Set all OpenType classes."""
		l = []
		for i in dict.keys():
			l.append(''.join([i, ' = [', ' '.join(dict[i]), '];']))
		self._object.ot_classes = '\n'.join(l)
		
	def getOTClass(self, name):
		"""Get a specific OpenType class."""
		classes = self.getOTClasses()
		return classes[name]
	
	def setOTClass(self, name, list):
		"""Set a specific OpenType class."""
		classes = self.getOTClasses()
		classes[name] = list
		self.setOTClasses(classes)
	
	def getOTFeatures(self):
		"""Return all OpenType features as a dict keyed by name.
		The value is a string of the text of the feature."""
		features = {}
		for i in self._object.features:
			v = []
			for j in i.value.replace('\r', '\n').split('\n'):
				if j.find(i.tag) == -1:
					v.append(j)
			features[i.tag] = '\n'.join(v)
		return features
	
	def setOTFeatures(self, dict):
		"""Set all OpenType features in the font."""
		features= {}
		for i in dict.keys():
			f = []
			f.append('feature %s {'%i)
			f.append(dict[i])
			f.append('} %s;'%i)
			features[i] = '\n'.join(f)
		self._object.features.clean()
		for i in features.keys():
			self._object.features.append(Feature(i, features[i]))
			
	def getOTFeature(self, name):
		"""return a specific OpenType feature."""
		features = self.getOTFeatures()
		return features[name]
	
	def setOTFeature(self, name, text):
		"""Set a specific OpenType feature."""
		features = self.getOTFeatures()
		features[name] = text
		self.setOTFeatures(features)
		
	#
	# guides
	#
	
	def getVGuides(self):
		"""Return a list of wrapped vertical guides in this RFont"""
		vguides=[]
		for i in range(len(self._object.vguides)):
			g = RGuide(self._object.vguides[i], i)
			g.setParent(self)
			vguides.append(g)
		return vguides
	
	def getHGuides(self):
		"""Return a list of wrapped horizontal guides in this RFont"""
		hguides=[]
		for i in range(len(self._object.hguides)):
			g = RGuide(self._object.hguides[i], i)
			g.setParent(self)
			hguides.append(g)
		return hguides
		
	def appendHGuide(self, position, angle=0):
		"""Append a horizontal guide"""
		position = int(round(position))
		angle = int(round(angle))
		g=Guide(position, angle)
		self._object.hguides.append(g)
		
	def appendVGuide(self, position, angle=0):
		"""Append a horizontal guide"""
		position = int(round(position))
		angle = int(round(angle))
		g=Guide(position, angle)
		self._object.vguides.append(g)
		
	def removeHGuide(self, guide):
		"""Remove a horizontal guide."""
		pos = (guide.position, guide.angle)
		for g in self.getHGuides():
			if  (g.position, g.angle) == pos:
				del self._object.hguides[g.index]
				break
				
	def removeVGuide(self, guide):
		"""Remove a vertical guide."""
		pos = (guide.position, guide.angle)
		for g in self.getVGuides():
			if  (g.position, g.angle) == pos:
				del self._object.vguides[g.index]
				break

	def clearHGuides(self):
		"""Clear all horizontal guides."""
		self._object.hguides.clean()
	
	def clearVGuides(self):
		"""Clear all vertical guides."""
		self._object.vguides.clean()


	#
	# generators
	#
	
	def generate(self, outputType, path=None):
		"""
		generate the font. outputType is the type of font to ouput.
		--Ouput Types:
		'pctype1'	:	PC Type 1 font (binary/PFB)
		'pcmm'		:	PC MultipleMaster font (PFB)
		'pctype1ascii'	:	PC Type 1 font (ASCII/PFA)
		'pcmmascii'	:	PC MultipleMaster font (ASCII/PFA)
		'unixascii'	:	UNIX ASCII font (ASCII/PFA)
		'mactype1'	:	Mac Type 1 font (generates suitcase  and LWFN file)
		'otfcff'		:	PS OpenType (CFF-based) font (OTF)
		'otfttf'		:	PC TrueType/TT OpenType font (TTF)
		'macttf'	:	Mac TrueType font (generates suitcase)
		'macttdfont'	:	Mac TrueType font (generates suitcase with resources in data fork)
					(doc adapted from http://dev.fontlab.net/flpydoc/)
		
		path can be a directory or a directory file name combo:
		path="DirectoryA/DirectoryB"
		path="DirectoryA/DirectoryB/MyFontName"
		if no path is given, the file will be output in the same directory
		as the vfb file. if no file name is given, the filename will be the
		vfb file name with the appropriate suffix.
		"""
		outputType = outputType.lower()
		if not _flGenerateTypes.has_key(outputType):
			raise RoboFabError, "%s output type is not supported"%outputType
		flOutputType, suffix = _flGenerateTypes[outputType]
		if path is None:
			filePath, fileName = os.path.split(self.path)
			fileName = fileName.replace('.vfb', '')
		else:
			if os.path.isdir(path):
				filePath = path
				fileName = os.path.split(self.path)[1].replace('.vfb', '')
			else:
				filePath, fileName = os.path.split(path)
		if '.' in fileName:
			raise RoboFabError, "filename cannot contain periods.", fileName
		fileName = '.'.join([fileName, suffix])
		finalPath = os.path.join(filePath, fileName)
		# generate is (oddly) an application level method
		# rather than a font level method. because of this,
		# the font must be the current font. so, make it so.
		fl.ifont = self.fontIndex
		fl.GenerateFont(flOutputType, finalPath)
	
	def _writeOpenTypeFeaturesToLib(self, fontLib):
		flFont = self.naked()
		if flFont.ot_classes:
			fontLib["org.robofab.opentype.classes"] = _normalizeLineEndings(
					flFont.ot_classes)
		if flFont.features:
			features = {}
			order = []
			for feature in flFont.features:
				order.append(feature.tag)
				features[feature.tag] = _normalizeLineEndings(feature.value)
			fontLib["org.robofab.opentype.features"] = features
			fontLib["org.robofab.opentype.featureorder"] = order
	
	def writeUFO(self, path=None, doProgress=False, glyphNameToFileNameFunc=None, doHints=False):
		"""write a font to .ufo"""
		from robofab.ufoLib import makeUFOPath, UFOWriter
		from robofab.interface.all.dialogs import ProgressBar
		if glyphNameToFileNameFunc is None:
			glyphNameToFileNameFunc = self.getGlyphNameToFileNameFunc()
			if glyphNameToFileNameFunc is None:
				from robofab.tools.glyphNameSchemes import glyphNameToShortFileName
				glyphNameToFileNameFunc = glyphNameToShortFileName
		if not path:
			if self.path is None:
				# XXX this should really raise an exception instead
				from robofab.interface.all.dialogs import Message
				Message("Please save this font first before exporting to UFO...")
				return
			else:
				path = makeUFOPath(self.path)
		nonGlyphCount = 4
		bar = None
		if doProgress:
			bar = ProgressBar('Exporting UFO', nonGlyphCount+len(self.glyphs))
		try:
			u = UFOWriter(path)
			u.writeInfo(self.info)
			if bar:
				bar.tick()
			u.writeKerning(self.kerning.asDict())
			if bar:
				bar.tick()
			u.writeGroups(self.groups)
			if bar:
				bar.tick()
			count = nonGlyphCount
			glyphSet = u.getGlyphSet(glyphNameToFileNameFunc)
			glyphOrder = []
			for nakedGlyph in self.naked().glyphs:
				glyph = RGlyph(nakedGlyph)
				glyphOrder.append(glyph.name)
				if doHints:
					hintStuff = _glyphHintsToDict(glyph.naked())
					if hintStuff:
						glyph.lib[postScriptHintDataLibKey] = hintStuff
				glyphSet.writeGlyph(glyph.name, glyph, glyph.drawPoints)
				# remove the hint dict from the lib
				if doHints and glyph.lib.has_key(postScriptHintDataLibKey):
					del glyph.lib[postScriptHintDataLibKey]
				if bar and not count % 10:
					bar.tick(count)
				count = count + 1
			assert None not in glyphOrder, glyphOrder
			glyphSet.writeContents()
			# We make a shallow copy if lib, since we add some stuff for export
			# that doesn't need to be retained in memory.
			fontLib = dict(self.lib)
			# Always export the postscript font hint values
			psh = PostScriptFontHintValues(self)
			d = psh.asDict()
			fontLib[postScriptHintDataLibKey] = d
			# Export the glyph order
			fontLib["org.robofab.glyphOrder"] = glyphOrder
			self._writeOpenTypeFeaturesToLib(fontLib)
			u.writeLib(fontLib)
			if bar:
				bar.tick()
		except KeyboardInterrupt:
			if bar:
				bar.close()
			bar = None
		if bar:
			bar.close()
	
	def _getGlyphOrderFromLib(self, fontLib, glyphSet):
		glyphOrder = fontLib.get("org.robofab.glyphOrder")
		if glyphOrder is not None:
			# no need to keep track if the glyph order in lib once the font is loaded.
			del fontLib["org.robofab.glyphOrder"]
			glyphNames = []
			done = {}
			for glyphName in glyphOrder:
				if glyphName in glyphSet:
					glyphNames.append(glyphName)
					done[glyphName] = 1
			allGlyphNames = glyphSet.keys()
			allGlyphNames.sort()
			for glyphName in allGlyphNames:
				if glyphName not in done:
					glyphNames.append(glyphName)
		else:
			glyphNames = glyphSet.keys()
			# Sort according to unicode would be best, but is really
			# expensive...
			glyphNames.sort()
		return glyphNames
	
	def _readOpenTypeFeaturesFromLib(self, fontLib):
		classes = fontLib.get("org.robofab.opentype.classes")
		if classes is not None:
			del fontLib["org.robofab.opentype.classes"]
			self.naked().ot_classes = classes
		features = fontLib.get("org.robofab.opentype.features")
		if features is not None:
			order = fontLib.get("org.robofab.opentype.featureorder")
			if order is None:
				# for UFOs saved without the feature order, do the same as before.
				order = features.keys()
				order.sort()
			else:
				del fontLib["org.robofab.opentype.featureorder"]
			del fontLib["org.robofab.opentype.features"]
			#features = features.items()
			orderedFeatures = []
			for tag in order:
				oneFeature = features.get(tag)
				if oneFeature is not None:
					orderedFeatures.append((tag, oneFeature))
			self.naked().features.clean()
			for tag, src in orderedFeatures:
				self.naked().features.append(Feature(tag, src))
	
	def readUFO(self, path, doProgress=False, doHints=True):
		"""read a .ufo into the font"""
		from robofab.ufoLib import UFOReader
		from robofab.pens.flPen import FLPointPen
		from robofab.interface.all.dialogs import ProgressBar
		nonGlyphCount = 4
		bar = None
		u = UFOReader(path)
		glyphSet = u.getGlyphSet()
		fontLib = u.readLib()
		glyphNames = self._getGlyphOrderFromLib(fontLib, glyphSet)
		if doProgress:
			bar = ProgressBar('Importing UFO', nonGlyphCount+len(glyphNames))
		try:
			u.readInfo(self.info)
			if bar:
				bar.tick()
			self._readOpenTypeFeaturesFromLib(fontLib)
			self.lib.clear()
			self.lib = fontLib
			if bar:
				bar.tick()
			count = 2
			for glyphName in glyphNames:
				glyph = self.newGlyph(glyphName, clear=True)
				pen = FLPointPen(glyph.naked())
				glyphSet.readGlyph(glyphName=glyphName, glyphObject=glyph, pointPen=pen)
				if doHints:
					hintData = glyph.lib.get(postScriptHintDataLibKey)
					if hintData:
						_dictHintsToGlyph(glyph.naked(), hintData)
					# now that the hints have been extracted from the glyph
					# there is no reason to keep the location in the lib.
					if glyph.lib.has_key(postScriptHintDataLibKey):
						del glyph.lib[postScriptHintDataLibKey]
				glyph.update()
				if bar and not count % 10:
					bar.tick(count)
				count = count + 1
			# import postscript font hint data
			self.psHints._loadFromLib(fontLib)
			self.kerning.clear()
			self.kerning.update(u.readKerning())
			if bar:
				bar.tick()
			self.groups.clear()
			self.groups = u.readGroups()
		except KeyboardInterrupt:
			bar.close()
			bar = None
		if bar:
			bar.close()


class RGlyph(BaseGlyph):
	"""RoboFab wrapper for FL Glyph object"""

	_title = "FLGlyph"

	def __init__(self, flGlyph):
		#BaseGlyph.__init__(self)
		if flGlyph is None:
			raise RoboFabError, "RGlyph: there's nothing to wrap!?"
		self._object = flGlyph
		self._lib = {}
		self._contours = None
		
	def __getitem__(self, index):
		return self.contours[index]
			
	def __delitem__(self, index):
		self._object.DeleteContour(index)
		self._invalidateContours()
	
	def __len__(self):
		return len(self.contours)
		
	lib = property(_get_lib, _set_lib, doc="glyph lib object")
	
	def _invalidateContours(self):
		self._contours = None
	
	def _buildContours(self):
		self._contours = []
		for contourIndex in range(self._object.GetContoursNumber()):
			c = RContour(contourIndex)
			c.setParent(self)
			c._buildSegments()
			self._contours.append(c)
		
	#
	# attribute handlers
	#
	
	def _get_index(self):
		return self._object.parent.FindGlyph(self.name)
	
	index = property(_get_index, doc="return the index of the glyph in the font")
	
	def _get_name(self):
		return self._object.name

	def _set_name(self, value):
		self._object.name = value

	name = property(_get_name, _set_name, doc="name")
	
	def _get_psName(self):
		return self._object.name

	def _set_psName(self, value):
		self._object.name = value

	psName = property(_get_psName, _set_psName, doc="name")
	
	def _get_baseName(self):
		return self._object.name.split('.')[0]
	
	baseName = property(_get_baseName, doc="")
	
	def _get_unicode(self):
		return self._object.unicode

	def _set_unicode(self, value):
		self._object.unicode = value

	unicode = property(_get_unicode, _set_unicode, doc="unicode")
	
	def _get_unicodes(self):
		return self._object.unicodes

	def _set_unicodes(self, value):
		self._object.unicodes = value

	unicodes = property(_get_unicodes, _set_unicodes, doc="unicodes")

	def _get_width(self):
		return self._object.width
	
	def _set_width(self, value):
		value = int(round(value))
		self._object.width = value
		
	width = property(_get_width, _set_width, doc="the width")
	
	def _get_box(self):
		if not len(self.contours) and not len(self.components):
			return (0, 0, 0, 0)
		r = self._object.GetBoundingRect()
		return (int(round(r.ll.x)), int(round(r.ll.y)), int(round(r.ur.x)), int(round(r.ur.y)))
			
	box = property(_get_box, doc="box of glyph as a tuple (xMin, yMin, xMax, yMax)")
	
	def _get_selected(self):
		if fl.Selected(self._object.parent.FindGlyph(self._object.name)):
			return 1
		else:
			return 0
			
	def _set_selected(self, value):
		fl.Select(self._object.name, value)
	
	selected = property(_get_selected, _set_selected, doc="Select or deselect the glyph in the font window")
	
	def _get_mark(self):
		return self._object.mark

	def _set_mark(self, value):
		self._object.mark = value

	mark = property(_get_mark, _set_mark, doc="mark")
	
	def _get_note(self):
		s = self._object.note
		if s is None:
			return s
		return unicode(s, LOCAL_ENCODING)

	def _set_note(self, value):
		if value is None:
			value = ''
		if type(value) == type(u""):
			value = value.encode(LOCAL_ENCODING)
		self._object.note = value

	note = property(_get_note, _set_note, doc="note")
	
	def _get_psHints(self):
		# get an object representing the postscript zone information
		return PostScriptGlyphHintValues(self)
		
	psHints = property(_get_psHints, doc="postscript hint data")
	
	#
	#	necessary evil
	#
			
	def update(self):
		"""Don't forget to update the glyph when you are done."""
		fl.UpdateGlyph(self._object.parent.FindGlyph(self._object.name))
	
	#
	#	methods to make RGlyph compatible with FL.Glyph
	#	##are these still needed?
	#
	
	def GetBoundingRect(self, masterIndex):
		"""FL compatibility"""
		return self._object.GetBoundingRect(masterIndex)
		
	def GetMetrics(self, masterIndex):
		"""FL compatibility"""
		return self._object.GetMetrics(masterIndex)
		
	def SetMetrics(self, value, masterIndex):
		"""FL compatibility"""
		return self._object.SetMetrics(value, masterIndex)
	
	#
	# object builders
	#
	
	def _get_anchors(self):
		return self.getAnchors()
	
	anchors = property(_get_anchors, doc="allow for iteration through glyph.anchors")
		
	def _get_components(self):
		return self.getComponents()
		
	components = property(_get_components, doc="allow for iteration through glyph.components")

	def _get_contours(self):
		if self._contours is None:
			self._buildContours()
		return self._contours
	
	contours = property(_get_contours, doc="allow for iteration through glyph.contours")

	def getAnchors(self):
		"""Return a list of wrapped anchors in this RGlyph."""
		anchors=[]
		for i in range(len(self._object.anchors)):
			a = RAnchor(self._object.anchors[i], i)
			a.setParent(self)
			anchors.append(a)
		return anchors
	
	def getComponents(self):
		"""Return a list of wrapped components in this RGlyph."""
		components=[]
		for i in range(len(self._object.components)):
			c = RComponent(self._object.components[i], i)
			c.setParent(self)
			components.append(c)
		return components
	
	def getVGuides(self):
		"""Return a list of wrapped vertical guides in this RGlyph"""
		vguides=[]
		for i in range(len(self._object.vguides)):
			g = RGuide(self._object.vguides[i], i)
			g.setParent(self)
			vguides.append(g)
		return vguides
	
	def getHGuides(self):
		"""Return a list of wrapped horizontal guides in this RGlyph"""
		hguides=[]
		for i in range(len(self._object.hguides)):
			g = RGuide(self._object.hguides[i], i)
			g.setParent(self)
			hguides.append(g)
		return hguides	
	
	#
	# tools
	#

	def getPointPen(self):
		self._invalidateContours()
		# Now just don't muck with glyph.contours before you're done drawing...
		return FLPointPen(self)

	def appendComponent(self, baseGlyph, offset=(0, 0), scale=(1, 1)):
		"""Append a component to the glyph. x and y are optional offset values"""
		offset = roundPt((offset[0], offset[1]))
		p = FLPointPen(self.naked())
		xx, yy = scale
		dx, dy = offset
		p.addComponent(baseGlyph, (xx, 0, 0, yy, dx, dy))
		
	def appendAnchor(self, name, position):
		"""Append an anchor to the glyph"""
		value = roundPt((position[0], position[1]))
		anchor = Anchor(name, value[0], value[1])
		self._object.anchors.append(anchor)
	
	def appendHGuide(self, position, angle=0):
		"""Append a horizontal guide"""
		position = int(round(position))
		g = Guide(position, angle)
		self._object.hguides.append(g)
		
	def appendVGuide(self, position, angle=0):
		"""Append a horizontal guide"""
		position = int(round(position))
		g = Guide(position, angle)
		self._object.vguides.append(g)
		
	def clearComponents(self):
		"""Clear all components."""
		self._object.components.clean()
	
	def clearAnchors(self):
		"""Clear all anchors."""
		self._object.anchors.clean()
	
	def clearHGuides(self):
		"""Clear all horizontal guides."""
		self._object.hguides.clean()
	
	def clearVGuides(self):
		"""Clear all vertical guides."""
		self._object.vguides.clean()
		
	def removeComponent(self, component):
		"""Remove a specific component from the glyph. This only works
		if the glyph does not have duplicate components in the same location."""
		pos = (component.baseGlyph, component.offset, component.scale)
		a = self.getComponents()
		found = []
		for i in a:
			if (i.baseGlyph, i.offset, i.scale) == pos:
				found.append(i)
		if len(found) > 1:
			raise RoboFabError, 'Found more than one possible component to remove'
		elif len(found) == 1:
			del self._object.components[found[0].index]
		else:
			raise RoboFabError, 'Component does not exist'
	
	def removeContour(self, index):
		"""remove a specific contour  from the glyph"""
		self._object.DeleteContour(index)
		self._invalidateContours()
		
	def removeAnchor(self, anchor):
		"""Remove a specific anchor from the glyph. This only works
		if the glyph does not have anchors with duplicate names
		in exactly the same location with the same mark."""
		pos = (anchor.name, anchor.position, anchor.mark)
		a = self.getAnchors()
		found = []
		for i in a:
			if (i.name, i.position, i.mark) == pos:
				found.append(i)
		if len(found) > 1:
			raise RoboFabError, 'Found more than one possible anchor to remove'
		elif len(found) == 1:
			del self._object.anchors[found[0].index]
		else:
			raise RoboFabError, 'Anchor does not exist'
		
	def removeHGuide(self, guide):
		"""Remove a horizontal guide."""
		pos = (guide.position, guide.angle)
		for g in self.getHGuides():
			if  (g.position, g.angle) == pos:
				del self._object.hguides[g.index]
				break
				
	def removeVGuide(self, guide):
		"""Remove a vertical guide."""
		pos = (guide.position, guide.angle)
		for g in self.getVGuides():
			if  (g.position, g.angle) == pos:
				del self._object.vguides[g.index]
				break

	def center(self, padding=None):
		"""Equalise sidebearings, set to padding if wanted."""
		left = self.leftMargin
		right = self.rightMargin
		if padding:
			e_left = e_right = padding
		else:
			e_left = (left + right)/2
			e_right = (left + right) - e_left
		self.leftMargin= e_left
		self.rightMargin= e_right
		
	def removeOverlap(self):
		"""Remove overlap"""
		self._object.RemoveOverlap()
		self._invalidateContours()
	
	def decompose(self):
		"""Decompose all components"""
		self._object.Decompose()
		self._invalidateContours()
	
	##broken!
	#def removeHints(self):
	#	"""Remove the hints."""
	#	self._object.RemoveHints()
		
	def autoHint(self):
		"""Automatically generate type 1 hints."""
		self._object.Autohint()
		
	def move(self, (x, y), contours=True, components=True, anchors=True):
		"""Move a glyph's items that are flagged as True"""
		x, y = roundPt((x, y))
		self._object.Shift(Point(x, y))
		for c in self.getComponents():
			c.move((x, y))
		for a in self.getAnchors():
			a.move((x, y))
	
	def clear(self, contours=True, components=True, anchors=True, guides=True, hints=True):
		"""Clear all items marked as true from the glyph"""
		if contours:
			self._object.Clear()
			self._invalidateContours()
		if components:
			self._object.components.clean()
		if anchors:
			self._object.anchors.clean()
		if guides:
			self._object.hguides.clean()
			self._object.vguides.clean()
		if hints:
			# RemoveHints requires an "integer mode" argument
			# but it is not documented. from some simple experiments
			# i deduced that
			# 1 = horizontal hints and links,
			# 2 = vertical hints and links
			# 3 = all hints and links
			self._object.RemoveHints(3)
	
	#
	#	special treatment for GlyphMath support in FontLab
	#
	
	def _getMathDestination(self):
		from robofab.objects.objectsRF import RGlyph as _RGlyph
		return _RGlyph()
	
	def copy(self, aParent=None):
		"""Make a copy of this glyph.
		Note: the copy is not a duplicate fontlab glyph, but
		a RF RGlyph with the same outlines. The new glyph is
		not part of the fontlab font in any way. Use font.appendGlyph(glyph)
		to get it in a FontLab glyph again."""
		from robofab.objects.objectsRF import RGlyph as _RGlyph
		newGlyph = _RGlyph()
		newGlyph.appendGlyph(self)
		for attr in GLYPH_COPY_ATTRS:
			value = getattr(self, attr)
			setattr(newGlyph, attr, value)
		# hints
		doHints = False
		parent = self.getParent()
		if parent is not None and parent._supportHints:
			hintStuff = _glyphHintsToDict(self.naked())
			if hintStuff:
				newGlyph.lib[postScriptHintDataLibKey] = hintStuff
		if aParent is not None:
			newGlyph.setParent(aParent)
		elif self.getParent() is not None:
			newGlyph.setParent(self.getParent())
		return newGlyph
	
	def __mul__(self, factor):
		return self.copy() *factor
	
	__rmul__ = __mul__

	def __sub__(self, other):
		return self.copy() - other.copy()
	
	def __add__(self, other):
		return self.copy() + other.copy()
	


class RContour(BaseContour):
	
	"""RoboFab wrapper for non FL contour object"""
		
	_title = "FLContour"
	
	def __init__(self, index):
		self._index = index
		self._parentGlyph = None
		self.segments = []
	
	def __len__(self):
		return len(self.points)
		
	def _buildSegments(self):		
		#######################
		# Notes about FL node contour structure
		#######################
		# for TT curves, FL lists them as seperate nodes:
		#	[move, off, off, off, line, off, off]
		# and, this list is sequential. after the last on curve,
		# it is possible (and likely) that there will be more offCurves
		# in our segment object, these should be associated with the
		# first segment in the contour.
		#
		# for PS curves, it is a very different scenerio.
		# curve nodes contain points:
		#	[on, off, off]
		# and the list is not in sequential order. the first point in
		# the list is the on curve and the subsequent points are the off
		# curve points leading up to that on curve.
		#
		# it is very important to remember these structures when trying
		# to understand the code below
		
		self.segments = []
		offList = []
		nodes = self._nakedParent.nodes
		for index in range(self._nodeLength):
			x = index + self._startNodeIndex
			node = nodes[x]
			# we do have a loose off curve. deal with it.
			if node.type == flOFFCURVE:
				offList.append(x)
			# we are not dealing with a loose off curve
			else:
				s = RSegment(x)
				s.setParent(self)
				# but do we have a collection of loose off curves above?
				# if so, apply them to the segment, and clear the list
				if len(offList) != 0:
					s._looseOffCurve = offList
				offList = []
				self.segments.append(s)
		# do we have some off curves now that the contour is complete?
		if len(offList) != 0:
			# ugh. apply them to the first segment
			self.segments[0]._looseOffCurve = offList
	
	def setParent(self, parentGlyph):
		self._parentGlyph = parentGlyph
		
	def getParent(self):
		return self._parentGlyph
		
	def _get__nakedParent(self):
		return self._parentGlyph.naked()
	
	_nakedParent = property(_get__nakedParent, doc="")
	
	def _get__startNodeIndex(self):
		return self._nakedParent.GetContourBegin(self._index)
	
	_startNodeIndex = property(_get__startNodeIndex, doc="")
	
	def _get__nodeLength(self):
		return self._nakedParent.GetContourLength(self._index)
		
	_nodeLength = property(_get__nodeLength, doc="")

	def _get__lastNodeIndex(self):
		return self._startNodeIndex + self._nodeLength - 1
		
	_lastNodeIndex = property(_get__lastNodeIndex, doc="")

	def _previousNodeIndex(self, index):
		return (index - 1) % self._nodeLength

	def _nextNodeIndex(self, index):
		return (index + 1) % self._nodeLength
	
	def _getNode(self, index):
		return self._nodes[index]
	
	def _get__nodes(self):
		nodes = []
		for node in self._nakedParent.nodes[self._startNodeIndex:self._startNodeIndex+self._nodeLength-1]:
			nodes.append(node)
		return nodes
	
	_nodes = property(_get__nodes, doc="")

	def _get_points(self):
		points = []
		for segment in self.segments:
			for point in segment.points:
				points.append(point)
		return points
		
	points = property(_get_points, doc="")

	def _get_bPoints(self):
		bPoints = []
		for segment in self.segments:
			bp = RBPoint(segment.index)
			bp.setParent(self)
			bPoints.append(bp)
		return bPoints
		
	bPoints = property(_get_bPoints, doc="")
	
	def _get_index(self):
		return self._index

	def _set_index(self, index):
		if index != self._index:
			self._nakedParent.ReorderContour(self._index, index)
			# reorder and set the _index of the existing RContour objects
			# this will be a better solution than reconstructing all the objects
			# segment objects will still, sadly, have to be reconstructed
			contourList = self.getParent().contours
			contourList.insert(index, contourList.pop(self._index))
			for i in range(len(contourList)):
				contourList[i]._index = i
				contourList[i]._buildSegments()
		
	
	index = property(_get_index, _set_index, doc="the index of the contour")

	def _get_selected(self):
		selected = 0
		nodes = self._nodes
		for node in nodes:
			if node.selected == 1:
				selected = 1
				break
		return selected
		
	def _set_selected(self, value):
		if value == 1:
			self._nakedParent.SelectContour(self._index)
		else:
			for node in self._nodes:
				node.selected = value

	selected = property(_get_selected, _set_selected, doc="selection of the contour: 1-selected or 0-unselected")

	def appendSegment(self, segmentType, points, smooth=False):
		segment = self.insertSegment(index=self._nodeLength, segmentType=segmentType, points=points, smooth=smooth)
		return segment
		
	def insertSegment(self, index, segmentType, points, smooth=False):
		"""insert a seggment into the contour"""
		# do a  qcurve insertion
		if segmentType == QCURVE:
			count = 0
			for point in points[:-1]:
				newNode = Node(flOFFCURVE, Point(point[0], point[1]))
				self._nakedParent.Insert(newNode, self._startNodeIndex + index + count)
				count = count + 1
			newNode = Node(flLINE, Point(points[-1][0], points[-1][1]))
			self._nakedParent.Insert(newNode, self._startNodeIndex + index +len(points) - 1)
		# do a regular insertion
		else:	
			onX, onY = points[-1]
			newNode = Node(_rfToFLSegmentType(segmentType), Point(onX, onY))
			# fix the off curves in case the user is inserting a curve
			# but is not specifying off curve points
			if segmentType == CURVE and len(points) == 1:
				pSeg = self._prevSegment(index)
				pOn = pSeg.onCurve
				newNode.points[1].Assign(Point(pOn.x, pOn.y))
				newNode.points[2].Assign(Point(onX, onY))
			for pointIndex in range(len(points[:-1])):
				x, y = points[pointIndex]
				newNode.points[1 + pointIndex].Assign(Point(x, y))
			if smooth:
				node.alignment = flSMOOTH
			self._nakedParent.Insert(newNode, self._startNodeIndex + index)
		self._buildSegments()
		return self.segments[index]
		
	def removeSegment(self, index):
		"""remove a segment from the contour"""
		segment = self.segments[index]
		# we have a qcurve. umph.
		if segment.type == QCURVE:
			indexList = [segment._nodeIndex] + segment._looseOffCurve
			indexList.sort()
			indexList.reverse()
			parent = self._nakedParent
			for nodeIndex in indexList:
				parent.DeleteNode(nodeIndex)
		# we have a more sane structure to follow
		else:
			# store some info for later
			next = self._nextSegment(index)
			nextOffA = None
			nextOffB = None
			nextType = next.type
			if nextType != LINE and nextType != MOVE:
				pA = next.offCurve[0]
				nextOffA = (pA.x, pA.y)
				pB = next.offCurve[-1]
				nextOffB = (pB.x, pB.y)
			nodeIndex = segment._nodeIndex
			self._nakedParent.DeleteNode(nodeIndex)
			self._buildSegments()
			# now we must override FL guessing about offCurves
			next = self._nextSegment(index - 1)
			nextType = next.type
			if nextType != LINE and nextType != MOVE:
				pA = next.offCurve[0]
				pB = next.offCurve[-1]
				pA.x, pA.y = nextOffA
				pB.x, pB.y = nextOffB
		
	def reverseContour(self):
		"""reverse contour direction"""
		self._nakedParent.ReverseContour(self._index)
		self._buildSegments()
			
	def setStartSegment(self, segmentIndex):
		"""set the first node on the contour"""
		self._nakedParent.SetStartNode(self._startNodeIndex + segmentIndex)
		self.getParent()._invalidateContours()
		self.getParent()._buildContours()

	def copy(self, aParent=None):
		"""Copy this object -- result is an ObjectsRF flavored object.
		There is no way to make this work using FontLab objects.
		Copy is mainly used for glyphmath.
		"""
		raise RoboFabError, "copy() for objectsFL.RContour is not implemented."
		


class RSegment(BaseSegment):
	
	_title = "FLSegment"
	
	def __init__(self, flNodeIndex):
		BaseSegment.__init__(self)
		self._nodeIndex = flNodeIndex
		self._looseOffCurve = []	#a list of indexes to loose off curve nodes
	
	def _get__node(self):
		glyph = self.getParent()._nakedParent
		return glyph.nodes[self._nodeIndex]
	
	_node = property(_get__node, doc="")
	
	def _get_qOffCurve(self):
		nodes = self.getParent()._nakedParent.nodes
		off = []
		for x in self._looseOffCurve:
			off.append(nodes[x])
		return off
		
	_qOffCurve = property(_get_qOffCurve, doc="free floating off curve nodes in the segment")

	def _get_index(self):
		contour = self.getParent()
		return self._nodeIndex - contour._startNodeIndex
		
	index = property(_get_index, doc="")
	
	def _isQCurve(self):
		# loose off curves only appear in q curves
		if len(self._looseOffCurve) != 0:
			return True
		return False

	def _get_type(self):
		if self._isQCurve():
			return QCURVE
		return _flToRFSegmentType(self._node.type)
	
	def _set_type(self, segmentType):
		if self._isQCurve():
			raise RoboFabError, 'qcurve point types cannot be changed'
		oldNode = self._node
		oldType = oldNode.type
		oldPointType = _flToRFSegmentType(oldType)
		if oldPointType == MOVE:
			raise RoboFabError, '%s point types cannot be changed'%oldPointType
		if segmentType == MOVE or segmentType == OFFCURVE:
			raise RoboFabError, '%s point types cannot be assigned'%oldPointType
		if oldPointType == segmentType:
			return
		oldNode.type = _rfToFLSegmentType(segmentType)
		
	type = property(_get_type, _set_type, doc="")
			
	def _get_smooth(self):
		alignment = self._node.alignment
		if alignment == flSMOOTH or alignment == flFIXED:
			return True
		return False
	
	def _set_smooth(self, value):
		if value:
			self._node.alignment = flSMOOTH
		else:
			self._node.alignment = flSHARP
		
	smooth = property(_get_smooth, _set_smooth, doc="")

	def _get_points(self):
		points = []
		node = self._node
		# gather the off curves
		#
		# are we dealing with a qCurve? ugh.
		# gather the loose off curves
		if self._isQCurve():
			off = self._qOffCurve
			x = 0
			for n in off:
				p = RPoint(0)
				p.setParent(self)
				p._qOffIndex = x
				points.append(p)
				x = x + 1
		# otherwise get the points associated with the node
		else:
			index = 1
			for point in node.points[1:]:
				p = RPoint(index)
				p.setParent(self)
				points.append(p)
				index = index + 1
		# the last point should always be the on curve
		p = RPoint(0)
		p.setParent(self)
		points.append(p)
		return points
		
	points = property(_get_points, doc="")

	def _get_selected(self):
		return self._node.selected
	
	def _set_selected(self, value):
		self._node.selected = value
	
	selected = property(_get_selected, _set_selected, doc="")

	def move(self, (x, y)):
		x, y = roundPt((x, y))
		self._node.Shift(Point(x, y))
		if self._isQCurve():
			qOff = self._qOffCurve
			for node in qOff:
				node.Shift(Point(x, y))

	def copy(self, aParent=None):
		"""Copy this object -- result is an ObjectsRF flavored object.
		There is no way to make this work using FontLab objects.
		Copy is mainly used for glyphmath.
		"""
		raise RoboFabError, "copy() for objectsFL.RSegment is not implemented."

		

class RPoint(BasePoint):
				
	_title = "FLPoint"
	
	def __init__(self, pointIndex):
		#BasePoint.__init__(self)
		self._pointIndex = pointIndex
		self._qOffIndex = None
		
	def _get__parentGlyph(self):
		return self._parentContour.getParent()
	
	_parentGlyph = property(_get__parentGlyph, doc="")

	def _get__parentContour(self):
		return self._parentSegment.getParent()
		
	_parentContour = property(_get__parentContour, doc="")

	def _get__parentSegment(self):
		return self.getParent()
	
	_parentSegment = property(_get__parentSegment, doc="")

	def _get__node(self):
		if self._qOffIndex is not None:
			return self.getParent()._qOffCurve[self._qOffIndex]
		return self.getParent()._node
	
	_node = property(_get__node, doc="")

	def _get__point(self):
		return self._node.points[self._pointIndex]

	_point = property(_get__point, doc="")

	def _get_x(self):
		return self._point.x
		
	def _set_x(self, value):
		value = int(round(value))
		self._point.x = value
	
	x = property(_get_x, _set_x, doc="")

	def _get_y(self):
		return self._point.y
	
	def _set_y(self, value):
		value = int(round(value))
		self._point.y = value

	y = property(_get_y, _set_y, doc="")

	def _get_type(self):
		if self._pointIndex == 0:
			# FL store quad contour data as a list of off curves and lines
			# (see note in RContour._buildSegments). So, we need to do
			# a bit of trickery to return a decent point type.
			# if the straight FL node type is off curve, it is a loose
			# quad off curve. return that.
			tp = _flToRFSegmentType(self._node.type)
			if tp == OFFCURVE:
				return OFFCURVE
			# otherwise we are dealing with an on curve. in this case,
			# we attempt to get the parent segment type and return it.
			segment = self.getParent()
			if segment is not None:
				return segment.type
			# we must not have a segment, fall back to straight conversion
			return tp
		return OFFCURVE
	
	type = property(_get_type, doc="")
	
	def _set_selected(self, value):
		if self._pointIndex == 0:
			self._node.selected = value
	
	def _get_selected(self):
		if self._pointIndex == 0:
			return self._node.selected
		return False
		
	selected = property(_get_selected, _set_selected, doc="")

	def move(self, (x, y)):
		x, y = roundPt((x, y))
		self._point.Shift(Point(x, y))
	
	def scale(self, (x, y), center=(0, 0)):
		centerX, centerY = roundPt(center)
		point = self._point
		point.x, point.y = _scalePointFromCenter((point.x, point.y), (x, y), (centerX, centerY))
	
	def copy(self, aParent=None):
		"""Copy this object -- result is an ObjectsRF flavored object.
		There is no way to make this work using FontLab objects.
		Copy is mainly used for glyphmath.
		"""
		raise RoboFabError, "copy() for objectsFL.RPoint is not implemented."
		

class RBPoint(BaseBPoint):
	
	_title = "FLBPoint"
	
	def __init__(self, segmentIndex):
		#BaseBPoint.__init__(self)
		self._segmentIndex = segmentIndex
		
	def _get__parentSegment(self):
		return self.getParent().segments[self._segmentIndex]
	
	_parentSegment = property(_get__parentSegment, doc="")
	
	def _get_index(self):
		return self._segmentIndex
	
	index = property(_get_index, doc="")
	
	def _get_selected(self):
		return self._parentSegment.selected
	
	def _set_selected(self, value):
		self._parentSegment.selected = value
		
	selected = property(_get_selected, _set_selected, doc="")

	def copy(self, aParent=None):
		"""Copy this object -- result is an ObjectsRF flavored object.
		There is no way to make this work using FontLab objects.
		Copy is mainly used for glyphmath.
		"""
		raise RoboFabError, "copy() for objectsFL.RBPoint is not implemented."
			
		
class RComponent(BaseComponent):
	
	"""RoboFab wrapper for FL Component object"""

	_title = "FLComponent"

	def __init__(self, flComponent, index):
		BaseComponent.__init__(self)
		self._object =  flComponent
		self._index=index
		
	def _get_index(self):
		return self._index
		
	index = property(_get_index, doc="index of component")

	def _get_baseGlyph(self):
		return self._object.parent.parent[self._object.index].name
		
	baseGlyph = property(_get_baseGlyph, doc="")

	def _get_offset(self):
		return (int(self._object.delta.x), int(self._object.delta.y))
	
	def _set_offset(self, value):
		value = roundPt((value[0], value[1]))
		self._object.delta=Point(value[0], value[1])
		
	offset = property(_get_offset, _set_offset, doc="the offset of the component")

	def _get_scale(self):
		return (self._object.scale.x, self._object.scale.y)
	
	def _set_scale(self, (x, y)):
		self._object.scale=Point(x, y)
		
	scale = property(_get_scale, _set_scale, doc="the scale of the component")

	def move(self, (x, y)):
		"""Move the component"""
		x, y = roundPt((x, y))
		self._object.delta=Point(self._object.delta.x+x, self._object.delta.y+y)
	
	def decompose(self):
		"""Decompose the component"""
		self._object.Paste()

	def copy(self, aParent=None):
		"""Copy this object -- result is an ObjectsRF flavored object.
		There is no way to make this work using FontLab objects.
		Copy is mainly used for glyphmath.
		"""
		raise RoboFabError, "copy() for objectsFL.RComponent is not implemented."
		


class RAnchor(BaseAnchor):
	"""RoboFab wrapper for FL Anchor object"""

	_title = "FLAnchor"

	def __init__(self, flAnchor, index):
		BaseAnchor.__init__(self)
		self._object =  flAnchor
		self._index = index
	
	def _get_y(self):
		return self._object.y

	def _set_y(self, value):
		self._object.y = int(round(value))

	y = property(_get_y, _set_y, doc="y")
	
	def _get_x(self):
		return self._object.x

	def _set_x(self, value):
		self._object.x = int(round(value))

	x = property(_get_x, _set_x, doc="x")
	
	def _get_name(self):
		return self._object.name

	def _set_name(self, value):
		self._object.name = value

	name = property(_get_name, _set_name, doc="name")
	
	def _get_mark(self):
		return self._object.mark

	def _set_mark(self, value):
		self._object.mark = value

	mark = property(_get_mark, _set_mark, doc="mark")
	
	def _get_index(self):
		return self._index
		
	index = property(_get_index, doc="index of the anchor")

	def _get_position(self):
		return (self._object.x, self._object.y)
		
	def _set_position(self, value):
		value = roundPt((value[0], value[1]))
		self._object.x=value[0]
		self._object.y=value[1]

	position = property(_get_position, _set_position, doc="position of the anchor")



class RGuide(BaseGuide):
	
	"""RoboFab wrapper for FL Guide object"""

	_title = "FLGuide"

	def __init__(self, flGuide, index):
		BaseGuide.__init__(self)
		self._object = flGuide
		self._index = index
		
	def __repr__(self):
		# this is a doozy!
		parent = "unknown_parent"
		parentObject = self.getParent()
		if parentObject is not None:
			# do we have a font?
			try:
				parent = parentObject.info.fullName
			except AttributeError:
				# or do we have a glyph?
				try:
					parent = parentObject.name
				# we must be an orphan
				except AttributeError: pass
		return "<Robofab guide wrapper for %s>"%parent
		
	def _get_position(self):
		return self._object.position

	def _set_position(self, value):
		self._object.position = value

	position = property(_get_position, _set_position, doc="position")
	
	def _get_angle(self):
		return self._object.angle

	def _set_angle(self, value):
		self._object.angle = value

	angle = property(_get_angle, _set_angle, doc="angle")
	
	def _get_index(self):
		return self._index

	index = property(_get_index, doc="index of the guide")
	

class RGroups(BaseGroups):
	
	"""RoboFab wrapper for FL group data"""
	
	_title = "FLGroups"
	
	def __init__(self, aDict):
		self.update(aDict)
	
	def __setitem__(self, key, value):
		# override baseclass so that data is stored in FL classes
		if not isinstance(key, str):
			raise RoboFabError, 'key must be a string'
		if not isinstance(value, list):
			raise RoboFabError, 'group must be a list'
		super(RGroups, self).__setitem__(key, value)
		self._setFLGroups()
			
	def __delitem__(self, key):
		# override baseclass so that data is stored in FL classes
		super(RGroups, self).__delitem__(key, value)
		self._setFLGroups()
		
	def _setFLGroups(self):
		# set the group data into the font.
		if self.getParent() is not None:
			groups = []
			for i in self.keys():
				value = ' '.join(self[i])
				groups.append(': '.join([i, value]))
			groups.sort()
			self.getParent().naked().classes = groups
	
	def update(self, aDict):
		# override baseclass so that data is stored in FL classes
		super(RGroups, self).update(aDict)
		self._setFLGroups()

	def clear(self):
		# override baseclass so that data is stored in FL classes
		super(RGroups, self).clear()
		self._setFLGroups()
			
	def pop(self, key):
		# override baseclass so that data is stored in FL classes
		i = super(RGroups, self).pop(key)
		self._setFLGroups()
		return i
		
	def popitem(self):
		# override baseclass so that data is stored in FL classes
		i = super(RGroups, self).popitem()
		self._setFLGroups()
		return i
	
	def setdefault(self, key, value=None):
		# override baseclass so that data is stored in FL classes
		i = super(RGroups, self).setdefault(key, value)
		self._setFLGroups()
		return i


class RKerning(BaseKerning):
	
	"""RoboFab wrapper for FL Kerning data"""
	
	_title = "FLKerning"

	def __setitem__(self, pair, value):
		if not isinstance(pair, tuple):
			raise RoboFabError, 'kerning pair must be a tuple: (left, right)'
		else:
			if len(pair) != 2:
				raise RoboFabError, 'kerning pair must be a tuple: (left, right)'
			else:
				if value == 0:
					if self._kerning.get(pair) is not None:
						#see note about setting kerning values to 0 below
						self._setFLKerning(pair, 0)
						del self._kerning[pair]
				else:
					#self._kerning[pair] = value
					self._setFLKerning(pair, value)
					
	def _setFLKerning(self, pair, value):
		# write a pair back into the font
		#
		# this is fairly speedy, but setting a pair to 0 is roughly
		# 2-3 times slower than setting a real value. this is because
		# of all the hoops that must be jumped through to keep FL
		# from storing kerning pairs with a value of 0.
		parentFont = self.getParent().naked()
		left = parentFont[pair[0]]
		right = parentFont.FindGlyph(pair[1])
		# the left glyph doesn not exist
		if left is None:
			return
		# the right glyph doesn not exist
		if right == -1:
			return
		self._kerning[pair] = value
		leftName = pair[0]
		value = int(round(value))
		# pairs set to 0 need to be handled carefully. FL will allow
		# for pairs to have a value of 0 (!?), so we must catch them
		# when they pop up and make sure that the pair is actually
		# removed from the font.
		if value == 0:
			foundPair = False
			# if the value is 0, we don't need to construct a pair
			# we just need to make sure that the pair is not in the list
			pairs = []
			# so, go through all the pairs and add them to a new list
			for flPair in left.kerning:
				# we have found the pair. flag it.
				if flPair.key == right:
					foundPair = True
				# not the pair. add it to the list.
				else:
					pairs.append((flPair.key, flPair.value))
			# if we found it, write it back to the glyph.
			if foundPair:
				left.kerning = []
				for p in pairs:
					new = KerningPair(p[0], p[1])
					left.kerning.append(new)
		else:
			# non-zero pairs are a bit easier to handle
			# we just need to look to see if the pair exists
			# if so, change the value and stop the loop.
			# if not, add a new pair to the glyph
			self._kerning[pair] = value
			foundPair = False
			for flPair in left.kerning:
				if flPair.key == right:
					flPair.value = value
					foundPair = True
					break
			if not foundPair:
				p = KerningPair(right, value)
				left.kerning.append(p)
		
	def update(self, kerningDict):
		"""replace kerning data with the data in the given kerningDict"""
		# override base class here for speed
		parentFont = self.getParent().naked()
		# add existing data to the new kerning dict is not being replaced
		for pair in self.keys():
			if not kerningDict.has_key(pair):
				kerningDict[pair] = self._kerning[pair]
		# now clear the existing kerning to make sure that
		# all the kerning in residing in the glyphs is gone
		self.clear()
		self._kerning = kerningDict
		kDict = {}
		# nest the pairs into a dict keyed by the left glyph
		# {'A':{'A':-10, 'B':20, ...}, 'B':{...}, ...}
		for left, right in kerningDict.keys():
			value = kerningDict[left, right]
			if not left in kDict:
				kDict[left] = {}
			kDict[left][right] = value
		for left in kDict.keys():
			leftGlyph = parentFont[left]
			if leftGlyph is not None:
				for right in kDict[left].keys():
					value = kDict[left][right]
					if value != 0:
						rightIndex = parentFont.FindGlyph(right)
						if rightIndex != -1:
							p = KerningPair(rightIndex, value)
							leftGlyph.kerning.append(p)
				
	def clear(self):
		"""clear all kerning"""
		# override base class here for speed
		self._kerning = {}
		for glyph in self.getParent().naked().glyphs:
			glyph.kerning = []

	def __add__(self, other):
		"""Math operations on FL Kerning objects return RF Kerning objects
		as they need to be orphaned objects and FL can't deal with that."""
		from sets import Set
		from robofab.objects.objectsRF import RKerning as _RKerning
		new = _RKerning()
		k = Set(self.keys()) | Set(other.keys())
		for key in k:
			new[key] = self.get(key, 0) + other.get(key, 0)
		return new
	
	def __sub__(self, other):
		"""Math operations on FL Kerning objects return RF Kerning objects
		as they need to be orphaned objects and FL can't deal with that."""
		from sets import Set
		from robofab.objects.objectsRF import RKerning as _RKerning
		new = _RKerning()
		k = Set(self.keys()) | Set(other.keys())
		for key in k:
			new[key] = self.get(key, 0) - other.get(key, 0)
		return new

	def __mul__(self, factor):
		"""Math operations on FL Kerning objects return RF Kerning objects
		as they need to be orphaned objects and FL can't deal with that."""
		from robofab.objects.objectsRF import RKerning as _RKerning
		new = _RKerning()
		for name, value in self.items():
			new[name] = value * factor
		return new
	
	__rmul__ = __mul__

	def __div__(self, factor):
		"""Math operations on FL Kerning objects return RF Kerning objects
		as they need to be orphaned objects and FL can't deal with that."""
		if factor == 0:
			raise ZeroDivisionError
		return self.__mul__(1.0/factor)
			

class RLib(BaseLib):
	
	"""RoboFab wrapper for FL lib"""
	
	# XXX: As of FL 4.6 the customdata field in glyph objects is busted.
	# storing anything there causes the glyph to become uneditable.
	# however, the customdata field in font objects is stable.
	
	def __init__(self, aDict):
		self.update(aDict)
		
	def __setitem__(self, key, value):
		# override baseclass so that data is stored in customdata field
		super(RLib, self).__setitem__(key, value)
		self._stashLib()
			
	def __delitem__(self, key):
		# override baseclass so that data is stored in customdata field
		super(RLib, self).__delitem__(key)
		self._stashLib()
		
	def _stashLib(self):
		# write the plist into the customdata field of the FL object
		if self.getParent() is None:
			return
		if not self:
			data = None
		elif len(self) == 1 and "org.robofab.fontlab.customdata" in self:
			data = self["org.robofab.fontlab.customdata"].data
		else:
			f = StringIO()
			writePlist(self, f)
			data = f.getvalue()
			f.close()
		parent = self.getParent()
		parent.naked().customdata = data
	
	def update(self, aDict):
		# override baseclass so that data is stored in customdata field
		super(RLib, self).update(aDict)
		self._stashLib()

	def clear(self):
		# override baseclass so that data is stored in customdata field
		super(RLib, self).clear()
		self._stashLib()
			
	def pop(self, key):
		# override baseclass so that data is stored in customdata field
		i = super(RLib, self).pop(key)
		self._stashLib()
		return i
		
	def popitem(self):
		# override baseclass so that data is stored in customdata field
		i = super(RLib, self).popitem()
		self._stashLib()
		return i
	
	def setdefault(self, key, value=None):
		# override baseclass so that data is stored in customdata field
		i = super(RLib, self).setdefault(key, value)
		self._stashLib()
		return i

			
class RInfo(BaseInfo):
	
	"""RoboFab wrapper for FL Font Info"""
	
	_title = "FLInfo"
	
	def __init__(self, font):
		BaseInfo.__init__(self)
		self._object = font
	
	def _get_familyName(self):
		return self._object.family_name

	def _set_familyName(self, value):
		self._object.family_name = value

	familyName = property(_get_familyName, _set_familyName, doc="family_name")
	
	def _get_styleName(self):
		return self._object.style_name

	def _set_styleName(self, value):
		self._object.style_name = value

	styleName = property(_get_styleName, _set_styleName, doc="style_name")
	
	def _get_fullName(self):
		return self._object.full_name

	def _set_fullName(self, value):
		self._object.full_name = value

	fullName = property(_get_fullName, _set_fullName, doc="full_name")
	
	def _get_fontName(self):
		return self._object.font_name

	def _set_fontName(self, value):
		self._object.font_name = value

	fontName = property(_get_fontName, _set_fontName, doc="font_name")
	
	def _get_menuName(self):
		return self._object.menu_name

	def _set_menuName(self, value):
		self._object.menu_name = value

	menuName = property(_get_menuName, _set_menuName, doc="menu_name")

	def _get_fondName(self):
		return self._object.apple_name

	def _set_fondName(self, value):
		self._object.apple_name = value

	fondName = property(_get_fondName, _set_fondName, doc="apple_name")
	
	def _get_otFamilyName(self):
		return self._object.pref_family_name

	def _set_otFamilyName(self, value):
		self._object.pref_family_name = value

	otFamilyName = property(_get_otFamilyName, _set_otFamilyName, doc="pref_family_name")

	def _get_otStyleName(self):
		return self._object.pref_style_name

	def _set_otStyleName(self, value):
		self._object.pref_style_name = value

	otStyleName = property(_get_otStyleName, _set_otStyleName, doc="pref_style_name")
	
	def _get_otMacName(self):
		return self._object.mac_compatible

	def _set_otMacName(self, value):
		self._object.mac_compatible = value

	otMacName = property(_get_otMacName, _set_otMacName, doc="mac_compatible")
	
	def _get_weightValue(self):
		return self._object.weight_code
	
	def _set_weightValue(self, value):
		value = int(round(value))	# FL can't take float - 28/8/07 / evb
		self._object.weight_code = value
	
	weightValue = property(_get_weightValue, _set_weightValue, doc="weight value")
	
	def _get_weightName(self):
		return self._object.weight
	
	def _set_weightName(self, value):
		self._object.weight = value
	
	weightName = property(_get_weightName, _set_weightName, doc="weight name")
	
	def _get_widthName(self):
		return self._object.width
	
	def _set_widthName(self, value):
		self._object.width = value
	
	widthName = property(_get_widthName, _set_widthName, doc="width name")

	def _get_fontStyle(self):
		return self._object.font_style

	def _set_fontStyle(self, value):
		self._object.font_style = value

	fontStyle = property(_get_fontStyle, _set_fontStyle, doc="font_style")
	
	def _get_msCharSet(self):
		return self._object.ms_charset

	def _set_msCharSet(self, value):
		self._object.ms_charset = value

	msCharSet = property(_get_msCharSet, _set_msCharSet, doc="ms_charset")
	
	def _get_fondID(self):
		return self._object.fond_id

	def _set_fondID(self, value):
		self._object.fond_id = value

	fondID = property(_get_fondID, _set_fondID, doc="fond_id")
	
	def _get_uniqueID(self):
		return self._object.unique_id

	def _set_uniqueID(self, value):
		self._object.unique_id = value

	uniqueID = property(_get_uniqueID, _set_uniqueID, doc="unique_id")
	
	def _get_versionMajor(self):
		return self._object.version_major

	def _set_versionMajor(self, value):
		self._object.version_major = value

	versionMajor = property(_get_versionMajor, _set_versionMajor, doc="version_major")
	
	def _get_versionMinor(self):
		return self._object.version_minor

	def _set_versionMinor(self, value):
		self._object.version_minor = value

	versionMinor = property(_get_versionMinor, _set_versionMinor, doc="version_minor")
	
	def _get_year(self):
		return self._object.year

	def _set_year(self, value):
		self._object.year = value

	year = property(_get_year, _set_year, doc="year")
	
	def _get_note(self):
		s = self._object.note
		if s is None:
			return s
		return unicode(s, LOCAL_ENCODING)

	def _set_note(self, value):
		if value is not None:
			value = value.encode(LOCAL_ENCODING)
		self._object.note = value

	note = property(_get_note, _set_note, doc="note")
	
	def _get_copyright(self):
		s = self._object.copyright
		if s is None:
			return s
		return unicode(s, LOCAL_ENCODING)

	def _set_copyright(self, value):
		if value is not None:
			value = value.encode(LOCAL_ENCODING)
		self._object.copyright = value

	copyright = property(_get_copyright, _set_copyright, doc="copyright")
	
	def _get_notice(self):
		s = self._object.notice
		if s is None:
			return s
		return unicode(s, LOCAL_ENCODING)

	def _set_notice(self, value):
		if value is not None:
			value = value.encode(LOCAL_ENCODING)
		self._object.notice = value

	notice = property(_get_notice, _set_notice, doc="notice")
	
	def _get_trademark(self):
		s = self._object.trademark
		if s is None:
			return s
		return unicode(s, LOCAL_ENCODING)

	def _set_trademark(self, value):
		if value is not None:
			value = value.encode(LOCAL_ENCODING)
		self._object.trademark = value

	trademark = property(_get_trademark, _set_trademark, doc="trademark")
	
	def _get_license(self):
		s = self._object.license
		if s is None:
			return s
		return unicode(s, LOCAL_ENCODING)

	def _set_license(self, value):
		if value is not None:
			value = value.encode(LOCAL_ENCODING)
		self._object.license = value

	license = property(_get_license, _set_license, doc="license")
	
	def _get_licenseURL(self):
		return self._object.license_url

	def _set_licenseURL(self, value):
		self._object.license_url = value

	licenseURL = property(_get_licenseURL, _set_licenseURL, doc="license_url")
	
	def _get_createdBy(self):
		s = self._object.source
		if s is None:
			return s
		return unicode(s, LOCAL_ENCODING)

	def _set_createdBy(self, value):
		if value is not None:
			value = value.encode(LOCAL_ENCODING)
		self._object.source = value

	createdBy = property(_get_createdBy, _set_createdBy, doc="source")
	
	def _get_designer(self):
		s = self._object.designer
		if s is None:
			return s
		return unicode(s, LOCAL_ENCODING)

	def _set_designer(self, value):
		if value is not None:
			value = value.encode(LOCAL_ENCODING)
		self._object.designer = value

	designer = property(_get_designer, _set_designer, doc="designer")
	
	def _get_designerURL(self):
		return self._object.designer_url

	def _set_designerURL(self, value):
		self._object.designer_url = value

	designerURL = property(_get_designerURL, _set_designerURL, doc="designer_url")
	
	def _get_vendorURL(self):
		return self._object.vendor_url

	def _set_vendorURL(self, value):
		self._object.vendor_url = value

	vendorURL = property(_get_vendorURL, _set_vendorURL, doc="vendor_url")
	
	def _get_ttVendor(self):
		return self._object.vendor

	def _set_ttVendor(self, value):
		self._object.vendor = value

	ttVendor = property(_get_ttVendor, _set_ttVendor, doc="vendor")
	
	def _get_ttUniqueID(self):
		return self._object.tt_u_id

	def _set_ttUniqueID(self, value):
		self._object.tt_u_id = value

	ttUniqueID = property(_get_ttUniqueID, _set_ttUniqueID, doc="tt_u_id")
	
	def _get_ttVersion(self):
		return self._object.tt_version

	def _set_ttVersion(self, value):
		self._object.tt_version = value

	ttVersion = property(_get_ttVersion, _set_ttVersion, doc="tt_version")
	
	def _get_unitsPerEm(self):
		return self._object.upm
		
	def _set_unitsPerEm(self, value):
		self._object.upm = int(round(value))

	unitsPerEm = property(_get_unitsPerEm, _set_unitsPerEm, doc="")
	
	def _get_ascender(self):
		return self._object.ascender[0]
	
	def _set_ascender(self, value):
		value = int(round(value))
		self._object.ascender[0] = value
	
	ascender = property(_get_ascender, _set_ascender, doc="ascender value")

	def _get_descender(self):
		return self._object.descender[0]
	
	def _set_descender(self, value):
		value = int(round(value))
		self._object.descender[0] = value
		
	descender = property(_get_descender, _set_descender, doc="descender value")
	
	def _get_capHeight(self):
		return self._object.cap_height[0]
	
	def _set_capHeight(self, value):
		value = int(round(value))
		self._object.cap_height[0] = value
		
	capHeight = property(_get_capHeight, _set_capHeight, doc="cap height value")

	def _get_xHeight(self):
		return self._object.x_height[0]
		
	def _set_xHeight(self, value):
		value = int(round(value))
		self._object.x_height[0] = value
		
	xHeight = property(_get_xHeight, _set_xHeight, doc="x height value")

	def _get_defaultWidth(self):
		return self._object.default_width[0]
	
	def _set_defaultWidth(self, value):
		value = int(round(value))
		self._object.default_width[0] = value	

	defaultWidth = property(_get_defaultWidth, _set_defaultWidth, doc="default width value")
	
	def _get_italicAngle(self):
		return self._object.italic_angle

	def _set_italicAngle(self, value):
		try:
			self._object.italic_angle = float(value)
		except TypeError:
			print "robofab.objects.objectsFL: can't set italic angle, possibly a FontLab API limitation"

	italicAngle = property(_get_italicAngle, _set_italicAngle, doc="italic_angle")
	
	def _get_slantAngle(self):
		return self._object.slant_angle

	def _set_slantAngle(self, value):
		try:
			self._object.slant_angle = float(value)
		except TypeError:
			print "robofab.objects.objectsFL: can't set slant angle, possibly a FontLab API limitation"

	slantAngle = property(_get_slantAngle, _set_slantAngle, doc="slant_angle")
	
	#is this still needed?
	def _get_full_name(self):
		return self._object.full_name

	def _set_full_name(self, value):
		self._object.full_name = value

	full_name = property(_get_full_name, _set_full_name, doc="FL: full_name")
	
	#is this still needed?
	def _get_ms_charset(self):
		return self._object.ms_charset

	def _set_ms_charset(self, value):
		self._object.ms_charset = value

	ms_charset = property(_get_ms_charset, _set_ms_charset, doc="FL: ms_charset")
