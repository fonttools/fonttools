"""\
usage: ttx [options] inputfile1 [... inputfileN]

    TTX %s -- From OpenType To XML And Back

    If an input file is a TrueType or OpenType font file, it will be
       dumped to an TTX file (an XML-based text format).
    If an input file is a TTX file, it will be compiled to a TrueType
       or OpenType font file.

    Output files are created so they are unique: an existing file is
       never overwritten.

    General options:
    -h Help: print this message
    -d <outputfolder> Specify a directory where the output files are
       to be created.
    -o <outputfile> Specify a file to write the output to.
    -v Verbose: more messages will be written to stdout about what
       is being done.
    -q Quiet: No messages will be written to stdout about what
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
    -z <format> Specify a bitmap data export option for EBDT:
       {'raw', 'row', 'bitwise', 'extfile'} or for the CBDT:
       {'raw', 'extfile'} Each option does one of the following:
         -z raw
            * export the bitmap data as a hex dump
         -z row
            * export each row as hex data
         -z bitwise
            * export each row as binary in an ASCII art style
         -z extfile
            * export the data as external files with XML refences
       If no export format is specified 'raw' format is used.
    -e Don't ignore decompilation errors, but show a full traceback
       and abort.
    -y <number> Select font number for TrueType Collection,
       starting from 0.

    Compile options:
    -m Merge with TrueType-input-file: specify a TrueType or OpenType
       font file to be merged with the TTX file. This option is only
       valid when at most one TTX file is specified.
    -b Don't recalc glyph bounding boxes: use the values in the TTX
       file as-is.
"""


from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont, TTLibError
from fontTools.misc.macCreatorType import getMacCreatorAndType
import os
import sys
import getopt
import re

def usage():
	from fontTools import version
	print(__doc__ % version)
	sys.exit(2)

	
numberAddedRE = re.compile("#\d+$")
opentypeheaderRE = re.compile('''sfntVersion=['"]OTTO["']''')

def makeOutputFileName(input, outputDir, extension):
	dirName, fileName = os.path.split(input)
	fileName, ext = os.path.splitext(fileName)
	if outputDir:
		dirName = outputDir
	fileName = numberAddedRE.split(fileName)[0]
	output = os.path.join(dirName, fileName + extension)
	n = 1
	while os.path.exists(output):
		output = os.path.join(dirName, fileName + "#" + repr(n) + extension)
		n = n + 1
	return output


class Options(object):

	listTables = False
	outputDir = None
	outputFile = None
	verbose = False
	quiet = False
	splitTables = False
	disassembleInstructions = True
	mergeFile = None
	recalcBBoxes = True
	allowVID = False
	ignoreDecompileErrors = True
	bitmapGlyphDataFormat = 'raw'

	def __init__(self, rawOptions, numFiles):
		self.onlyTables = []
		self.skipTables = []
		self.fontNumber = -1
		for option, value in rawOptions:
			# general options
			if option == "-h":
				from fontTools import version
				print(__doc__ % version)
				sys.exit(0)
			elif option == "-d":
				if not os.path.isdir(value):
					print("The -d option value must be an existing directory")
					sys.exit(2)
				self.outputDir = value
			elif option == "-o":
				self.outputFile = value
			elif option == "-v":
				self.verbose = True
			elif option == "-q":
				self.quiet = True
			# dump options
			elif option == "-l":
				self.listTables = True
			elif option == "-t":
				self.onlyTables.append(value)
			elif option == "-x":
				self.skipTables.append(value)
			elif option == "-s":
				self.splitTables = True
			elif option == "-i":
				self.disassembleInstructions = False
			elif option == "-z":
				validOptions = ('raw', 'row', 'bitwise', 'extfile')
				if value not in validOptions:
					print("-z does not allow %s as a format. Use %s" % (option, validOptions))
					sys.exit(2)
				self.bitmapGlyphDataFormat = value
			elif option == "-y":
				self.fontNumber = int(value)
			# compile options
			elif option == "-m":
				self.mergeFile = value
			elif option == "-b":
				self.recalcBBoxes = False
			elif option == "-a":
				self.allowVID = True
			elif option == "-e":
				self.ignoreDecompileErrors = False
		if self.onlyTables and self.skipTables:
			print("-t and -x options are mutually exclusive")
			sys.exit(2)
		if self.mergeFile and numFiles > 1:
			print("Must specify exactly one TTX source file when using -m")
			sys.exit(2)


def ttList(input, output, options):
	ttf = TTFont(input, fontNumber=options.fontNumber, lazy=True)
	reader = ttf.reader
	tags = sorted(reader.keys())
	print('Listing table info for "%s":' % input)
	format = "    %4s  %10s  %7s  %7s"
	print(format % ("tag ", "  checksum", " length", " offset"))
	print(format % ("----", "----------", "-------", "-------"))
	for tag in tags:
		entry = reader.tables[tag]
		checkSum = int(entry.checkSum)
		if checkSum < 0:
			checkSum = checkSum + 0x100000000
		checksum = "0x%08X" % checkSum
		print(format % (tag, checksum, entry.length, entry.offset))
	print()
	ttf.close()


def ttDump(input, output, options):
	if not options.quiet:
		print('Dumping "%s" to "%s"...' % (input, output))
	ttf = TTFont(input, 0, verbose=options.verbose, allowVID=options.allowVID,
			quiet=options.quiet,
			ignoreDecompileErrors=options.ignoreDecompileErrors,
			fontNumber=options.fontNumber)
	ttf.saveXML(output,
			quiet=options.quiet,
			tables=options.onlyTables,
			skipTables=options.skipTables,
			splitTables=options.splitTables,
			disassembleInstructions=options.disassembleInstructions,
			bitmapGlyphDataFormat=options.bitmapGlyphDataFormat)
	ttf.close()


def ttCompile(input, output, options):
	if not options.quiet:
		print('Compiling "%s" to "%s"...' % (input, output))
	ttf = TTFont(options.mergeFile,
			recalcBBoxes=options.recalcBBoxes,
			verbose=options.verbose, allowVID=options.allowVID)
	ttf.importXML(input, quiet=options.quiet)
	ttf.save(output)

	if options.verbose:
		import time
		print("finished at", time.strftime("%H:%M:%S", time.localtime(time.time())))


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
	head = Tag(header[:4])
	if head == "OTTO":
		return "OTF"
	elif head == "ttcf":
		return "TTC"
	elif head in ("\0\1\0\0", "true"):
		return "TTF"
	elif head == "wOFF":
		return "WOFF"
	elif head.lower() == "<?xm":
		# Use 'latin1' because that can't fail.
		header = tostr(header, 'latin1')
		if opentypeheaderRE.search(header):
			return "OTX"
		else:
			return "TTX"
	return None


def parseOptions(args):
	try:
		rawOptions, files = getopt.getopt(args, "ld:o:vqht:x:sim:z:baey:")
	except getopt.GetoptError:
		usage()
	
	if not files:
		usage()
	
	options = Options(rawOptions, len(files))
	jobs = []
	
	for input in files:
		tp = guessFileType(input)
		if tp in ("OTF", "TTF", "TTC", "WOFF"):
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
			print('Unknown file type: "%s"' % input)
			continue
		
		if options.outputFile:
			output = options.outputFile
		else:
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
	print('(Hit any key to exit)')
	while not msvcrt.kbhit():
		pass


def main(args):
	jobs, options = parseOptions(args)
	try:
		process(jobs, options)
	except KeyboardInterrupt:
		print("(Cancelled.)")
	except SystemExit:
		if sys.platform == "win32":
			waitForKeyPress()
		else:
			raise
	except TTLibError as e:
		print("Error:",e)
	except:
		if sys.platform == "win32":
			import traceback
			traceback.print_exc()
			waitForKeyPress()
		else:
			raise
	

if __name__ == "__main__":
	main(sys.argv[1:])
