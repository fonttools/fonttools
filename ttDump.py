#! /usr/bin/env python

"""\
usage: %s [-hvisf] [-t <table>] [-x <table>] [-d <output-dir>] TrueType-file(s) 

    Dump TrueType fonts as TTX files (an XML-based text format).

    Options:
    -h Help: print this message
    -v Verbose: messages will be written to stdout about what is 
       being done.
    -i Disassemble TT instructions: when this option is given, all
       TrueType programs (glyph programs, the font program and the
       pre-program) will be written to the TTX file as assembly instead
       of hex data.
    -s Split tables: save the TTX data into separate TTX files per table.
       The files will be saved in a directory. The name of this
       directory will be constructed from the input filename (by
       dropping the extension) or can be specified by the optional
       TTX-output-file argument. This option implies -f.
    -f Force overwriting existing files.
    -d <output-dir> Specify a directory in which the output file(s)
       should end up. The directory must exist.
    -t <table> Specify a table to dump. Multiple -t options
       are allowed. When no -t option is specified, all tables
       will be dumped.
    -x <table> Specify a table to exclude from the dump. Multiple
       -x options are allowed. -t and -x are mutually exclusive.
"""

import sys, os, getopt
from fontTools import ttLib

def usage():
	print __doc__ % sys.argv[0]
	sys.exit(2)

try:
	options, args = getopt.getopt(sys.argv[1:], "hvisft:x:d:")
except getopt.GetoptError:
	usage()

# default values
verbose = 0
splitTables = 0
disassembleInstructions = 0
forceOverwrite = 0
tables = []
skipTables = []
outputDir = None

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
	elif option == "-d":
		outputDir = value
	elif option == "-v":
		verbose = 1
	elif option == "-f":
		forceOverwrite = 1
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

if not args:
	usage()

for ttPath in args:
	path, ext = os.path.splitext(ttPath)
	if outputDir is not None:
		fileName = os.path.basename(path)
		path = os.path.join(outputDir, fileName)
	
	if splitTables:
		xmlPath = path
	else:
		xmlPath = path + ".ttx"
		if not forceOverwrite and os.path.exists(xmlPath):
			answer = raw_input('Overwrite "%s"? ' % xmlPath)
			if not answer[:1] in ("Y", "y"):
				print "skipped."
				continue
	print 'Dumping "%s" to "%s"...' % (ttPath, xmlPath)
	tt = ttLib.TTFont(ttPath, 0, verbose=verbose)
	tt.saveXML(xmlPath, tables=tables, skipTables=skipTables, 
		splitTables=splitTables, disassembleInstructions=disassembleInstructions)

