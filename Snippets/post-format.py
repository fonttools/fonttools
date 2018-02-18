#! /usr/bin/env python2
#
# Sample script to print post table version
#
# TODO: Extend convert an outfile.{o,t}tf with version 1, 2, 3, 4
# TODO: Extend to print all table versions
#
# To print the versions of all files under the present directory,
# and count them:
#
# $ for font in `find . -name \*.\*tf -print`; do \
#     python ~/post-format.py $font >> post-version.txt; \
#   done;
# $ cat post-version.txt | sort | cut -d\  -f1 | uniq -c ;

import sys
from fontTools.ttLib import TTFont

usage = """usage: post-format.py fontfile.{ot,}tf
output: [version] [fontfile.ttf]"""

fontfile = sys.argv[1]
font = TTFont(fontfile)
print str(font['post'].formatType), fontfile
