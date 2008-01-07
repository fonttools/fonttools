"""A collection of non-environment specific tools"""


import sys
import os
from robofab.objects.objectsRF import RInfo

if sys.platform == "darwin" and sys.version_info[:3] == (2, 2, 0):
	# the Mac support of Jaguar's Python 2.2 is broken
	have_broken_macsupport = 1
else:
	have_broken_macsupport = 0


import robofab
from robofab.plistlib import readPlist, writePlist

def readFoundrySettings(dstPath):
	"""read the foundry settings xml file and return a keyed dict."""
	fileName = os.path.basename(dstPath)
	if not os.path.exists(dstPath):
		import shutil
		# hm -- a fresh install, make a new default settings file
		print "RoboFab: creating a new foundry settings file at", dstPath
		srcDir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(robofab.__file__))), 'Data')
		srcPath = os.path.join(srcDir, 'template_' + fileName)
		shutil.copy(srcPath, dstPath)
	return readPlist(dstPath)

def getFoundrySetting(key, path):
	"""get a specific setting from the foundry settings xml file."""
	d = readFoundrySettings(path)
	return d.get(key)

writeFoundrySettings = writePlist

def setFoundrySetting(key, value, dstPath):
	"""write a specific entry in the foundry settings xml file."""
	d = readFoundrySettings(dstPath)
	d[key] = value
	writeFoundrySettings(d, dstPath)
	
def readGlyphConstructions():
	"""read GlyphConstruction.txt and turn it into a dict"""
	dataDir=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(robofab.__file__))), 'Data')
	glyphConstructions={}
	filePath = os.path.join(dataDir, 'GlyphConstruction.txt')
	f = open(filePath, 'rb')
	data = f.read().replace('\r', '\n').split('\n')
	f.close()
	for i in data:
		if len(i) == 0: continue
		if i[0] != '#':
			name = i.split(': ')[0]
			construction = i.split(': ')[1].split(' ')
			build = [construction[0]]
			for c in construction[1:]:
				accent = c.split('.')[0]
				position = c.split('.')[1]
				build.append((accent, position))
			glyphConstructions[name] = build
	return glyphConstructions




#
#
#	glyph.unicode: ttFont["cmap"].getcmap(3, 1)
#
#

def guessFileType(fileName):
	if not os.path.exists(fileName):
		return None
	base, ext = os.path.splitext(fileName)
	ext = ext.lower()
	if not have_broken_macsupport:
		try:
			import MacOS
		except ImportError:
			pass
		else:
			cr, tp = MacOS.GetCreatorAndType(fileName)
			if tp in ("sfnt", "FFIL"):
				return "TTF"
			if tp == "LWFN":
				return "Type 1"
			if ext == ".dfont":
				return "TTF"
	if ext in (".otf", ".ttf"):
		return "TTF"
	if ext in (".pfb", ".pfa"):
		return "Type 1"
	return None

def extractTTFFontInfo(font):
	# UFO.info attribute name / index. 
	# name table entries index according to http://www.microsoft.com/typography/otspec/name.htm
	attrs = [
			('copyright', 0),
			('familyName', 1),
			('fontStyle', 1),
			('fullName', 4),
			('trademark', 7),
			('designer', 9),
			('licenseURL', 14),
			('designerURL', 12),
			]
	info = RInfo()
	names = font['name']
	info.ascender = font['hhea'].ascent
	info.descender = font['hhea'].descent
	info.unitsPerEm = font['head'].unitsPerEm
	for name, index in attrs:
		entry = font["name"].getName(index, 3, 1)
		if entry is not None:
			setattr(info, name, unicode(entry.string, "utf16"))
	return info

def extractT1FontInfo(font):
	info = RInfo()
	src = font.font['FontInfo']
	factor = font.font['FontMatrix'][0]
	assert factor > 0
	info.unitsPerEm = int(round(1/factor, 0))
	# assume something for ascender descender
	info.ascender = (info.unitsPerEm / 5) * 4
	info.descender = info.ascender - info.unitsPerEm
	info.versionMajor = font.font['FontInfo']['version']
	info.fullName = font.font['FontInfo']['FullName']
	info.familyName = font.font['FontInfo']['FullName'].split("-")[0]
	info.notice = unicode(font.font['FontInfo']['Notice'], "macroman")
	info.italicAngle = font.font['FontInfo']['ItalicAngle']
	info.uniqueID = font['UniqueID']
	return info

def fontToUFO(src, dst, fileType=None):
	from robofab.ufoLib import UFOWriter
	from robofab.pens.adapterPens import SegmentToPointPen
	if fileType is None:
		fileType = guessFileType(src)
		if fileType is None:
			raise ValueError, "Can't determine input file type"
	ufoWriter = UFOWriter(dst)
	if fileType == "TTF":
		from fontTools.ttLib import TTFont
		font = TTFont(src, 0)
	elif fileType == "Type 1":
		from fontTools.t1Lib import T1Font
		font = T1Font(src)
	else:
		assert 0, "unknown file type: %r" % fileType
	inGlyphSet = font.getGlyphSet()
	outGlyphSet = ufoWriter.getGlyphSet()
	for glyphName in inGlyphSet.keys():
		print "-", glyphName
		glyph = inGlyphSet[glyphName]
		def drawPoints(pen):
			pen = SegmentToPointPen(pen)
			glyph.draw(pen)
		outGlyphSet.writeGlyph(glyphName, glyph, drawPoints)
	outGlyphSet.writeContents()
	if fileType == "TTF":
		info = extractTTFFontInfo(font)
	elif fileType == "Type 1":
		info = extractT1FontInfo(font)
	ufoWriter.writeInfo(info)
