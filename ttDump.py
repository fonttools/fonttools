#! /usr/bin/env python

"""\
usage: %s [-hvis] [-t <table>] [-x <table>] TrueType-file [TTX-output-file]
    Dump a TrueType font as a TTX file (an XML-based text format). If the 
    TTX-output-file argument is omitted, the out put file name will be 
    constructed from the input file name, like so: *.ttf becomes *.ttx. 
    Either way, existing files will be overwritten without warning!

    Options:
    -h help: print this message
    -v verbose: messages will be written to stdout about what is 
       being done.
    -i disassemble TT instructions: when this option is given, all
       TrueType programs (glyph programs, the font program and the
       pre-program) will be written to the TTX file as assembly instead
       of hex data.
    -s split tables: save the TTX data into separate TTX files per table.
       The files will be saved in a directory. The name of this
       directory will be constructed from the input filename (by
       dropping the extension) or can be specified by the optional
       TTX-output-file argument.
    -t <table> specify a table to dump. Multiple -t options
       are allowed. When no -t option is specified, all tables
       will be dumped
    -x <table> specify a table to exclude from the dump. Multiple
       -x options are allowed. -t and -x are mutually exclusive.
"""

import sys, os, getopt
from fontTools import ttLib

options, args = getopt.getopt(sys.argv[1:], "hvist:x:")

verbose = 0
splitTables = 0
disassembleInstructions = 0
tables = []
skipTables = []
for option, value in options:
	if option == "-t":
		if len(value) > 4:
			print "illegal table tag: " + value
			sys.exit(2)
		# normalize tag
		value = value + (4 - len(value)) * " "
		tables.append(value)
	elif option == "-x":
		if len(value) > 4:
			print "illegal table tag: " + value
			sys.exit(2)
		# normalize tag
		value = value + (4 - len(value)) * " "
		skipTables.append(value)
	elif option == "-v":
		verbose = 1
	elif option == "-h":
		print __doc__ % sys.argv[0]
		sys.exit(0)
	elif option == "-s":
		splitTables = 1
	elif option == "-i":
		disassembleInstructions = 1

if tables and skipTables:
	print "-t and -x options are mutually exlusive"
	sys.exit(2)

if len(args) == 1:
	ttPath = args[0]
	path, ext = os.path.splitext(ttPath)
	if splitTables:
		xmlPath = path
	else:
		xmlPath = path + '.ttx'
elif len(args) == 2:
	ttPath, xmlPath = args
else:
	print __doc__ % sys.argv[0]
	sys.exit(2)

tt = ttLib.TTFont(ttPath, 0, verbose=verbose)
tt.saveXML(xmlPath, tables=tables, skipTables=skipTables, 
		splitTables=splitTables, disassembleInstructions=disassembleInstructions)

