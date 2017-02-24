from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.merge import *
import unittest


class MergeIntegrationTest(unittest.TestCase):
	# TODO
	pass

class gaspMergeUnitTest(unittest.TestCase):
	def setUp(self):
		self.merger = Merger()

		self.table1 = ttLib.newTable('gasp')
		self.table1.version = 1
		self.table1.gaspRange = {
			0x8: 0xA ,
			0x10: 0x5,
		}

		self.table2 = ttLib.newTable('gasp')
		self.table2.version = 1
		self.table2.gaspRange = {
			0x6: 0xB ,
			0xFF: 0x4,
		}

		self.result = ttLib.newTable('gasp')

	def test_gasp_merge_basic(self):
		result = self.result.merge(self.merger, [self.table1, self.table2])
		self.assertEqual(result, self.table1)

		result = self.result.merge(self.merger, [self.table2, self.table1])
		self.assertEqual(result, self.table2)

	def test_gasp_merge_notImplemented(self):
		result = self.result.merge(self.merger, [NotImplemented, self.table1])
		self.assertEqual(result, NotImplemented)

		result = self.result.merge(self.merger, [self.table1, NotImplemented])
		self.assertEqual(result, self.table1)


class CmapMergeUnitTest(unittest.TestCase):
	def setUp(self):
		self.merger = Merger()
		self.table1 = ttLib.newTable('cmap')
		self.table2 = ttLib.newTable('cmap')
		self.mergedTable = ttLib.newTable('cmap')
		pass

	def tearDown(self):
		pass


	def makeSubtable(self, format, platformID, platEncID, cmap):
		module = ttLib.getTableModule('cmap')
		subtable = module.cmap_classes[format](format)
		(subtable.platformID,
			subtable.platEncID,
			subtable.language,
			subtable.cmap) = (platformID, platEncID, 0, cmap)
		return subtable

	# 4-3-1 table merged with 12-3-10 table with no dupes with codepoints outside BMP
	def test_cmap_merge_no_dupes(self):
		table1 = self.table1
		table2 = self.table2
		mergedTable = self.mergedTable

		cmap1 = {0x2603: 'SNOWMAN'}
		table1.tables = [self.makeSubtable(4,3,1, cmap1)]

		cmap2 = {0x26C4: 'SNOWMAN WITHOUT SNOW'}
		cmap2Extended = {0x1F93C: 'WRESTLERS'}
		cmap2Extended.update(cmap2)
		table2.tables = [self.makeSubtable(4,3,1, cmap2), self.makeSubtable(12,3,10, cmap2Extended)]

		self.merger.alternateGlyphsPerFont = [{},{}]
		mergedTable.merge(self.merger, [table1, table2])

		expectedCmap = cmap2.copy()
		expectedCmap.update(cmap1)
		expectedCmapExtended = cmap2Extended.copy()
		expectedCmapExtended.update(cmap1)
		self.assertEqual(mergedTable.numSubTables, 2)
		self.assertEqual([(table.format, table.platformID, table.platEncID, table.language) for table in mergedTable.tables],
			[(4,3,1,0),(12,3,10,0)])
		self.assertEqual(mergedTable.tables[0].cmap, expectedCmap)
		self.assertEqual(mergedTable.tables[1].cmap, expectedCmapExtended)

	# Tests Issue #322
	def test_cmap_merge_three_dupes(self):
		table1 = self.table1
		table2 = self.table2
		mergedTable = self.mergedTable

		cmap1 = {0x20: 'space#0', 0xA0: 'space#0'}
		table1.tables = [self.makeSubtable(4,3,1,cmap1)]
		cmap2 = {0x20: 'space#1', 0xA0: 'uni00A0#1'}
		table2.tables = [self.makeSubtable(4,3,1,cmap2)]

		self.merger.duplicateGlyphsPerFont = [{},{}]
		mergedTable.merge(self.merger, [table1, table2])

		expectedCmap = cmap1.copy()
		self.assertEqual(mergedTable.numSubTables, 1)
		table = mergedTable.tables[0]
		self.assertEqual((table.format, table.platformID, table.platEncID, table.language), (4,3,1,0))
		self.assertEqual(table.cmap, expectedCmap)
		self.assertEqual(self.merger.duplicateGlyphsPerFont, [{}, {'space#0': 'space#1'}])


if __name__ == "__main__":
	import sys
	sys.exit(unittest.main())
