"""fontTools.misc.timeTools.py -- tools for working with OpenType timestamps.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import time
import calendar


epoch_diff = calendar.timegm((1904, 1, 1, 0, 0, 0, 0, 0, 0))

def timestampToString(value):
	return time.asctime(time.gmtime(max(0, value + epoch_diff)))

def timestampFromString(value):
	return calendar.timegm(time.strptime(value)) - epoch_diff

def timestampNow():
	return int(time.time() - epoch_diff)

def timestampSinceEpoch(value):
	return int(value - epoch_diff)
