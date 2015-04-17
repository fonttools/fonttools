from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
import unittest
import fontTools.encodings.codecs # Not to be confused with "import codecs"

class ExtendedCodecsTest(unittest.TestCase):

	def test_decode_japanese(self):
		self.assertEqual(b'x\xfe\xfdy'.decode("x-mac-japanese-ttx"),
				 unichr(0x78)+unichr(0x2122)+unichr(0x00A9)+unichr(0x79))

	def test_encode_japanese(self):
		self.assertEqual(b'x\xfe\xfdy',
				 (unichr(0x78)+unichr(0x2122)+unichr(0x00A9)+unichr(0x79)).encode("x-mac-japanese-ttx"))

	def test_decode_romanian(self):
		self.assertEqual(b'x\xfb'.decode("x-mac-romanian-ttx"),
				 unichr(0x78)+unichr(0x02DA))

if __name__ == '__main__':
	unittest.main()
