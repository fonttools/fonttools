# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
import os
import unittest
from fontTools.ttLib import TTFont
from .xmlReader import XMLReader
import tempfile


class TestXMLReader(unittest.TestCase):

	def test_decode_utf8(self):

		class DebugXMLReader(XMLReader):

			def __init__(self, fileName, ttFont, progress=None, quiet=False):
				super(DebugXMLReader, self).__init__(
					fileName, ttFont, progress, quiet)
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

		with tempfile.NamedTemporaryFile(delete=False) as tmp:
			tmp.write(data.encode('utf-8'))
		reader = DebugXMLReader(tmp.name, TTFont(), quiet=True)
		reader.read()
		os.remove(tmp.name)
		content = strjoin(reader.contents[0]).strip() 
		self.assertEqual(expected, content)

	def test_normalise_newlines(self):

		class DebugXMLReader(XMLReader):

			def __init__(self, fileName, ttFont, progress=None, quiet=False):
				super(DebugXMLReader, self).__init__(
					fileName, ttFont, progress, quiet)
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
		with tempfile.NamedTemporaryFile(delete=False) as tmp:
			tmp.write(data.encode('utf-8'))
		reader = DebugXMLReader(tmp.name, TTFont(), quiet=True)
		reader.read()
		os.remove(tmp.name)
		expected = ['\n'] * 3 + ['\r', '\n'] * 3 + ['\n']
		self.assertEqual(expected, reader.newlines)


if __name__ == '__main__':
	unittest.main()
