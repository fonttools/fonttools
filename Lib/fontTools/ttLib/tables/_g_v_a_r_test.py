from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.ttLib import TTLibError, getTableClass, getTableModule, newTable
import unittest


gvar = getTableModule("gvar")
gvarClass = getTableClass("gvar")


def hexencode(s):
	h = hexStr(s).upper()
	return ' '.join([h[i:i+2] for i in range(0, len(h), 2)])


class GVARTableTest(unittest.TestCase):
	def test_compileOffsets_shortFormat(self):
		self.assertEqual((deHexStr("00 00 00 02 FF C0"), 0),
		                 gvarClass.compileOffsets_([0, 4, 0x1ff80]))

	def test_compileOffsets_longFormat(self):
		self.assertEqual((deHexStr("00 00 00 00 00 00 00 04 CA FE BE EF"), 1),
		                 gvarClass.compileOffsets_([0, 4, 0xCAFEBEEF]))

	def test_decompileOffsets_shortFormat(self):
		decompileOffsets = gvarClass.decompileOffsets_
		data = deHexStr("00 11 22 33 44 55 66 77 88 99 aa bb")
		self.assertEqual(
			[2*0x0011, 2*0x2233, 2*0x4455, 2*0x6677, 2*0x8899, 2*0xaabb],
			list(decompileOffsets(data, tableFormat=0, glyphCount=5)))

	def test_decompileOffsets_longFormat(self):
		decompileOffsets = gvarClass.decompileOffsets_
		data = deHexStr("00 11 22 33 44 55 66 77 88 99 aa bb")
		self.assertEqual(
			[0x00112233, 0x44556677, 0x8899aabb],
			list(decompileOffsets(data, tableFormat=1, glyphCount=2)))


if __name__ == "__main__":
	unittest.main()
