#! /usr/bin/env python

import os, sys
from distutils.core import setup, Extension
from distutils.command.build_ext import build_ext

try:
	# load py2exe distutils extension, if available
	import py2exe
except ImportError:
	pass

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


setup(
		name = "FontTools",
		version = "1.0",
		description = "Python FontTools",
		author = "Just van Rossum",
		author_email = "just@letterror.com",
		maintainer = "Just van Rossum",
		maintainer_email = "just@letterror.com",
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
		],
		scripts = ["Tools/ttx"],
		cmdclass = {"build_ext": build_ext_optional}
	)

