#! /usr/bin/env python

"""\
usage: %s TrueType-file(s)
List basic info for each table in one or more TrueType font files."""

import sys, getopt
from fontTools.ttLib import TTFont

def usage():
	print __doc__ % sys.argv[0]
	sys.exit(2)

try:
	options, args = getopt.getopt(sys.argv[1:], "")
except getopt.GetoptError:
	usage()

if not args:
	usage()

for fileName in args:
	ttf = TTFont(fileName)
	reader = ttf.reader
	tags = reader.keys()
	tags.sort()
	print 'Info for "%s":' % fileName
	for tag in tags:
		entry = reader.tables[tag]
		print
		print "       Tag:", `tag`
		print "  Checksum:", hex(entry.checkSum)
		print "    Length:", entry.length
		print "    Offset:", entry.offset
