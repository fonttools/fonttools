from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import os
import unittest
from .xmlWriter import XMLWriter

linesep = tobytes(os.linesep)
HEADER = b'<?xml version="1.0" encoding="UTF-8"?>' + linesep

class TestXMLWriter(unittest.TestCase):

	def test_comment_escaped(self):
		writer = XMLWriter(StringIO())
		writer.comment("This&that are <comments>")
		self.assertEqual(HEADER + b"<!-- This&amp;that are &lt;comments&gt; -->", writer.file.getvalue())

	def test_comment_multiline(self):
		writer = XMLWriter(StringIO())
		writer.comment("Hello world\nHow are you?")
		self.assertEqual(HEADER + b"<!-- Hello world" + linesep + b"     How are you? -->",
				 writer.file.getvalue())

	def test_encoding_default(self):
		writer = XMLWriter(StringIO())
		self.assertEqual(b'<?xml version="1.0" encoding="UTF-8"?>' + linesep,
				 writer.file.getvalue())

	def test_encoding_utf8(self):
		# https://github.com/behdad/fonttools/issues/246
		writer = XMLWriter(StringIO(), encoding="utf8")
		self.assertEqual(b'<?xml version="1.0" encoding="UTF-8"?>' + linesep,
				 writer.file.getvalue())

	def test_encoding_UTF_8(self):
		# https://github.com/behdad/fonttools/issues/246
		writer = XMLWriter(StringIO(), encoding="UTF-8")
		self.assertEqual(b'<?xml version="1.0" encoding="UTF-8"?>' + linesep,
				 writer.file.getvalue())

	def test_encoding_UTF8(self):
		# https://github.com/behdad/fonttools/issues/246
		writer = XMLWriter(StringIO(), encoding="UTF8")
		self.assertEqual(b'<?xml version="1.0" encoding="UTF-8"?>' + linesep,
				 writer.file.getvalue())

	def test_encoding_other(self):
		self.assertRaises(Exception, XMLWriter, StringIO(),
				  encoding="iso-8859-1")

	def test_write(self):
		writer = XMLWriter(StringIO())
		writer.write("foo&bar")
		self.assertEqual(HEADER + b"foo&amp;bar", writer.file.getvalue())

	def test_indent_dedent(self):
		writer = XMLWriter(StringIO())
		writer.write("foo")
		writer.newline()
		writer.indent()
		writer.write("bar")
		writer.newline()
		writer.dedent()
		writer.write("baz")
		self.assertEqual(HEADER + bytesjoin(["foo", "  bar", "baz"], linesep),
				 writer.file.getvalue())

	def test_writecdata(self):
		writer = XMLWriter(StringIO())
		writer.writecdata("foo&bar")
		self.assertEqual(HEADER + b"<![CDATA[foo&bar]]>", writer.file.getvalue())

	def test_simpletag(self):
		writer = XMLWriter(StringIO())
		writer.simpletag("tag", a="1", b="2")
		self.assertEqual(HEADER + b'<tag a="1" b="2"/>', writer.file.getvalue())

	def test_begintag_endtag(self):
		writer = XMLWriter(StringIO())
		writer.begintag("tag", attr="value")
		writer.write("content")
		writer.endtag("tag")
		self.assertEqual(HEADER + b'<tag attr="value">content</tag>', writer.file.getvalue())

	def test_dumphex(self):
		writer = XMLWriter(StringIO())
		writer.dumphex("Type is a beautiful group of letters, not a group of beautiful letters.")
		self.assertEqual(HEADER + bytesjoin([
		    "54797065 20697320 61206265 61757469",
		    "66756c20 67726f75 70206f66 206c6574",
		    "74657273 2c206e6f 74206120 67726f75",
		    "70206f66 20626561 75746966 756c206c",
		    "65747465 72732e  ", ""], joiner=linesep), writer.file.getvalue())

	def test_stringifyattrs(self):
		writer = XMLWriter(StringIO())
		expected = ' attr="0"'
		self.assertEqual(expected, writer.stringifyattrs(attr=0))
		self.assertEqual(expected, writer.stringifyattrs(attr=b'0'))
		self.assertEqual(expected, writer.stringifyattrs(attr='0'))
		self.assertEqual(expected, writer.stringifyattrs(attr=u'0'))


if __name__ == '__main__':
	unittest.main()
