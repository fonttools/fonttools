from __future__ import print_function, division, absolute_import
import sys


def main(args=None):
	if args is None:
		args = sys.argv[1:]

	# TODO Add help output, --help, etc.

	# TODO Handle library-wide options. Eg.:
	# --unicodedata
	# --verbose / other logging stuff

	# TODO Allow a way to run arbitrary modules? Useful for setting
	# library-wide options and calling another library. Eg.:
	#
	#   $ fonttools --unicodedata=... fontmake ...
	#
	# This allows for a git-like command where thirdparty commands
	# can be added.  Should we just try importing the fonttools
	# module first and try without if it fails?

	mod = 'fontTools.'+sys.argv[1]
	sys.argv[1] = sys.argv[0] + ' ' + sys.argv[1]
	del sys.argv[0]

	import runpy
	runpy.run_module(mod, run_name='__main__')


if __name__ == '__main__':
	sys.exit(main())
