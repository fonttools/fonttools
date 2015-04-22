from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.xmlWriter import XMLWriter
import unittest
from ._n_a_m_e import NameRecord

class NameRecordTest(unittest.TestCase):

	def makeName(self, text, nameID, platformID, platEncID, langID):
		name = NameRecord()
		name.nameID, name.platformID, name.platEncID, name.langID = (nameID, platformID, platEncID, langID)
		name.string = tobytes(text, encoding=name.getEncoding())
		return name

	def test_toUnicode_utf16be(self):
		name = self.makeName("Foo Bold", 111, 0, 2, 7)
		self.assertEqual("utf_16be", name.getEncoding())
		self.assertEqual("Foo Bold", name.toUnicode())

	def test_toUnicode_macroman(self):
		name = self.makeName("Foo Italic", 222, 1, 0, 7)  # MacRoman
		self.assertEqual("mac_roman", name.getEncoding())
		self.assertEqual("Foo Italic", name.toUnicode())

	def test_toUnicode_macromanian(self):
		name = self.makeName(b"Foo Italic\xfb", 222, 1, 0, 37)  # Mac Romanian
		self.assertEqual("x_mac_romanian_ttx", name.getEncoding())
		self.assertEqual("Foo Italic"+unichr(0x02DA), name.toUnicode())

	def test_toUnicode_UnicodeDecodeError(self):
		name = self.makeName(b"\1", 111, 0, 2, 7)
		self.assertEqual("utf_16be", name.getEncoding())
		self.assertRaises(UnicodeDecodeError, name.toUnicode)

	def toXML(self, name):
		writer = XMLWriter(StringIO())
		name.toXML(writer, ttFont=None)
		xml = writer.file.getvalue().decode("utf_8").strip()
		return xml.split(writer.newlinestr.decode("utf_8"))[1:]

	def test_toXML_utf16be(self):
		name = self.makeName("Foo Bold", 111, 0, 2, 7)
		self.assertEqual([
                    '<namerecord nameID="111" platformID="0" platEncID="2" langID="0x7">',
                    '  Foo Bold',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_utf16be_odd_length1(self):
		name = self.makeName(b"\0F\0o\0o\0", 111, 0, 2, 7)
		self.assertEqual([
                    '<namerecord nameID="111" platformID="0" platEncID="2" langID="0x7">',
                    '  Foo',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_utf16be_odd_length2(self):
		name = self.makeName(b"\0Fooz", 111, 0, 2, 7)
		self.assertEqual([
                    '<namerecord nameID="111" platformID="0" platEncID="2" langID="0x7">',
                    '  Fooz',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_macroman(self):
		name = self.makeName("Foo Italic", 222, 1, 0, 7)  # MacRoman
		self.assertEqual([
                    '<namerecord nameID="222" platformID="1" platEncID="0" langID="0x7" unicode="True">',
                    '  Foo Italic',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_unknownPlatEncID_nonASCII(self):
		name = self.makeName(b"B\x8arli", 333, 1, 9876, 7) # Unknown Mac encodingID
		self.assertEqual([
                    '<namerecord nameID="333" platformID="1" platEncID="9876" langID="0x7" unicode="False">',
                    '  B&#138;rli',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_unknownPlatEncID_ASCII(self):
		name = self.makeName(b"Barli", 333, 1, 9876, 7) # Unknown Mac encodingID
		self.assertEqual([
                    '<namerecord nameID="333" platformID="1" platEncID="9876" langID="0x7" unicode="True">',
                    '  Barli',
                    '</namerecord>'
		], self.toXML(name))

	def test_encoding_macroman_misc(self):
		name = self.makeName('', 123, 1, 0, 17) # Mac Turkish
		self.assertEqual(name.getEncoding(), "mac_turkish")
		name.langID = 37
		self.assertEqual(name.getEncoding(), "x_mac_romanian_ttx")
		name.langID = 45 # Other
		self.assertEqual(name.getEncoding(), "mac_roman")

	def test_extended_mac_encodings(self):
		name = self.makeName(b'\xfe', 123, 1, 1, 0) # Mac Japanese
		self.assertEqual(name.toUnicode(), unichr(0x2122))

	def test_extended_unknown(self):
		name = self.makeName(b'\xfe', 123, 10, 11, 12)
		self.assertEqual(name.getEncoding(), "ascii")
		self.assertEqual(name.getEncoding(None), None)
		self.assertEqual(name.getEncoding(default=None), None)

if __name__ == "__main__":
	unittest.main()
