"""fontTools.misc.timeTools.py -- miscellaneous routines."""


from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import time
import calendar


# OpenType timestamp handling

epoch_diff = calendar.timegm((1904, 1, 1, 0, 0, 0, 0, 0, 0))

def timestampToString(value):
	# https://github.com/behdad/fonttools/issues/99#issuecomment-66776810
	try:
		value = time.asctime(time.gmtime(max(0, value + epoch_diff)))
	except (OverflowError, ValueError):
		value = time.asctime(time.gmtime(0))

def timestampFromString(value):
	return calendar.timegm(time.strptime(value)) - epoch_diff

def timestampNow():
	return int(time.time() - epoch_diff)
