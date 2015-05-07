from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import sys
try:
	import MacOS
except ImportError:
	MacOS = None
from .py23 import *

def _reverseString(s):
	s = list(s)
	s.reverse()
	return strjoin(s)


def getMacCreatorAndType(path):
	if MacOS is not None:
		fileCreator, fileType = MacOS.GetCreatorAndType(path)
		if sys.version_info[:2] < (2, 7) and sys.byteorder == "little":
			# work around bug in MacOS.GetCreatorAndType() on intel:
			# http://bugs.python.org/issue1594
			# (fixed with Python 2.7)
			fileCreator = _reverseString(fileCreator)
			fileType = _reverseString(fileType)
		return fileCreator, fileType
	else:
		return None, None


def setMacCreatorAndType(path, fileCreator, fileType):
	if MacOS is not None:
		MacOS.SetCreatorAndType(path, fileCreator, fileType)
