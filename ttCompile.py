#! /usr/bin/env python

"""\
usage: %s [-hvbf] [-d output-dir] [-i TTF-input-file] [TTX-file...]

    Translate a TTX file (as output by ttDump) to a TrueType font file. 
    If a TTX-file argument is a directory instead of a file, all files in
    that directory ending in '.ttx' will be merged into one TrueType file. 
    This is mostly useful in conjunction with the -s option of ttDump.py.

    Options:
    -h Help: print this message
    -i TrueType-input-file: specify a TT file to be merged with the TTX file.
       This option is only valid when at most one TTX file (or directory
       containing separated TTX files) is specified.
    -b Don't recalc glyph boundig boxes: use the values in the TTX file as-is.
    -d <output-dir> Specify a directory in which the output file(s)
       should end up. The directory must exist.
    -f Force overwriting existing files.
    -v Verbose: messages will be written to stdout about what is being done
"""

import sys, os, getopt
from fontTools import ttLib

options, args = getopt.getopt(sys.argv[1:], "hvbfd:i:")

# default values
verbose = 0
ttInFile = None
recalcBBoxes = 1
forceOverwrite = 0
outputDir = None

for option, value in options:
	if option == "-i":
		ttInFile = value
	elif option == "-v":
		verbose = 1
	elif option == "-h":
		print __doc__ % sys.argv[0]
		sys.exit(0)
	elif option == "-b":
		recalcBBoxes = 0
	elif option == "-d":
		outputDir = value
	elif option == "-f":
		forceOverwrite = 1

if not args:
	print __doc__ % sys.argv[0]
	sys.exit(2)

if ttInFile and len(args) > 1:
	print "Must specify exactly one TTX file (or directory) when using -i"
	sys.exit(2)


for xmlPath in args:
	path, ext = os.path.splitext(xmlPath)
	if outputDir is not None:
		fileName = os.path.basename(path)
		path = os.path.join(outputDir, fileName)
	ttPath = path + '.ttf'
	
	if not forceOverwrite and os.path.exists(ttPath):
		answer = raw_input('Overwrite "%s"? ' % ttPath)
		if not answer[:1] in ("Y", "y"):
			print "skipped."
			continue
	
	tt = ttLib.TTFont(ttInFile, recalcBBoxes=recalcBBoxes, verbose=verbose)

	if os.path.isdir(xmlPath):
		import glob
		files = glob.glob1(xmlPath, "*.ttx")
		for xmlFile in files:
			xmlFile = os.path.join(xmlPath, xmlFile)
			tt.importXML(xmlFile)
	else:
		tt.importXML(xmlPath)

	tt.save(ttPath)

	if verbose:
		import time
		print "%s finished at" % sys.argv[0], time.strftime("%H:%M:%S", time.localtime(time.time()))
