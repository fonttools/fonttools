#! /usr/bin/env python

"""\
usage: %s [-h] [-v] [-s] [-t <table>] TrueType-file [XML-output-file]
    Dump a TrueType font as an XML file. If the XML-output-file argument
    is omitted, the out put file name will be constructed from the input
    file name, like so: *.ttf becomes *.xml. Either way, existing files
    will be overwritten without warning!

    Options:
    -t <table> specify a table to dump. Multiple -t options
       are allowed. When no -t option is specified, all tables
       will be dumped
    -v verbose: messages will be written to stdout about what is 
       being done.
    -s split tables: save the XML in a separate XML file per table. 
       The names of these files will be constructed from the 
       XML-output-file name as follows: *.xml becomes *.<tag>.xml
    -h help: print this message
"""

import sys, os, getopt
from fontTools import ttLib

options, args = getopt.getopt(sys.argv[1:], "shvt:")

verbose = 0
splitTables = 0
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
	elif option == "-s":
		splitTables = 1


if len(args) == 1:
	ttPath = args[0]
	name, ext = os.path.splitext(ttPath)
	xmlPath = name + '.xml'
elif len(args) == 2:
	ttPath, xmlPath = args
else:
	print __doc__ % sys.argv[0]
	sys.exit(2)

tt = ttLib.TTFont(ttPath, verbose=verbose)
tt.saveXML(xmlPath, tables=tables, splitTables=splitTables)
