#! /usr/bin/env python

# Sample script to convert legacy cmap subtables to format-4
# subtables.  Note that this is rarely what one needs.  You
# probably need to just drop the legacy subtables if the font
# already has a format-4 subtable.
#
# Other times, you would need to convert a non-Unicode cmap
# legacy subtable to a Unicode one.  In those cases, use the
# getEncoding() of subtable and use that encoding to map the
# characters to Unicode...  TODO: Extend this script to do that.

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
import sys

if len(sys.argv) != 3:
	print("usage: cmap-format.py fontfile.ttf outfile.ttf")
	sys.exit(1)
fontfile = sys.argv[1]
outfile = sys.argv[2]
font = TTFont(fontfile)

cmap = font['cmap']
outtables = []
for table in cmap.tables:
	if table.format in [4, 12, 13, 14]:
		outtables.append(table)
	# Convert ot format4
	newtable = CmapSubtable.newSubtable(4)
	newtable.platformID = table.platformID
	newtable.platEncID = table.platEncID
	newtable.language = table.language
	newtable.cmap = table.cmap
	outtables.append(newtable)
cmap.tables = outtables

font.save(outfile)
