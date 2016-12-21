#! /usr/bin/env python

from __future__ import print_function
import io
import sys
from setuptools import setup, find_packages, Command
from distutils import log
import subprocess as sp
import contextlib

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
needs_bumpversion = {'release'}.intersection(sys.argv)
bumpversion = ['bumpversion'] if needs_bumpversion else []

# Trove classifiers for PyPI
classifiers = {"classifiers": [
	"Development Status :: 5 - Production/Stable",
	"Environment :: Console",
	"Environment :: Other Environment",
	"Intended Audience :: Developers",
	"Intended Audience :: End Users/Desktop",
	"License :: OSI Approved :: BSD License",
	"Natural Language :: English",
	"Operating System :: OS Independent",
	"Programming Language :: Python",
	"Programming Language :: Python :: 2",
	"Programming Language :: Python :: 3",
	"Topic :: Text Processing :: Fonts",
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


@contextlib.contextmanager
def capture_logger(name):
	""" Context manager to capture a logger output with a StringIO stream.
	"""
	import logging

	logger = logging.getLogger(name)
	try:
		import StringIO
		stream = StringIO.StringIO()
	except ImportError:
		stream = io.StringIO()
	handler = logging.StreamHandler(stream)
	logger.addHandler(handler)
	try:
		yield stream
	finally:
		logger.removeHandler(handler)


class release(Command):
	"""
	Tag a new release with a single command, using the 'bumpversion' tool
	to update all the version strings in the source code.
	The version scheme conforms to 'SemVer' and PEP 440 specifications.

	Firstly, the pre-release '.devN' suffix is dropped to signal that this is
	a stable release. If '--major' or '--minor' options are passed, the
	the first or second 'semver' digit is also incremented. Major is usually
	for backward-incompatible API changes, while minor is used when adding
	new backward-compatible functionalities. No options imply 'patch' or bug-fix
	release.

	A new header is also added to the changelog file ("NEWS"), containing the
	new version string and the current 'YYYY-MM-DD' date.

	All changes are committed, and an annotated git tag is generated. With the
	--sign option, the tag is GPG-signed with the user's default key.

	Finally, the 'patch' part of the version string is bumped again, and a
	pre-release suffix '.dev0' is appended to mark the opening of a new
	development cycle.

	Links:
	- http://semver.org/
	- https://www.python.org/dev/peps/pep-0440/
	- https://github.com/peritus/bumpversion
	"""

	description = "update version strings for release"

	user_options = [
		("major", None, "bump the first digit (incompatible API changes)"),
		("minor", None, "bump the second digit (new backward-compatible features)"),
		("sign", "s", "make a GPG-signed tag, using the default key"),
		("allow-dirty", None, "don't abort if working directory is dirty"),
	]

	changelog_name = "NEWS"
	changelog_header = u"## TTX/FontTools Version "
	changelog_date_fmt = "%Y-%m-%d"
	commit_message = "Release {new_version}"
	tag_name = "{new_version}"
	version_files = [
		"setup.cfg",
		"setup.py",
		"Lib/fontTools/__init__.py",
	]

	def initialize_options(self):
		self.minor = False
		self.major = False
		self.sign = False
		self.allow_dirty = False

	def finalize_options(self):
		if all([self.major, self.minor]):
			from distutils.errors import DistutilsOptionError
			raise DistutilsOptionError("--major/--minor are mutually exclusive")
		self.part = "major" if self.major else "minor" if self.minor else None

	def run(self):
		if self.part is not None:
			log.info("bumping '%s' version" % self.part)
			self.bumpversion(self.part, commit=False)
			release_version = self.bumpversion(
				"release", commit=False, allow_dirty=True)
		else:
			log.info("stripping pre-release suffix")
			release_version = self.bumpversion("release")
		log.info("  version = %s" % release_version)

		changes = self.format_changelog(release_version)

		self.git_commit(release_version)
		self.git_tag(release_version, changes, self.sign)

		log.info("bumping 'patch' version and pre-release suffix")
		next_dev_version = self.bumpversion('patch', commit=True)
		log.info("  version = %s" % next_dev_version)

	def git_commit(self, version):
		""" Stage and commit all relevant version files, and format the commit
		message with specified 'version' string.
		"""
		files = self.version_files + [self.changelog_name]

		log.info("committing changes")
		for f in files:
			log.info("  %s" % f)
		if self.dry_run:
			return
		sp.check_call(["git", "add"] + files)
		msg = self.commit_message.format(new_version=version)
		sp.check_call(["git", "commit", "-m", msg], stdout=sp.PIPE)

	def git_tag(self, version, message, sign=False):
		""" Create annotated git tag with given 'version' and 'message'.
		Optionally 'sign' the tag with the user's GPG key.
		"""
		log.info("creating %s git tag '%s'" % (
			"signed" if sign else "annotated", version))
		if self.dry_run:
			return
		# create an annotated (or signed) tag from the new version
		tag_opt = "-s" if sign else "-a"
		tag_name = self.tag_name.format(new_version=version)
		proc = sp.Popen(
			["git", "tag", tag_opt, "-F", "-", tag_name], stdin=sp.PIPE)
		# use the latest changes from the changelog file as the tag message
		tag_message = u"%s\n\n%s" % (tag_name, message)
		proc.communicate(tag_message.encode('utf-8'))
		if proc.returncode != 0:
			sys.exit(proc.returncode)

	def bumpversion(self, part, commit=False, message=None, allow_dirty=None):
		""" Run bumpversion.main() with the specified arguments, and return the
		new computed version string (cf. 'bumpversion --help' for more info)
		"""
		import bumpversion

		args = (
			(['--verbose'] if self.verbose > 1 else []) +
			(['--dry-run'] if self.dry_run else []) +
			(['--allow-dirty'] if (allow_dirty or self.allow_dirty) else []) +
			(['--commit'] if commit else ['--no-commit']) +
			(['--message', message] if message is not None else []) +
			['--list', part]
		)
		log.debug("$ bumpversion %s" % " ".join(a.replace(" ", "\\ ") for a in args))

		with capture_logger("bumpversion.list") as out:
			bumpversion.main(args)

		last_line = out.getvalue().splitlines()[-1]
		new_version = last_line.replace("new_version=", "")
		return new_version

	def format_changelog(self, version):
		""" Write new header at beginning of changelog file with the specified
		'version' and the current date.
		Return the changelog content for the current release.
		"""
		from datetime import datetime

		log.info("formatting changelog")

		changes = []
		with io.open(self.changelog_name, "r+", encoding="utf-8") as f:
			for ln in f:
				if ln.startswith(self.changelog_header):
					break
				else:
					changes.append(ln)
			if not self.dry_run:
				f.seek(0)
				content = f.read()
				f.seek(0)
				f.write(u"%s%s\n\n%s\n\n%s" % (
					self.changelog_header,
					version,
					datetime.today().strftime(self.changelog_date_fmt),
					content))

		return u"".join(changes)


setup(
	name="fonttools",
	version="3.4.0",
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
	include_package_data=True,
	data_files=[
		('share/man/man1', ["Doc/ttx.1"])
	] if sys.platform.startswith('linux') else [],
	setup_requires=pytest_runner + wheel + bumpversion,
	tests_require=[
		'pytest>=2.8',
	],
	entry_points={
		'console_scripts': [
			"fonttools = fontTools.__main__:main",
			"ttx = fontTools.ttx:main",
			"pyftsubset = fontTools.subset:main",
			"pyftmerge = fontTools.merge:main",
			"pyftinspect = fontTools.inspect:main"
		]
	},
	cmdclass={
		"release": release,
	},
	**classifiers
)
