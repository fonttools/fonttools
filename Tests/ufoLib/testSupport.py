"""Miscellaneous helpers for our test suite."""

from __future__ import absolute_import, unicode_literals
import os
from fontTools.ufoLib.utils import numberTypes

try:
	basestring
except NameError:
	basestring = str

def getDemoFontPath():
	"""Return the path to Data/DemoFont.ufo/."""
	testdata = os.path.join(os.path.dirname(__file__), "testdata")
	return os.path.join(testdata, "DemoFont.ufo")


def getDemoFontGlyphSetPath():
	"""Return the path to Data/DemoFont.ufo/glyphs/."""
	return os.path.join(getDemoFontPath(), "glyphs")


# GLIF test tools

class Glyph(object):

	def __init__(self):
		self.name = None
		self.width = None
		self.height = None
		self.unicodes = None
		self.note = None
		self.lib = None
		self.image = None
		self.guidelines = None
		self.anchors = None
		self.outline = []

	def _writePointPenCommand(self, command, args, kwargs):
		args = _listToString(args)
		kwargs = _dictToString(kwargs)
		if args and kwargs:
			return "pointPen.%s(*%s, **%s)" % (command, args, kwargs)
		elif len(args):
			return "pointPen.%s(*%s)" % (command, args)
		elif len(kwargs):
			return "pointPen.%s(**%s)" % (command, kwargs)
		else:
			return "pointPen.%s()" % command

	def beginPath(self, **kwargs):
		self.outline.append(self._writePointPenCommand("beginPath", [], kwargs))

	def endPath(self):
		self.outline.append(self._writePointPenCommand("endPath", [], {}))

	def addPoint(self, *args, **kwargs):
		self.outline.append(self._writePointPenCommand("addPoint", args, kwargs))

	def addComponent(self, *args, **kwargs):
		self.outline.append(self._writePointPenCommand("addComponent", args, kwargs))

	def drawPoints(self, pointPen):
		if self.outline:
			py = "\n".join(self.outline)
			exec(py, {"pointPen" : pointPen})

	def py(self):
		text = []
		if self.name is not None:
			text.append("glyph.name = \"%s\"" % self.name)
		if self.width:
			text.append("glyph.width = %r" % self.width)
		if self.height:
			text.append("glyph.height = %r" % self.height)
		if self.unicodes is not None:
			text.append("glyph.unicodes = [%s]" % ", ".join([str(i) for i in self.unicodes]))
		if self.note is not None:
			text.append("glyph.note = \"%s\"" % self.note)
		if self.lib is not None:
			text.append("glyph.lib = %s" % _dictToString(self.lib))
		if self.image is not None:
			text.append("glyph.image = %s" % _dictToString(self.image))
		if self.guidelines is not None:
			text.append("glyph.guidelines = %s" % _listToString(self.guidelines))
		if self.anchors is not None:
			text.append("glyph.anchors = %s" % _listToString(self.anchors))
		if self.outline:
			text += self.outline
		return "\n".join(text)

def _dictToString(d):
	text = []
	for key, value in sorted(d.items()):
		if value is None:
			continue
		key = "\"%s\"" % key
		if isinstance(value, dict):
			value = _dictToString(value)
		elif isinstance(value, list):
			value = _listToString(value)
		elif isinstance(value, tuple):
			value = _tupleToString(value)
		elif isinstance(value, numberTypes):
			value = repr(value)
		elif isinstance(value, basestring):
			value = "\"%s\"" % value
		text.append("%s : %s" % (key, value))
	if not text:
		return ""
	return "{%s}" % ", ".join(text)

def _listToString(l):
	text = []
	for value in l:
		if isinstance(value, dict):
			value = _dictToString(value)
		elif isinstance(value, list):
			value = _listToString(value)
		elif isinstance(value, tuple):
			value = _tupleToString(value)
		elif isinstance(value, numberTypes):
			value = repr(value)
		elif isinstance(value, basestring):
			value = "\"%s\"" % value
		text.append(value)
	if not text:
		return ""
	return "[%s]" % ", ".join(text)

def _tupleToString(t):
	text = []
	for value in t:
		if isinstance(value, dict):
			value = _dictToString(value)
		elif isinstance(value, list):
			value = _listToString(value)
		elif isinstance(value, tuple):
			value = _tupleToString(value)
		elif isinstance(value, numberTypes):
			value = repr(value)
		elif isinstance(value, basestring):
			value = "\"%s\"" % value
		text.append(value)
	if not text:
		return ""
	return "(%s)" % ", ".join(text)

def stripText(text):
	new = []
	for line in text.strip().splitlines():
		line = line.strip()
		if not line:
			continue
		new.append(line)
	return "\n".join(new)

# font info values used by several tests

fontInfoVersion1 = {
	"familyName"   : "Some Font (Family Name)",
	"styleName"	   : "Regular (Style Name)",
	"fullName"	   : "Some Font-Regular (Postscript Full Name)",
	"fontName"	   : "SomeFont-Regular (Postscript Font Name)",
	"menuName"	   : "Some Font Regular (Style Map Family Name)",
	"fontStyle"	   : 64,
	"note"		   : "A note.",
	"versionMajor" : 1,
	"versionMinor" : 0,
	"year"		   : 2008,
	"copyright"	   : "Copyright Some Foundry.",
	"notice"	   : "Some Font by Some Designer for Some Foundry.",
	"trademark"	   : "Trademark Some Foundry",
	"license"	   : "License info for Some Foundry.",
	"licenseURL"   : "http://somefoundry.com/license",
	"createdBy"	   : "Some Foundry",
	"designer"	   : "Some Designer",
	"designerURL"  : "http://somedesigner.com",
	"vendorURL"	   : "http://somefoundry.com",
	"unitsPerEm"   : 1000,
	"ascender"	   : 750,
	"descender"	   : -250,
	"capHeight"	   : 750,
	"xHeight"	   : 500,
	"defaultWidth" : 400,
	"slantAngle"   : -12.5,
	"italicAngle"  : -12.5,
	"widthName"	   : "Medium (normal)",
	"weightName"   : "Medium",
	"weightValue"  : 500,
	"fondName"	   : "SomeFont Regular (FOND Name)",
	"otFamilyName" : "Some Font (Preferred Family Name)",
	"otStyleName"  : "Regular (Preferred Subfamily Name)",
	"otMacName"	   : "Some Font Regular (Compatible Full Name)",
	"msCharSet"	   : 0,
	"fondID"	   : 15000,
	"uniqueID"	   : 4000000,
	"ttVendor"	   : "SOME",
	"ttUniqueID"   : "OpenType name Table Unique ID",
	"ttVersion"	   : "OpenType name Table Version",
}

fontInfoVersion2 = {
	"familyName"						 : "Some Font (Family Name)",
	"styleName"							 : "Regular (Style Name)",
	"styleMapFamilyName"				 : "Some Font Regular (Style Map Family Name)",
	"styleMapStyleName"					 : "regular",
	"versionMajor"						 : 1,
	"versionMinor"						 : 0,
	"year"								 : 2008,
	"copyright"							 : "Copyright Some Foundry.",
	"trademark"							 : "Trademark Some Foundry",
	"unitsPerEm"						 : 1000,
	"descender"							 : -250,
	"xHeight"							 : 500,
	"capHeight"							 : 750,
	"ascender"							 : 750,
	"italicAngle"						 : -12.5,
	"note"								 : "A note.",
	"openTypeHeadCreated"				 : "2000/01/01 00:00:00",
	"openTypeHeadLowestRecPPEM"			 : 10,
	"openTypeHeadFlags"					 : [0, 1],
	"openTypeHheaAscender"				 : 750,
	"openTypeHheaDescender"				 : -250,
	"openTypeHheaLineGap"				 : 200,
	"openTypeHheaCaretSlopeRise"		 : 1,
	"openTypeHheaCaretSlopeRun"			 : 0,
	"openTypeHheaCaretOffset"			 : 0,
	"openTypeNameDesigner"				 : "Some Designer",
	"openTypeNameDesignerURL"			 : "http://somedesigner.com",
	"openTypeNameManufacturer"			 : "Some Foundry",
	"openTypeNameManufacturerURL"		 : "http://somefoundry.com",
	"openTypeNameLicense"				 : "License info for Some Foundry.",
	"openTypeNameLicenseURL"			 : "http://somefoundry.com/license",
	"openTypeNameVersion"				 : "OpenType name Table Version",
	"openTypeNameUniqueID"				 : "OpenType name Table Unique ID",
	"openTypeNameDescription"			 : "Some Font by Some Designer for Some Foundry.",
	"openTypeNamePreferredFamilyName"	 : "Some Font (Preferred Family Name)",
	"openTypeNamePreferredSubfamilyName" : "Regular (Preferred Subfamily Name)",
	"openTypeNameCompatibleFullName"	 : "Some Font Regular (Compatible Full Name)",
	"openTypeNameSampleText"			 : "Sample Text for Some Font.",
	"openTypeNameWWSFamilyName"			 : "Some Font (WWS Family Name)",
	"openTypeNameWWSSubfamilyName"		 : "Regular (WWS Subfamily Name)",
	"openTypeOS2WidthClass"				 : 5,
	"openTypeOS2WeightClass"			 : 500,
	"openTypeOS2Selection"				 : [3],
	"openTypeOS2VendorID"				 : "SOME",
	"openTypeOS2Panose"					 : [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
	"openTypeOS2FamilyClass"			 : [1, 1],
	"openTypeOS2UnicodeRanges"			 : [0, 1],
	"openTypeOS2CodePageRanges"			 : [0, 1],
	"openTypeOS2TypoAscender"			 : 750,
	"openTypeOS2TypoDescender"			 : -250,
	"openTypeOS2TypoLineGap"			 : 200,
	"openTypeOS2WinAscent"				 : 750,
	"openTypeOS2WinDescent"				 : 250,
	"openTypeOS2Type"					 : [],
	"openTypeOS2SubscriptXSize"			 : 200,
	"openTypeOS2SubscriptYSize"			 : 400,
	"openTypeOS2SubscriptXOffset"		 : 0,
	"openTypeOS2SubscriptYOffset"		 : -100,
	"openTypeOS2SuperscriptXSize"		 : 200,
	"openTypeOS2SuperscriptYSize"		 : 400,
	"openTypeOS2SuperscriptXOffset"		 : 0,
	"openTypeOS2SuperscriptYOffset"		 : 200,
	"openTypeOS2StrikeoutSize"			 : 20,
	"openTypeOS2StrikeoutPosition"		 : 300,
	"openTypeVheaVertTypoAscender"		 : 750,
	"openTypeVheaVertTypoDescender"		 : -250,
	"openTypeVheaVertTypoLineGap"		 : 200,
	"openTypeVheaCaretSlopeRise"		 : 0,
	"openTypeVheaCaretSlopeRun"			 : 1,
	"openTypeVheaCaretOffset"			 : 0,
	"postscriptFontName"				 : "SomeFont-Regular (Postscript Font Name)",
	"postscriptFullName"				 : "Some Font-Regular (Postscript Full Name)",
	"postscriptSlantAngle"				 : -12.5,
	"postscriptUniqueID"				 : 4000000,
	"postscriptUnderlineThickness"		 : 20,
	"postscriptUnderlinePosition"		 : -200,
	"postscriptIsFixedPitch"			 : False,
	"postscriptBlueValues"				 : [500, 510],
	"postscriptOtherBlues"				 : [-250, -260],
	"postscriptFamilyBlues"				 : [500, 510],
	"postscriptFamilyOtherBlues"		 : [-250, -260],
	"postscriptStemSnapH"				 : [100, 120],
	"postscriptStemSnapV"				 : [80, 90],
	"postscriptBlueFuzz"				 : 1,
	"postscriptBlueShift"				 : 7,
	"postscriptBlueScale"				 : 0.039625,
	"postscriptForceBold"				 : True,
	"postscriptDefaultWidthX"			 : 400,
	"postscriptNominalWidthX"			 : 400,
	"postscriptWeightName"				 : "Medium",
	"postscriptDefaultCharacter"		 : ".notdef",
	"postscriptWindowsCharacterSet"		 : 1,
	"macintoshFONDFamilyID"				 : 15000,
	"macintoshFONDName"					 : "SomeFont Regular (FOND Name)",
}

fontInfoVersion3 = {
	"familyName"						 : "Some Font (Family Name)",
	"styleName"							 : "Regular (Style Name)",
	"styleMapFamilyName"				 : "Some Font Regular (Style Map Family Name)",
	"styleMapStyleName"					 : "regular",
	"versionMajor"						 : 1,
	"versionMinor"						 : 0,
	"year"								 : 2008,
	"copyright"							 : "Copyright Some Foundry.",
	"trademark"							 : "Trademark Some Foundry",
	"unitsPerEm"						 : 1000,
	"descender"							 : -250,
	"xHeight"							 : 500,
	"capHeight"							 : 750,
	"ascender"							 : 750,
	"italicAngle"						 : -12.5,
	"note"								 : "A note.",
	"openTypeGaspRangeRecords"			 : [
		dict(rangeMaxPPEM=10, rangeGaspBehavior=[0]),
		dict(rangeMaxPPEM=20, rangeGaspBehavior=[1]),
		dict(rangeMaxPPEM=30, rangeGaspBehavior=[2]),
		dict(rangeMaxPPEM=40, rangeGaspBehavior=[3]),
		dict(rangeMaxPPEM=50, rangeGaspBehavior=[0, 1, 2, 3]),
		dict(rangeMaxPPEM=0xFFFF, rangeGaspBehavior=[0])
	],
	"openTypeHeadCreated"				 : "2000/01/01 00:00:00",
	"openTypeHeadLowestRecPPEM"			 : 10,
	"openTypeHeadFlags"					 : [0, 1],
	"openTypeHheaAscender"				 : 750,
	"openTypeHheaDescender"				 : -250,
	"openTypeHheaLineGap"				 : 200,
	"openTypeHheaCaretSlopeRise"		 : 1,
	"openTypeHheaCaretSlopeRun"			 : 0,
	"openTypeHheaCaretOffset"			 : 0,
	"openTypeNameDesigner"				 : "Some Designer",
	"openTypeNameDesignerURL"			 : "http://somedesigner.com",
	"openTypeNameManufacturer"			 : "Some Foundry",
	"openTypeNameManufacturerURL"		 : "http://somefoundry.com",
	"openTypeNameLicense"				 : "License info for Some Foundry.",
	"openTypeNameLicenseURL"			 : "http://somefoundry.com/license",
	"openTypeNameVersion"				 : "OpenType name Table Version",
	"openTypeNameUniqueID"				 : "OpenType name Table Unique ID",
	"openTypeNameDescription"			 : "Some Font by Some Designer for Some Foundry.",
	"openTypeNamePreferredFamilyName"	 : "Some Font (Preferred Family Name)",
	"openTypeNamePreferredSubfamilyName" : "Regular (Preferred Subfamily Name)",
	"openTypeNameCompatibleFullName"	 : "Some Font Regular (Compatible Full Name)",
	"openTypeNameSampleText"			 : "Sample Text for Some Font.",
	"openTypeNameWWSFamilyName"			 : "Some Font (WWS Family Name)",
	"openTypeNameWWSSubfamilyName"		 : "Regular (WWS Subfamily Name)",
	"openTypeNameRecords"				 : [
		dict(nameID=1, platformID=1, encodingID=1, languageID=1, string="Name Record."),
		dict(nameID=2, platformID=1, encodingID=1, languageID=1, string="Name Record.")
	],
	"openTypeOS2WidthClass"				 : 5,
	"openTypeOS2WeightClass"			 : 500,
	"openTypeOS2Selection"				 : [3],
	"openTypeOS2VendorID"				 : "SOME",
	"openTypeOS2Panose"					 : [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
	"openTypeOS2FamilyClass"			 : [1, 1],
	"openTypeOS2UnicodeRanges"			 : [0, 1],
	"openTypeOS2CodePageRanges"			 : [0, 1],
	"openTypeOS2TypoAscender"			 : 750,
	"openTypeOS2TypoDescender"			 : -250,
	"openTypeOS2TypoLineGap"			 : 200,
	"openTypeOS2WinAscent"				 : 750,
	"openTypeOS2WinDescent"				 : 250,
	"openTypeOS2Type"					 : [],
	"openTypeOS2SubscriptXSize"			 : 200,
	"openTypeOS2SubscriptYSize"			 : 400,
	"openTypeOS2SubscriptXOffset"		 : 0,
	"openTypeOS2SubscriptYOffset"		 : -100,
	"openTypeOS2SuperscriptXSize"		 : 200,
	"openTypeOS2SuperscriptYSize"		 : 400,
	"openTypeOS2SuperscriptXOffset"		 : 0,
	"openTypeOS2SuperscriptYOffset"		 : 200,
	"openTypeOS2StrikeoutSize"			 : 20,
	"openTypeOS2StrikeoutPosition"		 : 300,
	"openTypeVheaVertTypoAscender"		 : 750,
	"openTypeVheaVertTypoDescender"		 : -250,
	"openTypeVheaVertTypoLineGap"		 : 200,
	"openTypeVheaCaretSlopeRise"		 : 0,
	"openTypeVheaCaretSlopeRun"			 : 1,
	"openTypeVheaCaretOffset"			 : 0,
	"postscriptFontName"				 : "SomeFont-Regular (Postscript Font Name)",
	"postscriptFullName"				 : "Some Font-Regular (Postscript Full Name)",
	"postscriptSlantAngle"				 : -12.5,
	"postscriptUniqueID"				 : 4000000,
	"postscriptUnderlineThickness"		 : 20,
	"postscriptUnderlinePosition"		 : -200,
	"postscriptIsFixedPitch"			 : False,
	"postscriptBlueValues"				 : [500, 510],
	"postscriptOtherBlues"				 : [-250, -260],
	"postscriptFamilyBlues"				 : [500, 510],
	"postscriptFamilyOtherBlues"		 : [-250, -260],
	"postscriptStemSnapH"				 : [100, 120],
	"postscriptStemSnapV"				 : [80, 90],
	"postscriptBlueFuzz"				 : 1,
	"postscriptBlueShift"				 : 7,
	"postscriptBlueScale"				 : 0.039625,
	"postscriptForceBold"				 : True,
	"postscriptDefaultWidthX"			 : 400,
	"postscriptNominalWidthX"			 : 400,
	"postscriptWeightName"				 : "Medium",
	"postscriptDefaultCharacter"		 : ".notdef",
	"postscriptWindowsCharacterSet"		 : 1,
	"macintoshFONDFamilyID"				 : 15000,
	"macintoshFONDName"					 : "SomeFont Regular (FOND Name)",
	"woffMajorVersion"					 : 1,
	"woffMinorVersion"					 : 0,
	"woffMetadataUniqueID"				 : dict(id="string"),
	"woffMetadataVendor"				 : dict(name="Some Foundry", url="http://somefoundry.com"),
	"woffMetadataCredits"				 : dict(
												credits=[
													dict(name="Some Designer"),
													dict(name=""),
													dict(name="Some Designer", url="http://somedesigner.com"),
													dict(name="Some Designer", url=""),
													dict(name="Some Designer", role="Designer"),
													dict(name="Some Designer", role=""),
													dict(name="Some Designer", dir="ltr"),
													dict(name="rengiseD emoS", dir="rtl"),
													{"name" : "Some Designer", "class" : "hello"},
													{"name" : "Some Designer", "class" : ""},
												]
											),
	"woffMetadataDescription"			 : dict(
												url="http://somefoundry.com/foo/description",
												text=[
													dict(text="foo"),
													dict(text=""),
													dict(text="foo", language="bar"),
													dict(text="foo", language=""),
													dict(text="foo", dir="ltr"),
													dict(text="foo", dir="rtl"),
													{"text" : "foo", "class" : "foo"},
													{"text" : "foo", "class" : ""},
												]
											),
	"woffMetadataLicense"				 : dict(
												url="http://somefoundry.com/foo/license",
												id="foo",
												text=[
													dict(text="foo"),
													dict(text=""),
													dict(text="foo", language="bar"),
													dict(text="foo", language=""),
													dict(text="foo", dir="ltr"),
													dict(text="foo", dir="rtl"),
													{"text" : "foo", "class" : "foo"},
													{"text" : "foo", "class" : ""},
												]
											),
	"woffMetadataCopyright"				 : dict(
												text=[
													dict(text="foo"),
													dict(text=""),
													dict(text="foo", language="bar"),
													dict(text="foo", language=""),
													dict(text="foo", dir="ltr"),
													dict(text="foo", dir="rtl"),
													{"text" : "foo", "class" : "foo"},
													{"text" : "foo", "class" : ""},
												]
											),
	"woffMetadataTrademark"				 : dict(
												text=[
													dict(text="foo"),
													dict(text=""),
													dict(text="foo", language="bar"),
													dict(text="foo", language=""),
													dict(text="foo", dir="ltr"),
													dict(text="foo", dir="rtl"),
													{"text" : "foo", "class" : "foo"},
													{"text" : "foo", "class" : ""},
												]
											),
	"woffMetadataLicensee"				 : dict(
												name="Some Licensee"
											),
	"woffMetadataExtensions"			 : [
												dict(
													# everything
													names=[
														dict(text="foo"),
														dict(text=""),
														dict(text="foo", language="bar"),
														dict(text="foo", language=""),
														dict(text="foo", dir="ltr"),
														dict(text="foo", dir="rtl"),
														{"text" : "foo", "class" : "hello"},
														{"text" : "foo", "class" : ""},
													],
													items=[
														# everything
														dict(
															id="foo",
															names=[
																dict(text="foo"),
																dict(text=""),
																dict(text="foo", language="bar"),
																dict(text="foo", language=""),
																dict(text="foo", dir="ltr"),
																dict(text="foo", dir="rtl"),
																{"text" : "foo", "class" : "hello"},
																{"text" : "foo", "class" : ""},
															],
															values=[
																dict(text="foo"),
																dict(text=""),
																dict(text="foo", language="bar"),
																dict(text="foo", language=""),
																dict(text="foo", dir="ltr"),
																dict(text="foo", dir="rtl"),
																{"text" : "foo", "class" : "hello"},
																{"text" : "foo", "class" : ""},
															]
														),
														# no id
														dict(
															names=[
																dict(text="foo")
															],
															values=[
																dict(text="foo")
															]
														)
													]
												),
												# no names
												dict(
													items=[
														dict(
															id="foo",
															names=[
																dict(text="foo")
															],
															values=[
																dict(text="foo")
															]
														)
													]
												),
											],
	"guidelines"						 : [
											# ints
											dict(x=100, y=200, angle=45),
											# floats
											dict(x=100.5, y=200.5, angle=45.5),
											# edges
											dict(x=0, y=0, angle=0),
											dict(x=0, y=0, angle=360),
											dict(x=0, y=0, angle=360.0),
											# no y
											dict(x=100),
											# no x
											dict(y=200),
											# name
											dict(x=100, y=200, angle=45, name="foo"),
											dict(x=100, y=200, angle=45, name=""),
											# identifier
											dict(x=100, y=200, angle=45, identifier="guide1"),
											dict(x=100, y=200, angle=45, identifier="guide2"),
											dict(x=100, y=200, angle=45, identifier="\x20"),
											dict(x=100, y=200, angle=45, identifier="\x7E"),
											# colors
											dict(x=100, y=200, angle=45, color="0,0,0,0"),
											dict(x=100, y=200, angle=45, color="1,0,0,0"),
											dict(x=100, y=200, angle=45, color="1,1,1,1"),
											dict(x=100, y=200, angle=45, color="0,1,0,0"),
											dict(x=100, y=200, angle=45, color="0,0,1,0"),
											dict(x=100, y=200, angle=45, color="0,0,0,1"),
											dict(x=100, y=200, angle=45, color="1, 0, 0, 0"),
											dict(x=100, y=200, angle=45, color="0, 1, 0, 0"),
											dict(x=100, y=200, angle=45, color="0, 0, 1, 0"),
											dict(x=100, y=200, angle=45, color="0, 0, 0, 1"),
											dict(x=100, y=200, angle=45, color=".5,0,0,0"),
											dict(x=100, y=200, angle=45, color="0,.5,0,0"),
											dict(x=100, y=200, angle=45, color="0,0,.5,0"),
											dict(x=100, y=200, angle=45, color="0,0,0,.5"),
											dict(x=100, y=200, angle=45, color=".5,1,1,1"),
											dict(x=100, y=200, angle=45, color="1,.5,1,1"),
											dict(x=100, y=200, angle=45, color="1,1,.5,1"),
											dict(x=100, y=200, angle=45, color="1,1,1,.5"),
										],
}

expectedFontInfo1To2Conversion = {
	"familyName"						: "Some Font (Family Name)",
	"styleMapFamilyName"				: "Some Font Regular (Style Map Family Name)",
	"styleMapStyleName"					: "regular",
	"styleName"							: "Regular (Style Name)",
	"unitsPerEm"						: 1000,
	"ascender"							: 750,
	"capHeight"							: 750,
	"xHeight"							: 500,
	"descender"							: -250,
	"italicAngle"						: -12.5,
	"versionMajor"						: 1,
	"versionMinor"						: 0,
	"year"								: 2008,
	"copyright"							: "Copyright Some Foundry.",
	"trademark"							: "Trademark Some Foundry",
	"note"								: "A note.",
	"macintoshFONDFamilyID"				: 15000,
	"macintoshFONDName"					: "SomeFont Regular (FOND Name)",
	"openTypeNameCompatibleFullName"	: "Some Font Regular (Compatible Full Name)",
	"openTypeNameDescription"			: "Some Font by Some Designer for Some Foundry.",
	"openTypeNameDesigner"				: "Some Designer",
	"openTypeNameDesignerURL"			: "http://somedesigner.com",
	"openTypeNameLicense"				: "License info for Some Foundry.",
	"openTypeNameLicenseURL"			: "http://somefoundry.com/license",
	"openTypeNameManufacturer"			: "Some Foundry",
	"openTypeNameManufacturerURL"		: "http://somefoundry.com",
	"openTypeNamePreferredFamilyName"	: "Some Font (Preferred Family Name)",
	"openTypeNamePreferredSubfamilyName": "Regular (Preferred Subfamily Name)",
	"openTypeNameCompatibleFullName"	: "Some Font Regular (Compatible Full Name)",
	"openTypeNameUniqueID"				: "OpenType name Table Unique ID",
	"openTypeNameVersion"				: "OpenType name Table Version",
	"openTypeOS2VendorID"				: "SOME",
	"openTypeOS2WeightClass"			: 500,
	"openTypeOS2WidthClass"				: 5,
	"postscriptDefaultWidthX"			: 400,
	"postscriptFontName"				: "SomeFont-Regular (Postscript Font Name)",
	"postscriptFullName"				: "Some Font-Regular (Postscript Full Name)",
	"postscriptSlantAngle"				: -12.5,
	"postscriptUniqueID"				: 4000000,
	"postscriptWeightName"				: "Medium",
	"postscriptWindowsCharacterSet"		: 1
}

expectedFontInfo2To1Conversion = {
	"familyName"  	: "Some Font (Family Name)",
	"menuName"	  	: "Some Font Regular (Style Map Family Name)",
	"fontStyle"	  	: 64,
	"styleName"	  	: "Regular (Style Name)",
	"unitsPerEm"  	: 1000,
	"ascender"	  	: 750,
	"capHeight"	  	: 750,
	"xHeight"	  	: 500,
	"descender"	  	: -250,
	"italicAngle" 	: -12.5,
	"versionMajor"	: 1,
	"versionMinor"	: 0,
	"copyright"	  	: "Copyright Some Foundry.",
	"trademark"	  	: "Trademark Some Foundry",
	"note"		  	: "A note.",
	"fondID"	  	: 15000,
	"fondName"	  	: "SomeFont Regular (FOND Name)",
	"fullName"	  	: "Some Font Regular (Compatible Full Name)",
	"notice"	  	: "Some Font by Some Designer for Some Foundry.",
	"designer"	  	: "Some Designer",
	"designerURL" 	: "http://somedesigner.com",
	"license"	  	: "License info for Some Foundry.",
	"licenseURL"  	: "http://somefoundry.com/license",
	"createdBy"	  	: "Some Foundry",
	"vendorURL"	  	: "http://somefoundry.com",
	"otFamilyName"	: "Some Font (Preferred Family Name)",
	"otStyleName" 	: "Regular (Preferred Subfamily Name)",
	"otMacName"	  	: "Some Font Regular (Compatible Full Name)",
	"ttUniqueID"  	: "OpenType name Table Unique ID",
	"ttVersion"	  	: "OpenType name Table Version",
	"ttVendor"	  	: "SOME",
	"weightValue" 	: 500,
	"widthName"	  	: "Medium (normal)",
	"defaultWidth"	: 400,
	"fontName"	  	: "SomeFont-Regular (Postscript Font Name)",
	"fullName"	  	: "Some Font-Regular (Postscript Full Name)",
	"slantAngle"  	: -12.5,
	"uniqueID"	  	: 4000000,
	"weightName"  	: "Medium",
	"msCharSet"	  	: 0,
	"year"			: 2008
}
