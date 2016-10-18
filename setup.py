#! /usr/bin/env python
import sys
from setuptools import setup, find_packages


long_description = """\
ufoLib reads and writes Unified Font Object (UFO) files.
UFO is a file format that stores fonts source files.

http://unifiedfontobject.org
"""

needs_pytest = {'pytest', 'test'}.intersection(sys.argv)
pytest_runner = ['pytest_runner'] if needs_pytest else []
needs_wheel = {'bdist_wheel'}.intersection(sys.argv)
wheel = ['wheel'] if needs_wheel else []

setup_params = dict(
	name="ufoLib",
	version="2.0.0",
	description="A low-level UFO reader and writer.",
	author="Just van Rossum, Tal Leming, Erik van Blokland, others",
	author_email="info@robofab.com",
	maintainer="Just van Rossum, Tal Leming, Erik van Blokland",
	maintainer_email="info@robofab.com",
	url="https://github.com/unified-font-object/ufoLib",
	license="OpenSource, BSD-style",
	platforms=["Any"],
	long_description=long_description,
	package_dir={'': 'Lib'},
	packages=find_packages('Lib'),
	include_package_data=True,
	setup_requires=pytest_runner + wheel,
	tests_require=[
		'pytest>=3.0.2',
	],
	install_requires=[
		"fonttools>=3.1.2",
	],
	classifiers=[
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
)


if __name__ == "__main__":
	setup(**setup_params)
