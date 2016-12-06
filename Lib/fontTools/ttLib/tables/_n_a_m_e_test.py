# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.misc.loggingTools import CapturingLogHandler
import struct
import unittest
from ._n_a_m_e import table__n_a_m_e, NameRecord, nameRecordFormat, nameRecordSize
from ._n_a_m_e import makeName, log


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
                        struct.pack(">HHH", 1, 1, 6 + nameRecordSize),
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
	unittest.main()
