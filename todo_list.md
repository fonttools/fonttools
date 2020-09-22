# lib/__main__.py/main
to do for main function

##TODO Handle library-wide options. Eg.:
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


