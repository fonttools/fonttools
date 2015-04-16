from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
import unittest
import fontTools.encodings.codecs # Not to be confused with "import codecs"

class ExtendedCodecsTest(unittest.TestCase):

	def test_decode(self):
		self.assertEqual(b'x\xfe\xfdy'.decode("x-mac-japanese-ttx"),
				 unichr(0x78)+unichr(0x2122)+unichr(0x00A9)+unichr(0x79))

	def test_encode(self):
		self.assertEqual(b'x\xfe\xfdy',
				 (unichr(0x78)+unichr(0x2122)+unichr(0x00A9)+unichr(0x79)).encode("x-mac-japanese-ttx"))

if __name__ == '__main__':
	unittest.main()
