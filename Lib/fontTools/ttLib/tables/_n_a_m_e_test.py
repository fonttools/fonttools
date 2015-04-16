from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.xmlWriter import XMLWriter
import unittest
from ._n_a_m_e import NameRecord

class NameRecordTest(unittest.TestCase):

	def toXML(self, name):
		writer = XMLWriter(StringIO())
		name.toXML(writer, ttFont=None)
		xml = writer.file.getvalue().decode("utf-8").strip()
		return xml.split(writer.newlinestr.decode("utf-8"))[1:]

	def test_toXML_utf16be(self):
		name = NameRecord()
		name.string = "Foo Bold".encode("utf-16be")
		name.nameID, name.platformID, name.platEncID, name.langID = (111, 0, 2, 7)
		self.assertEquals([
                    '<namerecord nameID="111" platformID="0" platEncID="2" langID="0x7">',
                    '  Foo Bold',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_macroman(self):
		name = NameRecord()
		name.string = "Foo Italic".encode("macroman")
		name.nameID, name.platformID, name.platEncID, name.langID = (222, 1, 0, 7)
		self.assertEquals([
                    '<namerecord nameID="222" platformID="1" platEncID="0" langID="0x7" unicode="True">',
                    '  Foo Italic',
                    '</namerecord>'
		], self.toXML(name))

	def test_toXML_unknownPlatEncID(self):
		name = NameRecord()
		name.string = b"B\x8arli"
		name.nameID, name.platformID, name.platEncID, name.langID = (333, 1, 9876, 7)
		self.assertEquals([
                    '<namerecord nameID="333" platformID="1" platEncID="9876" langID="0x7" unicode="False">',
                    '  B&#138;rli',
                    '</namerecord>'
		], self.toXML(name))


if __name__ == '__main__':
	unittest.main()
