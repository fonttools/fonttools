"""
A py23 shim to plistlib. Reimplements plistlib under py2 naming.
"""
from __future__ import absolute_import
import sys
try:
	from plistlib import (
		load as readPlist, dump as writePlist,
		loads as readPlistFromString, dumps as writePlistToString)
	from plistlib import _PlistParser, _PlistWriter
	# Public API changed in Python 3.4
	if sys.version_info >= (3, 4):
		class PlistWriter(_PlistWriter):

			def __init__(self, *args, **kwargs):
				if "indentLevel" in kwargs:
					kwargs["indent_level"] = kwargs["indentLevel"]
					del kwargs["indentLevel"]
				super().__init__(*args, **kwargs)

			def writeValue(self, *args, **kwargs):
				super().write_value(*args, **kwargs)

			def writeData(self, *args, **kwargs):
				super().write_data(*args, **kwargs)

			def writeDict(self, *args, **kwargs):
				super().write_dict(*args, **kwargs)

			def writeArray(self, *args, **kwargs):
				super().write_array(*args, **kwargs)

		class PlistParser(_PlistParser):

			def __init__(self):
				super().__init__(use_builtin_types=True, dict_type=dict)

			def parseElement(self, *args, **kwargs):
				super().parse_element(*args, **kwargs)

			def handleBeginElement(self, *args, **kwargs):
				super().handle_begin_element(*args, **kwargs)

			def handleData(self, *args, **kwargs):
				super().handle_data(*args, **kwargs)

			def handleEndElement(self, *args, **kwargs):
				super().handle_end_element(*args, **kwargs)
	else:
		PlistWriter = _PlistWriter
		PlistParser = _PlistParser
except ImportError:
	from plistlib import readPlist, writePlist, readPlistFromString, writePlistToString
	from plistlib import PlistParser, PlistWriter
