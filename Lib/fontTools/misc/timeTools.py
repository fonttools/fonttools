"""fontTools.misc.timeTools.py -- tools for working with OpenType timestamps.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import os
import time
import calendar


epoch_diff = calendar.timegm((1904, 1, 1, 0, 0, 0, 0, 0, 0))

DAYNAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHNAMES = [None, "Jan", "Feb", "Mar", "Apr", "May", "Jun",
			  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def asctime(t=None):
	"""
	Convert a tuple or struct_time representing a time as returned by gmtime()
	or localtime() to a 24-character string of the following form:

	>>> asctime(time.gmtime(0))
	'Thu Jan  1 00:00:00 1970'

	If t is not provided, the current time as returned by localtime() is used.
	Locale information is not used by asctime().

	This is meant to normalise the output of the built-in time.asctime() across
	different platforms and Python versions.
	In Python 3.x, the day of the month is right-justified, whereas on Windows
	Python 2.7 it is padded with zeros.

	See https://github.com/behdad/fonttools/issues/455
	"""
	if t is None:
		t = time.localtime()
	s = "%s %s %2s %s" % (
		DAYNAMES[t.tm_wday], MONTHNAMES[t.tm_mon], t.tm_mday,
		time.strftime("%H:%M:%S %Y", t))
	return s


def timestampToString(value):
	return asctime(time.gmtime(max(0, value + epoch_diff)))

def timestampFromString(value):
	return calendar.timegm(time.strptime(value)) - epoch_diff

def timestampNow():
	# https://reproducible-builds.org/specs/source-date-epoch/
	source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
	if source_date_epoch is not None:
		return int(source_date_epoch) - epoch_diff
	return int(time.time() - epoch_diff)

def timestampSinceEpoch(value):
	return int(value - epoch_diff)


if __name__ == "__main__":
	import sys
	import doctest
	sys.exit(doctest.testmod().failed)
