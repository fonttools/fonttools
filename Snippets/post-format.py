#! /usr/bin/env python
#
# Sample script to print post table version, based on cmap-format.py
#
# TODO: Extend convert an outfile.{o,t}tf with version 1, 2, 3, 4
#
# To print the versions of all files under the present directory,
# and count them:
#
# $ for font in `find . -name \*.\*tf -print`; do \
#     python ~/post-format.py $font >> post-version.txt; \
#   done;
# $ cat post-version.txt | sort | cut -d\  -f1 | uniq -c ;

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._p_o_s_t import DefaultTable
import sys

usage = """usage: post-format.py fontfile.{ot,}tf
output: [version] [fontfile.ttf]"""

if len(sys.argv) != 2:
	print(usage)
	sys.exit(1)
fontfile = sys.argv[1]
font = TTFont(fontfile)

post = font['post']

if post.formatType in [1.0, 2.0, 3.0]:
    print(str(post.formatType), fontfile) 
