#! /usr/bin/env python

import os, sys

try:
	from setuptools import setup
	extra_kwargs = {
		"test_suite": "ufoLib.test"
	}
except ImportError:
	from distutils.core import setup
	extra_kwargs = {}

try:
	import fontTools
except ImportError:
	print("*** Warning: ufoLib needs FontTools for some operations, see:")
	print("        https://github.com/behdad/fonttools")


long_description = """\
ufoLib reads and writes Unified Font Object (UFO) files. UFO is a file format
that stores fonts source files.
"""

setup(
		name = "ufoLib",
		version = "1.2",
		description = "A low-level UFO reader and writer.",
		author = "Just van Rossum, Tal Leming, Erik van Blokland, others",
		author_email = "info@robofab.com",
		maintainer = "Just van Rossum, Tal Leming, Erik van Blokland",
		maintainer_email = "info@robofab.com",
		url = "http://unifiedfontobject.org",
		license = "OpenSource, BSD-style",
		platforms = ["Any"],
		long_description = long_description,

		packages = [
			"ufoLib",
		],
		package_dir = {'': 'Lib'},
		classifiers = [
			"Development Status :: 4 - Beta",
			"Environment :: Console",
			"Environment :: Other Environment",
			"Intended Audience :: Developers",
			"Intended Audience :: End Users/Desktop",
			"License :: OSI Approved :: BSD License",
			"Natural Language :: English",
			"Operating System :: OS Independent",
			"Programming Language :: Python",
			"Topic :: Multimedia :: Graphics",
			"Topic :: Multimedia :: Graphics :: Graphics Conversion",
		],
		**extra_kwargs
	)
