#! /usr/bin/env python

"""\
usage: %s [-hvb] [-i TrueType-input-file] XML-file [TrueType-output-file]
    Translate an XML file (as output by tt2xml.py) to a TrueType font file. 
    If the XML-file argument is a directory instead of a file, all files 
    ending in '.xml' will be merged into one TrueType file. This is mostly 
    useful in conjunction with the -s option of tt2xml.py.

    Options:
    -i TrueType-input-file: specify a TT file to be merged with the XML file(s)
    -v verbose: messages will be written to stdout about what is being done
    -b Don't recalc glyph boundig boxes: use the values in the XML file as-is.
    -h help: print this message
"""
import sys, os, getopt
from fontTools import ttLib

options, args = getopt.getopt(sys.argv[1:], "hvi:b")

verbose = 0
ttInFile = None
recalcBBoxes = 1
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

if len(args) == 1:
	xmlPath = args[0]
	name, ext = os.path.splitext(xmlPath)
	ttPath = name + '.ttf'
elif len(args) == 2:
	xmlPath, ttPath = args
else:
	print __doc__ % sys.argv[0]
	sys.exit(2)

tt = ttLib.TTFont(ttInFile, recalcBBoxes=recalcBBoxes, verbose=verbose)

if os.path.isdir(xmlPath):
	import glob
	oldDir = os.getcwd()
	os.chdir(xmlPath)
	files = glob.glob("*.xml")
	os.chdir(oldDir)
	for xmlFile in files:
		xmlFile = os.path.join(xmlPath, xmlFile)
		tt.importXML(xmlFile)
else:
	tt.importXML(xmlPath)
tt.save(ttPath)
del tt
if verbose:
	import time
	print "%s finished at" % sys.argv[0], time.strftime("%H:%M:%S", time.localtime(time.time()))
