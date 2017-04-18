from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.testTools import parseXML
from fontTools.misc.xmlWriter import XMLWriter
import os
import struct
import unittest
from fontTools.ttLib import newTable


class Test_l_t_a_g(unittest.TestCase):

	DATA_ = struct.pack(b">LLLHHHHHH", 1, 0, 3, 24 + 0, 2, 24 + 2, 7, 24 + 2, 2) + b"enzh-Hant"
	TAGS_ = ["en", "zh-Hant", "zh"]

	def test_addTag(self):
		table = newTable("ltag")
		self.assertEqual(table.addTag("de-CH"), 0)
		self.assertEqual(table.addTag("gsw-LI"), 1)
		self.assertEqual(table.addTag("de-CH"), 0)
		self.assertEqual(table.tags, ["de-CH", "gsw-LI"])

	def test_decompile_compile(self):
		table = newTable("ltag")
		table.decompile(self.DATA_, ttFont=None)
		self.assertEqual(1, table.version)
		self.assertEqual(0, table.flags)
		self.assertEqual(self.TAGS_, table.tags)
		compiled = table.compile(ttFont=None)
		self.assertEqual(self.DATA_, compiled)
		self.assertIsInstance(compiled, bytes)

	def test_fromXML(self):
		table = newTable("ltag")
		for name, attrs, content in parseXML(
				'<version value="1"/>'
				'<flags value="777"/>'
				'<LanguageTag tag="sr-Latn"/>'
				'<LanguageTag tag="fa"/>'):
			table.fromXML(name, attrs, content, ttFont=None)
		self.assertEqual(1, table.version)
		self.assertEqual(777, table.flags)
		self.assertEqual(["sr-Latn", "fa"], table.tags)

	def test_toXML(self):
		writer = XMLWriter(BytesIO())
		table = newTable("ltag")
		table.decompile(self.DATA_, ttFont=None)
		table.toXML(writer, ttFont=None)
		expected = os.linesep.join([
			'<?xml version="1.0" encoding="UTF-8"?>',
			'<version value="1"/>',
			'<flags value="0"/>',
			'<LanguageTag tag="en"/>',
			'<LanguageTag tag="zh-Hant"/>',
			'<LanguageTag tag="zh"/>'
		]) + os.linesep
		self.assertEqual(expected.encode("utf_8"), writer.file.getvalue())


if __name__ == '__main__':
	import sys
	sys.exit(unittest.main())
