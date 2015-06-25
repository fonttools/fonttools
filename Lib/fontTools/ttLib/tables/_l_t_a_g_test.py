from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.xmlWriter import XMLWriter
import os
import struct
import unittest
from ._l_t_a_g import table__l_t_a_g

class Test_l_t_a_g(unittest.TestCase):

	DATA_ = struct.pack(b">LLLHHHHHH", 1, 0, 3, 24 + 0, 2, 24 + 2, 7, 24 + 2, 2) + b"enzh-Hant"
	TAGS_ = ["en", "zh-Hant", "zh"]

	def test_decompile_compile(self):
		table = table__l_t_a_g()
		table.decompile(self.DATA_, ttFont=None)
		self.assertEqual(1, table.version)
		self.assertEqual(0, table.flags)
		self.assertEqual(self.TAGS_, table.tags)
		self.assertEqual(self.DATA_, table.compile(ttFont=None))

	def test_fromXML(self):
		table = table__l_t_a_g()
		table.fromXML("version", {"value": "1"}, content=None, ttFont=None)
		table.fromXML("flags", {"value": "777"}, content=None, ttFont=None)
		table.fromXML("LanguageTag", {"tag": "sr-Latn"}, content=None, ttFont=None)
		table.fromXML("LanguageTag", {"tag": "fa"}, content=None, ttFont=None)
		self.assertEqual(1, table.version)
		self.assertEqual(777, table.flags)
		self.assertEqual(["sr-Latn", "fa"], table.tags)

	def test_toXML(self):
		writer = XMLWriter(StringIO())
		table = table__l_t_a_g()
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
	unittest.main()
