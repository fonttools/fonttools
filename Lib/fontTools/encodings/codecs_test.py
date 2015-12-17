from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
import unittest
import fontTools.encodings.codecs # Not to be confused with "import codecs"

class ExtendedCodecsTest(unittest.TestCase):

	def test_decode_mac_japanese(self):
		self.assertEqual(b'x\xfe\xfdy'.decode("x_mac_japanese_ttx"),
				 unichr(0x78)+unichr(0x2122)+unichr(0x00A9)+unichr(0x79))

	def test_encode_mac_japanese(self):
		self.assertEqual(b'x\xfe\xfdy',
				 (unichr(0x78)+unichr(0x2122)+unichr(0x00A9)+unichr(0x79)).encode("x_mac_japanese_ttx"))

	def test_decode_mac_trad_chinese(self):
		self.assertEqual(b'\x80'.decode("x_mac_trad_chinese_ttx"),
				 unichr(0x5C))

	def test_decode_mac_romanian(self):
		self.assertEqual(b'x\xfb'.decode("mac_romanian"),
				 unichr(0x78)+unichr(0x02DA))

if __name__ == '__main__':
	unittest.main()
