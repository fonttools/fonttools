#! /usr/bin/env python

"""\
usage: %s [-h] [-v] [-i TrueType-input-file] XML-file [TrueType-file]
    -i TrueType-input-file: specify a TT file to be merged with the XML file
    -v verbose: messages will be written to stdout about what is being done
    -h help: print this message
"""
import sys, os, getopt
from fontTools import ttLib

options, args = getopt.getopt(sys.argv[1:], "hvi:")

verbose = 0
tt_infile = None
for option, value in options:
	if option == "-i":
		tt_infile = value
	elif option == "-v":
		verbose = 1
	elif option == "-h":
		print __doc__ % sys.argv[0]
		sys.exit(0)


if len(args) == 1:
	xmlpath = args[0]
	name, ext = os.path.splitext(xmlpath)
	ttpath = name + '.ttf'
elif len(args) == 2:
	xmlpath, ttpath = args
else:
	print __doc__ % sys.argv[0]
	sys.exit(2)

tt = ttLib.TTFont(tt_infile, verbose=verbose)
tt.importXML(xmlpath)
tt.save(ttpath)
