from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import sys
try:
	import xattr
except ImportError:
	xattr = None
try:
	import MacOS
except ImportError:
	MacOS = None


def _reverseString(s):
	s = list(s)
	s.reverse()
	return strjoin(s)


def getMacCreatorAndType(path):
	if xattr is not None:
		try:
			finderInfo = xattr.getxattr(path, 'com.apple.FinderInfo')
		except (KeyError, IOError):
			pass
		else:
			fileType = Tag(finderInfo[:4])
			fileCreator = Tag(finderInfo[4:8])
			return fileCreator, fileType
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
	if xattr is not None:
		from fontTools.misc.textTools import pad
		if not all(len(s) == 4 for s in (fileCreator, fileType)):
			raise TypeError('arg must be string of 4 chars')
		finderInfo = pad(bytesjoin([fileType, fileCreator]), 32)
		xattr.setxattr(path, 'com.apple.FinderInfo', finderInfo)
	if MacOS is not None:
		MacOS.SetCreatorAndType(path, fileCreator, fileType)
