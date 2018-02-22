# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.loggingTools import CapturingLogHandler
from fontTools.misc.testTools import FakeFont
from fontTools.misc.xmlWriter import XMLWriter
import struct
import unittest
from fontTools.ttLib import newTable
from fontTools.ttLib.tables._n_a_m_e import (
	table__n_a_m_e, NameRecord, nameRecordFormat, nameRecordSize, makeName, log)


def names(nameTable):
	result = [(n.nameID, n.platformID, n.platEncID, n.langID, n.string)
                  for n in nameTable.names]
	result.sort()
	return result


class NameTableTest(unittest.TestCase):

	def test_getDebugName(self):
		table = table__n_a_m_e()
		table.names = [
			makeName("Bold", 258, 1, 0, 0),  # Mac, MacRoman, English
			makeName("Gras", 258, 1, 0, 1),  # Mac, MacRoman, French
			makeName("Fett", 258, 1, 0, 2),  # Mac, MacRoman, German
			makeName("Sem Fracções", 292, 1, 0, 8)  # Mac, MacRoman, Portuguese
		]
		self.assertEqual("Bold", table.getDebugName(258))
		self.assertEqual("Sem Fracções", table.getDebugName(292))
		self.assertEqual(None, table.getDebugName(999))

	def test_setName(self):
		table = table__n_a_m_e()
		table.setName("Regular", 2, 1, 0, 0)
		table.setName("Version 1.000", 5, 3, 1, 0x409)
		table.setName("寬鬆", 276, 1, 2, 0x13)
		self.assertEqual("Regular", table.getName(2, 1, 0, 0).toUnicode())
		self.assertEqual("Version 1.000", table.getName(5, 3, 1, 0x409).toUnicode())
		self.assertEqual("寬鬆", table.getName(276, 1, 2, 0x13).toUnicode())
		self.assertTrue(len(table.names) == 3)
		table.setName("緊縮", 276, 1, 2, 0x13)
		self.assertEqual("緊縮", table.getName(276, 1, 2, 0x13).toUnicode())
		self.assertTrue(len(table.names) == 3)
		# passing bytes issues a warning
		with CapturingLogHandler(log, "WARNING") as captor:
			table.setName(b"abc", 0, 1, 0, 0)
		self.assertTrue(
			len([r for r in captor.records if "string is bytes" in r.msg]) == 1)
		# anything other than unicode or bytes raises an error
		with self.assertRaises(TypeError):
			table.setName(1.000, 5, 1, 0, 0)

	def test_addName(self):
		table = table__n_a_m_e()
		nameIDs = []
		for string in ("Width", "Weight", "Custom"):
			nameIDs.append(table.addName(string))

		self.assertEqual(nameIDs[0], 256)
		self.assertEqual(nameIDs[1], 257)
		self.assertEqual(nameIDs[2], 258)
		self.assertEqual(len(table.names), 6)
		self.assertEqual(table.names[0].string, "Width")
		self.assertEqual(table.names[1].string, "Width")
		self.assertEqual(table.names[2].string, "Weight")
		self.assertEqual(table.names[3].string, "Weight")
		self.assertEqual(table.names[4].string, "Custom")
		self.assertEqual(table.names[5].string, "Custom")

		with self.assertRaises(ValueError):
			table.addName('Invalid nameID', minNameID=32767)
		with self.assertRaises(TypeError):
			table.addName(b"abc")  # must be unicode string

	def test_addMultilingualName(self):
		# Microsoft Windows has language codes for “English” (en)
		# and for “Standard German as used in Switzerland” (de-CH).
		# In this case, we expect that the implementation just
		# encodes the name for the Windows platform; Apple platforms
		# have been able to decode Windows names since the early days
		# of OSX (~2001). However, Windows has no language code for
		# “Swiss German as used in Liechtenstein” (gsw-LI), so we
		# expect that the implementation populates the 'ltag' table
 		# to represent that particular, rather exotic BCP47 code.
		font = FakeFont(glyphs=[".notdef", "A"])
		nameTable = font.tables['name'] = newTable("name")
		with CapturingLogHandler(log, "WARNING") as captor:
			widthID = nameTable.addMultilingualName({
				"en": "Width",
				"de-CH": "Breite",
				"gsw-LI": "Bräiti",
			}, ttFont=font)
			self.assertEqual(widthID, 256)
			xHeightID = nameTable.addMultilingualName({
				"en": "X-Height",
				"gsw-LI": "X-Hööchi"
			}, ttFont=font)
			self.assertEqual(xHeightID, 257)
		captor.assertRegex("cannot add Windows name in language gsw-LI")
		self.assertEqual(names(nameTable), [
			(256, 0, 4,      0, "Bräiti"),
			(256, 3, 1, 0x0409, "Width"),
			(256, 3, 1, 0x0807, "Breite"),
			(257, 0, 4,      0, "X-Hööchi"),
			(257, 3, 1, 0x0409, "X-Height"),
		])
		self.assertEqual(set(font.tables.keys()), {"ltag", "name"})
		self.assertEqual(font["ltag"].tags, ["gsw-LI"])

	def test_addMultilingualName_legacyMacEncoding(self):
		# Windows has no language code for Latin; MacOS has a code;
		# and we actually can convert the name to the legacy MacRoman
		# encoding. In this case, we expect that the name gets encoded
		# as Macintosh name (platformID 1) with the corresponding Mac
		# language code (133); the 'ltag' table should not be used.
		font = FakeFont(glyphs=[".notdef", "A"])
		nameTable = font.tables['name'] = newTable("name")
		with CapturingLogHandler(log, "WARNING") as captor:
			nameTable.addMultilingualName({"la": "SPQR"},
			                              ttFont=font)
		captor.assertRegex("cannot add Windows name in language la")
		self.assertEqual(names(nameTable), [(256, 1, 0, 131, "SPQR")])
		self.assertNotIn("ltag", font.tables.keys())

	def test_addMultilingualName_legacyMacEncodingButUnencodableName(self):
		# Windows has no language code for Latin; MacOS has a code;
		# but we cannot encode the name into this encoding because
		# it contains characters that are not representable.
		# In this case, we expect that the name gets encoded as
		# Unicode name (platformID 0) with the language tag being
		# added to the 'ltag' table.
		font = FakeFont(glyphs=[".notdef", "A"])
		nameTable = font.tables['name'] = newTable("name")
		with CapturingLogHandler(log, "WARNING") as captor:
			nameTable.addMultilingualName({"la": "ⱾƤℚⱤ"},
			                              ttFont=font)
		captor.assertRegex("cannot add Windows name in language la")
		self.assertEqual(names(nameTable), [(256, 0, 4, 0, "ⱾƤℚⱤ")])
		self.assertIn("ltag", font.tables)
		self.assertEqual(font["ltag"].tags, ["la"])

	def test_addMultilingualName_legacyMacEncodingButNoCodec(self):
		# Windows has no language code for “Azeri written in the
		# Arabic script” (az-Arab); MacOS would have a code (50);
		# but we cannot encode the name into the legacy encoding
		# because we have no codec for MacArabic in fonttools.
		# In this case, we expect that the name gets encoded as
		# Unicode name (platformID 0) with the language tag being
		# added to the 'ltag' table.
		font = FakeFont(glyphs=[".notdef", "A"])
		nameTable = font.tables['name'] = newTable("name")
		with CapturingLogHandler(log, "WARNING") as captor:
			nameTable.addMultilingualName({"az-Arab": "آذربايجان ديلی"},
			                              ttFont=font)
		captor.assertRegex("cannot add Windows name in language az-Arab")
		self.assertEqual(names(nameTable), [(256, 0, 4, 0, "آذربايجان ديلی")])
		self.assertIn("ltag", font.tables)
		self.assertEqual(font["ltag"].tags, ["az-Arab"])

	def test_addMultilingualName_noTTFont(self):
		# If the ttFont argument is not passed, the implementation
		# should add whatever names it can, but it should not crash
		# just because it cannot build an ltag table.
		nameTable = newTable("name")
		with CapturingLogHandler(log, "WARNING") as captor:
			nameTable.addMultilingualName({"en": "A", "la": "ⱾƤℚⱤ"})
		captor.assertRegex("cannot store language la into 'ltag' table")

	def test_decompile_badOffset(self):
                # https://github.com/behdad/fonttools/issues/525
		table = table__n_a_m_e()
		badRecord = {
			"platformID": 1,
			"platEncID": 3,
			"langID": 7,
			"nameID": 1,
			"length": 3,
			"offset": 8765  # out of range
		}
		data = bytesjoin([
                        struct.pack(tostr(">HHH"), 1, 1, 6 + nameRecordSize),
                        sstruct.pack(nameRecordFormat, badRecord)])
		table.decompile(data, ttFont=None)
		self.assertEqual(table.names, [])


class NameRecordTest(unittest.TestCase):

	def test_toUnicode_utf16be(self):
		name = makeName("Foo Bold", 111, 0, 2, 7)
		self.assertEqual("utf_16_be", name.getEncoding())
		self.assertEqual("Foo Bold", name.toUnicode())

	def test_toUnicode_macroman(self):
		name = makeName("Foo Italic", 222, 1, 0, 7)  # MacRoman
		self.assertEqual("mac_roman", name.getEncoding())
		self.assertEqual("Foo Italic", name.toUnicode())

	def test_toUnicode_macromanian(self):
		name = makeName(b"Foo Italic\xfb", 222, 1, 0, 37)  # Mac Romanian
		self.assertEqual("mac_romanian", name.getEncoding())
		self.assertEqual("Foo Italic"+unichr(0x02DA), name.toUnicode())

	def test_toUnicode_UnicodeDecodeError(self):
		name = makeName(b"\1", 111, 0, 2, 7)
		self.assertEqual("utf_16_be", name.getEncoding())
		self.assertRaises(UnicodeDecodeError, name.toUnicode)

	def toXML(self, name):
		writer = XMLWriter(BytesIO())
		name.toXML(writer, ttFont=None)
		xml = writer.file.getvalue().decode("utf_8").strip()
		return xml.split(writer.newlinestr.decode("utf_8"))[1:]

	def test_toXML_utf16be(self):
		name = makeName("Foo Bold", 111, 0, 2, 7)
		self.assertEqual([
                    '<namerecord nameID="111" platformID="0" platEncID="2" langID="0x7">',
                    '  Foo Bold',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_utf16be_odd_length1(self):
		name = makeName(b"\0F\0o\0o\0", 111, 0, 2, 7)
		self.assertEqual([
                    '<namerecord nameID="111" platformID="0" platEncID="2" langID="0x7">',
                    '  Foo',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_utf16be_odd_length2(self):
		name = makeName(b"\0Fooz", 111, 0, 2, 7)
		self.assertEqual([
                    '<namerecord nameID="111" platformID="0" platEncID="2" langID="0x7">',
                    '  Fooz',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_utf16be_double_encoded(self):
		name = makeName(b"\0\0\0F\0\0\0o", 111, 0, 2, 7)
		self.assertEqual([
                    '<namerecord nameID="111" platformID="0" platEncID="2" langID="0x7">',
                    '  Fo',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_macroman(self):
		name = makeName("Foo Italic", 222, 1, 0, 7)  # MacRoman
		self.assertEqual([
                    '<namerecord nameID="222" platformID="1" platEncID="0" langID="0x7" unicode="True">',
                    '  Foo Italic',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_macroman_actual_utf16be(self):
		name = makeName("\0F\0o\0o", 222, 1, 0, 7)
		self.assertEqual([
                    '<namerecord nameID="222" platformID="1" platEncID="0" langID="0x7" unicode="True">',
                    '  Foo',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_unknownPlatEncID_nonASCII(self):
		name = makeName(b"B\x8arli", 333, 1, 9876, 7) # Unknown Mac encodingID
		self.assertEqual([
                    '<namerecord nameID="333" platformID="1" platEncID="9876" langID="0x7" unicode="False">',
                    '  B&#138;rli',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_unknownPlatEncID_ASCII(self):
		name = makeName(b"Barli", 333, 1, 9876, 7) # Unknown Mac encodingID
		self.assertEqual([
                    '<namerecord nameID="333" platformID="1" platEncID="9876" langID="0x7" unicode="True">',
                    '  Barli',
                    '</namerecord>'
		], self.toXML(name))

	def test_encoding_macroman_misc(self):
		name = makeName('', 123, 1, 0, 17) # Mac Turkish
		self.assertEqual(name.getEncoding(), "mac_turkish")
		name.langID = 37
		self.assertEqual(name.getEncoding(), "mac_romanian")
		name.langID = 45 # Other
		self.assertEqual(name.getEncoding(), "mac_roman")

	def test_extended_mac_encodings(self):
		name = makeName(b'\xfe', 123, 1, 1, 0) # Mac Japanese
		self.assertEqual(name.toUnicode(), unichr(0x2122))

	def test_extended_unknown(self):
		name = makeName(b'\xfe', 123, 10, 11, 12)
		self.assertEqual(name.getEncoding(), "ascii")
		self.assertEqual(name.getEncoding(None), None)
		self.assertEqual(name.getEncoding(default=None), None)

if __name__ == "__main__":
	import sys
	sys.exit(unittest.main())
