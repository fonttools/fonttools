#! /usr/bin/env python

import os, sys
from distutils.core import setup, Extension


try:
	import Numeric
except ImportError:
	print "*** Warning: FontTools needs Numerical Python (NumPy), see:"
	print "        http://sourceforge.net/projects/numpy/"

try:
	import xml.parsers.expat
except ImportError:
	print "*** Warning: FontTools needs PyXML, see:"
	print "        http://sourceforge.net/projects/pyxml/"



setup(	name = "FontTools",
		version = "1.0",
		description = "FontTools",
		author = "Just van Rossum",
		author_email = "just@letterror.com",
		url = "http://fonttools.sourceforge.net/",
		
		packages = [
			"",
			"fontTools",
			"fontTools.encodings",
			"fontTools.misc",
			"fontTools.ttLib",
			"fontTools.ttLib.tables",
			"fontTools.ttLib.test",
		],
		package_dir = {'': 'Lib'},
		extra_path = 'FontTools',
		ext_modules = [
			Extension(
				"fontTools.misc.eexecOp",
				["Src/eexecOp/eexecOpmodule.c"],
				include_dirs=[],
				define_macros=[],
				library_dirs=[],
				libraries=[],
			)
		]

	)

