# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import shutil
import unittest
import tempfile
from io import open
from fontTools.misc.py23 import unicode
from fontTools.ufoLib import UFOReader, UFOWriter, UFOLibError
from fontTools.ufoLib.glifLib import GlifLibError
from fontTools.misc import plistlib
from .testSupport import fontInfoVersion3


class TestInfoObject(object): pass


# --------------
# fontinfo.plist
# --------------

class ReadFontInfoVersion3TestCase(unittest.TestCase):

	def setUp(self):
		self.dstDir = tempfile.mktemp()
		os.mkdir(self.dstDir)
		metaInfo = {
			"creator": "test",
			"formatVersion": 3
		}
		path = os.path.join(self.dstDir, "metainfo.plist")
		with open(path, "wb") as f:
			plistlib.dump(metaInfo, f)

	def tearDown(self):
		shutil.rmtree(self.dstDir)

	def _writeInfoToPlist(self, info):
		path = os.path.join(self.dstDir, "fontinfo.plist")
		with open(path, "wb") as f:
			plistlib.dump(info, f)

	def testRead(self):
		originalData = dict(fontInfoVersion3)
		self._writeInfoToPlist(originalData)
		infoObject = TestInfoObject()
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(infoObject)
		readData = {}
		for attr in list(fontInfoVersion3.keys()):
			readData[attr] = getattr(infoObject, attr)
		self.assertEqual(originalData, readData)

	def testGenericRead(self):
		# familyName
		info = dict(fontInfoVersion3)
		info["familyName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# styleName
		info = dict(fontInfoVersion3)
		info["styleName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# styleMapFamilyName
		info = dict(fontInfoVersion3)
		info["styleMapFamilyName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# styleMapStyleName
		## not a string
		info = dict(fontInfoVersion3)
		info["styleMapStyleName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## out of range
		info = dict(fontInfoVersion3)
		info["styleMapStyleName"] = "REGULAR"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# versionMajor
		info = dict(fontInfoVersion3)
		info["versionMajor"] = "1"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# versionMinor
		info = dict(fontInfoVersion3)
		info["versionMinor"] = "0"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["versionMinor"] = -1
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# copyright
		info = dict(fontInfoVersion3)
		info["copyright"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# trademark
		info = dict(fontInfoVersion3)
		info["trademark"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# unitsPerEm
		info = dict(fontInfoVersion3)
		info["unitsPerEm"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["unitsPerEm"] = -1
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["unitsPerEm"] = -1.0
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# descender
		info = dict(fontInfoVersion3)
		info["descender"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# xHeight
		info = dict(fontInfoVersion3)
		info["xHeight"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# capHeight
		info = dict(fontInfoVersion3)
		info["capHeight"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# ascender
		info = dict(fontInfoVersion3)
		info["ascender"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# italicAngle
		info = dict(fontInfoVersion3)
		info["italicAngle"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())

	def testGaspRead(self):
		# not a list
		info = dict(fontInfoVersion3)
		info["openTypeGaspRangeRecords"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# empty list
		info = dict(fontInfoVersion3)
		info["openTypeGaspRangeRecords"] = []
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		# not a dict
		info = dict(fontInfoVersion3)
		info["openTypeGaspRangeRecords"] = ["abc"]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# dict not properly formatted
		info = dict(fontInfoVersion3)
		info["openTypeGaspRangeRecords"] = [dict(rangeMaxPPEM=0xFFFF, notTheRightKey=1)]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeGaspRangeRecords"] = [dict(notTheRightKey=1, rangeGaspBehavior=[0])]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# not an int for ppem
		info = dict(fontInfoVersion3)
		info["openTypeGaspRangeRecords"] = [dict(rangeMaxPPEM="abc", rangeGaspBehavior=[0]), dict(rangeMaxPPEM=0xFFFF, rangeGaspBehavior=[0])]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# not a list for behavior
		info = dict(fontInfoVersion3)
		info["openTypeGaspRangeRecords"] = [dict(rangeMaxPPEM=10, rangeGaspBehavior="abc"), dict(rangeMaxPPEM=0xFFFF, rangeGaspBehavior=[0])]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# invalid behavior value
		info = dict(fontInfoVersion3)
		info["openTypeGaspRangeRecords"] = [dict(rangeMaxPPEM=10, rangeGaspBehavior=[-1]), dict(rangeMaxPPEM=0xFFFF, rangeGaspBehavior=[0])]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# not sorted
		info = dict(fontInfoVersion3)
		info["openTypeGaspRangeRecords"] = [dict(rangeMaxPPEM=0xFFFF, rangeGaspBehavior=[0]), dict(rangeMaxPPEM=10, rangeGaspBehavior=[0])]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# no 0xFFFF
		info = dict(fontInfoVersion3)
		info["openTypeGaspRangeRecords"] = [dict(rangeMaxPPEM=10, rangeGaspBehavior=[0]), dict(rangeMaxPPEM=20, rangeGaspBehavior=[0])]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())

	def testHeadRead(self):
		# openTypeHeadCreated
		## not a string
		info = dict(fontInfoVersion3)
		info["openTypeHeadCreated"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## invalid format
		info = dict(fontInfoVersion3)
		info["openTypeHeadCreated"] = "2000-Jan-01 00:00:00"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeHeadLowestRecPPEM
		info = dict(fontInfoVersion3)
		info["openTypeHeadLowestRecPPEM"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeHeadLowestRecPPEM"] = -1
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeHeadFlags
		info = dict(fontInfoVersion3)
		info["openTypeHeadFlags"] = [-1]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())

	def testHheaRead(self):
		# openTypeHheaAscender
		info = dict(fontInfoVersion3)
		info["openTypeHheaAscender"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeHheaDescender
		info = dict(fontInfoVersion3)
		info["openTypeHheaDescender"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeHheaLineGap
		info = dict(fontInfoVersion3)
		info["openTypeHheaLineGap"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeHheaCaretSlopeRise
		info = dict(fontInfoVersion3)
		info["openTypeHheaCaretSlopeRise"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeHheaCaretSlopeRun
		info = dict(fontInfoVersion3)
		info["openTypeHheaCaretSlopeRun"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeHheaCaretOffset
		info = dict(fontInfoVersion3)
		info["openTypeHheaCaretOffset"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())

	def testNameRead(self):
		# openTypeNameDesigner
		info = dict(fontInfoVersion3)
		info["openTypeNameDesigner"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameDesignerURL
		info = dict(fontInfoVersion3)
		info["openTypeNameDesignerURL"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameManufacturer
		info = dict(fontInfoVersion3)
		info["openTypeNameManufacturer"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameManufacturerURL
		info = dict(fontInfoVersion3)
		info["openTypeNameManufacturerURL"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameLicense
		info = dict(fontInfoVersion3)
		info["openTypeNameLicense"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameLicenseURL
		info = dict(fontInfoVersion3)
		info["openTypeNameLicenseURL"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameVersion
		info = dict(fontInfoVersion3)
		info["openTypeNameVersion"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameUniqueID
		info = dict(fontInfoVersion3)
		info["openTypeNameUniqueID"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameDescription
		info = dict(fontInfoVersion3)
		info["openTypeNameDescription"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNamePreferredFamilyName
		info = dict(fontInfoVersion3)
		info["openTypeNamePreferredFamilyName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNamePreferredSubfamilyName
		info = dict(fontInfoVersion3)
		info["openTypeNamePreferredSubfamilyName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameCompatibleFullName
		info = dict(fontInfoVersion3)
		info["openTypeNameCompatibleFullName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameSampleText
		info = dict(fontInfoVersion3)
		info["openTypeNameSampleText"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameWWSFamilyName
		info = dict(fontInfoVersion3)
		info["openTypeNameWWSFamilyName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameWWSSubfamilyName
		info = dict(fontInfoVersion3)
		info["openTypeNameWWSSubfamilyName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeNameRecords
		## not a list
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## not a dict
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = ["abc"]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## invalid dict structure
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [dict(foo="bar")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## incorrect keys
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(nameID=1, platformID=1, encodingID=1, languageID=1, string="Name Record.", foo="bar")
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(platformID=1, encodingID=1, languageID=1, string="Name Record.")
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(nameID=1, encodingID=1, languageID=1, string="Name Record.")
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(nameID=1, platformID=1, languageID=1, string="Name Record.")
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(nameID=1, platformID=1, encodingID=1, string="Name Record.")
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(nameID=1, platformID=1, encodingID=1, languageID=1)
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## invalid values
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(nameID="1", platformID=1, encodingID=1, languageID=1, string="Name Record.")
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(nameID=1, platformID="1", encodingID=1, languageID=1, string="Name Record.")
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(nameID=1, platformID=1, encodingID="1", languageID=1, string="Name Record.")
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(nameID=1, platformID=1, encodingID=1, languageID="1", string="Name Record.")
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(nameID=1, platformID=1, encodingID=1, languageID=1, string=1)
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## duplicate
		info = dict(fontInfoVersion3)
		info["openTypeNameRecords"] = [
			dict(nameID=1, platformID=1, encodingID=1, languageID=1, string="Name Record."),
			dict(nameID=1, platformID=1, encodingID=1, languageID=1, string="Name Record.")
		]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())

	def testOS2Read(self):
		# openTypeOS2WidthClass
		## not an int
		info = dict(fontInfoVersion3)
		info["openTypeOS2WidthClass"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## out or range
		info = dict(fontInfoVersion3)
		info["openTypeOS2WidthClass"] = 15
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2WeightClass
		info = dict(fontInfoVersion3)
		## not an int
		info["openTypeOS2WeightClass"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## out of range
		info["openTypeOS2WeightClass"] = -50
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2Selection
		info = dict(fontInfoVersion3)
		info["openTypeOS2Selection"] = [-1]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2VendorID
		info = dict(fontInfoVersion3)
		info["openTypeOS2VendorID"] = 1234
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2Panose
		## not an int
		info = dict(fontInfoVersion3)
		info["openTypeOS2Panose"] = [0, 1, 2, 3, 4, 5, 6, 7, 8, str(9)]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## negative
		info = dict(fontInfoVersion3)
		info["openTypeOS2Panose"] = [0, 1, 2, 3, 4, 5, 6, 7, 8, -9]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## too few values
		info = dict(fontInfoVersion3)
		info["openTypeOS2Panose"] = [0, 1, 2, 3]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## too many values
		info = dict(fontInfoVersion3)
		info["openTypeOS2Panose"] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2FamilyClass
		## not an int
		info = dict(fontInfoVersion3)
		info["openTypeOS2FamilyClass"] = [1, str(1)]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## too few values
		info = dict(fontInfoVersion3)
		info["openTypeOS2FamilyClass"] = [1]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## too many values
		info = dict(fontInfoVersion3)
		info["openTypeOS2FamilyClass"] = [1, 1, 1]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## out of range
		info = dict(fontInfoVersion3)
		info["openTypeOS2FamilyClass"] = [1, 201]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2UnicodeRanges
		## not an int
		info = dict(fontInfoVersion3)
		info["openTypeOS2UnicodeRanges"] = ["0"]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## out of range
		info = dict(fontInfoVersion3)
		info["openTypeOS2UnicodeRanges"] = [-1]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2CodePageRanges
		## not an int
		info = dict(fontInfoVersion3)
		info["openTypeOS2CodePageRanges"] = ["0"]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## out of range
		info = dict(fontInfoVersion3)
		info["openTypeOS2CodePageRanges"] = [-1]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2TypoAscender
		info = dict(fontInfoVersion3)
		info["openTypeOS2TypoAscender"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2TypoDescender
		info = dict(fontInfoVersion3)
		info["openTypeOS2TypoDescender"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2TypoLineGap
		info = dict(fontInfoVersion3)
		info["openTypeOS2TypoLineGap"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2WinAscent
		info = dict(fontInfoVersion3)
		info["openTypeOS2WinAscent"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeOS2WinAscent"] = -1
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2WinDescent
		info = dict(fontInfoVersion3)
		info["openTypeOS2WinDescent"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		info = dict(fontInfoVersion3)
		info["openTypeOS2WinDescent"] = -1
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2Type
		## not an int
		info = dict(fontInfoVersion3)
		info["openTypeOS2Type"] = ["1"]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		## out of range
		info = dict(fontInfoVersion3)
		info["openTypeOS2Type"] = [-1]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2SubscriptXSize
		info = dict(fontInfoVersion3)
		info["openTypeOS2SubscriptXSize"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2SubscriptYSize
		info = dict(fontInfoVersion3)
		info["openTypeOS2SubscriptYSize"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2SubscriptXOffset
		info = dict(fontInfoVersion3)
		info["openTypeOS2SubscriptXOffset"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2SubscriptYOffset
		info = dict(fontInfoVersion3)
		info["openTypeOS2SubscriptYOffset"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2SuperscriptXSize
		info = dict(fontInfoVersion3)
		info["openTypeOS2SuperscriptXSize"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2SuperscriptYSize
		info = dict(fontInfoVersion3)
		info["openTypeOS2SuperscriptYSize"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2SuperscriptXOffset
		info = dict(fontInfoVersion3)
		info["openTypeOS2SuperscriptXOffset"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2SuperscriptYOffset
		info = dict(fontInfoVersion3)
		info["openTypeOS2SuperscriptYOffset"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2StrikeoutSize
		info = dict(fontInfoVersion3)
		info["openTypeOS2StrikeoutSize"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeOS2StrikeoutPosition
		info = dict(fontInfoVersion3)
		info["openTypeOS2StrikeoutPosition"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())

	def testVheaRead(self):
		# openTypeVheaVertTypoAscender
		info = dict(fontInfoVersion3)
		info["openTypeVheaVertTypoAscender"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeVheaVertTypoDescender
		info = dict(fontInfoVersion3)
		info["openTypeVheaVertTypoDescender"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeVheaVertTypoLineGap
		info = dict(fontInfoVersion3)
		info["openTypeVheaVertTypoLineGap"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeVheaCaretSlopeRise
		info = dict(fontInfoVersion3)
		info["openTypeVheaCaretSlopeRise"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeVheaCaretSlopeRun
		info = dict(fontInfoVersion3)
		info["openTypeVheaCaretSlopeRun"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# openTypeVheaCaretOffset
		info = dict(fontInfoVersion3)
		info["openTypeVheaCaretOffset"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())

	def testFONDRead(self):
		# macintoshFONDFamilyID
		info = dict(fontInfoVersion3)
		info["macintoshFONDFamilyID"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# macintoshFONDName
		info = dict(fontInfoVersion3)
		info["macintoshFONDName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())

	def testPostscriptRead(self):
		# postscriptFontName
		info = dict(fontInfoVersion3)
		info["postscriptFontName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# postscriptFullName
		info = dict(fontInfoVersion3)
		info["postscriptFullName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# postscriptSlantAngle
		info = dict(fontInfoVersion3)
		info["postscriptSlantAngle"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, info=TestInfoObject())
		# postscriptUniqueID
		info = dict(fontInfoVersion3)
		info["postscriptUniqueID"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptUnderlineThickness
		info = dict(fontInfoVersion3)
		info["postscriptUnderlineThickness"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptUnderlinePosition
		info = dict(fontInfoVersion3)
		info["postscriptUnderlinePosition"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptIsFixedPitch
		info = dict(fontInfoVersion3)
		info["postscriptIsFixedPitch"] = 2
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptBlueValues
		## not a list
		info = dict(fontInfoVersion3)
		info["postscriptBlueValues"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## uneven value count
		info = dict(fontInfoVersion3)
		info["postscriptBlueValues"] = [500]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## too many values
		info = dict(fontInfoVersion3)
		info["postscriptBlueValues"] = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptOtherBlues
		## not a list
		info = dict(fontInfoVersion3)
		info["postscriptOtherBlues"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## uneven value count
		info = dict(fontInfoVersion3)
		info["postscriptOtherBlues"] = [500]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## too many values
		info = dict(fontInfoVersion3)
		info["postscriptOtherBlues"] = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptFamilyBlues
		## not a list
		info = dict(fontInfoVersion3)
		info["postscriptFamilyBlues"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## uneven value count
		info = dict(fontInfoVersion3)
		info["postscriptFamilyBlues"] = [500]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## too many values
		info = dict(fontInfoVersion3)
		info["postscriptFamilyBlues"] = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptFamilyOtherBlues
		## not a list
		info = dict(fontInfoVersion3)
		info["postscriptFamilyOtherBlues"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## uneven value count
		info = dict(fontInfoVersion3)
		info["postscriptFamilyOtherBlues"] = [500]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## too many values
		info = dict(fontInfoVersion3)
		info["postscriptFamilyOtherBlues"] = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptStemSnapH
		## not list
		info = dict(fontInfoVersion3)
		info["postscriptStemSnapH"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## too many values
		info = dict(fontInfoVersion3)
		info["postscriptStemSnapH"] = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptStemSnapV
		## not list
		info = dict(fontInfoVersion3)
		info["postscriptStemSnapV"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## too many values
		info = dict(fontInfoVersion3)
		info["postscriptStemSnapV"] = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptBlueFuzz
		info = dict(fontInfoVersion3)
		info["postscriptBlueFuzz"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptBlueShift
		info = dict(fontInfoVersion3)
		info["postscriptBlueShift"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptBlueScale
		info = dict(fontInfoVersion3)
		info["postscriptBlueScale"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptForceBold
		info = dict(fontInfoVersion3)
		info["postscriptForceBold"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptDefaultWidthX
		info = dict(fontInfoVersion3)
		info["postscriptDefaultWidthX"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptNominalWidthX
		info = dict(fontInfoVersion3)
		info["postscriptNominalWidthX"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptWeightName
		info = dict(fontInfoVersion3)
		info["postscriptWeightName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptDefaultCharacter
		info = dict(fontInfoVersion3)
		info["postscriptDefaultCharacter"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# postscriptWindowsCharacterSet
		info = dict(fontInfoVersion3)
		info["postscriptWindowsCharacterSet"] = -1
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# macintoshFONDFamilyID
		info = dict(fontInfoVersion3)
		info["macintoshFONDFamilyID"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# macintoshFONDName
		info = dict(fontInfoVersion3)
		info["macintoshFONDName"] = 123
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())

	def testWOFFRead(self):
		# woffMajorVersion
		info = dict(fontInfoVersion3)
		info["woffMajorVersion"] = 1.0
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["woffMajorVersion"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# woffMinorVersion
		info = dict(fontInfoVersion3)
		info["woffMinorVersion"] = 1.0
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["woffMinorVersion"] = "abc"
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# woffMetadataUniqueID
		## none
		info = dict(fontInfoVersion3)
		del info["woffMetadataUniqueID"]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		## not a dict
		info = dict(fontInfoVersion3)
		info["woffMetadataUniqueID"] = 1
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## unknown key
		info = dict(fontInfoVersion3)
		info["woffMetadataUniqueID"] = dict(id="foo", notTheRightKey=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## no id
		info = dict(fontInfoVersion3)
		info["woffMetadataUniqueID"] = dict()
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## not a string for id
		info = dict(fontInfoVersion3)
		info["woffMetadataUniqueID"] = dict(id=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## empty string
		info = dict(fontInfoVersion3)
		info["woffMetadataUniqueID"] = dict(id="")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		# woffMetadataVendor
		## no name
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = dict(url="foo")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## name not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = dict(name=1, url="foo")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## name an empty string
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = dict(name="", url="foo")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		## no URL
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = dict(name="foo")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		## url not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = dict(name="foo", url=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## url empty string
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = dict(name="foo", url="")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		## have dir
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = dict(name="foo", url="bar", dir="ltr")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = dict(name="foo", url="bar", dir="rtl")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		## dir not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = dict(name="foo", url="bar", dir=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## dir not ltr or rtl
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = dict(name="foo", url="bar", dir="utd")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## have class
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = {"name"  : "foo", "url" : "bar", "class" : "hello"}
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		## class not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = {"name"  : "foo", "url" : "bar", "class" : 1}
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## class empty string
		info = dict(fontInfoVersion3)
		info["woffMetadataVendor"] = {"name"  : "foo", "url" : "bar", "class" : ""}
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		# woffMetadataCredits
		## no credits attribute
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = {}
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## unknown attribute
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits=[dict(name="foo")], notTheRightKey=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## not a list
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits="abc")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## no elements in credits
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits=[])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## credit not a dict
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits=["abc"])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## unknown key
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits=[dict(name="foo", notTheRightKey=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## no name
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits=[dict(url="foo")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## name not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits=[dict(name=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## url not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits=[dict(name="foo", url=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## role not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits=[dict(name="foo", role=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## dir not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits=[dict(name="foo", dir=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## dir not ltr or rtl
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits=[dict(name="foo", dir="utd")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## class not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataCredits"] = dict(credits=[{"name"  : "foo", "class" : 1}])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# woffMetadataDescription
		## no url
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(text=[dict(text="foo")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		## url not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(text=[dict(text="foo")], url=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## no text
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(url="foo")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text not a list
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(text="abc")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item not a dict
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(text=["abc"])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item unknown key
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(text=[dict(text="foo", notTheRightKey=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item missing text
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(text=[dict(language="foo")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(text=[dict(text=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## url not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(text=[dict(text="foo", url=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## language not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(text=[dict(text="foo", language=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## dir not ltr or rtl
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(text=[dict(text="foo", dir="utd")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## class not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataDescription"] = dict(text=[{"text"  : "foo", "class" : 1}])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# woffMetadataLicense
		## no url
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text=[dict(text="foo")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		## url not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text=[dict(text="foo")], url=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## id not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text=[dict(text="foo")], id=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## no text
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(url="foo")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		## text not a list
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text="abc")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item not a dict
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text=["abc"])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item unknown key
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text=[dict(text="foo", notTheRightKey=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item missing text
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text=[dict(language="foo")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text=[dict(text=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## url not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text=[dict(text="foo", url=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## language not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text=[dict(text="foo", language=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## dir not ltr or rtl
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text=[dict(text="foo", dir="utd")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## class not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataLicense"] = dict(text=[{"text"  : "foo", "class" : 1}])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# woffMetadataCopyright
		## unknown attribute
		info = dict(fontInfoVersion3)
		info["woffMetadataCopyright"] = dict(text=[dict(text="foo")], notTheRightKey=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## no text
		info = dict(fontInfoVersion3)
		info["woffMetadataCopyright"] = dict()
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text not a list
		info = dict(fontInfoVersion3)
		info["woffMetadataCopyright"] = dict(text="abc")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item not a dict
		info = dict(fontInfoVersion3)
		info["woffMetadataCopyright"] = dict(text=["abc"])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item unknown key
		info = dict(fontInfoVersion3)
		info["woffMetadataCopyright"] = dict(text=[dict(text="foo", notTheRightKey=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item missing text
		info = dict(fontInfoVersion3)
		info["woffMetadataCopyright"] = dict(text=[dict(language="foo")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataCopyright"] = dict(text=[dict(text=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## url not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataCopyright"] = dict(text=[dict(text="foo", url=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## language not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataCopyright"] = dict(text=[dict(text="foo", language=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## dir not ltr or rtl
		info = dict(fontInfoVersion3)
		info["woffMetadataCopyright"] = dict(text=[dict(text="foo", dir="utd")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## class not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataCopyright"] = dict(text=[{"text"  : "foo", "class" : 1}])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# woffMetadataTrademark
		## unknown attribute
		info = dict(fontInfoVersion3)
		info["woffMetadataTrademark"] = dict(text=[dict(text="foo")], notTheRightKey=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## no text
		info = dict(fontInfoVersion3)
		info["woffMetadataTrademark"] = dict()
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text not a list
		info = dict(fontInfoVersion3)
		info["woffMetadataTrademark"] = dict(text="abc")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item not a dict
		info = dict(fontInfoVersion3)
		info["woffMetadataTrademark"] = dict(text=["abc"])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item unknown key
		info = dict(fontInfoVersion3)
		info["woffMetadataTrademark"] = dict(text=[dict(text="foo", notTheRightKey=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text item missing text
		info = dict(fontInfoVersion3)
		info["woffMetadataTrademark"] = dict(text=[dict(language="foo")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## text not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataTrademark"] = dict(text=[dict(text=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## url not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataTrademark"] = dict(text=[dict(text="foo", url=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## language not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataTrademark"] = dict(text=[dict(text="foo", language=1)])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## dir not ltr or rtl
		info = dict(fontInfoVersion3)
		info["woffMetadataTrademark"] = dict(text=[dict(text="foo", dir="utd")])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## class not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataTrademark"] = dict(text=[{"text"  : "foo", "class" : 1}])
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# woffMetadataLicensee
		## no name
		info = dict(fontInfoVersion3)
		info["woffMetadataLicensee"] = dict()
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## unknown attribute
		info = dict(fontInfoVersion3)
		info["woffMetadataLicensee"] = dict(name="foo", notTheRightKey=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## name not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataLicensee"] = dict(name=1)
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## dir options
		info = dict(fontInfoVersion3)
		info["woffMetadataLicensee"] = dict(name="foo", dir="ltr")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		info = dict(fontInfoVersion3)
		info["woffMetadataLicensee"] = dict(name="foo", dir="rtl")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		## dir not ltr or rtl
		info = dict(fontInfoVersion3)
		info["woffMetadataLicensee"] = dict(name="foo", dir="utd")
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## have class
		info = dict(fontInfoVersion3)
		info["woffMetadataLicensee"] = {"name" : "foo", "class" : "hello"}
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		reader.readInfo(TestInfoObject())
		## class not a string
		info = dict(fontInfoVersion3)
		info["woffMetadataLicensee"] = {"name" : "foo", "class" : 1}
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())

	def testGuidelinesRead(self):
		# x
		## not an int or float
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x="1")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# y
		## not an int or float
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(y="1")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# angle
		## < 0
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, y=0, angle=-1)]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## > 360
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, y=0, angle=361)]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# name
		## not a string
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, name=1)]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# color
		## not a string
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color=1)]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## not enough commas
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="1 0, 0, 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="1 0 0, 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="1 0 0 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## not enough parts
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color=", 0, 0, 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="1, , 0, 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="1, 0, , 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="1, 0, 0, ")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color=", , , ")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## not a number in all positions
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="r, 1, 1, 1")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="1, g, 1, 1")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="1, 1, b, 1")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="1, 1, 1, a")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## too many parts
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="1, 0, 0, 0, 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## < 0 in each position
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="-1, 0, 0, 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="0, -1, 0, 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="0, 0, -1, 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="0, 0, 0, -1")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		## > 1 in each position
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="2, 0, 0, 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="0, 2, 0, 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="0, 0, 2, 0")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, color="0, 0, 0, 2")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())
		# identifier
		## duplicate
		info = dict(fontInfoVersion3)
		info["guidelines"] = [dict(x=0, identifier="guide1"), dict(y=0, identifier="guide1")]
		self._writeInfoToPlist(info)
		reader = UFOReader(self.dstDir, validate=True)
		self.assertRaises(UFOLibError, reader.readInfo, TestInfoObject())


class WriteFontInfoVersion3TestCase(unittest.TestCase):

	def setUp(self):
		self.tempDir = tempfile.mktemp()
		os.mkdir(self.tempDir)
		self.dstDir = os.path.join(self.tempDir, "test.ufo")

	def tearDown(self):
		shutil.rmtree(self.tempDir)

	def tearDownUFO(self):
		if os.path.exists(self.dstDir):
			shutil.rmtree(self.dstDir)

	def makeInfoObject(self):
		infoObject = TestInfoObject()
		for attr, value in list(fontInfoVersion3.items()):
			setattr(infoObject, attr, value)
		return infoObject

	def readPlist(self):
		path = os.path.join(self.dstDir, "fontinfo.plist")
		with open(path, "rb") as f:
			plist = plistlib.load(f)
		return plist

	def testWrite(self):
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		writtenData = self.readPlist()
		for attr, originalValue in list(fontInfoVersion3.items()):
			newValue = writtenData[attr]
			self.assertEqual(newValue, originalValue)
		self.tearDownUFO()

	def testGenericWrite(self):
		# familyName
		infoObject = self.makeInfoObject()
		infoObject.familyName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# styleName
		infoObject = self.makeInfoObject()
		infoObject.styleName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# styleMapFamilyName
		infoObject = self.makeInfoObject()
		infoObject.styleMapFamilyName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# styleMapStyleName
		## not a string
		infoObject = self.makeInfoObject()
		infoObject.styleMapStyleName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## out of range
		infoObject = self.makeInfoObject()
		infoObject.styleMapStyleName = "REGULAR"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# versionMajor
		infoObject = self.makeInfoObject()
		infoObject.versionMajor = "1"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# versionMinor
		infoObject = self.makeInfoObject()
		infoObject.versionMinor = "0"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# copyright
		infoObject = self.makeInfoObject()
		infoObject.copyright = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# trademark
		infoObject = self.makeInfoObject()
		infoObject.trademark = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# unitsPerEm
		infoObject = self.makeInfoObject()
		infoObject.unitsPerEm = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# descender
		infoObject = self.makeInfoObject()
		infoObject.descender = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# xHeight
		infoObject = self.makeInfoObject()
		infoObject.xHeight = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# capHeight
		infoObject = self.makeInfoObject()
		infoObject.capHeight = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# ascender
		infoObject = self.makeInfoObject()
		infoObject.ascender = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# italicAngle
		infoObject = self.makeInfoObject()
		infoObject.italicAngle = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()

	def testGaspWrite(self):
		# not a list
		infoObject = self.makeInfoObject()
		infoObject.openTypeGaspRangeRecords = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# empty list
		infoObject = self.makeInfoObject()
		infoObject.openTypeGaspRangeRecords = []
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		# not a dict
		infoObject = self.makeInfoObject()
		infoObject.openTypeGaspRangeRecords = ["abc"]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# dict not properly formatted
		infoObject = self.makeInfoObject()
		infoObject.openTypeGaspRangeRecords = [dict(rangeMaxPPEM=0xFFFF, notTheRightKey=1)]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeGaspRangeRecords = [dict(notTheRightKey=1, rangeGaspBehavior=[0])]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# not an int for ppem
		infoObject = self.makeInfoObject()
		infoObject.openTypeGaspRangeRecords = [dict(rangeMaxPPEM="abc", rangeGaspBehavior=[0]), dict(rangeMaxPPEM=0xFFFF, rangeGaspBehavior=[0])]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# not a list for behavior
		infoObject = self.makeInfoObject()
		infoObject.openTypeGaspRangeRecords = [dict(rangeMaxPPEM=10, rangeGaspBehavior="abc"), dict(rangeMaxPPEM=0xFFFF, rangeGaspBehavior=[0])]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# invalid behavior value
		infoObject = self.makeInfoObject()
		infoObject.openTypeGaspRangeRecords = [dict(rangeMaxPPEM=10, rangeGaspBehavior=[-1]), dict(rangeMaxPPEM=0xFFFF, rangeGaspBehavior=[0])]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# not sorted
		infoObject = self.makeInfoObject()
		infoObject.openTypeGaspRangeRecords = [dict(rangeMaxPPEM=0xFFFF, rangeGaspBehavior=[0]), dict(rangeMaxPPEM=10, rangeGaspBehavior=[0])]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# no 0xFFFF
		infoObject = self.makeInfoObject()
		infoObject.openTypeGaspRangeRecords = [dict(rangeMaxPPEM=10, rangeGaspBehavior=[0]), dict(rangeMaxPPEM=20, rangeGaspBehavior=[0])]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()

	def testHeadWrite(self):
		# openTypeHeadCreated
		## not a string
		infoObject = self.makeInfoObject()
		infoObject.openTypeHeadCreated = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## invalid format
		infoObject = self.makeInfoObject()
		infoObject.openTypeHeadCreated = "2000-Jan-01 00:00:00"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeHeadLowestRecPPEM
		infoObject = self.makeInfoObject()
		infoObject.openTypeHeadLowestRecPPEM = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeHeadFlags
		infoObject = self.makeInfoObject()
		infoObject.openTypeHeadFlags = [-1]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()

	def testHheaWrite(self):
		# openTypeHheaAscender
		infoObject = self.makeInfoObject()
		infoObject.openTypeHheaAscender = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeHheaDescender
		infoObject = self.makeInfoObject()
		infoObject.openTypeHheaDescender = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeHheaLineGap
		infoObject = self.makeInfoObject()
		infoObject.openTypeHheaLineGap = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeHheaCaretSlopeRise
		infoObject = self.makeInfoObject()
		infoObject.openTypeHheaCaretSlopeRise = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeHheaCaretSlopeRun
		infoObject = self.makeInfoObject()
		infoObject.openTypeHheaCaretSlopeRun = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeHheaCaretOffset
		infoObject = self.makeInfoObject()
		infoObject.openTypeHheaCaretOffset = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()

	def testNameWrite(self):
		# openTypeNameDesigner
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameDesigner = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameDesignerURL
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameDesignerURL = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameManufacturer
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameManufacturer = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameManufacturerURL
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameManufacturerURL = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameLicense
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameLicense = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameLicenseURL
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameLicenseURL = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameVersion
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameVersion = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameUniqueID
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameUniqueID = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameDescription
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameDescription = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNamePreferredFamilyName
		infoObject = self.makeInfoObject()
		infoObject.openTypeNamePreferredFamilyName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNamePreferredSubfamilyName
		infoObject = self.makeInfoObject()
		infoObject.openTypeNamePreferredSubfamilyName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameCompatibleFullName
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameCompatibleFullName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameSampleText
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameSampleText = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameWWSFamilyName
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameWWSFamilyName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameWWSSubfamilyName
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameWWSSubfamilyName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeNameRecords
		## not a list
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## not a dict
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = ["abc"]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## invalid dict structure
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [dict(foo="bar")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## incorrect keys
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(nameID=1, platformID=1, encodingID=1, languageID=1, string="Name Record.", foo="bar")
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(platformID=1, encodingID=1, languageID=1, string="Name Record.")
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(nameID=1, encodingID=1, languageID=1, string="Name Record.")
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(nameID=1, platformID=1, languageID=1, string="Name Record.")
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(nameID=1, platformID=1, encodingID=1, string="Name Record.")
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(nameID=1, platformID=1, encodingID=1, languageID=1)
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## invalid values
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(nameID="1", platformID=1, encodingID=1, languageID=1, string="Name Record.")
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(nameID=1, platformID="1", encodingID=1, languageID=1, string="Name Record.")
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(nameID=1, platformID=1, encodingID="1", languageID=1, string="Name Record.")
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(nameID=1, platformID=1, encodingID=1, languageID="1", string="Name Record.")
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(nameID=1, platformID=1, encodingID=1, languageID=1, string=1)
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## duplicate
		infoObject = self.makeInfoObject()
		infoObject.openTypeNameRecords = [
			dict(nameID=1, platformID=1, encodingID=1, languageID=1, string="Name Record."),
			dict(nameID=1, platformID=1, encodingID=1, languageID=1, string="Name Record.")
		]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)

	def testOS2Write(self):
		# openTypeOS2WidthClass
		## not an int
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2WidthClass = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## out or range
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2WidthClass = 15
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2WeightClass
		## not an int
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2WeightClass = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## out of range
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2WeightClass = -50
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2Selection
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2Selection = [-1]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2VendorID
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2VendorID = 1234
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2Panose
		## not an int
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2Panose = [0, 1, 2, 3, 4, 5, 6, 7, 8, str(9)]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## too few values
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2Panose = [0, 1, 2, 3]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## too many values
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2Panose = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2FamilyClass
		## not an int
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2FamilyClass = [0, str(1)]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## too few values
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2FamilyClass = [1]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## too many values
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2FamilyClass = [1, 1, 1]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## out of range
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2FamilyClass = [1, 20]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2UnicodeRanges
		## not an int
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2UnicodeRanges = ["0"]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## out of range
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2UnicodeRanges = [-1]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2CodePageRanges
		## not an int
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2CodePageRanges = ["0"]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## out of range
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2CodePageRanges = [-1]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2TypoAscender
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2TypoAscender = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2TypoDescender
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2TypoDescender = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2TypoLineGap
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2TypoLineGap = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2WinAscent
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2WinAscent = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2WinAscent = -1
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2WinDescent
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2WinDescent = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2WinDescent = -1
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2Type
		## not an int
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2Type = ["1"]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## out of range
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2Type = [-1]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2SubscriptXSize
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2SubscriptXSize = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2SubscriptYSize
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2SubscriptYSize = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2SubscriptXOffset
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2SubscriptXOffset = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2SubscriptYOffset
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2SubscriptYOffset = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2SuperscriptXSize
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2SuperscriptXSize = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2SuperscriptYSize
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2SuperscriptYSize = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2SuperscriptXOffset
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2SuperscriptXOffset = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2SuperscriptYOffset
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2SuperscriptYOffset = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2StrikeoutSize
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2StrikeoutSize = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeOS2StrikeoutPosition
		infoObject = self.makeInfoObject()
		infoObject.openTypeOS2StrikeoutPosition = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()

	def testVheaWrite(self):
		# openTypeVheaVertTypoAscender
		infoObject = self.makeInfoObject()
		infoObject.openTypeVheaVertTypoAscender = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeVheaVertTypoDescender
		infoObject = self.makeInfoObject()
		infoObject.openTypeVheaVertTypoDescender = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeVheaVertTypoLineGap
		infoObject = self.makeInfoObject()
		infoObject.openTypeVheaVertTypoLineGap = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeVheaCaretSlopeRise
		infoObject = self.makeInfoObject()
		infoObject.openTypeVheaCaretSlopeRise = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeVheaCaretSlopeRun
		infoObject = self.makeInfoObject()
		infoObject.openTypeVheaCaretSlopeRun = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# openTypeVheaCaretOffset
		infoObject = self.makeInfoObject()
		infoObject.openTypeVheaCaretOffset = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()

	def testFONDWrite(self):
		# macintoshFONDFamilyID
		infoObject = self.makeInfoObject()
		infoObject.macintoshFONDFamilyID = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# macintoshFONDName
		infoObject = self.makeInfoObject()
		infoObject.macintoshFONDName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()

	def testPostscriptWrite(self):
		# postscriptFontName
		infoObject = self.makeInfoObject()
		infoObject.postscriptFontName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptFullName
		infoObject = self.makeInfoObject()
		infoObject.postscriptFullName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptSlantAngle
		infoObject = self.makeInfoObject()
		infoObject.postscriptSlantAngle = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptUniqueID
		infoObject = self.makeInfoObject()
		infoObject.postscriptUniqueID = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptUnderlineThickness
		infoObject = self.makeInfoObject()
		infoObject.postscriptUnderlineThickness = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptUnderlinePosition
		infoObject = self.makeInfoObject()
		infoObject.postscriptUnderlinePosition = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptIsFixedPitch
		infoObject = self.makeInfoObject()
		infoObject.postscriptIsFixedPitch = 2
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptBlueValues
		## not a list
		infoObject = self.makeInfoObject()
		infoObject.postscriptBlueValues = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## uneven value count
		infoObject = self.makeInfoObject()
		infoObject.postscriptBlueValues = [500]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## too many values
		infoObject = self.makeInfoObject()
		infoObject.postscriptBlueValues = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptOtherBlues
		## not a list
		infoObject = self.makeInfoObject()
		infoObject.postscriptOtherBlues = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## uneven value count
		infoObject = self.makeInfoObject()
		infoObject.postscriptOtherBlues = [500]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## too many values
		infoObject = self.makeInfoObject()
		infoObject.postscriptOtherBlues = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptFamilyBlues
		## not a list
		infoObject = self.makeInfoObject()
		infoObject.postscriptFamilyBlues = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## uneven value count
		infoObject = self.makeInfoObject()
		infoObject.postscriptFamilyBlues = [500]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## too many values
		infoObject = self.makeInfoObject()
		infoObject.postscriptFamilyBlues = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptFamilyOtherBlues
		## not a list
		infoObject = self.makeInfoObject()
		infoObject.postscriptFamilyOtherBlues = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## uneven value count
		infoObject = self.makeInfoObject()
		infoObject.postscriptFamilyOtherBlues = [500]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## too many values
		infoObject = self.makeInfoObject()
		infoObject.postscriptFamilyOtherBlues = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptStemSnapH
		## not list
		infoObject = self.makeInfoObject()
		infoObject.postscriptStemSnapH = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## too many values
		infoObject = self.makeInfoObject()
		infoObject.postscriptStemSnapH = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptStemSnapV
		## not list
		infoObject = self.makeInfoObject()
		infoObject.postscriptStemSnapV = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## too many values
		infoObject = self.makeInfoObject()
		infoObject.postscriptStemSnapV = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptBlueFuzz
		infoObject = self.makeInfoObject()
		infoObject.postscriptBlueFuzz = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptBlueShift
		infoObject = self.makeInfoObject()
		infoObject.postscriptBlueShift = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptBlueScale
		infoObject = self.makeInfoObject()
		infoObject.postscriptBlueScale = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptForceBold
		infoObject = self.makeInfoObject()
		infoObject.postscriptForceBold = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptDefaultWidthX
		infoObject = self.makeInfoObject()
		infoObject.postscriptDefaultWidthX = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptNominalWidthX
		infoObject = self.makeInfoObject()
		infoObject.postscriptNominalWidthX = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptWeightName
		infoObject = self.makeInfoObject()
		infoObject.postscriptWeightName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptDefaultCharacter
		infoObject = self.makeInfoObject()
		infoObject.postscriptDefaultCharacter = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# postscriptWindowsCharacterSet
		infoObject = self.makeInfoObject()
		infoObject.postscriptWindowsCharacterSet = -1
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# macintoshFONDFamilyID
		infoObject = self.makeInfoObject()
		infoObject.macintoshFONDFamilyID = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# macintoshFONDName
		infoObject = self.makeInfoObject()
		infoObject.macintoshFONDName = 123
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()

	def testWOFFWrite(self):
		# woffMajorVersion
		infoObject = self.makeInfoObject()
		infoObject.woffMajorVersion = 1.0
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.woffMajorVersion = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# woffMinorVersion
		infoObject = self.makeInfoObject()
		infoObject.woffMinorVersion = 1.0
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.woffMinorVersion = "abc"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# woffMetadataUniqueID
		## none
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataUniqueID = None
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		## not a dict
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataUniqueID = 1
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## unknown key
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataUniqueID = dict(id="foo", notTheRightKey=1)
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## no id
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataUniqueID = dict()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## not a string for id
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataUniqueID = dict(id=1)
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## empty string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataUniqueID = dict(id="")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		# woffMetadataVendor
		## no name
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = dict(url="foo")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## name not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = dict(name=1, url="foo")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## name an empty string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = dict(name="", url="foo")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		## no URL
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = dict(name="foo")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		## url not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = dict(name="foo", url=1)
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## url empty string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = dict(name="foo", url="")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		## have dir
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = dict(name="foo", url="bar", dir="ltr")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = dict(name="foo", url="bar", dir="rtl")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		## dir not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = dict(name="foo", url="bar", dir=1)
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## dir not ltr or rtl
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = dict(name="foo", url="bar", dir="utd")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## have class
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = {"name"  : "foo", "url" : "bar", "class" : "hello"}
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		## class not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = {"name"  : "foo", "url" : "bar", "class" : 1}
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## class empty string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataVendor = {"name"  : "foo", "url" : "bar", "class" : ""}
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		# woffMetadataCredits
		## no credits attribute
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = {}
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## unknown attribute
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits=[dict(name="foo")], notTheRightKey=1)
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## not a list
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits="abc")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## no elements in credits
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits=[])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## credit not a dict
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits=["abc"])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## unknown key
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits=[dict(name="foo", notTheRightKey=1)])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## no name
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits=[dict(url="foo")])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## name not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits=[dict(name=1)])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## url not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits=[dict(name="foo", url=1)])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## role not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits=[dict(name="foo", role=1)])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## dir not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits=[dict(name="foo", dir=1)])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## dir not ltr or rtl
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits=[dict(name="foo", dir="utd")])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## class not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCredits = dict(credits=[{"name"  : "foo", "class" : 1}])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# woffMetadataDescription
		## no url
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(text=[dict(text="foo")])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		## url not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(text=[dict(text="foo")], url=1)
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## no text
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(url="foo")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text not a list
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(text="abc")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item not a dict
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(text=["abc"])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item unknown key
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(text=[dict(text="foo", notTheRightKey=1)])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item missing text
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(text=[dict(language="foo")])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(text=[dict(text=1)])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## url not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(text=[dict(text="foo", url=1)])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## language not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(text=[dict(text="foo", language=1)])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## dir not ltr or rtl
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(text=[dict(text="foo", dir="utd")])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## class not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataDescription = dict(text=[{"text"  : "foo", "class" : 1}])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# woffMetadataLicense
		## no url
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicense = dict(text=[dict(text="foo")])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		## url not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicense = dict(text=[dict(text="foo")], url=1)
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## id not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicense = dict(text=[dict(text="foo")], id=1)
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## no text
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicense = dict(url="foo")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		## text not a list
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicense = dict(text="abc")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item not a dict
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicense = dict(text=["abc"])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item unknown key
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicense = dict(text=[dict(text="foo", notTheRightKey=1)])
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item missing text
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataLicense = dict(text=[dict(language="foo")])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataLicense = dict(text=[dict(text=1)])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## url not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataLicense = dict(text=[dict(text="foo", url=1)])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## language not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataLicense = dict(text=[dict(text="foo", language=1)])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## dir not ltr or rtl
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataLicense = dict(text=[dict(text="foo", dir="utd")])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## class not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataLicense = dict(text=[{"text"  : "foo", "class" : 1}])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# woffMetadataCopyright
		## unknown attribute
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataCopyright = dict(text=[dict(text="foo")], notTheRightKey=1)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## no text
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataCopyright = dict()
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text not a list
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataCopyright = dict(text="abc")
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item not a dict
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataCopyright = dict(text=["abc"])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item unknown key
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataCopyright = dict(text=[dict(text="foo", notTheRightKey=1)])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item missing text
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataCopyright = dict(text=[dict(language="foo")])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataCopyright = dict(text=[dict(text=1)])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## url not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataCopyright = dict(text=[dict(text="foo", url=1)])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## language not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataCopyright = dict(text=[dict(text="foo", language=1)])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## dir not ltr or rtl
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataCopyright = dict(text=[dict(text="foo", dir="utd")])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## class not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataCopyright = dict(text=[{"text"  : "foo", "class" : 1}])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# woffMetadataTrademark
		## unknown attribute
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataTrademark = dict(text=[dict(text="foo")], notTheRightKey=1)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## no text
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataTrademark = dict()
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text not a list
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataTrademark = dict(text="abc")
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item not a dict
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataTrademark = dict(text=["abc"])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item unknown key
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataTrademark = dict(text=[dict(text="foo", notTheRightKey=1)])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text item missing text
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataTrademark = dict(text=[dict(language="foo")])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## text not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataTrademark = dict(text=[dict(text=1)])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## url not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataTrademark = dict(text=[dict(text="foo", url=1)])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## language not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataTrademark = dict(text=[dict(text="foo", language=1)])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## dir not ltr or rtl
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataTrademark = dict(text=[dict(text="foo", dir="utd")])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## class not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataTrademark = dict(text=[{"text"  : "foo", "class" : 1}])
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# woffMetadataLicensee
		## no name
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataLicensee = dict()
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## unknown attribute
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataLicensee = dict(name="foo", notTheRightKey=1)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## name not a string
		infoObject = self.makeInfoObject()
		writer = UFOWriter(self.dstDir, formatVersion=3)
		infoObject.woffMetadataLicensee = dict(name=1)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## dir options
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicensee = dict(name="foo", dir="ltr")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicensee = dict(name="foo", dir="rtl")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		## dir not ltr or rtl
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicensee = dict(name="foo", dir="utd")
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## have class
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicensee = {"name" : "foo", "class" : "hello"}
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeInfo(infoObject)
		self.tearDownUFO()
		## class not a string
		infoObject = self.makeInfoObject()
		infoObject.woffMetadataLicensee = {"name" : "foo", "class" : 1}
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()

	def testGuidelinesWrite(self):
		# x
		## not an int or float
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x="1")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# y
		## not an int or float
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(y="1")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# angle
		## < 0
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, y=0, angle=-1)]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## > 360
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, y=0, angle=361)]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# name
		## not a string
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, name=1)]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# color
		## not a string
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color=1)]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## not enough commas
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="1 0, 0, 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="1 0 0, 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="1 0 0 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## not enough parts
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color=", 0, 0, 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="1, , 0, 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="1, 0, , 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="1, 0, 0, ")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color=", , , ")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## not a number in all positions
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="r, 1, 1, 1")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="1, g, 1, 1")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="1, 1, b, 1")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="1, 1, 1, a")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## too many parts
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="1, 0, 0, 0, 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## < 0 in each position
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="-1, 0, 0, 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="0, -1, 0, 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="0, 0, -1, 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="0, 0, 0, -1")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## > 1 in each position
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="2, 0, 0, 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="0, 2, 0, 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="0, 0, 2, 0")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, color="0, 0, 0, 2")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		# identifier
		## duplicate
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, identifier="guide1"), dict(y=0, identifier="guide1")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## below min
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, identifier="\0x1F")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()
		## above max
		infoObject = self.makeInfoObject()
		infoObject.guidelines = [dict(x=0, identifier="\0x7F")]
		writer = UFOWriter(self.dstDir, formatVersion=3)
		self.assertRaises(UFOLibError, writer.writeInfo, info=infoObject)
		self.tearDownUFO()


# ------
# layers
# ------

class UFO3ReadLayersTestCase(unittest.TestCase):

	def setUp(self):
		self.tempDir = tempfile.mktemp()
		os.mkdir(self.tempDir)
		self.ufoPath = os.path.join(self.tempDir, "test.ufo")

	def tearDown(self):
		shutil.rmtree(self.tempDir)

	def makeUFO(self, metaInfo=None, layerContents=None):
		self.clearUFO()
		if not os.path.exists(self.ufoPath):
			os.mkdir(self.ufoPath)
		# metainfo.plist
		if metaInfo is None:
			metaInfo = dict(creator="test", formatVersion=3)
		path = os.path.join(self.ufoPath, "metainfo.plist")
		with open(path, "wb") as f:
			plistlib.dump(metaInfo, f)
		# layers
		if layerContents is None:
			layerContents = [
				("public.default", "glyphs"),
				("layer 1", "glyphs.layer 1"),
				("layer 2", "glyphs.layer 2"),
			]
		if layerContents:
			path = os.path.join(self.ufoPath, "layercontents.plist")
			with open(path, "wb") as f:
				plistlib.dump(layerContents, f)
		else:
			layerContents = [("", "glyphs")]
		for name, directory in layerContents:
			glyphsPath = os.path.join(self.ufoPath, directory)
			os.mkdir(glyphsPath)
			contents = dict(a="a.glif")
			path = os.path.join(glyphsPath, "contents.plist")
			with open(path, "wb") as f:
				plistlib.dump(contents, f)
			path = os.path.join(glyphsPath, "a.glif")
			with open(path, "w") as f:
				f.write(" ")

	def clearUFO(self):
		if os.path.exists(self.ufoPath):
			shutil.rmtree(self.ufoPath)

	# valid

	def testValidRead(self):
		# UFO 1
		self.makeUFO(
			metaInfo=dict(creator="test", formatVersion=1),
			layerContents=dict()
		)
		reader = UFOReader(self.ufoPath, validate=True)
		reader.getGlyphSet()
		# UFO 2
		self.makeUFO(
			metaInfo=dict(creator="test", formatVersion=2),
			layerContents=dict()
		)
		reader = UFOReader(self.ufoPath, validate=True)
		reader.getGlyphSet()
		# UFO 3
		self.makeUFO()
		reader = UFOReader(self.ufoPath, validate=True)
		reader.getGlyphSet()

	# missing layer contents

	def testMissingLayerContents(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		reader = UFOReader(self.ufoPath, validate=True)
		self.assertRaises(UFOLibError, reader.getGlyphSet)

	# layer contents invalid format

	def testInvalidLayerContentsFormat(self):
		# bogus
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		with open(path, "w") as f:
			f.write("test")
		reader = UFOReader(self.ufoPath, validate=True)
		self.assertRaises(UFOLibError, reader.getGlyphSet)
		# dict
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = {
			"public.default" : "glyphs",
			"layer 1" : "glyphs.layer 1",
			"layer 2" : "glyphs.layer 2",
		}
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		self.assertRaises(UFOLibError, reader.getGlyphSet)

	# layer contents invalid name format

	def testInvalidLayerContentsNameFormat(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			(1, "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		self.assertRaises(UFOLibError, reader.getGlyphSet)

	# layer contents invalid directory format

	def testInvalidLayerContentsDirectoryFormat(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("public.foregound", "glyphs"),
			("layer 1", 1),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		self.assertRaises(UFOLibError, reader.getGlyphSet)

	# directory listed in contents not on disk

	def testLayerContentsHasMissingDirectory(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("public.foregound", "glyphs"),
			("layer 1", "glyphs.doesnotexist"),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		self.assertRaises(UFOLibError, reader.getGlyphSet)

	# # directory on disk not listed in contents
	# XXX should this raise an error?
	#
	# def testLayerContentsHasMissingDirectory(self):
	# 	self.makeUFO()
	# 	path = os.path.join(self.ufoPath, "layercontents.plist")
	# 	os.remove(path)
	# 	layerContents = [
	# 		("public.foregound", "glyphs"),
	# 		("layer 1", "glyphs.layer 2")
	# 	]
	# 	with open(path, "wb") as f:
	# 		plistlib.dump(layerContents, f)
	# 	reader = UFOReader(self.ufoPath, validate=True)
	# 	with self.assertRaises(UFOLibError):
	# 		reader.getGlyphSet()

	# no default layer on disk

	def testMissingDefaultLayer(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		self.assertRaises(UFOLibError, reader.getGlyphSet)

	# duplicate layer name

	def testDuplicateLayerName(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("public.foregound", "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 1", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		self.assertRaises(UFOLibError, reader.getGlyphSet)

	# directory referenced by two layer names

	def testDuplicateLayerDirectory(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("public.foregound", "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 1")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		self.assertRaises(UFOLibError, reader.getGlyphSet)

	# default without a name

	def testDefaultLayerNoName(self):
		# get the glyph set
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("public.foregound", "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		reader.getGlyphSet()

	# default with a name

	def testDefaultLayerName(self):
		# get the name
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("custom name", "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 2")
		]
		expected = layerContents[0][0]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		result = reader.getDefaultLayerName()
		self.assertEqual(expected, result)
		# get the glyph set
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("custom name", "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		reader.getGlyphSet(expected)

	# layer order

	def testLayerOrder(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("public.foregound", "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 2")
		]
		expected = [name for (name, directory) in layerContents]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		result = reader.getLayerNames()
		self.assertEqual(expected, result)
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("layer 1", "glyphs.layer 1"),
			("public.foregound", "glyphs"),
			("layer 2", "glyphs.layer 2")
		]
		expected = [name for (name, directory) in layerContents]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		result = reader.getLayerNames()
		self.assertEqual(expected, result)
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("layer 2", "glyphs.layer 2"),
			("layer 1", "glyphs.layer 1"),
			("public.foregound", "glyphs")
		]
		expected = [name for (name, directory) in layerContents]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		reader = UFOReader(self.ufoPath, validate=True)
		result = reader.getLayerNames()
		self.assertEqual(expected, result)


class UFO3WriteLayersTestCase(unittest.TestCase):

	def setUp(self):
		self.tempDir = tempfile.mktemp()
		os.mkdir(self.tempDir)
		self.ufoPath = os.path.join(self.tempDir, "test.ufo")

	def tearDown(self):
		shutil.rmtree(self.tempDir)

	def makeUFO(self, metaInfo=None, layerContents=None):
		self.clearUFO()
		if not os.path.exists(self.ufoPath):
			os.mkdir(self.ufoPath)
		# metainfo.plist
		if metaInfo is None:
			metaInfo = dict(creator="test", formatVersion=3)
		path = os.path.join(self.ufoPath, "metainfo.plist")
		with open(path, "wb") as f:
			plistlib.dump(metaInfo, f)
		# layers
		if layerContents is None:
			layerContents = [
				("public.default", "glyphs"),
				("layer 1", "glyphs.layer 1"),
				("layer 2", "glyphs.layer 2"),
			]
		if layerContents:
			path = os.path.join(self.ufoPath, "layercontents.plist")
			with open(path, "wb") as f:
				plistlib.dump(layerContents, f)
		else:
			layerContents = [("", "glyphs")]
		for name, directory in layerContents:
			glyphsPath = os.path.join(self.ufoPath, directory)
			os.mkdir(glyphsPath)
			contents = dict(a="a.glif")
			path = os.path.join(glyphsPath, "contents.plist")
			with open(path, "wb") as f:
				plistlib.dump(contents, f)
			path = os.path.join(glyphsPath, "a.glif")
			with open(path, "w") as f:
				f.write(" ")

	def clearUFO(self):
		if os.path.exists(self.ufoPath):
			shutil.rmtree(self.ufoPath)

	# __init__: missing layer contents

	def testMissingLayerContents(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		self.assertRaises(UFOLibError, UFOWriter, self.ufoPath)

	# __init__: layer contents invalid format

	def testInvalidLayerContentsFormat(self):
		# bogus
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		with open(path, "w") as f:
			f.write("test")
		self.assertRaises(UFOLibError, UFOWriter, self.ufoPath)
		# dict
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = {
			"public.default" : "glyphs",
			"layer 1" : "glyphs.layer 1",
			"layer 2" : "glyphs.layer 2",
		}
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		self.assertRaises(UFOLibError, UFOWriter, self.ufoPath)

	# __init__: layer contents invalid name format

	def testInvalidLayerContentsNameFormat(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			(1, "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		self.assertRaises(UFOLibError, UFOWriter, self.ufoPath)

	# __init__: layer contents invalid directory format

	def testInvalidLayerContentsDirectoryFormat(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("public.foregound", "glyphs"),
			("layer 1", 1),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		self.assertRaises(UFOLibError, UFOWriter, self.ufoPath)

	# __init__: directory listed in contents not on disk

	def testLayerContentsHasMissingDirectory(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("public.foregound", "glyphs"),
			("layer 1", "glyphs.doesnotexist"),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		self.assertRaises(UFOLibError, UFOWriter, self.ufoPath)

	# __init__: no default layer on disk

	def testMissingDefaultLayer(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		self.assertRaises(UFOLibError, UFOWriter, self.ufoPath)

	# __init__: duplicate layer name

	def testDuplicateLayerName(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("public.foregound", "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 1", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		self.assertRaises(UFOLibError, UFOWriter, self.ufoPath)

	# __init__: directory referenced by two layer names

	def testDuplicateLayerDirectory(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("public.foregound", "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 1")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		self.assertRaises(UFOLibError, UFOWriter, self.ufoPath)

	# __init__: default without a name

	def testDefaultLayerNoName(self):
		# get the glyph set
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("public.foregound", "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		writer = UFOWriter(self.ufoPath)

	# __init__: default with a name

	def testDefaultLayerName(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "layercontents.plist")
		os.remove(path)
		layerContents = [
			("custom name", "glyphs"),
			("layer 1", "glyphs.layer 1"),
			("layer 2", "glyphs.layer 2")
		]
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		writer = UFOWriter(self.ufoPath)

	# __init__: up convert 1 > 3

	def testUpConvert1To3(self):
		self.makeUFO(
			metaInfo=dict(creator="test", formatVersion=1),
			layerContents=dict()
		)
		writer = UFOWriter(self.ufoPath)
		writer.writeLayerContents(["public.default"])
		path = os.path.join(self.ufoPath, "layercontents.plist")
		with open(path, "rb") as f:
			result = plistlib.load(f)
		expected = [["public.default", "glyphs"]]
		self.assertEqual(expected, result)

	# __init__: up convert 2 > 3

	def testUpConvert2To3(self):
		self.makeUFO(
			metaInfo=dict(creator="test", formatVersion=2),
			layerContents=dict()
		)
		writer = UFOWriter(self.ufoPath)
		writer.writeLayerContents(["public.default"])
		path = os.path.join(self.ufoPath, "layercontents.plist")
		with open(path, "rb") as f:
			result = plistlib.load(f)
		expected = [["public.default", "glyphs"]]
		self.assertEqual(expected, result)

	# __init__: down convert 3 > 1

	def testDownConvert3To1(self):
		self.makeUFO()
		self.assertRaises(UFOLibError, UFOWriter, self.ufoPath, formatVersion=1)

	# __init__: down convert 3 > 2

	def testDownConvert3To2(self):
		self.makeUFO()
		self.assertRaises(UFOLibError, UFOWriter, self.ufoPath, formatVersion=2)

	# get glyph sets

	def testGetGlyphSets(self):
		self.makeUFO()
		# hack contents.plist
		path = os.path.join(self.ufoPath, "glyphs.layer 1", "contents.plist")
		with open(path, "wb") as f:
			plistlib.dump(dict(b="a.glif"), f)
		path = os.path.join(self.ufoPath, "glyphs.layer 2", "contents.plist")
		with open(path, "wb") as f:
			plistlib.dump(dict(c="a.glif"), f)
		# now test
		writer = UFOWriter(self.ufoPath)
		# default
		expected = ["a"]
		result = list(writer.getGlyphSet().keys())
		self.assertEqual(expected, result)
		# layer 1
		expected = ["b"]
		result = list(writer.getGlyphSet("layer 1", defaultLayer=False).keys())
		self.assertEqual(expected, result)
		# layer 2
		expected = ["c"]
		result = list(writer.getGlyphSet("layer 2", defaultLayer=False).keys())
		self.assertEqual(expected, result)

	# make a new font with two layers

	def testNewFontOneLayer(self):
		self.clearUFO()
		writer = UFOWriter(self.ufoPath)
		writer.getGlyphSet()
		writer.writeLayerContents(["public.default"])
		# directory
		path = os.path.join(self.ufoPath, "glyphs")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		# layer contents
		path = os.path.join(self.ufoPath, "layercontents.plist")
		with open(path, "rb") as f:
			result = plistlib.load(f)
		expected = [["public.default", "glyphs"]]
		self.assertEqual(expected, result)

	def testNewFontThreeLayers(self):
		self.clearUFO()
		writer = UFOWriter(self.ufoPath)
		writer.getGlyphSet("layer 1", defaultLayer=False)
		writer.getGlyphSet()
		writer.getGlyphSet("layer 2", defaultLayer=False)
		writer.writeLayerContents(["layer 1", "public.default", "layer 2"])
		# directories
		path = os.path.join(self.ufoPath, "glyphs")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 1")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 2")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		# layer contents
		path = os.path.join(self.ufoPath, "layercontents.plist")
		with open(path, "rb") as f:
			result = plistlib.load(f)
		expected = [["layer 1", "glyphs.layer 1"], ["public.default", "glyphs"], ["layer 2", "glyphs.layer 2"]]
		self.assertEqual(expected, result)

	# add a layer to an existing font

	def testAddLayerToExistingFont(self):
		self.makeUFO()
		writer = UFOWriter(self.ufoPath)
		writer.getGlyphSet("layer 3", defaultLayer=False)
		writer.writeLayerContents(["public.default", "layer 1", "layer 2", "layer 3"])
		# directories
		path = os.path.join(self.ufoPath, "glyphs")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 1")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 2")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 3")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		# layer contents
		path = os.path.join(self.ufoPath, "layercontents.plist")
		with open(path, "rb") as f:
			result = plistlib.load(f)
		expected = [['public.default', 'glyphs'], ['layer 1', 'glyphs.layer 1'], ['layer 2', 'glyphs.layer 2'], ["layer 3", "glyphs.layer 3"]]
		self.assertEqual(expected, result)

	# rename valid name

	def testRenameLayer(self):
		self.makeUFO()
		writer = UFOWriter(self.ufoPath)
		writer.renameGlyphSet("layer 1", "layer 3")
		writer.writeLayerContents(["public.default", "layer 3", "layer 2"])
		# directories
		path = os.path.join(self.ufoPath, "glyphs")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 1")
		exists = os.path.exists(path)
		self.assertEqual(False, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 2")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 3")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		# layer contents
		path = os.path.join(self.ufoPath, "layercontents.plist")
		with open(path, "rb") as f:
			result = plistlib.load(f)
		expected = [['public.default', 'glyphs'], ['layer 3', 'glyphs.layer 3'], ['layer 2', 'glyphs.layer 2']]
		self.assertEqual(expected, result)

	def testRenameLayerDefault(self):
		self.makeUFO()
		writer = UFOWriter(self.ufoPath)
		writer.renameGlyphSet("public.default", "layer xxx")
		writer.renameGlyphSet("layer 1", "layer 1", defaultLayer=True)
		writer.writeLayerContents(["layer xxx", "layer 1", "layer 2"])
		path = os.path.join(self.ufoPath, "glyphs")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 1")
		exists = os.path.exists(path)
		self.assertEqual(False, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 2")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer xxx")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		# layer contents
		path = os.path.join(self.ufoPath, "layercontents.plist")
		with open(path, "rb") as f:
			result = plistlib.load(f)
		expected = [['layer xxx', 'glyphs.layer xxx'], ['layer 1', 'glyphs'], ['layer 2', 'glyphs.layer 2']]
		self.assertEqual(expected, result)

	# rename duplicate name

	def testRenameLayerDuplicateName(self):
		self.makeUFO()
		writer = UFOWriter(self.ufoPath)
		self.assertRaises(UFOLibError, writer.renameGlyphSet, "layer 1", "layer 2")

	# rename unknown layer

	def testRenameLayerUnknownName(self):
		self.makeUFO()
		writer = UFOWriter(self.ufoPath)
		self.assertRaises(UFOLibError, writer.renameGlyphSet, "does not exist", "layer 2")

	# remove valid layer

	def testRemoveLayer(self):
		self.makeUFO()
		writer = UFOWriter(self.ufoPath)
		writer.deleteGlyphSet("layer 1")
		writer.writeLayerContents(["public.default", "layer 2"])
		# directories
		path = os.path.join(self.ufoPath, "glyphs")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 1")
		exists = os.path.exists(path)
		self.assertEqual(False, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 2")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		# layer contents
		path = os.path.join(self.ufoPath, "layercontents.plist")
		with open(path, "rb") as f:
			result = plistlib.load(f)
		expected = [["public.default", "glyphs"], ["layer 2", "glyphs.layer 2"]]
		self.assertEqual(expected, result)

	# remove default layer

	def testRemoveDefaultLayer(self):
		self.makeUFO()
		writer = UFOWriter(self.ufoPath)
		writer.deleteGlyphSet("public.default")
		# directories
		path = os.path.join(self.ufoPath, "glyphs")
		exists = os.path.exists(path)
		self.assertEqual(False, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 1")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		path = os.path.join(self.ufoPath, "glyphs.layer 2")
		exists = os.path.exists(path)
		self.assertEqual(True, exists)
		# layer contents
		path = os.path.join(self.ufoPath, "layercontents.plist")
		with open(path, "rb") as f:
			result = plistlib.load(f)
		expected = [["layer 1", "glyphs.layer 1"], ["layer 2", "glyphs.layer 2"]]
		self.assertEqual(expected, result)

	# remove unknown layer

	def testRemoveDefaultLayer(self):
		self.makeUFO()
		writer = UFOWriter(self.ufoPath)
		self.assertRaises(UFOLibError, writer.deleteGlyphSet, "does not exist")

	def testWriteAsciiLayerOrder(self):
		self.makeUFO(
			layerContents=[
				["public.default", "glyphs"],
				["layer 1", "glyphs.layer 1"],
				["layer 2", "glyphs.layer 2"],
			]
		)
		writer = UFOWriter(self.ufoPath)
		# if passed bytes string, it'll be decoded to ASCII unicode string
		writer.writeLayerContents(["public.default", "layer 2", b"layer 1"])
		path = os.path.join(self.ufoPath, "layercontents.plist")
		with open(path, "rb") as f:
			result = plistlib.load(f)
		expected = [
			["public.default", "glyphs"],
			["layer 2", "glyphs.layer 2"],
			["layer 1", "glyphs.layer 1"],
		]
		self.assertEqual(expected, result)
		for layerName, directory in result:
			assert isinstance(layerName, unicode)

# -----
# /data
# -----


class UFO3ReadDataTestCase(unittest.TestCase):

	def getFontPath(self):
		testdata = os.path.join(os.path.dirname(__file__), "testdata")
		return os.path.join(testdata, "UFO3-Read Data.ufo")

	def testUFOReaderDataDirectoryListing(self):
		reader = UFOReader(self.getFontPath())
		found = reader.getDataDirectoryListing()
		expected = [
			'org.unifiedfontobject.directory/bar/lol.txt',
			'org.unifiedfontobject.directory/foo.txt',
			'org.unifiedfontobject.file.txt'
		]
		self.assertEqual(set(found), set(expected))

	def testUFOReaderBytesFromPath(self):
		reader = UFOReader(self.getFontPath())
		found = reader.readBytesFromPath("data/org.unifiedfontobject.file.txt")
		expected = b"file.txt"
		self.assertEqual(found, expected)
		found = reader.readBytesFromPath("data/org.unifiedfontobject.directory/bar/lol.txt")
		expected = b"lol.txt"
		self.assertEqual(found, expected)
		found = reader.readBytesFromPath("data/org.unifiedfontobject.doesNotExist")
		expected = None
		self.assertEqual(found, expected)

	def testUFOReaderReadFileFromPath(self):
		reader = UFOReader(self.getFontPath())
		fileObject = reader.getReadFileForPath("data/org.unifiedfontobject.file.txt")
		self.assertNotEqual(fileObject, None)
		hasRead = hasattr(fileObject, "read")
		self.assertEqual(hasRead, True)
		fileObject.close()
		fileObject = reader.getReadFileForPath("data/org.unifiedfontobject.doesNotExist")
		self.assertEqual(fileObject, None)


class UFO3WriteDataTestCase(unittest.TestCase):

	def setUp(self):
		self.tempDir = tempfile.mktemp()
		os.mkdir(self.tempDir)
		self.dstDir = os.path.join(self.tempDir, "test.ufo")

	def tearDown(self):
		shutil.rmtree(self.tempDir)

	def tearDownUFO(self):
		if os.path.exists(self.dstDir):
			shutil.rmtree(self.dstDir)

	def testUFOWriterWriteBytesToPath(self):
		# basic file
		path = "data/org.unifiedfontobject.writebytesbasicfile.txt"
		testBytes = b"test"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeBytesToPath(path, testBytes)
		path = os.path.join(self.dstDir, path)
		self.assertEqual(os.path.exists(path), True)
		with open(path, "rb") as f:
			written = f.read()
		self.assertEqual(testBytes, written)
		self.tearDownUFO()
		# basic file with unicode text
		path = "data/org.unifiedfontobject.writebytesbasicunicodefile.txt"
		text = b"t\xeb\xdft"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeBytesToPath(path, text)
		path = os.path.join(self.dstDir, path)
		self.assertEqual(os.path.exists(path), True)
		with open(path, "rb") as f:
			written = f.read()
		self.assertEqual(text, written)
		self.tearDownUFO()
		# basic directory
		path = "data/org.unifiedfontobject.writebytesdirectory/level1/level2/file.txt"
		testBytes = b"test"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeBytesToPath(path, testBytes)
		path = os.path.join(self.dstDir, path)
		self.assertEqual(os.path.exists(path), True)
		with open(path, "rb") as f:
			written = f.read()
		self.assertEqual(testBytes, written)
		self.tearDownUFO()

	def testUFOWriterWriteFileToPath(self):
		# basic file
		path = "data/org.unifiedfontobject.getwritefile.txt"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		fileObject = writer.getFileObjectForPath(path)
		self.assertNotEqual(fileObject, None)
		hasRead = hasattr(fileObject, "read")
		self.assertEqual(hasRead, True)
		fileObject.close()
		self.tearDownUFO()

	def testUFOWriterRemoveFile(self):
		path1 = "data/org.unifiedfontobject.removefile/level1/level2/file1.txt"
		path2 = "data/org.unifiedfontobject.removefile/level1/level2/file2.txt"
		path3 = "data/org.unifiedfontobject.removefile/level1/file3.txt"
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.writeBytesToPath(path1, b"test")
		writer.writeBytesToPath(path2, b"test")
		writer.writeBytesToPath(path3, b"test")
		self.assertEqual(os.path.exists(os.path.join(self.dstDir, path1)), True)
		self.assertEqual(os.path.exists(os.path.join(self.dstDir, path2)), True)
		self.assertEqual(os.path.exists(os.path.join(self.dstDir, path3)), True)
		writer.removeFileForPath(path1)
		self.assertEqual(os.path.exists(os.path.join(self.dstDir, path1)), False)
		self.assertEqual(os.path.exists(os.path.dirname(os.path.join(self.dstDir, path1))), True)
		self.assertEqual(os.path.exists(os.path.join(self.dstDir, path2)), True)
		self.assertEqual(os.path.exists(os.path.join(self.dstDir, path3)), True)
		writer.removeFileForPath(path2)
		self.assertEqual(os.path.exists(os.path.dirname(os.path.join(self.dstDir, path1))), False)
		self.assertEqual(os.path.exists(os.path.join(self.dstDir, path2)), False)
		self.assertEqual(os.path.exists(os.path.join(self.dstDir, path3)), True)
		writer.removeFileForPath(path3)
		self.assertEqual(os.path.exists(os.path.join(self.dstDir, path3)), False)
		self.assertEqual(os.path.exists(os.path.dirname(os.path.join(self.dstDir, path2))), False)
		self.assertEqual(os.path.exists(os.path.join(self.dstDir, "data/org.unifiedfontobject.removefile")), False)
		self.assertRaises(UFOLibError, writer.removeFileForPath, path="data/org.unifiedfontobject.doesNotExist.txt")
		self.tearDownUFO()

	def testUFOWriterCopy(self):
		sourceDir = self.dstDir.replace(".ufo", "") + "-copy source" + ".ufo"
		dataPath = "data/org.unifiedfontobject.copy/level1/level2/file1.txt"
		writer = UFOWriter(sourceDir, formatVersion=3)
		writer.writeBytesToPath(dataPath, b"test")
		# copy a file
		reader = UFOReader(sourceDir)
		writer = UFOWriter(self.dstDir, formatVersion=3)
		writer.copyFromReader(reader, dataPath, dataPath)
		path = os.path.join(self.dstDir, dataPath)
		self.assertEqual(os.path.exists(path), True)
		self.tearDownUFO()
		# copy a directory
		reader = UFOReader(sourceDir)
		writer = UFOWriter(self.dstDir, formatVersion=3)
		p = "data/org.unifiedfontobject.copy"
		writer.copyFromReader(reader, p, p)
		path = os.path.join(self.dstDir, dataPath)
		self.assertEqual(os.path.exists(path), True)
		self.tearDownUFO()

# ---------------
# layerinfo.plist
# ---------------

class TestLayerInfoObject(object):

	color = guidelines = lib = None


class UFO3ReadLayerInfoTestCase(unittest.TestCase):

	def setUp(self):
		self.tempDir = tempfile.mktemp()
		os.mkdir(self.tempDir)
		self.ufoPath = os.path.join(self.tempDir, "test.ufo")

	def tearDown(self):
		shutil.rmtree(self.tempDir)

	def makeUFO(self, formatVersion=3, layerInfo=None):
		self.clearUFO()
		if not os.path.exists(self.ufoPath):
			os.mkdir(self.ufoPath)
		# metainfo.plist
		metaInfo = dict(creator="test", formatVersion=formatVersion)
		path = os.path.join(self.ufoPath, "metainfo.plist")
		with open(path, "wb") as f:
			plistlib.dump(metaInfo, f)
		# layercontents.plist
		layerContents = [("public.default", "glyphs")]
		path = os.path.join(self.ufoPath, "layercontents.plist")
		with open(path, "wb") as f:
			plistlib.dump(layerContents, f)
		# glyphs
		glyphsPath = os.path.join(self.ufoPath, "glyphs")
		os.mkdir(glyphsPath)
		contents = dict(a="a.glif")
		path = os.path.join(glyphsPath, "contents.plist")
		with open(path, "wb") as f:
			plistlib.dump(contents, f)
		path = os.path.join(glyphsPath, "a.glif")
		with open(path, "w") as f:
			f.write(" ")
		# layerinfo.plist
		if layerInfo is None:
			layerInfo = dict(
				color="0,0,0,1",
				lib={"foo" : "bar"}
			)
		path = os.path.join(glyphsPath, "layerinfo.plist")
		with open(path, "wb") as f:
			plistlib.dump(layerInfo, f)

	def clearUFO(self):
		if os.path.exists(self.ufoPath):
			shutil.rmtree(self.ufoPath)

	def testValidLayerInfo(self):
		self.makeUFO()
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		info = TestLayerInfoObject()
		glyphSet.readLayerInfo(info)
		expectedColor = "0,0,0,1"
		self.assertEqual(expectedColor, info.color)
		expectedLib = {"foo": "bar"}
		self.assertEqual(expectedLib, info.lib)

	def testMissingLayerInfo(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "glyphs", "layerinfo.plist")
		os.remove(path)
		# read
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		info = TestLayerInfoObject()
		glyphSet.readLayerInfo(info)
		self.assertEqual(None, info.color)
		self.assertEqual(None, info.guidelines)
		self.assertEqual(None, info.lib)

	def testBogusLayerInfo(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "glyphs", "layerinfo.plist")
		os.remove(path)
		with open(path, "w") as f:
			f.write("test")
		# read
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		info = TestLayerInfoObject()
		self.assertRaises(UFOLibError, glyphSet.readLayerInfo, info)

	def testInvalidFormatLayerInfo(self):
		self.makeUFO()
		path = os.path.join(self.ufoPath, "glyphs", "layerinfo.plist")
		info = [("color", "0,0,0,0")]
		with open(path, "wb") as f:
			plistlib.dump(info, f)
		# read
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		info = TestLayerInfoObject()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, info)

	def testColor(self):
		## not a string
		info = {}
		info["color"] = 1
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		## not enough commas
		info = {}
		info["color"] = "1 0, 0, 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "1 0 0, 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "1 0 0 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		## not enough parts
		info = {}
		info["color"] = ", 0, 0, 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "1, , 0, 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "1, 0, , 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "1, 0, 0, "
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = ", , , "
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		## not a number in all positions
		info = {}
		info["color"] = "r, 1, 1, 1"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "1, g, 1, 1"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "1, 1, b, 1"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "1, 1, 1, a"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		## too many parts
		info = {}
		info["color"] = "1, 0, 0, 0, 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		## < 0 in each position
		info = {}
		info["color"] = "-1, 0, 0, 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "0, -1, 0, 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "0, 0, -1, 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "0, 0, 0, -1"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		## > 1 in each position
		info = {}
		info["color"] = "2, 0, 0, 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "0, 2, 0, 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "0, 0, 2, 0"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())
		info = {}
		info["color"] = "0, 0, 0, 2"
		self.makeUFO(layerInfo=info)
		reader = UFOReader(self.ufoPath, validate=True)
		glyphSet = reader.getGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.readLayerInfo, TestLayerInfoObject())


class UFO3WriteLayerInfoTestCase(unittest.TestCase):

	def setUp(self):
		self.tempDir = tempfile.mktemp()
		os.mkdir(self.tempDir)
		self.ufoPath = os.path.join(self.tempDir, "test.ufo")

	def tearDown(self):
		shutil.rmtree(self.tempDir)

	def makeGlyphSet(self):
		self.clearUFO()
		writer = UFOWriter(self.ufoPath)
		return writer.getGlyphSet()

	def clearUFO(self):
		if os.path.exists(self.ufoPath):
			shutil.rmtree(self.ufoPath)

	def testValidWrite(self):
		expected = dict(
			color="0,0,0,1",
			lib={"foo" : "bar"}
		)
		info = TestLayerInfoObject()
		info.color = expected["color"]
		info.lib = expected["lib"]
		glyphSet = self.makeGlyphSet()
		glyphSet.writeLayerInfo(info)
		path = os.path.join(self.ufoPath, "glyphs", "layerinfo.plist")
		with open(path, "rb") as f:
			result = plistlib.load(f)
		self.assertEqual(expected, result)

	def testColor(self):
		## not a string
		info = TestLayerInfoObject()
		info.color = 1
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		## not enough commas
		info = TestLayerInfoObject()
		info.color = "1 0, 0, 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "1 0 0, 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "1 0 0 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		## not enough parts
		info = TestLayerInfoObject()
		info.color = ", 0, 0, 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "1, , 0, 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "1, 0, , 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "1, 0, 0, "
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = ", , , "
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		## not a number in all positions
		info = TestLayerInfoObject()
		info.color = "r, 1, 1, 1"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "1, g, 1, 1"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "1, 1, b, 1"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "1, 1, 1, a"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		## too many parts
		info = TestLayerInfoObject()
		info.color = "1, 0, 0, 0, 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		## < 0 in each position
		info = TestLayerInfoObject()
		info.color = "-1, 0, 0, 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "0, -1, 0, 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "0, 0, -1, 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "0, 0, 0, -1"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		## > 1 in each position
		info = TestLayerInfoObject()
		info.color = "2, 0, 0, 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "0, 2, 0, 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "0, 0, 2, 0"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
		info = TestLayerInfoObject()
		info.color = "0, 0, 0, 2"
		glyphSet = self.makeGlyphSet()
		self.assertRaises(GlifLibError, glyphSet.writeLayerInfo, info)
