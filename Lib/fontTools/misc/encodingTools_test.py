from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
import unittest
from .encodingTools import getEncoding

class EncodingTest(unittest.TestCase):

	def test_encoding_unicode(self):

		self.assertEqual(getEncoding(3, 0, None), "utf-16be") # MS Symbol is Unicode as well
		self.assertEqual(getEncoding(3, 1, None), "utf-16be")
		self.assertEqual(getEncoding(3, 10, None), "utf-16be")
		self.assertEqual(getEncoding(0, 3, None), "utf-16be")

	def test_encoding_macroman_misc(self):
		self.assertEqual(getEncoding(1, 0, 17), "mac-turkish")
		self.assertEqual(getEncoding(1, 0, 37), "x-mac-romanian-ttx")
		self.assertEqual(getEncoding(1, 0, 45), "mac-roman")

	def test_extended_mac_encodings(self):
		encoding = getEncoding(1, 1, 0) # Mac Japanese
		decoded = b'\xfe'.decode(encoding)
		self.assertEqual(decoded, unichr(0x2122))

	def test_extended_unknown(self):
		self.assertEqual(getEncoding(10, 11, 12), None)
		self.assertEqual(getEncoding(10, 11, 12, "ascii"), "ascii")
		self.assertEqual(getEncoding(10, 11, 12, default="ascii"), "ascii")

if __name__ == "__main__":
	unittest.main()
