#! /usr/bin/env python
from myfonttools import MyFontTools
import sys

CMAP_ERROR_1 = 1
CMAP_ERROR_2 = 2
VHEA_ERROR = 3

SUPPORT_FIXED_METHOD = [(CMAP_ERROR_1, 'ERROR: cmap: misaligned table'),
                        (CMAP_ERROR_2, 'ERROR: cmap: no supported subtables were found'),
                        (VHEA_ERROR, 'ERROR: vhea: Bad vhea version 10001')]

if len(sys.argv) != 4:
    print("usage: fixfont.py fontfile.ttf outfile.ttf error_type")
    sys.exit(1)

fontfile = sys.argv[1]
outfile = sys.argv[2]
error_type  = int(sys.argv[3])

myfonttools = MyFontTools(fontfile)

if error_type in [CMAP_ERROR_1, CMAP_ERROR_2]:
    myfonttools.to_platformID = 3
    myfonttools.to_platEncID = 1
    myfonttools.cmap_format_gbk2utf8()
elif error_type in [VHEA_ERROR]:
    myfonttools.vhea_fixed()

myfonttools.save(outfile)