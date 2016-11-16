#! /usr/bin/env python

from __future__ import print_function
import sys
from setuptools import setup, find_packages
import versioneer

# Force distutils to use py_compile.compile() function with 'doraise' argument
# set to True, in order to raise an exception on compilation errors
import py_compile
orig_py_compile = py_compile.compile

def doraise_py_compile(file, cfile=None, dfile=None, doraise=False):
	orig_py_compile(file, cfile=cfile, dfile=dfile, doraise=True)

py_compile.compile = doraise_py_compile

needs_pytest = {'pytest', 'test'}.intersection(sys.argv)
pytest_runner = ['pytest_runner'] if needs_pytest else []
needs_wheel = {'bdist_wheel'}.intersection(sys.argv)
wheel = ['wheel'] if needs_wheel else []

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
	name="fonttools",
	version=versioneer.get_version(),
	description="Tools to manipulate font files",
	author="Just van Rossum",
	author_email="just@letterror.com",
	maintainer="Behdad Esfahbod",
	maintainer_email="behdad@behdad.org",
	url="http://github.com/fonttools/fonttools",
	license="OpenSource, BSD-style",
	platforms=["Any"],
	long_description=long_description,
	package_dir={'': 'Lib'},
	packages=find_packages("Lib"),
	py_modules=['sstruct', 'xmlWriter'],
	include_package_data=True,
	data_files=[
		('share/man/man1', ["Doc/ttx.1"])
	] if sys.platform.startswith('linux') else [],
	setup_requires=pytest_runner + wheel,
	tests_require=[
		'pytest>=2.8',
	],
	entry_points={
		'console_scripts': [
			"fonttools = fontTools.__main__:main",
			"ttx = fontTools.ttx:main",
			"pyftsubset = fontTools.subset:main",
			"pyftmerge = fontTools.merge:main",
			"pyftinspect = fontTools.inspect:main",
			"pyftanalysis = fontTools.analysis:main"
		]
	},
	cmdclass=versioneer.get_cmdclass(),
	**classifiers
)
