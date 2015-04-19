"""fontTools.misc.timeTools.py -- tools for working with OpenType encodings.
"""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import fontTools.encodings.codecs

# Map keyed by platformID, then platEncID, then possibly langID
_encodingMap =	{
	0: { # Unicode
		0: 'utf-16be',
		1: 'utf-16be',
		2: 'utf-16be',
		3: 'utf-16be',
		4: 'utf-16be',
		5: 'utf-16be',
		6: 'utf-16be',
	},
	1: { # Macintosh
		# See
		# https://github.com/behdad/fonttools/issues/236
		0: { # Macintosh, platEncID==0, keyed by langID
			15: "mac-iceland",
			17: "mac-turkish",
			18: "x-mac-croatian-ttx",
			24: "mac-latin2",
			25: "mac-latin2",
			26: "mac-latin2",
			27: "mac-latin2",
			28: "mac-latin2",
			36: "mac-latin2",
			37: "x-mac-romanian-ttx",
			38: "mac-latin2",
			39: "mac-latin2",
			40: "mac-latin2",
			Ellipsis: 'mac-roman', # Other
		},
		1: 'x-mac-japanese-ttx',
		2: 'x-mac-chinesetrad-ttx',
		3: 'x-mac-korean-ttx',
		6: 'mac-greek',
		7: 'mac-cyrillic',
		25: 'x-mac-chinesesimp-ttx',
		29: 'mac-latin2',
		35: 'mac-turkish',
		37: 'mac-iceland',
	},
	2: { # ISO
		0: 'ascii',
		1: 'utf-16be',
		2: 'latin1',
	},
	3: { # Microsoft
		0: 'utf-16be',
		1: 'utf-16be',
		2: 'shift-jis',
		3: 'gb2312',
		4: 'big5',
		5: 'wansung',
		6: 'johab',
		10: 'utf-16be',
	},
}

def getEncoding(platformID, platEncID, langID, default=None):
	"""Returns the Python encoding name for OpenType platformID/encodingID/langID
	triplet.  If encoding for these values is not known, by default None is
	returned.  That can be overriden by passing a value to the default argument.
	"""
	encoding = _encodingMap.get(platformID, {}).get(platEncID, default)
	if isinstance(encoding, dict):
		encoding = encoding.get(langID, encoding[Ellipsis])
	return encoding
