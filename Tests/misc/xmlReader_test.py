# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
import os
import unittest
from fontTools.ttLib import TTFont
from fontTools.misc.xmlReader import XMLReader, ProgressPrinter, BUFSIZE
import tempfile


class TestXMLReader(unittest.TestCase):

	def test_decode_utf8(self):

		class DebugXMLReader(XMLReader):

			def __init__(self, fileOrPath, ttFont, progress=None):
				super(DebugXMLReader, self).__init__(
					fileOrPath, ttFont, progress)
				self.contents = []

			def _endElementHandler(self, name):
				if self.stackSize == 3:
					name, attrs, content = self.root
					self.contents.append(content)
				super(DebugXMLReader, self)._endElementHandler(name)

		expected = 'fôôbär'
		data = '''\
<?xml version="1.0" encoding="UTF-8"?>
<ttFont>
  <name>
    <namerecord nameID="1" platformID="3" platEncID="1" langID="0x409">
      %s
    </namerecord>
  </name>
</ttFont>
''' % expected

		with BytesIO(data.encode('utf-8')) as tmp:
			reader = DebugXMLReader(tmp, TTFont())
			reader.read()
		content = strjoin(reader.contents[0]).strip()
		self.assertEqual(expected, content)

	def test_normalise_newlines(self):

		class DebugXMLReader(XMLReader):

			def __init__(self, fileOrPath, ttFont, progress=None):
				super(DebugXMLReader, self).__init__(
					fileOrPath, ttFont, progress)
				self.newlines = []

			def _characterDataHandler(self, data):
				self.newlines.extend([c for c in data if c in ('\r', '\n')])

		# notice how when CR is escaped, it is not normalised by the XML parser
		data = (
			'<ttFont>\r'                                    #        \r -> \n
			'  <test>\r\n'                                  #      \r\n -> \n 
			'    a line of text\n'                          #              \n
			'    escaped CR and unix newline &#13;\n'       #   &#13;\n -> \r\n
			'    escaped CR and macintosh newline &#13;\r'  #   &#13;\r -> \r\n
			'    escaped CR and windows newline &#13;\r\n'  # &#13;\r\n -> \r\n
			'  </test>\n'                                   #              \n
			'</ttFont>')

		with BytesIO(data.encode('utf-8')) as tmp:
			reader = DebugXMLReader(tmp, TTFont())
			reader.read()
		expected = ['\n'] * 3 + ['\r', '\n'] * 3 + ['\n']
		self.assertEqual(expected, reader.newlines)

	def test_progress(self):

		class DummyProgressPrinter(ProgressPrinter):

			def __init__(self, title, maxval=100):
				self.label = title
				self.maxval = maxval
				self.pos = 0

			def set(self, val, maxval=None):
				if maxval is not None:
					self.maxval = maxval
				self.pos = val

			def increment(self, val=1):
				self.pos += val

			def setLabel(self, text):
				self.label = text

		data = (
			'<ttFont>\n'
			'  <test>\n'
			'    %s\n'
			'  </test>\n'
			'</ttFont>\n'
			% ("z" * 2 * BUFSIZE)
			).encode('utf-8')

		dataSize = len(data)
		progressBar = DummyProgressPrinter('test')
		with BytesIO(data) as tmp:
			reader = XMLReader(tmp, TTFont(), progress=progressBar)
			self.assertEqual(progressBar.pos, 0)
			reader.read()
		self.assertEqual(progressBar.pos, dataSize // 100)
		self.assertEqual(progressBar.maxval, dataSize // 100)
		self.assertTrue('test' in progressBar.label)
		with BytesIO(b"<ttFont></ttFont>") as tmp:
			reader = XMLReader(tmp, TTFont(), progress=progressBar)
			reader.read()
		# when data size is less than 100 bytes, 'maxval' is 1
		self.assertEqual(progressBar.maxval, 1)

	def test_close_file_path(self):
		with tempfile.NamedTemporaryFile(delete=False) as tmp:
			tmp.write(b'<ttFont></ttFont>')
		reader = XMLReader(tmp.name, TTFont())
		reader.read()
		# when reading from path, the file is closed automatically at the end
		self.assertTrue(reader.file.closed)
		# this does nothing
		reader.close()
		self.assertTrue(reader.file.closed)
		os.remove(tmp.name)

	def test_close_file_obj(self):
		with tempfile.NamedTemporaryFile(delete=False) as tmp:
			tmp.write(b'<ttFont>"hello"</ttFont>')
		with open(tmp.name, "rb") as f:
			reader = XMLReader(f, TTFont())
			reader.read()
			# when reading from a file or file-like object, the latter is kept open
			self.assertFalse(reader.file.closed)
		# ... until the user explicitly closes it
		reader.close()
		self.assertTrue(reader.file.closed)
		os.remove(tmp.name)

	def test_read_sub_file(self):
		# Verifies that sub-file content is able to be read to a table.
		expectedContent = 'testContent'
		expectedNameID = '1'
		expectedPlatform = '3'
		expectedLangId = '0x409'

		with tempfile.NamedTemporaryFile(delete=False) as tmp:
			subFileData = (
				'<ttFont ttLibVersion="3.15">'
					'<name>'
						'<namerecord nameID="%s" platformID="%s" platEncID="1" langID="%s">'
							'%s'
						'</namerecord>'
					'</name>'
				'</ttFont>'
			) % (expectedNameID, expectedPlatform, expectedLangId, expectedContent)
			tmp.write(subFileData.encode("utf-8"))

		with tempfile.NamedTemporaryFile(delete=False) as tmp2:
			fileData = (
				'<ttFont ttLibVersion="3.15">'
					'<name>'
						'<namerecord src="%s"/>'
					'</name>'
				'</ttFont>'
			) % tmp.name
			tmp2.write(fileData.encode('utf-8'))

		ttf = TTFont()
		with open(tmp2.name, "rb") as f:
			reader = XMLReader(f, ttf)
			reader.read()
			reader.close()
			nameTable = ttf['name']
			self.assertTrue(int(expectedNameID) == nameTable.names[0].nameID)
			self.assertTrue(int(expectedLangId, 16) == nameTable.names[0].langID)
			self.assertTrue(int(expectedPlatform) == nameTable.names[0].platformID)
			self.assertEqual(expectedContent, nameTable.names[0].string.decode(nameTable.names[0].getEncoding()))

		os.remove(tmp.name)
		os.remove(tmp2.name)

if __name__ == '__main__':
	import sys
	sys.exit(unittest.main())
