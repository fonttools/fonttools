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
import subprocess
from codepoint_convert import convert_from_gbk

SUPPORT_CONVERT_FROM_ENCODE = ['gb2312', 'gbk']

if len(sys.argv) != 6:
	print("usage: cmap-format.py fontfile.ttf outfile.ttf to_platEncID to_platEncID from_encode")
	sys.exit(1)
fontfile = sys.argv[1]
outfile = sys.argv[2]
to_platformID  = int(sys.argv[3])
to_platEncID = int(sys.argv[4])
from_encode = sys.argv[5]

if from_encode not in SUPPORT_CONVERT_FROM_ENCODE:
    print("Sorry, only support gb2312, gbk codepoint conversion.")
    sys.exit(1)

font = TTFont(fontfile)

cmap = font['cmap']
outtables = []
for table in cmap.tables:
	if table.format in [4, 12, 13, 14]:
		outtables.append(table)

	# Convert ot format4
        if table.getEncoding() in SUPPORT_CONVERT_FROM_ENCODE:
            for gbk_code in table.cmap.keys():
                uni_code= convert_from_gbk(gbk_code)
                if gbk_code != uni_code:
                    table.cmap[uni_code] = table.cmap.pop(gbk_code)
                
            newtable = CmapSubtable.newSubtable(4)
            newtable.platformID = to_platformID
            newtable.platEncID = to_platEncID
            newtable.language = table.language
            newtable.cmap = table.cmap
            outtables.append(newtable)
cmap.tables = outtables

font.save(outfile)
