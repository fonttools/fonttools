from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from cStringIO import StringIO
import unittest
from .xmlWriter import XMLWriter

HEADER = '<?xml version="1.0" encoding="utf-8"?>\n'

class TestXMLWriter(unittest.TestCase):

	def test_comment_escaped(self):
		writer = XMLWriter(StringIO())
		writer.comment("This&that are <comments>")
		self.assertEquals(HEADER + "<!-- This&amp;that are &lt;comments&gt; -->", writer.file.getvalue())

	def test_comment_multiline(self):
		writer = XMLWriter(StringIO())
		writer.comment("Hello world\nHow are you?")
		self.assertEquals(HEADER + "<!-- Hello world\n     How are you? -->", writer.file.getvalue())

	def test_write(self):
		writer = XMLWriter(StringIO())
		writer.write("foo&bar")
		self.assertEquals(HEADER + "foo&amp;bar", writer.file.getvalue())

	def test_indent_dedent(self):
		writer = XMLWriter(StringIO())
		writer.write("foo")
		writer.newline()
		writer.indent()
		writer.write("bar")
		writer.newline()
		writer.dedent()
		writer.write("baz")
		self.assertEquals(HEADER + "foo\n  bar\nbaz", writer.file.getvalue())

	def test_writecdata(self):
		writer = XMLWriter(StringIO())
		writer.writecdata("foo&bar")
		self.assertEquals(HEADER + "<![CDATA[foo&bar]]>", writer.file.getvalue())

	def test_simpletag(self):
		writer = XMLWriter(StringIO())
		writer.simpletag("tag", a="1", b="2")
		self.assertEquals(HEADER + '<tag a="1" b="2"/>', writer.file.getvalue())

	def test_begintag_endtag(self):
		writer = XMLWriter(StringIO())
		writer.begintag("tag", attr="value")
		writer.write("content")
		writer.endtag("tag")
		self.assertEquals(HEADER + '<tag attr="value">content</tag>', writer.file.getvalue())

	def test_dumphex(self):
		writer = XMLWriter(StringIO())
		writer.dumphex("Type is a beautiful group of letters, not a group of beautiful letters.")
		self.assertEquals(HEADER + "\n".join([
		    "54797065 20697320 61206265 61757469",
		    "66756c20 67726f75 70206f66 206c6574",
		    "74657273 2c206e6f 74206120 67726f75",
		    "70206f66 20626561 75746966 756c206c",
		    "65747465 72732e  \n"]), writer.file.getvalue())


if __name__ == '__main__':
    unittest.main()

