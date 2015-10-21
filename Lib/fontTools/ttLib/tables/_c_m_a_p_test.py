from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools import ttLib
import unittest
from ._c_m_a_p import CmapSubtable, table__c_m_a_p

class CmapSubtableTest(unittest.TestCase):

	def makeSubtable(self, cmapFormat, platformID, platEncID, langID):
		subtable = CmapSubtable.newSubtable(cmapFormat)
		subtable.platformID, subtable.platEncID, subtable.language = (platformID, platEncID, langID)
		return subtable

	def test_toUnicode_utf16be(self):
		subtable = self.makeSubtable(4, 0, 2, 7)
		self.assertEqual("utf_16_be", subtable.getEncoding())
		self.assertEqual(True, subtable.isUnicode())

	def test_toUnicode_macroman(self):
		subtable = self.makeSubtable(4, 1, 0, 7)  # MacRoman
		self.assertEqual("mac_roman", subtable.getEncoding())
		self.assertEqual(False, subtable.isUnicode())

	def test_toUnicode_macromanian(self):
		subtable = self.makeSubtable(4, 1, 0, 37)  # Mac Romanian
		self.assertNotEqual(None, subtable.getEncoding())
		self.assertEqual(False, subtable.isUnicode())

	def test_extended_mac_encodings(self):
		subtable = self.makeSubtable(4, 1, 1, 0) # Mac Japanese
		self.assertNotEqual(None, subtable.getEncoding())
		self.assertEqual(False, subtable.isUnicode())

	def test_extended_unknown(self):
		subtable = self.makeSubtable(4, 10, 11, 12)
		self.assertEqual(subtable.getEncoding(), None)
		self.assertEqual(subtable.getEncoding("ascii"), "ascii")
		self.assertEqual(subtable.getEncoding(default="xyz"), "xyz")

	def test_decompile_4(self):
		subtable = CmapSubtable.newSubtable(4)
		font = ttLib.TTFont()
		font.setGlyphOrder([])
		subtable.decompile(b'\0' * 3 + b'\x10' + b'\0' * 12, font)

	def test_decompile_12(self):
		subtable = CmapSubtable.newSubtable(12)
		font = ttLib.TTFont()
		font.setGlyphOrder([])
		subtable.decompile(b'\0' * 7 + b'\x10' + b'\0' * 8, font)

	def test_buildReversed(self):
		c4 = self.makeSubtable(4, 3, 1, 0)
		c4.cmap = {0x0041:'A', 0x0391:'A'}
		c12 = self.makeSubtable(12, 3, 10, 0)
		c12.cmap = {0x10314: 'u10314'}
		cmap = table__c_m_a_p()
		cmap.tables = [c4, c12]
		self.assertEqual(cmap.buildReversed(), {'A':{0x0041, 0x0391}, 'u10314':{0x10314}})


if __name__ == "__main__":
	unittest.main()
