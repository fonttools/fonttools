from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.ttLib import woff2
from fontTools.ttLib.woff2 import (
	WOFF2Reader, woff2DirectorySize, woff2DirectoryFormat,
	woff2FlagsSize, woff2UnknownTagSize, woff2Base128MaxSize, WOFF2DirectoryEntry,
	getKnownTagIndex, packBase128, base128Size, woff2UnknownTagIndex,
	WOFF2FlavorData, woff2TransformedTableTags, WOFF2GlyfTable, WOFF2LocaTable,
	WOFF2HmtxTable, WOFF2Writer, unpackBase128, unpack255UShort, pack255UShort)
import unittest
from fontTools.misc import sstruct
from fontTools import fontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
import struct
import os
import random
import copy
from collections import OrderedDict
from functools import partial
import pytest

haveBrotli = False
try:
	try:
		import brotlicffi as brotli
	except ImportError:
		import brotli
	haveBrotli = True
except ImportError:
	pass


# Python 3 renamed 'assertRaisesRegexp' to 'assertRaisesRegex', and fires
# deprecation warnings if a program uses the old name.
if not hasattr(unittest.TestCase, 'assertRaisesRegex'):
	unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp


current_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
data_dir = os.path.join(current_dir, 'data')
TTX = os.path.join(data_dir, 'TestTTF-Regular.ttx')
OTX = os.path.join(data_dir, 'TestOTF-Regular.otx')
METADATA = os.path.join(data_dir, 'test_woff2_metadata.xml')

TT_WOFF2 = BytesIO()
CFF_WOFF2 = BytesIO()


def setUpModule():
	if not haveBrotli:
		raise unittest.SkipTest("No module named brotli")
	assert os.path.exists(TTX)
	assert os.path.exists(OTX)
	# import TT-flavoured test font and save it as WOFF2
	ttf = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False)
	ttf.importXML(TTX)
	ttf.flavor = "woff2"
	ttf.save(TT_WOFF2, reorderTables=None)
	# import CFF-flavoured test font and save it as WOFF2
	otf = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False)
	otf.importXML(OTX)
	otf.flavor = "woff2"
	otf.save(CFF_WOFF2, reorderTables=None)


class WOFF2ReaderTest(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.file = BytesIO(CFF_WOFF2.getvalue())
		cls.font = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False)
		cls.font.importXML(OTX)

	def setUp(self):
		self.file.seek(0)

	def test_bad_signature(self):
		with self.assertRaisesRegex(ttLib.TTLibError, 'bad signature'):
			WOFF2Reader(BytesIO(b"wOFF"))

	def test_not_enough_data_header(self):
		incomplete_header = self.file.read(woff2DirectorySize - 1)
		with self.assertRaisesRegex(ttLib.TTLibError, 'not enough data'):
			WOFF2Reader(BytesIO(incomplete_header))

	def test_incorrect_compressed_size(self):
		data = self.file.read(woff2DirectorySize)
		header = sstruct.unpack(woff2DirectoryFormat, data)
		header['totalCompressedSize'] = 0
		data = sstruct.pack(woff2DirectoryFormat, header)
		with self.assertRaises((brotli.error, ttLib.TTLibError)):
			WOFF2Reader(BytesIO(data + self.file.read()))

	def test_incorrect_uncompressed_size(self):
		decompress_backup = brotli.decompress
		brotli.decompress = lambda data: b""  # return empty byte string
		with self.assertRaisesRegex(ttLib.TTLibError, 'unexpected size for decompressed'):
			WOFF2Reader(self.file)
		brotli.decompress = decompress_backup

	def test_incorrect_file_size(self):
		data = self.file.read(woff2DirectorySize)
		header = sstruct.unpack(woff2DirectoryFormat, data)
		header['length'] -= 1
		data = sstruct.pack(woff2DirectoryFormat, header)
		with self.assertRaisesRegex(
				ttLib.TTLibError, "doesn't match the actual file size"):
			WOFF2Reader(BytesIO(data + self.file.read()))

	def test_num_tables(self):
		tags = [t for t in self.font.keys() if t not in ('GlyphOrder', 'DSIG')]
		data = self.file.read(woff2DirectorySize)
		header = sstruct.unpack(woff2DirectoryFormat, data)
		self.assertEqual(header['numTables'], len(tags))

	def test_table_tags(self):
		tags = set([t for t in self.font.keys() if t not in ('GlyphOrder', 'DSIG')])
		reader = WOFF2Reader(self.file)
		self.assertEqual(set(reader.keys()), tags)

	def test_get_normal_tables(self):
		woff2Reader = WOFF2Reader(self.file)
		specialTags = woff2TransformedTableTags + ('head', 'GlyphOrder', 'DSIG')
		for tag in [t for t in self.font.keys() if t not in specialTags]:
			origData = self.font.getTableData(tag)
			decompressedData = woff2Reader[tag]
			self.assertEqual(origData, decompressedData)

	def test_reconstruct_unknown(self):
		reader = WOFF2Reader(self.file)
		with self.assertRaisesRegex(ttLib.TTLibError, 'transform for table .* unknown'):
			reader.reconstructTable('head')


class WOFF2ReaderTTFTest(WOFF2ReaderTest):
	""" Tests specific to TT-flavored fonts. """

	@classmethod
	def setUpClass(cls):
		cls.file = BytesIO(TT_WOFF2.getvalue())
		cls.font = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False)
		cls.font.importXML(TTX)

	def setUp(self):
		self.file.seek(0)

	def test_reconstruct_glyf(self):
		woff2Reader = WOFF2Reader(self.file)
		reconstructedData = woff2Reader['glyf']
		self.assertEqual(self.font.getTableData('glyf'), reconstructedData)

	def test_reconstruct_loca(self):
		woff2Reader = WOFF2Reader(self.file)
		reconstructedData = woff2Reader['loca']
		self.font.getTableData("glyf")  # 'glyf' needs to be compiled before 'loca'
		self.assertEqual(self.font.getTableData('loca'), reconstructedData)
		self.assertTrue(hasattr(woff2Reader.tables['glyf'], 'data'))

	def test_reconstruct_loca_not_match_orig_size(self):
		reader = WOFF2Reader(self.file)
		reader.tables['loca'].origLength -= 1
		with self.assertRaisesRegex(
				ttLib.TTLibError, "'loca' table doesn't match original size"):
			reader.reconstructTable('loca')


def normalise_table(font, tag, padding=4):
	""" Return normalised table data. Keep 'font' instance unmodified. """
	assert tag in ('glyf', 'loca', 'head')
	assert tag in font
	if tag == 'head':
		origHeadFlags = font['head'].flags
		font['head'].flags |= (1 << 11)
		tableData = font['head'].compile(font)
	if font.sfntVersion in ("\x00\x01\x00\x00", "true"):
		assert {'glyf', 'loca', 'head'}.issubset(font.keys())
		origIndexFormat = font['head'].indexToLocFormat
		if hasattr(font['loca'], 'locations'):
			origLocations = font['loca'].locations[:]
		else:
			origLocations = []
		glyfTable = ttLib.newTable('glyf')
		glyfTable.decompile(font.getTableData('glyf'), font)
		glyfTable.padding = padding
		if tag == 'glyf':
			tableData = glyfTable.compile(font)
		elif tag == 'loca':
			glyfTable.compile(font)
			tableData = font['loca'].compile(font)
		if tag == 'head':
			glyfTable.compile(font)
			font['loca'].compile(font)
			tableData = font['head'].compile(font)
		font['head'].indexToLocFormat = origIndexFormat
		font['loca'].set(origLocations)
	if tag == 'head':
		font['head'].flags = origHeadFlags
	return tableData


def normalise_font(font, padding=4):
	""" Return normalised font data. Keep 'font' instance unmodified. """
	# drop DSIG but keep a copy
	DSIG_copy = copy.deepcopy(font['DSIG'])
	del font['DSIG']
	# override TTFont attributes
	origFlavor = font.flavor
	origRecalcBBoxes = font.recalcBBoxes
	origRecalcTimestamp = font.recalcTimestamp
	origLazy = font.lazy
	font.flavor = None
	font.recalcBBoxes = False
	font.recalcTimestamp = False
	font.lazy = True
	# save font to temporary stream
	infile = BytesIO()
	font.save(infile)
	infile.seek(0)
	# reorder tables alphabetically
	outfile = BytesIO()
	reader = ttLib.sfnt.SFNTReader(infile)
	writer = ttLib.sfnt.SFNTWriter(
		outfile, len(reader.tables), reader.sfntVersion, reader.flavor, reader.flavorData)
	for tag in sorted(reader.keys()):
		if tag in woff2TransformedTableTags + ('head',):
			writer[tag] = normalise_table(font, tag, padding)
		else:
			writer[tag] = reader[tag]
	writer.close()
	# restore font attributes
	font['DSIG'] = DSIG_copy
	font.flavor = origFlavor
	font.recalcBBoxes = origRecalcBBoxes
	font.recalcTimestamp = origRecalcTimestamp
	font.lazy = origLazy
	return outfile.getvalue()


class WOFF2DirectoryEntryTest(unittest.TestCase):

	def setUp(self):
		self.entry = WOFF2DirectoryEntry()

	def test_not_enough_data_table_flags(self):
		with self.assertRaisesRegex(ttLib.TTLibError, "can't read table 'flags'"):
			self.entry.fromString(b"")

	def test_not_enough_data_table_tag(self):
		incompleteData = bytearray([0x3F, 0, 0, 0])
		with self.assertRaisesRegex(ttLib.TTLibError, "can't read table 'tag'"):
			self.entry.fromString(bytes(incompleteData))

	def test_loca_zero_transformLength(self):
		data = bytechr(getKnownTagIndex('loca'))  # flags
		data += packBase128(random.randint(1, 100))  # origLength
		data += packBase128(1)  # non-zero transformLength
		with self.assertRaisesRegex(
				ttLib.TTLibError, "transformLength of the 'loca' table must be 0"):
			self.entry.fromString(data)

	def test_fromFile(self):
		unknownTag = Tag('ZZZZ')
		data = bytechr(getKnownTagIndex(unknownTag))
		data += unknownTag.tobytes()
		data += packBase128(random.randint(1, 100))
		expectedPos = len(data)
		f = BytesIO(data + b'\0'*100)
		self.entry.fromFile(f)
		self.assertEqual(f.tell(), expectedPos)

	def test_transformed_toString(self):
		self.entry.tag = Tag('glyf')
		self.entry.flags = getKnownTagIndex(self.entry.tag)
		self.entry.origLength = random.randint(101, 200)
		self.entry.length = random.randint(1, 100)
		expectedSize = (woff2FlagsSize + base128Size(self.entry.origLength) +
			base128Size(self.entry.length))
		data = self.entry.toString()
		self.assertEqual(len(data), expectedSize)

	def test_known_toString(self):
		self.entry.tag = Tag('head')
		self.entry.flags = getKnownTagIndex(self.entry.tag)
		self.entry.origLength = 54
		expectedSize = (woff2FlagsSize + base128Size(self.entry.origLength))
		data = self.entry.toString()
		self.assertEqual(len(data), expectedSize)

	def test_unknown_toString(self):
		self.entry.tag = Tag('ZZZZ')
		self.entry.flags = woff2UnknownTagIndex
		self.entry.origLength = random.randint(1, 100)
		expectedSize = (woff2FlagsSize + woff2UnknownTagSize +
			base128Size(self.entry.origLength))
		data = self.entry.toString()
		self.assertEqual(len(data), expectedSize)

	def test_glyf_loca_transform_flags(self):
		for tag in ("glyf", "loca"):
			entry = WOFF2DirectoryEntry()
			entry.tag = Tag(tag)
			entry.flags = getKnownTagIndex(entry.tag)

			self.assertEqual(entry.transformVersion, 0)
			self.assertTrue(entry.transformed)

			entry.transformed = False

			self.assertEqual(entry.transformVersion, 3)
			self.assertEqual(entry.flags & 0b11000000, (3 << 6))
			self.assertFalse(entry.transformed)

	def test_other_transform_flags(self):
		entry = WOFF2DirectoryEntry()
		entry.tag = Tag('ZZZZ')
		entry.flags = woff2UnknownTagIndex

		self.assertEqual(entry.transformVersion, 0)
		self.assertFalse(entry.transformed)

		entry.transformed = True

		self.assertEqual(entry.transformVersion, 1)
		self.assertEqual(entry.flags & 0b11000000, (1 << 6))
		self.assertTrue(entry.transformed)


class DummyReader(WOFF2Reader):

	def __init__(self, file, checkChecksums=1, fontNumber=-1):
		self.file = file
		for attr in ('majorVersion', 'minorVersion', 'metaOffset', 'metaLength',
				'metaOrigLength', 'privLength', 'privOffset'):
			setattr(self, attr, 0)
		self.tables = {}


class WOFF2FlavorDataTest(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		assert os.path.exists(METADATA)
		with open(METADATA, 'rb') as f:
			cls.xml_metadata = f.read()
		cls.compressed_metadata = brotli.compress(cls.xml_metadata, mode=brotli.MODE_TEXT)
		# make random byte strings; font data must be 4-byte aligned
		cls.fontdata = bytes(bytearray(random.sample(range(0, 256), 80)))
		cls.privData = bytes(bytearray(random.sample(range(0, 256), 20)))

	def setUp(self):
		self.file = BytesIO(self.fontdata)
		self.file.seek(0, 2)

	def test_get_metaData_no_privData(self):
		self.file.write(self.compressed_metadata)
		reader = DummyReader(self.file)
		reader.metaOffset = len(self.fontdata)
		reader.metaLength = len(self.compressed_metadata)
		reader.metaOrigLength = len(self.xml_metadata)
		flavorData = WOFF2FlavorData(reader)
		self.assertEqual(self.xml_metadata, flavorData.metaData)

	def test_get_privData_no_metaData(self):
		self.file.write(self.privData)
		reader = DummyReader(self.file)
		reader.privOffset = len(self.fontdata)
		reader.privLength = len(self.privData)
		flavorData = WOFF2FlavorData(reader)
		self.assertEqual(self.privData, flavorData.privData)

	def test_get_metaData_and_privData(self):
		self.file.write(self.compressed_metadata + self.privData)
		reader = DummyReader(self.file)
		reader.metaOffset = len(self.fontdata)
		reader.metaLength = len(self.compressed_metadata)
		reader.metaOrigLength = len(self.xml_metadata)
		reader.privOffset = reader.metaOffset + reader.metaLength
		reader.privLength = len(self.privData)
		flavorData = WOFF2FlavorData(reader)
		self.assertEqual(self.xml_metadata, flavorData.metaData)
		self.assertEqual(self.privData, flavorData.privData)

	def test_get_major_minorVersion(self):
		reader = DummyReader(self.file)
		reader.majorVersion = reader.minorVersion = 1
		flavorData = WOFF2FlavorData(reader)
		self.assertEqual(flavorData.majorVersion, 1)
		self.assertEqual(flavorData.minorVersion, 1)

	def test_mutually_exclusive_args(self):
		msg = "arguments are mutually exclusive"
		reader = DummyReader(self.file)
		with self.assertRaisesRegex(TypeError, msg):
			WOFF2FlavorData(reader, transformedTables={"hmtx"})
		with self.assertRaisesRegex(TypeError, msg):
			WOFF2FlavorData(reader, data=WOFF2FlavorData())

	def test_transformedTables_default(self):
		flavorData = WOFF2FlavorData()
		self.assertEqual(flavorData.transformedTables, set(woff2TransformedTableTags))

	def test_transformedTables_invalid(self):
		msg = r"'glyf' and 'loca' must be transformed \(or not\) together"

		with self.assertRaisesRegex(ValueError, msg):
			WOFF2FlavorData(transformedTables={"glyf"})

		with self.assertRaisesRegex(ValueError, msg):
			WOFF2FlavorData(transformedTables={"loca"})


class WOFF2WriterTest(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.font = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False, flavor="woff2")
		cls.font.importXML(OTX)
		cls.tags = sorted(t for t in cls.font.keys() if t != 'GlyphOrder')
		cls.numTables = len(cls.tags)
		cls.file = BytesIO(CFF_WOFF2.getvalue())
		cls.file.seek(0, 2)
		cls.length = (cls.file.tell() + 3) & ~3
		cls.setUpFlavorData()

	@classmethod
	def setUpFlavorData(cls):
		assert os.path.exists(METADATA)
		with open(METADATA, 'rb') as f:
			cls.xml_metadata = f.read()
		cls.compressed_metadata = brotli.compress(cls.xml_metadata, mode=brotli.MODE_TEXT)
		cls.privData = bytes(bytearray(random.sample(range(0, 256), 20)))

	def setUp(self):
		self.file.seek(0)
		self.writer = WOFF2Writer(BytesIO(), self.numTables, self.font.sfntVersion)

	def test_DSIG_dropped(self):
		self.writer['DSIG'] = b"\0"
		self.assertEqual(len(self.writer.tables), 0)
		self.assertEqual(self.writer.numTables, self.numTables-1)

	def test_no_rewrite_table(self):
		self.writer['ZZZZ'] = b"\0"
		with self.assertRaisesRegex(ttLib.TTLibError, "cannot rewrite"):
			self.writer['ZZZZ'] = b"\0"

	def test_num_tables(self):
		self.writer['ABCD'] = b"\0"
		with self.assertRaisesRegex(ttLib.TTLibError, "wrong number of tables"):
			self.writer.close()

	def test_required_tables(self):
		font = ttLib.TTFont(flavor="woff2")
		with self.assertRaisesRegex(ttLib.TTLibError, "missing required table"):
			font.save(BytesIO())

	def test_head_transform_flag(self):
		headData = self.font.getTableData('head')
		origFlags = byteord(headData[16])
		woff2font = ttLib.TTFont(self.file)
		newHeadData = woff2font.getTableData('head')
		modifiedFlags = byteord(newHeadData[16])
		self.assertNotEqual(origFlags, modifiedFlags)
		restoredFlags = modifiedFlags & ~0x08  # turn off bit 11
		self.assertEqual(origFlags, restoredFlags)

	def test_tables_sorted_alphabetically(self):
		expected = sorted([t for t in self.tags if t != 'DSIG'])
		woff2font = ttLib.TTFont(self.file)
		self.assertEqual(expected, list(woff2font.reader.keys()))

	def test_checksums(self):
		normFile = BytesIO(normalise_font(self.font, padding=4))
		normFile.seek(0)
		normFont = ttLib.TTFont(normFile, checkChecksums=2)
		w2font = ttLib.TTFont(self.file)
		# force reconstructing glyf table using 4-byte padding
		w2font.reader.padding = 4
		for tag in [t for t in self.tags if t != 'DSIG']:
			w2data = w2font.reader[tag]
			normData = normFont.reader[tag]
			if tag == "head":
				w2data = w2data[:8] + b'\0\0\0\0' + w2data[12:]
				normData = normData[:8] + b'\0\0\0\0' + normData[12:]
			w2CheckSum = ttLib.sfnt.calcChecksum(w2data)
			normCheckSum = ttLib.sfnt.calcChecksum(normData)
			self.assertEqual(w2CheckSum, normCheckSum)
		normCheckSumAdjustment = normFont['head'].checkSumAdjustment
		self.assertEqual(normCheckSumAdjustment, w2font['head'].checkSumAdjustment)

	def test_calcSFNTChecksumsLengthsAndOffsets(self):
		normFont = ttLib.TTFont(BytesIO(normalise_font(self.font, padding=4)))
		for tag in self.tags:
			self.writer[tag] = self.font.getTableData(tag)
		self.writer._normaliseGlyfAndLoca(padding=4)
		self.writer._setHeadTransformFlag()
		self.writer.tables = OrderedDict(sorted(self.writer.tables.items()))
		self.writer._calcSFNTChecksumsLengthsAndOffsets()
		for tag, entry in normFont.reader.tables.items():
			self.assertEqual(entry.offset, self.writer.tables[tag].origOffset)
			self.assertEqual(entry.length, self.writer.tables[tag].origLength)
			self.assertEqual(entry.checkSum, self.writer.tables[tag].checkSum)

	def test_bad_sfntVersion(self):
		for i in range(self.numTables):
			self.writer[bytechr(65 + i)*4] = b"\0"
		self.writer.sfntVersion = 'ZZZZ'
		with self.assertRaisesRegex(ttLib.TTLibError, "bad sfntVersion"):
			self.writer.close()

	def test_calcTotalSize_no_flavorData(self):
		expected = self.length
		self.writer.file = BytesIO()
		for tag in self.tags:
			self.writer[tag] = self.font.getTableData(tag)
		self.writer.close()
		self.assertEqual(expected, self.writer.length)
		self.assertEqual(expected, self.writer.file.tell())

	def test_calcTotalSize_with_metaData(self):
		expected = self.length + len(self.compressed_metadata)
		flavorData = self.writer.flavorData = WOFF2FlavorData()
		flavorData.metaData = self.xml_metadata
		self.writer.file = BytesIO()
		for tag in self.tags:
			self.writer[tag] = self.font.getTableData(tag)
		self.writer.close()
		self.assertEqual(expected, self.writer.length)
		self.assertEqual(expected, self.writer.file.tell())

	def test_calcTotalSize_with_privData(self):
		expected = self.length + len(self.privData)
		flavorData = self.writer.flavorData = WOFF2FlavorData()
		flavorData.privData = self.privData
		self.writer.file = BytesIO()
		for tag in self.tags:
			self.writer[tag] = self.font.getTableData(tag)
		self.writer.close()
		self.assertEqual(expected, self.writer.length)
		self.assertEqual(expected, self.writer.file.tell())

	def test_calcTotalSize_with_metaData_and_privData(self):
		metaDataLength = (len(self.compressed_metadata) + 3) & ~3
		expected = self.length + metaDataLength + len(self.privData)
		flavorData = self.writer.flavorData = WOFF2FlavorData()
		flavorData.metaData = self.xml_metadata
		flavorData.privData = self.privData
		self.writer.file = BytesIO()
		for tag in self.tags:
			self.writer[tag] = self.font.getTableData(tag)
		self.writer.close()
		self.assertEqual(expected, self.writer.length)
		self.assertEqual(expected, self.writer.file.tell())

	def test_getVersion(self):
		# no version
		self.assertEqual((0, 0), self.writer._getVersion())
		# version from head.fontRevision
		fontRevision = self.font['head'].fontRevision
		versionTuple = tuple(int(i) for i in str(fontRevision).split("."))
		entry = self.writer.tables['head'] = ttLib.newTable('head')
		entry.data = self.font.getTableData('head')
		self.assertEqual(versionTuple, self.writer._getVersion())
		# version from writer.flavorData
		flavorData = self.writer.flavorData = WOFF2FlavorData()
		flavorData.majorVersion, flavorData.minorVersion = (10, 11)
		self.assertEqual((10, 11), self.writer._getVersion())

	def test_hmtx_trasform(self):
		tableTransforms = {"glyf", "loca", "hmtx"}

		writer = WOFF2Writer(BytesIO(), self.numTables, self.font.sfntVersion)
		writer.flavorData = WOFF2FlavorData(transformedTables=tableTransforms)

		for tag in self.tags:
			writer[tag] = self.font.getTableData(tag)
		writer.close()

		# enabling hmtx transform has no effect when font has no glyf table
		self.assertEqual(writer.file.getvalue(), CFF_WOFF2.getvalue())

	def test_no_transforms(self):
		writer = WOFF2Writer(BytesIO(), self.numTables, self.font.sfntVersion)
		writer.flavorData = WOFF2FlavorData(transformedTables=())

		for tag in self.tags:
			writer[tag] = self.font.getTableData(tag)
		writer.close()

		# transforms settings have no effect when font is CFF-flavored, since
		# all the current transforms only apply to TrueType-flavored fonts.
		self.assertEqual(writer.file.getvalue(), CFF_WOFF2.getvalue())

class WOFF2WriterTTFTest(WOFF2WriterTest):

	@classmethod
	def setUpClass(cls):
		cls.font = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False, flavor="woff2")
		cls.font.importXML(TTX)
		cls.tags = sorted(t for t in cls.font.keys() if t != 'GlyphOrder')
		cls.numTables = len(cls.tags)
		cls.file = BytesIO(TT_WOFF2.getvalue())
		cls.file.seek(0, 2)
		cls.length = (cls.file.tell() + 3) & ~3
		cls.setUpFlavorData()

	def test_normaliseGlyfAndLoca(self):
		normTables = {}
		for tag in ('head', 'loca', 'glyf'):
			normTables[tag] = normalise_table(self.font, tag, padding=4)
		for tag in self.tags:
			tableData = self.font.getTableData(tag)
			self.writer[tag] = tableData
			if tag in normTables:
				self.assertNotEqual(tableData, normTables[tag])
		self.writer._normaliseGlyfAndLoca(padding=4)
		self.writer._setHeadTransformFlag()
		for tag in normTables:
			self.assertEqual(self.writer.tables[tag].data, normTables[tag])

	def test_hmtx_trasform(self):
		tableTransforms = {"glyf", "loca", "hmtx"}

		writer = WOFF2Writer(BytesIO(), self.numTables, self.font.sfntVersion)
		writer.flavorData = WOFF2FlavorData(transformedTables=tableTransforms)

		for tag in self.tags:
			writer[tag] = self.font.getTableData(tag)
		writer.close()

		length = len(writer.file.getvalue())

		# enabling optional hmtx transform shaves off a few bytes
		self.assertLess(length, len(TT_WOFF2.getvalue()))

	def test_no_transforms(self):
		writer = WOFF2Writer(BytesIO(), self.numTables, self.font.sfntVersion)
		writer.flavorData = WOFF2FlavorData(transformedTables=())

		for tag in self.tags:
			writer[tag] = self.font.getTableData(tag)
		writer.close()

		self.assertNotEqual(writer.file.getvalue(), TT_WOFF2.getvalue())

		writer.file.seek(0)
		reader = WOFF2Reader(writer.file)
		self.assertEqual(len(reader.flavorData.transformedTables), 0)


class WOFF2LocaTableTest(unittest.TestCase):

	def setUp(self):
		self.font = font = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False)
		font['head'] = ttLib.newTable('head')
		font['loca'] = WOFF2LocaTable()
		font['glyf'] = WOFF2GlyfTable()

	def test_compile_short_loca(self):
		locaTable = self.font['loca']
		locaTable.set(list(range(0, 0x20000, 2)))
		self.font['glyf'].indexFormat = 0
		locaData = locaTable.compile(self.font)
		self.assertEqual(len(locaData), 0x20000)

	def test_compile_short_loca_overflow(self):
		locaTable = self.font['loca']
		locaTable.set(list(range(0x20000 + 1)))
		self.font['glyf'].indexFormat = 0
		with self.assertRaisesRegex(
				ttLib.TTLibError, "indexFormat is 0 but local offsets > 0x20000"):
			locaTable.compile(self.font)

	def test_compile_short_loca_not_multiples_of_2(self):
		locaTable = self.font['loca']
		locaTable.set([1, 3, 5, 7])
		self.font['glyf'].indexFormat = 0
		with self.assertRaisesRegex(ttLib.TTLibError, "offsets not multiples of 2"):
			locaTable.compile(self.font)

	def test_compile_long_loca(self):
		locaTable = self.font['loca']
		locaTable.set(list(range(0x20001)))
		self.font['glyf'].indexFormat = 1
		locaData = locaTable.compile(self.font)
		self.assertEqual(len(locaData), 0x20001 * 4)

	def test_compile_set_indexToLocFormat_0(self):
		locaTable = self.font['loca']
		# offsets are all multiples of 2 and max length is < 0x10000
		locaTable.set(list(range(0, 0x20000, 2)))
		locaTable.compile(self.font)
		newIndexFormat = self.font['head'].indexToLocFormat
		self.assertEqual(0, newIndexFormat)

	def test_compile_set_indexToLocFormat_1(self):
		locaTable = self.font['loca']
		# offsets are not multiples of 2
		locaTable.set(list(range(10)))
		locaTable.compile(self.font)
		newIndexFormat = self.font['head'].indexToLocFormat
		self.assertEqual(1, newIndexFormat)
		# max length is >= 0x10000
		locaTable.set(list(range(0, 0x20000 + 1, 2)))
		locaTable.compile(self.font)
		newIndexFormat = self.font['head'].indexToLocFormat
		self.assertEqual(1, newIndexFormat)


class WOFF2GlyfTableTest(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		font = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False)
		font.importXML(TTX)
		cls.tables = {}
		cls.transformedTags = ('maxp', 'head', 'loca', 'glyf')
		for tag in reversed(cls.transformedTags):  # compile in inverse order
			cls.tables[tag] = font.getTableData(tag)
		infile = BytesIO(TT_WOFF2.getvalue())
		reader = WOFF2Reader(infile)
		cls.transformedGlyfData = reader.tables['glyf'].loadData(
			reader.transformBuffer)
		cls.glyphOrder = ['.notdef'] + ["glyph%.5d" % i for i in range(1, font['maxp'].numGlyphs)]

	def setUp(self):
		self.font = font = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False)
		font.setGlyphOrder(self.glyphOrder)
		font['head'] = ttLib.newTable('head')
		font['maxp'] = ttLib.newTable('maxp')
		font['loca'] = WOFF2LocaTable()
		font['glyf'] = WOFF2GlyfTable()
		for tag in self.transformedTags:
			font[tag].decompile(self.tables[tag], font)

	def test_reconstruct_glyf_padded_4(self):
		glyfTable = WOFF2GlyfTable()
		glyfTable.reconstruct(self.transformedGlyfData, self.font)
		glyfTable.padding = 4
		data = glyfTable.compile(self.font)
		normGlyfData = normalise_table(self.font, 'glyf', glyfTable.padding)
		self.assertEqual(normGlyfData, data)

	def test_reconstruct_glyf_padded_2(self):
		glyfTable = WOFF2GlyfTable()
		glyfTable.reconstruct(self.transformedGlyfData, self.font)
		glyfTable.padding = 2
		data = glyfTable.compile(self.font)
		normGlyfData = normalise_table(self.font, 'glyf', glyfTable.padding)
		self.assertEqual(normGlyfData, data)

	def test_reconstruct_glyf_unpadded(self):
		glyfTable = WOFF2GlyfTable()
		glyfTable.reconstruct(self.transformedGlyfData, self.font)
		data = glyfTable.compile(self.font)
		self.assertEqual(self.tables['glyf'], data)

	def test_reconstruct_glyf_incorrect_glyphOrder(self):
		glyfTable = WOFF2GlyfTable()
		badGlyphOrder = self.font.getGlyphOrder()[:-1]
		self.font.setGlyphOrder(badGlyphOrder)
		with self.assertRaisesRegex(ttLib.TTLibError, "incorrect glyphOrder"):
			glyfTable.reconstruct(self.transformedGlyfData, self.font)

	def test_reconstruct_glyf_missing_glyphOrder(self):
		glyfTable = WOFF2GlyfTable()
		del self.font.glyphOrder
		numGlyphs = self.font['maxp'].numGlyphs
		del self.font['maxp']
		glyfTable.reconstruct(self.transformedGlyfData, self.font)
		expected = [".notdef"]
		expected.extend(["glyph%.5d" % i for i in range(1, numGlyphs)])
		self.assertEqual(expected, glyfTable.glyphOrder)

	def test_reconstruct_loca_padded_4(self):
		locaTable = self.font['loca'] = WOFF2LocaTable()
		glyfTable = self.font['glyf'] = WOFF2GlyfTable()
		glyfTable.reconstruct(self.transformedGlyfData, self.font)
		glyfTable.padding = 4
		glyfTable.compile(self.font)
		data = locaTable.compile(self.font)
		normLocaData = normalise_table(self.font, 'loca', glyfTable.padding)
		self.assertEqual(normLocaData, data)

	def test_reconstruct_loca_padded_2(self):
		locaTable = self.font['loca'] = WOFF2LocaTable()
		glyfTable = self.font['glyf'] = WOFF2GlyfTable()
		glyfTable.reconstruct(self.transformedGlyfData, self.font)
		glyfTable.padding = 2
		glyfTable.compile(self.font)
		data = locaTable.compile(self.font)
		normLocaData = normalise_table(self.font, 'loca', glyfTable.padding)
		self.assertEqual(normLocaData, data)

	def test_reconstruct_loca_unpadded(self):
		locaTable = self.font['loca'] = WOFF2LocaTable()
		glyfTable = self.font['glyf'] = WOFF2GlyfTable()
		glyfTable.reconstruct(self.transformedGlyfData, self.font)
		glyfTable.compile(self.font)
		data = locaTable.compile(self.font)
		self.assertEqual(self.tables['loca'], data)

	def test_reconstruct_glyf_header_not_enough_data(self):
		with self.assertRaisesRegex(ttLib.TTLibError, "not enough 'glyf' data"):
			WOFF2GlyfTable().reconstruct(b"", self.font)

	def test_reconstruct_glyf_table_incorrect_size(self):
		msg = "incorrect size of transformed 'glyf'"
		with self.assertRaisesRegex(ttLib.TTLibError, msg):
			WOFF2GlyfTable().reconstruct(self.transformedGlyfData + b"\x00", self.font)
		with self.assertRaisesRegex(ttLib.TTLibError, msg):
			WOFF2GlyfTable().reconstruct(self.transformedGlyfData[:-1], self.font)

	def test_transform_glyf(self):
		glyfTable = self.font['glyf']
		data = glyfTable.transform(self.font)
		self.assertEqual(self.transformedGlyfData, data)

	def test_roundtrip_glyf_reconstruct_and_transform(self):
		glyfTable = WOFF2GlyfTable()
		glyfTable.reconstruct(self.transformedGlyfData, self.font)
		data = glyfTable.transform(self.font)
		self.assertEqual(self.transformedGlyfData, data)

	def test_roundtrip_glyf_transform_and_reconstruct(self):
		glyfTable = self.font['glyf']
		transformedData = glyfTable.transform(self.font)
		newGlyfTable = WOFF2GlyfTable()
		newGlyfTable.reconstruct(transformedData, self.font)
		newGlyfTable.padding = 4
		reconstructedData = newGlyfTable.compile(self.font)
		normGlyfData = normalise_table(self.font, 'glyf', newGlyfTable.padding)
		self.assertEqual(normGlyfData, reconstructedData)


@pytest.fixture(scope="module")
def fontfile():

	class Glyph(object):
		def __init__(self, empty=False, **kwargs):
			if not empty:
				self.draw = partial(self.drawRect, **kwargs)
			else:
				self.draw = lambda pen: None

		@staticmethod
		def drawRect(pen, xMin, xMax):
			pen.moveTo((xMin, 0))
			pen.lineTo((xMin, 1000))
			pen.lineTo((xMax, 1000))
			pen.lineTo((xMax, 0))
			pen.closePath()

	class CompositeGlyph(object):
		def __init__(self, components):
			self.components = components

		def draw(self, pen):
			for baseGlyph, (offsetX, offsetY) in self.components:
				pen.addComponent(baseGlyph, (1, 0, 0, 1, offsetX, offsetY))

	fb = fontBuilder.FontBuilder(unitsPerEm=1000, isTTF=True)
	fb.setupGlyphOrder(
		[".notdef", "space", "A", "acutecomb", "Aacute", "zero", "one", "two"]
	)
	fb.setupCharacterMap(
		{
			0x20: "space",
			0x41: "A",
			0x0301: "acutecomb",
			0xC1: "Aacute",
			0x30: "zero",
			0x31: "one",
			0x32: "two",
		}
	)
	fb.setupHorizontalMetrics(
		{
			".notdef": (500, 50),
			"space": (600, 0),
			"A": (550, 40),
			"acutecomb": (0, -40),
			"Aacute": (550, 40),
			"zero": (500, 30),
			"one": (500, 50),
			"two": (500, 40),
		}
	)
	fb.setupHorizontalHeader(ascent=1000, descent=-200)

	srcGlyphs = {
		".notdef": Glyph(xMin=50, xMax=450),
		"space": Glyph(empty=True),
		"A": Glyph(xMin=40, xMax=510),
		"acutecomb": Glyph(xMin=-40, xMax=60),
		"Aacute": CompositeGlyph([("A", (0, 0)), ("acutecomb", (200, 0))]),
		"zero": Glyph(xMin=30, xMax=470),
		"one": Glyph(xMin=50, xMax=450),
		"two": Glyph(xMin=40, xMax=460),
	}
	pen = TTGlyphPen(srcGlyphs)
	glyphSet = {}
	for glyphName, glyph in srcGlyphs.items():
		glyph.draw(pen)
		glyphSet[glyphName] = pen.glyph()
	fb.setupGlyf(glyphSet)

	fb.setupNameTable(
		{
			"familyName": "TestWOFF2",
			"styleName": "Regular",
			"uniqueFontIdentifier": "TestWOFF2 Regular; Version 1.000; ABCD",
			"fullName": "TestWOFF2 Regular",
			"version": "Version 1.000",
			"psName": "TestWOFF2-Regular",
		}
	)
	fb.setupOS2()
	fb.setupPost()

	buf = BytesIO()
	fb.save(buf)
	buf.seek(0)

	assert fb.font["maxp"].numGlyphs == 8
	assert fb.font["hhea"].numberOfHMetrics == 6
	for glyphName in fb.font.getGlyphOrder():
		xMin = getattr(fb.font["glyf"][glyphName], "xMin", 0)
		assert xMin == fb.font["hmtx"][glyphName][1]

	return buf


@pytest.fixture
def ttFont(fontfile):
	return ttLib.TTFont(fontfile, recalcBBoxes=False, recalcTimestamp=False)


class WOFF2HmtxTableTest(object):
	def test_transform_no_sidebearings(self, ttFont):
		hmtxTable = WOFF2HmtxTable()
		hmtxTable.metrics = ttFont["hmtx"].metrics

		data = hmtxTable.transform(ttFont)

		assert data == (
			b"\x03"  # 00000011 | bits 0 and 1 are set (no sidebearings arrays)

			# advanceWidthArray
			b'\x01\xf4'  # .notdef: 500
			b'\x02X'     # space: 600
			b'\x02&'     # A: 550
			b'\x00\x00'  # acutecomb: 0
			b'\x02&'     # Aacute: 550
			b'\x01\xf4'  # zero: 500
		)

	def test_transform_proportional_sidebearings(self, ttFont):
		hmtxTable = WOFF2HmtxTable()
		metrics = ttFont["hmtx"].metrics
		# force one of the proportional glyphs to have its left sidebearing be
		# different from its xMin (40)
		metrics["A"] = (550, 39)
		hmtxTable.metrics = metrics

		assert ttFont["glyf"]["A"].xMin != metrics["A"][1]

		data = hmtxTable.transform(ttFont)

		assert data == (
			b"\x02"  # 00000010 | bits 0 unset: explicit proportional sidebearings

			# advanceWidthArray
			b'\x01\xf4'  # .notdef: 500
			b'\x02X'     # space: 600
			b'\x02&'     # A: 550
			b'\x00\x00'  # acutecomb: 0
			b'\x02&'     # Aacute: 550
			b'\x01\xf4'  # zero: 500

			# lsbArray
			b'\x002'     # .notdef: 50
			b'\x00\x00'  # space: 0
			b"\x00'"     # A: 39 (xMin: 40)
			b'\xff\xd8'  # acutecomb: -40
			b'\x00('     # Aacute: 40
			b'\x00\x1e'  # zero: 30
		)

	def test_transform_monospaced_sidebearings(self, ttFont):
		hmtxTable = WOFF2HmtxTable()
		metrics = ttFont["hmtx"].metrics
		hmtxTable.metrics = metrics

		# force one of the monospaced glyphs at the end of hmtx table to have
		# its xMin different from its left sidebearing (50)
		ttFont["glyf"]["one"].xMin = metrics["one"][1] + 1

		data = hmtxTable.transform(ttFont)

		assert data == (
			b"\x01"  # 00000001 | bits 1 unset: explicit monospaced sidebearings

			# advanceWidthArray
			b'\x01\xf4'  # .notdef: 500
			b'\x02X'     # space: 600
			b'\x02&'     # A: 550
			b'\x00\x00'  # acutecomb: 0
			b'\x02&'     # Aacute: 550
			b'\x01\xf4'  # zero: 500

			# leftSideBearingArray
			b'\x002'     # one: 50 (xMin: 51)
			b'\x00('     # two: 40
		)

	def test_transform_not_applicable(self, ttFont):
		hmtxTable = WOFF2HmtxTable()
		metrics = ttFont["hmtx"].metrics
		# force both a proportional and monospaced glyph to have sidebearings
		# different from the respective xMin coordinates
		metrics["A"] = (550, 39)
		metrics["one"] = (500, 51)
		hmtxTable.metrics = metrics

		# 'None' signals to fall back using untransformed hmtx table data
		assert hmtxTable.transform(ttFont) is None

	def test_reconstruct_no_sidebearings(self, ttFont):
		hmtxTable = WOFF2HmtxTable()

		data = (
			b"\x03"  # 00000011 | bits 0 and 1 are set (no sidebearings arrays)

			# advanceWidthArray
			b'\x01\xf4'  # .notdef: 500
			b'\x02X'     # space: 600
			b'\x02&'     # A: 550
			b'\x00\x00'  # acutecomb: 0
			b'\x02&'     # Aacute: 550
			b'\x01\xf4'  # zero: 500
		)

		hmtxTable.reconstruct(data, ttFont)

		assert hmtxTable.metrics == {
			".notdef": (500, 50),
			"space": (600, 0),
			"A": (550, 40),
			"acutecomb": (0, -40),
			"Aacute": (550, 40),
			"zero": (500, 30),
			"one": (500, 50),
			"two": (500, 40),
		}

	def test_reconstruct_proportional_sidebearings(self, ttFont):
		hmtxTable = WOFF2HmtxTable()

		data = (
			b"\x02"  # 00000010 | bits 0 unset: explicit proportional sidebearings

			# advanceWidthArray
			b'\x01\xf4'  # .notdef: 500
			b'\x02X'     # space: 600
			b'\x02&'     # A: 550
			b'\x00\x00'  # acutecomb: 0
			b'\x02&'     # Aacute: 550
			b'\x01\xf4'  # zero: 500

			# lsbArray
			b'\x002'     # .notdef: 50
			b'\x00\x00'  # space: 0
			b"\x00'"     # A: 39 (xMin: 40)
			b'\xff\xd8'  # acutecomb: -40
			b'\x00('     # Aacute: 40
			b'\x00\x1e'  # zero: 30
		)

		hmtxTable.reconstruct(data, ttFont)

		assert hmtxTable.metrics == {
			".notdef": (500, 50),
			"space": (600, 0),
			"A": (550, 39),
			"acutecomb": (0, -40),
			"Aacute": (550, 40),
			"zero": (500, 30),
			"one": (500, 50),
			"two": (500, 40),
		}

		assert ttFont["glyf"]["A"].xMin == 40

	def test_reconstruct_monospaced_sidebearings(self, ttFont):
		hmtxTable = WOFF2HmtxTable()

		data = (
			b"\x01"  # 00000001 | bits 1 unset: explicit monospaced sidebearings

			# advanceWidthArray
			b'\x01\xf4'  # .notdef: 500
			b'\x02X'     # space: 600
			b'\x02&'     # A: 550
			b'\x00\x00'  # acutecomb: 0
			b'\x02&'     # Aacute: 550
			b'\x01\xf4'  # zero: 500

			# leftSideBearingArray
			b'\x003'     # one: 51 (xMin: 50)
			b'\x00('     # two: 40
		)

		hmtxTable.reconstruct(data, ttFont)

		assert hmtxTable.metrics == {
			".notdef": (500, 50),
			"space": (600, 0),
			"A": (550, 40),
			"acutecomb": (0, -40),
			"Aacute": (550, 40),
			"zero": (500, 30),
			"one": (500, 51),
			"two": (500, 40),
		}

		assert ttFont["glyf"]["one"].xMin == 50

	def test_reconstruct_flags_reserved_bits(self):
		hmtxTable = WOFF2HmtxTable()

		with pytest.raises(
			ttLib.TTLibError, match="Bits 2-7 of 'hmtx' flags are reserved"
		):
			hmtxTable.reconstruct(b"\xFF", ttFont=None)

	def test_reconstruct_flags_required_bits(self):
		hmtxTable = WOFF2HmtxTable()

		with pytest.raises(ttLib.TTLibError, match="either bits 0 or 1 .* must set"):
			hmtxTable.reconstruct(b"\x00", ttFont=None)

	def test_reconstruct_too_much_data(self, ttFont):
		ttFont["hhea"].numberOfHMetrics = 2
		data = b'\x03\x01\xf4\x02X\x02&'
		hmtxTable = WOFF2HmtxTable()

		with pytest.raises(ttLib.TTLibError, match="too much 'hmtx' table data"):
			hmtxTable.reconstruct(data, ttFont)


class WOFF2RoundtripTest(object):
	@staticmethod
	def roundtrip(infile):
		infile.seek(0)
		ttFont = ttLib.TTFont(infile, recalcBBoxes=False, recalcTimestamp=False)
		outfile = BytesIO()
		ttFont.save(outfile)
		return outfile, ttFont

	def test_roundtrip_default_transforms(self, ttFont):
		ttFont.flavor = "woff2"
		# ttFont.flavorData = None
		tmp = BytesIO()
		ttFont.save(tmp)

		tmp2, ttFont2 = self.roundtrip(tmp)

		assert tmp.getvalue() == tmp2.getvalue()
		assert ttFont2.reader.flavorData.transformedTables == {"glyf", "loca"}

	def test_roundtrip_no_transforms(self, ttFont):
		ttFont.flavor = "woff2"
		ttFont.flavorData = WOFF2FlavorData(transformedTables=[])
		tmp = BytesIO()
		ttFont.save(tmp)

		tmp2, ttFont2 = self.roundtrip(tmp)

		assert tmp.getvalue() == tmp2.getvalue()
		assert not ttFont2.reader.flavorData.transformedTables

	def test_roundtrip_all_transforms(self, ttFont):
		ttFont.flavor = "woff2"
		ttFont.flavorData = WOFF2FlavorData(transformedTables=["glyf", "loca", "hmtx"])
		tmp = BytesIO()
		ttFont.save(tmp)

		tmp2, ttFont2 = self.roundtrip(tmp)

		assert tmp.getvalue() == tmp2.getvalue()
		assert ttFont2.reader.flavorData.transformedTables == {"glyf", "loca", "hmtx"}

	def test_roundtrip_only_hmtx_no_glyf_transform(self, ttFont):
		ttFont.flavor = "woff2"
		ttFont.flavorData = WOFF2FlavorData(transformedTables=["hmtx"])
		tmp = BytesIO()
		ttFont.save(tmp)

		tmp2, ttFont2 = self.roundtrip(tmp)

		assert tmp.getvalue() == tmp2.getvalue()
		assert ttFont2.reader.flavorData.transformedTables == {"hmtx"}

	def test_roundtrip_no_glyf_and_loca_tables(self):
		ttx = os.path.join(
			os.path.dirname(current_dir), "subset", "data", "google_color.ttx"
		)
		ttFont = ttLib.TTFont()
		ttFont.importXML(ttx)

		assert "glyf" not in ttFont
		assert "loca" not in ttFont

		ttFont.flavor = "woff2"
		tmp = BytesIO()
		ttFont.save(tmp)

		tmp2, ttFont2 = self.roundtrip(tmp)
		assert tmp.getvalue() == tmp2.getvalue()
		assert ttFont.flavor == "woff2"


class MainTest(object):

	@staticmethod
	def make_ttf(tmpdir):
		ttFont = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False)
		ttFont.importXML(TTX)
		filename = str(tmpdir / "TestTTF-Regular.ttf")
		ttFont.save(filename)
		return filename

	def test_compress_ttf(self, tmpdir):
		input_file = self.make_ttf(tmpdir)

		assert woff2.main(["compress", input_file]) is None

		assert (tmpdir / "TestTTF-Regular.woff2").check(file=True)

	def test_compress_ttf_no_glyf_transform(self, tmpdir):
		input_file = self.make_ttf(tmpdir)

		assert woff2.main(["compress", "--no-glyf-transform", input_file]) is None

		assert (tmpdir / "TestTTF-Regular.woff2").check(file=True)

	def test_compress_ttf_hmtx_transform(self, tmpdir):
		input_file = self.make_ttf(tmpdir)

		assert woff2.main(["compress", "--hmtx-transform", input_file]) is None

		assert (tmpdir / "TestTTF-Regular.woff2").check(file=True)

	def test_compress_ttf_no_glyf_transform_hmtx_transform(self, tmpdir):
		input_file = self.make_ttf(tmpdir)

		assert woff2.main(
			["compress", "--no-glyf-transform", "--hmtx-transform", input_file]
		) is None

		assert (tmpdir / "TestTTF-Regular.woff2").check(file=True)

	def test_compress_output_file(self, tmpdir):
		input_file = self.make_ttf(tmpdir)
		output_file = tmpdir / "TestTTF.woff2"

		assert woff2.main(
			["compress", "-o", str(output_file), str(input_file)]
		) is None

		assert output_file.check(file=True)

	def test_compress_otf(self, tmpdir):
		ttFont = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False)
		ttFont.importXML(OTX)
		input_file = str(tmpdir / "TestOTF-Regular.otf")
		ttFont.save(input_file)

		assert woff2.main(["compress", input_file]) is None

		assert (tmpdir / "TestOTF-Regular.woff2").check(file=True)

	def test_recompress_woff2_keeps_flavorData(self, tmpdir):
		woff2_font = ttLib.TTFont(BytesIO(TT_WOFF2.getvalue()))
		woff2_font.flavorData.privData = b"FOOBAR"
		woff2_file = tmpdir / "TestTTF-Regular.woff2"
		woff2_font.save(str(woff2_file))

		assert woff2_font.flavorData.transformedTables == {"glyf", "loca"}

		woff2.main(["compress", "--hmtx-transform", str(woff2_file)])

		output_file = tmpdir / "TestTTF-Regular#1.woff2"
		assert output_file.check(file=True)

		new_woff2_font = ttLib.TTFont(str(output_file))

		assert new_woff2_font.flavorData.transformedTables == {"glyf", "loca", "hmtx"}
		assert new_woff2_font.flavorData.privData == b"FOOBAR"

	def test_decompress_ttf(self, tmpdir):
		input_file = tmpdir / "TestTTF-Regular.woff2"
		input_file.write_binary(TT_WOFF2.getvalue())

		assert woff2.main(["decompress", str(input_file)]) is None

		assert (tmpdir / "TestTTF-Regular.ttf").check(file=True)

	def test_decompress_otf(self, tmpdir):
		input_file = tmpdir / "TestTTF-Regular.woff2"
		input_file.write_binary(CFF_WOFF2.getvalue())

		assert woff2.main(["decompress", str(input_file)]) is None

		assert (tmpdir / "TestTTF-Regular.otf").check(file=True)

	def test_decompress_output_file(self, tmpdir):
		input_file = tmpdir / "TestTTF-Regular.woff2"
		input_file.write_binary(TT_WOFF2.getvalue())
		output_file = tmpdir / "TestTTF.ttf"

		assert woff2.main(
			["decompress", "-o", str(output_file), str(input_file)]
		) is None

		assert output_file.check(file=True)

	def test_no_subcommand_show_help(self, capsys):
		with pytest.raises(SystemExit):
			woff2.main(["--help"])

		captured = capsys.readouterr()
		assert "usage: fonttools ttLib.woff2" in captured.out


class Base128Test(unittest.TestCase):

	def test_unpackBase128(self):
		self.assertEqual(unpackBase128(b'\x3f\x00\x00'), (63, b"\x00\x00"))
		self.assertEqual(unpackBase128(b'\x8f\xff\xff\xff\x7f')[0], 4294967295)

		self.assertRaisesRegex(
			ttLib.TTLibError,
			"UIntBase128 value must not start with leading zeros",
			unpackBase128, b'\x80\x80\x3f')

		self.assertRaisesRegex(
			ttLib.TTLibError,
			"UIntBase128-encoded sequence is longer than 5 bytes",
			unpackBase128, b'\x8f\xff\xff\xff\xff\x7f')

		self.assertRaisesRegex(
			ttLib.TTLibError,
			r"UIntBase128 value exceeds 2\*\*32-1",
			unpackBase128, b'\x90\x80\x80\x80\x00')

		self.assertRaisesRegex(
			ttLib.TTLibError,
			"not enough data to unpack UIntBase128",
			unpackBase128, b'')

	def test_base128Size(self):
		self.assertEqual(base128Size(0), 1)
		self.assertEqual(base128Size(24567), 3)
		self.assertEqual(base128Size(2**32-1), 5)

	def test_packBase128(self):
		self.assertEqual(packBase128(63), b"\x3f")
		self.assertEqual(packBase128(2**32-1), b'\x8f\xff\xff\xff\x7f')
		self.assertRaisesRegex(
			ttLib.TTLibError,
			r"UIntBase128 format requires 0 <= integer <= 2\*\*32-1",
			packBase128, 2**32+1)
		self.assertRaisesRegex(
			ttLib.TTLibError,
			r"UIntBase128 format requires 0 <= integer <= 2\*\*32-1",
			packBase128, -1)


class UShort255Test(unittest.TestCase):

	def test_unpack255UShort(self):
		self.assertEqual(unpack255UShort(bytechr(252))[0], 252)
		# some numbers (e.g. 506) can have multiple encodings
		self.assertEqual(
			unpack255UShort(struct.pack(b"BB", 254, 0))[0], 506)
		self.assertEqual(
			unpack255UShort(struct.pack(b"BB", 255, 253))[0], 506)
		self.assertEqual(
			unpack255UShort(struct.pack(b"BBB", 253, 1, 250))[0], 506)

		self.assertRaisesRegex(
			ttLib.TTLibError,
			"not enough data to unpack 255UInt16",
			unpack255UShort, struct.pack(b"BB", 253, 0))

		self.assertRaisesRegex(
			ttLib.TTLibError,
			"not enough data to unpack 255UInt16",
			unpack255UShort, struct.pack(b"B", 254))

		self.assertRaisesRegex(
			ttLib.TTLibError,
			"not enough data to unpack 255UInt16",
			unpack255UShort, struct.pack(b"B", 255))

	def test_pack255UShort(self):
		self.assertEqual(pack255UShort(252), b'\xfc')
		self.assertEqual(pack255UShort(505), b'\xff\xfc')
		self.assertEqual(pack255UShort(506), b'\xfe\x00')
		self.assertEqual(pack255UShort(762), b'\xfd\x02\xfa')

		self.assertRaisesRegex(
			ttLib.TTLibError,
			"255UInt16 format requires 0 <= integer <= 65535",
			pack255UShort, -1)

		self.assertRaisesRegex(
			ttLib.TTLibError,
			"255UInt16 format requires 0 <= integer <= 65535",
			pack255UShort, 0xFFFF+1)


if __name__ == "__main__":
	import sys
	sys.exit(unittest.main())
