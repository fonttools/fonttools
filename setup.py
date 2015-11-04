#! /usr/bin/env python

import os, sys
from setuptools import setup

try:
	import fontTools
except ImportError:
	print("*** Warning: RoboFab needs FontTools for some operations, see:")
	print("        http://sourceforge.net/projects/fonttools/")


long_description = """\
RoboFab is a Python library with objects that deal with data usually associated with fonts and type design.
"""

setup(
		name = "robofab",
		version = "1.2",
		description = "Tools to manipulate font sources",
		author = "Just van Rossum, Tal Leming, Erik van Blokland, others",
		author_email = "info@robofab.com",
		maintainer = "Just van Rossum, Tal Leming, Erik van Blokland",
		maintainer_email = "info@robofab.com",
		url = "http://robofab.com/",
		license = "OpenSource, BSD-style",
		platforms = ["Any"],
		long_description = long_description,

		packages = [
			"robofab",
			"robofab.interface",
			"robofab.interface.mac",
			"robofab.interface.win",
			"robofab.interface.all",
			"robofab.misc",
			"robofab.objects",
			"robofab.pens",
			"robofab.tools",
			"ufoLib",
		],
		package_dir = {'': 'Lib'},
		test_suite = "ufoLib.test",
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
		]
	)
