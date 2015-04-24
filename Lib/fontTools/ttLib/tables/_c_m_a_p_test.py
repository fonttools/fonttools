from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
import unittest
from ._c_m_a_p import CmapSubtable

class CmapSubtableTest(unittest.TestCase):

	def makeSubtable(self, platformID, platEncID, langID):
		subtable = CmapSubtable(None)
		subtable.platformID, subtable.platEncID, subtable.language = (platformID, platEncID, langID)
		return subtable

	def test_toUnicode_utf16be(self):
		subtable = self.makeSubtable(0, 2, 7)
		self.assertEqual("utf_16_be", subtable.getEncoding())
		self.assertEqual(True, subtable.isUnicode())

	def test_toUnicode_macroman(self):
		subtable = self.makeSubtable(1, 0, 7)  # MacRoman
		self.assertEqual("mac_roman", subtable.getEncoding())
		self.assertEqual(False, subtable.isUnicode())

	def test_toUnicode_macromanian(self):
		subtable = self.makeSubtable(1, 0, 37)  # Mac Romanian
		self.assertNotEqual(None, subtable.getEncoding())
		self.assertEqual(False, subtable.isUnicode())

	def test_extended_mac_encodings(self):
		subtable = self.makeSubtable(1, 1, 0) # Mac Japanese
		self.assertNotEqual(None, subtable.getEncoding())
		self.assertEqual(False, subtable.isUnicode())

	def test_extended_unknown(self):
		subtable = self.makeSubtable(10, 11, 12)
		self.assertEqual(subtable.getEncoding(), None)
		self.assertEqual(subtable.getEncoding("ascii"), "ascii")
		self.assertEqual(subtable.getEncoding(default="xyz"), "xyz")

if __name__ == "__main__":
	unittest.main()
