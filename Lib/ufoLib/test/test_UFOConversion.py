# -*- coding: utf-8 -*-

import os
import shutil
import unittest
import tempfile
import codecs
from plistlib import writePlist, readPlist
from ufoLib import convertUFOFormatVersion1ToFormatVersion2, convertUFOFormatVersion2ToFormatVersion1
from testSupport import expectedFontInfo1To2Conversion, expectedFontInfo2To1Conversion


# the format version 1 lib.plist contains some data
# that these tests shouldn't be concerned about.
removeFromFormatVersion1Lib = [
	"org.robofab.opentype.classes",
	"org.robofab.opentype.features",
	"org.robofab.opentype.featureorder",
	"org.robofab.postScriptHintData"
]


class ConversionFunctionsTestCase(unittest.TestCase):

	def tearDown(self):
		path = self.getFontPath("TestFont1 (UFO1) converted.ufo")
		if os.path.exists(path):
			shutil.rmtree(path)
		path = self.getFontPath("TestFont1 (UFO2) converted.ufo")
		if os.path.exists(path):
			shutil.rmtree(path)

	def getFontPath(self, fileName):
		import robofab
		path = os.path.dirname(robofab.__file__)
		path = os.path.dirname(path)
		path = os.path.dirname(path)
		path = os.path.join(path, "TestData", fileName)
		return path

	def compareFileStructures(self, path1, path2, expectedInfoData, testFeatures):
		# result
		metainfoPath1 = os.path.join(path1, "metainfo.plist")
		fontinfoPath1 = os.path.join(path1, "fontinfo.plist")
		kerningPath1 = os.path.join(path1, "kerning.plist")
		groupsPath1 = os.path.join(path1, "groups.plist")
		libPath1 = os.path.join(path1, "lib.plist")
		featuresPath1 = os.path.join(path1, "features.plist")
		glyphsPath1 = os.path.join(path1, "glyphs")
		glyphsPath1_contents = os.path.join(glyphsPath1, "contents.plist")
		glyphsPath1_A = os.path.join(glyphsPath1, "A_.glif")
		glyphsPath1_B = os.path.join(glyphsPath1, "B_.glif")
		# expected result
		metainfoPath2 = os.path.join(path2, "metainfo.plist")
		fontinfoPath2 = os.path.join(path2, "fontinfo.plist")
		kerningPath2 = os.path.join(path2, "kerning.plist")
		groupsPath2 = os.path.join(path2, "groups.plist")
		libPath2 = os.path.join(path2, "lib.plist")
		featuresPath2 = os.path.join(path2, "features.plist")
		glyphsPath2 = os.path.join(path2, "glyphs")
		glyphsPath2_contents = os.path.join(glyphsPath2, "contents.plist")
		glyphsPath2_A = os.path.join(glyphsPath2, "A_.glif")
		glyphsPath2_B = os.path.join(glyphsPath2, "B_.glif")
		# look for existence
		self.assertEqual(os.path.exists(metainfoPath1), True)
		self.assertEqual(os.path.exists(fontinfoPath1), True)
		self.assertEqual(os.path.exists(kerningPath1), True)
		self.assertEqual(os.path.exists(groupsPath1), True)
		self.assertEqual(os.path.exists(libPath1), True)
		self.assertEqual(os.path.exists(glyphsPath1), True)
		self.assertEqual(os.path.exists(glyphsPath1_contents), True)
		self.assertEqual(os.path.exists(glyphsPath1_A), True)
		self.assertEqual(os.path.exists(glyphsPath1_B), True)
		if testFeatures:
			self.assertEqual(os.path.exists(featuresPath1), True)
		# look for aggrement
		data1 = readPlist(metainfoPath1)
		data2 = readPlist(metainfoPath2)
		self.assertEqual(data1, data2)
		data1 = readPlist(fontinfoPath1)
		self.assertEqual(sorted(data1.items()), sorted(expectedInfoData.items()))
		data1 = readPlist(kerningPath1)
		data2 = readPlist(kerningPath2)
		self.assertEqual(data1, data2)
		data1 = readPlist(groupsPath1)
		data2 = readPlist(groupsPath2)
		self.assertEqual(data1, data2)
		data1 = readPlist(libPath1)
		data2 = readPlist(libPath2)
		if "UFO1" in libPath1:
			for key in removeFromFormatVersion1Lib:
				if key in data1:
					del data1[key]
		if "UFO1" in libPath2:
			for key in removeFromFormatVersion1Lib:
				if key in data2:
					del data2[key]
		self.assertEqual(data1, data2)
		data1 = readPlist(glyphsPath1_contents)
		data2 = readPlist(glyphsPath2_contents)
		self.assertEqual(data1, data2)
		data1 = readPlist(glyphsPath1_A)
		data2 = readPlist(glyphsPath2_A)
		self.assertEqual(data1, data2)
		data1 = readPlist(glyphsPath1_B)
		data2 = readPlist(glyphsPath2_B)
		self.assertEqual(data1, data2)

	def test1To2(self):
		path1 = self.getFontPath("TestFont1 (UFO1).ufo")
		path2 = self.getFontPath("TestFont1 (UFO1) converted.ufo")
		path3 = self.getFontPath("TestFont1 (UFO2).ufo")
		convertUFOFormatVersion1ToFormatVersion2(path1, path2)
		self.compareFileStructures(path2, path3, expectedFontInfo1To2Conversion, False)

	def test2To1(self):
		path1 = self.getFontPath("TestFont1 (UFO2).ufo")
		path2 = self.getFontPath("TestFont1 (UFO2) converted.ufo")
		path3 = self.getFontPath("TestFont1 (UFO1).ufo")
		convertUFOFormatVersion2ToFormatVersion1(path1, path2)
		self.compareFileStructures(path2, path3, expectedFontInfo2To1Conversion, False)


if __name__ == "__main__":
	from robofab.test.testSupport import runTests
	runTests()
