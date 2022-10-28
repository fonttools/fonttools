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
	"""Open font with TTFont() or TTCollection()"""
	from fontTools import configLogger

	if args is None:
		args = sys.argv[1:]

	for f in args:
		try:
			font = TTFont(f)
		except TTLibFileIsCollectionError:
			font = TTCollection(f)

		#font.save(outfile)

if __name__ == "__main__":
	sys.exit(main())
