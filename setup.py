#! /usr/bin/env python

from __future__ import print_function
import os, sys
from distutils.core import setup, Extension
from distutils.command.build_ext import build_ext

try:
	# load py2exe distutils extension, if available
	import py2exe
except ImportError:
	pass

try:
	import xml.parsers.expat
except ImportError:
	print("*** Warning: FontTools needs PyXML, see:")
	print("        http://sourceforge.net/projects/pyxml/")


class build_ext_optional(build_ext):
	"""build_ext command which doesn't abort when it fails."""
	def build_extension(self, ext):
		# Skip extensions which cannot be built
		try:
			build_ext.build_extension(self, ext)
		except:
			self.announce(
				'*** WARNING: Building of extension "%s" '
				'failed: %s' %
				(ext.name, sys.exc_info()[1]))


if sys.version_info > (2, 3, 0, 'alpha', 1):
	# Trove classifiers for PyPI
	classifiers = {"classifiers": [
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
	]}
else:
	classifiers = {}

long_description = """\
FontTools/TTX is a library to manipulate font files from Python.
It supports reading and writing of TrueType/OpenType fonts, reading
and writing of AFM files, reading (and partially writing) of PS Type 1
fonts. The package also contains a tool called "TTX" which converts
TrueType/OpenType fonts to and from an XML-based format.
"""

setup(
		name = "fonttools",
		version = "2.4",
		description = "Tools to manipulate font files",
		author = "Just van Rossum",
		author_email = "just@letterror.com",
		maintainer = "Just van Rossum",
		maintainer_email = "just@letterror.com",
		url = "http://fonttools.sourceforge.net/",
		license = "OpenSource, BSD-style",
		platforms = ["Any"],
		long_description = long_description,
		
		packages = [
			"fontTools",
			"fontTools.encodings",
			"fontTools.misc",
			"fontTools.pens",
			"fontTools.ttLib",
			"fontTools.ttLib.tables",
		],
		package_dir = {'': 'Lib'},
		extra_path = 'FontTools',
		scripts = ["Tools/ttx", "Tools/pyftsubset", "Tools/pyftinspect", "Tools/pyftmerge"],
		cmdclass = {"build_ext": build_ext_optional},
		data_files = [('share/man/man1', ["Doc/ttx.1"])],
		**classifiers
	)
