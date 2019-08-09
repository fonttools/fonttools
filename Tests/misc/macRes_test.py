from fontTools.misc.py23 import *
import sys
import os
import tempfile
import unittest
from fontTools.misc.textTools import deHexStr
from fontTools.misc.macRes import ResourceReader


# test resource data in DeRez notation
"""
data 'TEST' (128, "name1") { $"4865 6C6C 6F" };                   /* Hello */
data 'TEST' (129, "name2") { $"576F 726C 64" };                   /* World */
data 'test' (130, "name3") { $"486F 7720 6172 6520 796F 753F" };  /* How are you? */
"""
# the same data, compiled using Rez
# $ /usr/bin/Rez testdata.rez -o compiled
# $ hexdump -v compiled/..namedfork/rsrc
TEST_RSRC_FORK = deHexStr(
	"00 00 01 00 00 00 01 22 00 00 00 22 00 00 00 64 "  # 0x00000000
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x00000010
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x00000020
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x00000030
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x00000040
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x00000050
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x00000060
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x00000070
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x00000080
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x00000090
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x000000A0
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x000000B0
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x000000C0
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x000000D0
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x000000E0
	"00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x000000F0
	"00 00 00 05 48 65 6c 6c 6f 00 00 00 05 57 6f 72 "  # 0x00000100
	"6c 64 00 00 00 0c 48 6f 77 20 61 72 65 20 79 6f "  # 0x00000110
	"75 3f 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "  # 0x00000120
	"00 00 00 00 00 00 00 00 00 00 00 1c 00 52 00 01 "  # 0x00000130
	"54 45 53 54 00 01 00 12 74 65 73 74 00 00 00 2a "  # 0x00000140
	"00 80 00 00 00 00 00 00 00 00 00 00 00 81 00 06 "  # 0x00000150
	"00 00 00 09 00 00 00 00 00 82 00 0c 00 00 00 12 "  # 0x00000160
	"00 00 00 00 05 6e 61 6d 65 31 05 6e 61 6d 65 32 "  # 0x00000170
	"05 6e 61 6d 65 33                               "  # 0x00000180
)


class ResourceReaderTest(unittest.TestCase):

	def test_read_file(self):
		infile = BytesIO(TEST_RSRC_FORK)
		reader = ResourceReader(infile)
		resources = [res for typ in reader.keys() for res in reader[typ]]
		self.assertExpected(resources)

	def test_read_datafork(self):
		with tempfile.NamedTemporaryFile(delete=False) as tmp:
			tmp.write(TEST_RSRC_FORK)
		try:
			reader = ResourceReader(tmp.name)
			resources = [res for typ in reader.keys() for res in reader[typ]]
			reader.close()
			self.assertExpected(resources)
		finally:
			os.remove(tmp.name)

	def test_read_namedfork_rsrc(self):
		if sys.platform != 'darwin':
			self.skipTest('Not supported on "%s"' % sys.platform)
		tmp = tempfile.NamedTemporaryFile(delete=False)
		tmp.close()
		try:
			with open(tmp.name + '/..namedfork/rsrc', 'wb') as fork:
				fork.write(TEST_RSRC_FORK)
			reader = ResourceReader(tmp.name)
			resources = [res for typ in reader.keys() for res in reader[typ]]
			reader.close()
			self.assertExpected(resources)
		finally:
			os.remove(tmp.name)

	def assertExpected(self, resources):
		self.assertRezEqual(resources[0], 'TEST', b'Hello', 128, 'name1')
		self.assertRezEqual(resources[1], 'TEST', b'World', 129, 'name2')
		self.assertRezEqual(
			resources[2], 'test', b'How are you?', 130, 'name3')

	def assertRezEqual(self, res, type_, data, id, name):
		self.assertEqual(res.type, type_)
		self.assertEqual(res.data, data)
		self.assertEqual(res.id, id)
		self.assertEqual(res.name, name)


if __name__ == '__main__':
	sys.exit(unittest.main())
