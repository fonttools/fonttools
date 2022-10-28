"""fontTools.ttLib -- a package for dealing with TrueType fonts."""

from fontTools.misc.loggingTools import deprecateFunction
import logging
import sys


log = logging.getLogger(__name__)

class TTLibError(Exception): pass
class TTLibFileIsCollectionError (TTLibError): pass

@deprecateFunction("use logging instead", category=DeprecationWarning)
def debugmsg(msg):
	import time
	print(msg + time.strftime("  (%H:%M:%S)", time.localtime(time.time())))

from fontTools.ttLib.ttFont import *
from fontTools.ttLib.ttCollection import TTCollection


def main(args=None):
	"""Open font with TTFont() or TTCollection()

	  ./fonttools ttLib [-oFILE] [-yNUMBER] files...

	If multiple files are given on the command-line,
	they are each opened (as a font or collection),
	and added to the font list.

	If -o (output-file) argument is given, the font
	list is then saved to the output file, either as
	a single font, if there is only one font, or as
	a collection otherwise.

	If -y (font-number) argument is given, only the
	specified font from collections is opened.

	The above allow extracting a single font from a
	collection, or combining multiple fonts into a
	collection.

	If --lazy or --no-lazy are give, those are passed
	to the TTFont() or TTCollection() constructors.
	"""
	from fontTools import configLogger

	if args is None:
		args = sys.argv[1:]

	import getopt
	options, files = getopt.getopt(args, "o:y:",
		["lazy", "no-lazy"])

	fontNumber = -1
	outFile = None
	lazy = None
	for option, value in options:
		if option == "-o":
			outFile = value
		elif option == "-y":
			fontNumber = int(value)
		elif option == "--lazy":
			lazy = True
		elif option == "--no-lazy":
			lazy = False

	fonts = []
	for f in files:
		try:
			font = TTFont(f, fontNumber=fontNumber, lazy=lazy)
			fonts.append(font)
		except TTLibFileIsCollectionError:
			collection = TTCollection(f, lazy=lazy)
			fonts.extend(collection.fonts)

		if outFile is not None:
			if len(fonts) == 1:
				fonts[0].save(outFile)
			else:
				collection = TTCollection()
				collection.fonts = fonts
				collection.save(outFile)

if __name__ == "__main__":
	sys.exit(main())
