#! /usr/bin/env python

"""\
usage: %s [-h] [-v] [-t <table>] TrueType-file [XML-output-file]
    -t <table> specify a table to dump. Multiple -t options
       are allowed. When no -t option is specified, all tables
       will be dumped
    -v verbose: messages will be written to stdout about what is being done
    -h help: print this message
"""

import sys, os, getopt
from fontTools import ttLib

options, args = getopt.getopt(sys.argv[1:], "hvt:")

verbose = 0
tables = []
for option, value in options:
	if option == "-t":
		if len(value) > 4:
			print "illegal table tag: " + value
			sys.exit(2)
		# normalize tag
		value = value + (4 - len(value)) * " "
		tables.append(value)
	elif option == "-v":
		verbose = 1
	elif option == "-h":
		print __doc__ % sys.argv[0]
		sys.exit(0)


if len(args) == 1:
	ttpath = args[0]
	name, ext = os.path.splitext(ttpath)
	xmlpath = name + '.xml'
elif len(args) == 2:
	ttpath, xmlpath = args
else:
	print __doc__ % sys.argv[0]
	sys.exit(2)

tt = ttLib.TTFont(ttpath, verbose=verbose)
tt.saveXML(xmlpath, tables=tables)
