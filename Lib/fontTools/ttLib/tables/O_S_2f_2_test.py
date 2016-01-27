from __future__ import print_function, division, absolute_import
from fontTools.ttLib import TTFont, newTable, getTableModule
from .O_S_2f_2 import *
import unittest


class OS2TableTest(unittest.TestCase):

	def test_getUnicodeRanges(self):
		table = table_O_S_2f_2()
		table.ulUnicodeRange1 = 0xFFFFFFFF
		table.ulUnicodeRange2 = 0xFFFFFFFF
		table.ulUnicodeRange3 = 0xFFFFFFFF
		table.ulUnicodeRange4 = 0xFFFFFFFF
		bits = table.getUnicodeRanges()
		for i in range(127):
			self.assertIn(i, bits)

	def test_setUnicodeRanges(self):
		table = table_O_S_2f_2()
		table.ulUnicodeRange1 = 0
		table.ulUnicodeRange2 = 0
		table.ulUnicodeRange3 = 0
		table.ulUnicodeRange4 = 0
		bits = set(range(123))
		table.setUnicodeRanges(bits)
		self.assertEqual(table.getUnicodeRanges(), bits)
		with self.assertRaises(ValueError):
			table.setUnicodeRanges([-1, 127, 255])

	def test_recalcUnicodeRanges(self):
		font = TTFont()
		font['OS/2'] = os2 = newTable('OS/2')
		font['cmap'] = cmap = newTable('cmap')
		st = getTableModule('cmap').CmapSubtable.newSubtable(4)
		st.platformID, st.platEncID, st.language = 3, 1, 0
		st.cmap = {0x0041:'A', 0x03B1: 'alpha', 0x0410: 'Acyr'}
		cmap.tables = []
		cmap.tables.append(st)
		os2.setUnicodeRanges({0, 1, 9})
		# 'pruneOnly' will clear any bits for which there's no intersection:
		# bit 1 ('Latin 1 Supplement'), in this case. However, it won't set
		# bit 7 ('Greek and Coptic') despite the "alpha" character is present.
		self.assertEqual(os2.recalcUnicodeRanges(font, pruneOnly=True), {0, 9})
		# try again with pruneOnly=False: bit 7 is now set.
		self.assertEqual(os2.recalcUnicodeRanges(font), {0, 7, 9})
		# add a non-BMP char from 'Mahjong Tiles' block (bit 122)
		st.cmap[0x1F000] = 'eastwindtile'
		# the bit 122 and the special bit 57 ('Non Plane 0') are also enabled
		self.assertEqual(os2.recalcUnicodeRanges(font), {0, 7, 9, 57, 122})


if __name__ == "__main__":
	unittest.main()
