from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.xmlWriter import XMLWriter
import unittest
from ._n_a_m_e import NameRecord

class NameRecordTest(unittest.TestCase):

	def makeName(self, text, nameID, platformID, platEncID, langID):
		name = NameRecord()
		name.nameID, name.platformID, name.platEncID, name.langID = (nameID, platformID, platEncID, langID)
		name.string = text.encode(name.getEncoding())
		return name

	def test_toUnicode_utf16be(self):
		name = self.makeName("Foo Bold", 111, 0, 2, 7)
		self.assertEqual("utf-16be", name.getEncoding())
		self.assertEqual("Foo Bold", name.toUnicode())

	def test_toUnicode_macroman(self):
		name = self.makeName("Foo Italic", 222, 1, 0, 7)  # MacRoman
		self.assertEqual("macroman", name.getEncoding())
		self.assertEqual("Foo Italic", name.toUnicode())

	def test_toUnicode_UnicodeDecodeError(self):
		name = self.makeName("Foo Bold", 111, 0, 2, 7)
		self.assertEqual("utf-16be", name.getEncoding())
		name.string = b"X"  # invalid utf-16be sequence
		self.assertRaises(UnicodeDecodeError, name.toUnicode)

	def toXML(self, name):
		writer = XMLWriter(StringIO())
		name.toXML(writer, ttFont=None)
		xml = writer.file.getvalue().decode("utf-8").strip()
		return xml.split(writer.newlinestr.decode("utf-8"))[1:]

	def test_toXML_utf16be(self):
		name = self.makeName("Foo Bold", 111, 0, 2, 7)
		self.assertEqual([
                    '<namerecord nameID="111" platformID="0" platEncID="2" langID="0x7">',
                    '  Foo Bold',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_macroman(self):
		name = self.makeName("Foo Italic", 222, 1, 0, 7)  # MacRoman
		self.assertEqual([
                    '<namerecord nameID="222" platformID="1" platEncID="0" langID="0x7" unicode="True">',
                    '  Foo Italic',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_unknownPlatEncID(self):
		name = NameRecord()
		name.string = b"B\x8arli"
		name.nameID, name.platformID, name.platEncID, name.langID = (333, 1, 9876, 7)
		self.assertEqual([
                    '<namerecord nameID="333" platformID="1" platEncID="9876" langID="0x7" unicode="False">',
                    '  B&#138;rli',
                    '</namerecord>'
		], self.toXML(name))


if __name__ == "__main__":
	unittest.main()
