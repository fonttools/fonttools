import os
import shutil
import unittest
import tempfile
from io import open
from fontTools.ufoLib import UFOReader, UFOWriter, UFOLibError
from fontTools.ufoLib import plistlib
from .testSupport import fontInfoVersion1, fontInfoVersion2


class TestInfoObject:
    pass


class ReadFontInfoVersion1TestCase(unittest.TestCase):
    def setUp(self):
        self.dstDir = tempfile.mktemp()
        os.mkdir(self.dstDir)
        metaInfo = {"creator": "test", "formatVersion": 1}
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
        originalData = dict(fontInfoVersion1)
        self._writeInfoToPlist(originalData)
        infoObject = TestInfoObject()
        reader = UFOReader(self.dstDir, validate=True)
        reader.readInfo(infoObject)
        for attr in dir(infoObject):
            if attr not in fontInfoVersion2:
                continue
            originalValue = fontInfoVersion2[attr]
            readValue = getattr(infoObject, attr)
            self.assertEqual(originalValue, readValue)

    def testFontStyleConversion(self):
        fontStyle1To2 = {64: "regular", 1: "italic", 32: "bold", 33: "bold italic"}
        for old, new in list(fontStyle1To2.items()):
            info = dict(fontInfoVersion1)
            info["fontStyle"] = old
            self._writeInfoToPlist(info)
            reader = UFOReader(self.dstDir, validate=True)
            infoObject = TestInfoObject()
            reader.readInfo(infoObject)
            self.assertEqual(new, infoObject.styleMapStyleName)

    def testWidthNameConversion(self):
        widthName1To2 = {
            "Ultra-condensed": 1,
            "Extra-condensed": 2,
            "Condensed": 3,
            "Semi-condensed": 4,
            "Medium (normal)": 5,
            "Semi-expanded": 6,
            "Expanded": 7,
            "Extra-expanded": 8,
            "Ultra-expanded": 9,
        }
        for old, new in list(widthName1To2.items()):
            info = dict(fontInfoVersion1)
            info["widthName"] = old
            self._writeInfoToPlist(info)
            reader = UFOReader(self.dstDir, validate=True)
            infoObject = TestInfoObject()
            reader.readInfo(infoObject)
            self.assertEqual(new, infoObject.openTypeOS2WidthClass)


class WriteFontInfoVersion1TestCase(unittest.TestCase):
    def setUp(self):
        self.tempDir = tempfile.mktemp()
        os.mkdir(self.tempDir)
        self.dstDir = os.path.join(self.tempDir, "test.ufo")

    def tearDown(self):
        shutil.rmtree(self.tempDir)

    def makeInfoObject(self):
        infoObject = TestInfoObject()
        for attr, value in list(fontInfoVersion2.items()):
            setattr(infoObject, attr, value)
        return infoObject

    def readPlist(self):
        path = os.path.join(self.dstDir, "fontinfo.plist")
        with open(path, "rb") as f:
            plist = plistlib.load(f)
        return plist

    def testWrite(self):
        infoObject = self.makeInfoObject()
        writer = UFOWriter(self.dstDir, formatVersion=1)
        writer.writeInfo(infoObject)
        writtenData = self.readPlist()
        for attr, originalValue in list(fontInfoVersion1.items()):
            newValue = writtenData[attr]
            self.assertEqual(newValue, originalValue)

    def testFontStyleConversion(self):
        fontStyle1To2 = {64: "regular", 1: "italic", 32: "bold", 33: "bold italic"}
        for old, new in list(fontStyle1To2.items()):
            infoObject = self.makeInfoObject()
            infoObject.styleMapStyleName = new
            writer = UFOWriter(self.dstDir, formatVersion=1)
            writer.writeInfo(infoObject)
            writtenData = self.readPlist()
            self.assertEqual(writtenData["fontStyle"], old)

    def testWidthNameConversion(self):
        widthName1To2 = {
            "Ultra-condensed": 1,
            "Extra-condensed": 2,
            "Condensed": 3,
            "Semi-condensed": 4,
            "Medium (normal)": 5,
            "Semi-expanded": 6,
            "Expanded": 7,
            "Extra-expanded": 8,
            "Ultra-expanded": 9,
        }
        for old, new in list(widthName1To2.items()):
            infoObject = self.makeInfoObject()
            infoObject.openTypeOS2WidthClass = new
            writer = UFOWriter(self.dstDir, formatVersion=1)
            writer.writeInfo(infoObject)
            writtenData = self.readPlist()
            self.assertEqual(writtenData["widthName"], old)
