#! /usr/bin/env python

"""\
usage: ttx [options] inputfile1 [... inputfileN]

    TTX %s -- From OpenType To XML And Back

    If an input file is a TrueType or OpenType font file, it will be
       dumped to an TTX file (an XML-based text format).
    If an input file is a TTX file, it will be compiled to a TrueType
       or OpenType font file.

    Output files are created so they are unique: an existing file is
       never overwrritten.

    General options:
    -h Help: print this message
    -d <outputfolder> Specify a directory where the output files are
       to be created.
    -v Verbose: more messages will be written to stdout about what
       is being done.
    -a allow virtual glyphs ID's on compile or decompile.

    Dump options:
    -l List table info: instead of dumping to a TTX file, list some
       minimal info about each table.
    -t <table> Specify a table to dump. Multiple -t options
       are allowed. When no -t option is specified, all tables
       will be dumped.
    -x <table> Specify a table to exclude from the dump. Multiple
       -x options are allowed. -t and -x are mutually exclusive.
    -s Split tables: save the TTX data into separate TTX files per
       table and write one small TTX file that contains references
       to the individual table dumps. This file can be used as
       input to ttx, as long as the table files are in the
       same directory.
    -i Do NOT disassemble TT instructions: when this option is given,
       all TrueType programs (glyph programs, the font program and the
       pre-program) will be written to the TTX file as hex data
       instead of assembly. This saves some time and makes the TTX
       file smaller.
    -e Don't ignore decompilation errors, but show a full traceback
       and abort.
    -y <number> Select font number for TrueType Collection,
       starting from 0.

    Compile options:
    -m Merge with TrueType-input-file: specify a TrueType or OpenType
       font file to be merged with the TTX file. This option is only
       valid when at most one TTX file is specified.
    -b Don't recalc glyph boundig boxes: use the values in the TTX
       file as-is.
"""


import sys
import os
import getopt
import re
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.otBase import OTLOffsetOverflowError
from fontTools.ttLib.tables.otTables import fixLookupOverFlows, fixSubTableOverFlows
from fontTools.misc.macCreatorType import getMacCreatorAndType
from fontTools import version

def usage():
	print __doc__ % version
	sys.exit(2)

	
numberAddedRE = re.compile("(.*)#\d+$")

def makeOutputFileName(input, outputDir, extension):
	dir, file = os.path.split(input)
	file, ext = os.path.splitext(file)
	if outputDir:
		dir = outputDir
	output = os.path.join(dir, file + extension)
	m = numberAddedRE.match(file)
	if m:
		file = m.group(1)
	n = 1
	while os.path.exists(output):
		output = os.path.join(dir, file + "#" + repr(n) + extension)
		n = n + 1
	return output


class Options:

	listTables = 0
	outputDir = None
	verbose = 0
	splitTables = 0
	disassembleInstructions = 1
	mergeFile = None
	recalcBBoxes = 1
	allowVID = 0
	ignoreDecompileErrors = True

	def __init__(self, rawOptions, numFiles):
		self.onlyTables = []
		self.skipTables = []
		self.fontNumber = -1
		for option, value in rawOptions:
			# general options
			if option == "-h":
				print __doc__ % version
				sys.exit(0)
			elif option == "-d":
				if not os.path.isdir(value):
					print "The -d option value must be an existing directory"
					sys.exit(2)
				self.outputDir = value
			elif option == "-v":
				self.verbose = 1
			# dump options
			elif option == "-l":
				self.listTables = 1
			elif option == "-t":
				self.onlyTables.append(value)
			elif option == "-x":
				self.skipTables.append(value)
			elif option == "-s":
				self.splitTables = 1
			elif option == "-i":
				self.disassembleInstructions = 0
			elif option == "-y":
				self.fontNumber = int(value)
			# compile options
			elif option == "-m":
				self.mergeFile = value
			elif option == "-b":
				self.recalcBBoxes = 0
			elif option == "-a":
				self.allowVID = 1
			elif option == "-e":
				self.ignoreDecompileErrors = False
		if self.onlyTables and self.skipTables:
			print "-t and -x options are mutually exclusive"
			sys.exit(2)
		if self.mergeFile and numFiles > 1:
			print "Must specify exactly one TTX source file when using -m"
			sys.exit(2)


def ttList(input, output, options):
	import string
	ttf = TTFont(input, fontNumber=options.fontNumber)
	reader = ttf.reader
	tags = reader.keys()
	tags.sort()
	print 'Listing table info for "%s":' % input
	format = "    %4s  %10s  %7s  %7s"
	print format % ("tag ", "  checksum", " length", " offset")
	print format % ("----", "----------", "-------", "-------")
	for tag in tags:
		entry = reader.tables[tag]
		checkSum = long(entry.checkSum)
		if checkSum < 0:
			checkSum = checkSum + 0x100000000L
		checksum = "0x" + string.zfill(hex(checkSum)[2:-1], 8)
		print format % (tag, checksum, entry.length, entry.offset)
	print
	ttf.close()


def ttDump(input, output, options):
	print 'Dumping "%s" to "%s"...' % (input, output)
	ttf = TTFont(input, 0, verbose=options.verbose, allowVID=options.allowVID,
			ignoreDecompileErrors=options.ignoreDecompileErrors,
			fontNumber=options.fontNumber)
	ttf.saveXML(output,
			tables=options.onlyTables,
			skipTables=options.skipTables, 
			splitTables=options.splitTables,
			disassembleInstructions=options.disassembleInstructions)
	ttf.close()


def ttCompile(input, output, options):
	print 'Compiling "%s" to "%s"...' % (input, output)
	ttf = TTFont(options.mergeFile,
			recalcBBoxes=options.recalcBBoxes,
			verbose=options.verbose, allowVID=options.allowVID)
	ttf.importXML(input)
	try:
		ttf.save(output)
	except OTLOffsetOverflowError, e:
		# XXX This shouldn't be here at all, it should be as close to the
		# OTL code as possible.
		overflowRecord = e.value
		print "Attempting to fix OTLOffsetOverflowError", e
		lastItem = overflowRecord 
		while 1:
			ok = 0
			if overflowRecord.itemName == None:
				ok = fixLookupOverFlows(ttf, overflowRecord)
			else:
				ok = fixSubTableOverFlows(ttf, overflowRecord)
			if not ok:
				raise

			try:
				ttf.save(output)
				break
			except OTLOffsetOverflowError, e:
				print "Attempting to fix OTLOffsetOverflowError", e
				overflowRecord = e.value
				if overflowRecord == lastItem:
					raise

	if options.verbose:
		import time
		print "finished at", time.strftime("%H:%M:%S", time.localtime(time.time()))


def guessFileType(fileName):
	base, ext = os.path.splitext(fileName)
	try:
		f = open(fileName, "rb")
	except IOError:
		return None
	cr, tp = getMacCreatorAndType(fileName)
	if tp in ("sfnt", "FFIL"):
		return "TTF"
	if ext == ".dfont":
		return "TTF"
	header = f.read(256)
	head = header[:4]
	if head == "OTTO":
		return "OTF"
	elif head == "ttcf":
		return "TTC"
	elif head in ("\0\1\0\0", "true"):
		return "TTF"
	elif head.lower() == "<?xm":
		if header.find('sfntVersion="OTTO"') > 0:
			return "OTX"
		else:
			return "TTX"
	return None


def parseOptions(args):
	try:
		rawOptions, files = getopt.getopt(args, "ld:vht:x:sim:baey:")
	except getopt.GetoptError:
		usage()
	
	if not files:
		usage()
	
	options = Options(rawOptions, len(files))
	jobs = []
	
	for input in files:
		tp = guessFileType(input)
		if tp in ("OTF", "TTF", "TTC"):
			extension = ".ttx"
			if options.listTables:
				action = ttList
			else:
				action = ttDump
		elif tp == "TTX":
			extension = ".ttf"
			action = ttCompile
		elif tp == "OTX":
			extension = ".otf"
			action = ttCompile
		else:
			print 'Unknown file type: "%s"' % input
			continue
		
		output = makeOutputFileName(input, options.outputDir, extension)
		jobs.append((action, input, output))
	return jobs, options


def process(jobs, options):
	for action, input, output in jobs:
		action(input, output, options)


def waitForKeyPress():
	"""Force the DOS Prompt window to stay open so the user gets
	a chance to see what's wrong."""
	import msvcrt
	print '(Hit any key to exit)'
	while not msvcrt.kbhit():
		pass


def main(args):
	jobs, options = parseOptions(args)
	try:
		process(jobs, options)
	except KeyboardInterrupt:
		print "(Cancelled.)"
	except SystemExit:
		if sys.platform == "win32":
			waitForKeyPress()
		else:
			raise
	except:
		if sys.platform == "win32":
			import traceback
			traceback.print_exc()
			waitForKeyPress()
		else:
			raise
	

if __name__ == "__main__":
	main(sys.argv[1:])
