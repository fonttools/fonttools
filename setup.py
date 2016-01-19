#! /usr/bin/env python

from __future__ import print_function
import os, sys

# if setuptools is not installed, fall back to distutils
try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup
	distutils_scripts = [
		"Tools/ttx", "Tools/pyftsubset", "Tools/pyftinspect", "Tools/pyftmerge"]
else:
	distutils_scripts = []


# Force distutils to use py_compile.compile() function with 'doraise' argument
# set to True, in order to raise an exception on compilation errors
import py_compile
orig_py_compile = py_compile.compile

def doraise_py_compile(file, cfile=None, dfile=None, doraise=False):
    orig_py_compile(file, cfile=cfile, dfile=dfile, doraise=True)

py_compile.compile = doraise_py_compile


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

long_description = """\
FontTools/TTX is a library to manipulate font files from Python.
It supports reading and writing of TrueType/OpenType fonts, reading
and writing of AFM files, reading (and partially writing) of PS Type 1
fonts. The package also contains a tool called "TTX" which converts
TrueType/OpenType fonts to and from an XML-based format.
"""

setup(
		name = "fonttools",
		version = "3.0",
		description = "Tools to manipulate font files",
		author = "Just van Rossum",
		author_email = "just@letterror.com",
		maintainer = "Behdad Esfahbod",
		maintainer_email = "behdad@behdad.org",
		url = "http://github.com/behdad/fonttools",
		license = "OpenSource, BSD-style",
		platforms = ["Any"],
		long_description = long_description,

		packages = [
			"fontTools",
			"fontTools.encodings",
			"fontTools.feaLib",
			"fontTools.misc",
			"fontTools.mtiLib",
			"fontTools.pens",
			"fontTools.ttLib",
			"fontTools.t1Lib",
			"fontTools.subset",
			"fontTools.otlLib",
			"fontTools.ttLib.tables",
		],
		py_modules = ['sstruct', 'xmlWriter'],
		package_dir = {'': 'Lib'},
		extra_path = 'FontTools',
		data_files = [('share/man/man1', ["Doc/ttx.1"])],
		scripts = distutils_scripts,
		entry_points = {
				'console_scripts': [
					"ttx = fontTools.ttx:main",
					"pyftsubset = fontTools.subset:main",
					"pyftmerge = fontTools.merge:main",
					"pyftinspect = fontTools.inspect:main"
				]
			},
		**classifiers
	)
