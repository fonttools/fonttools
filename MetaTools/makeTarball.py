#! /usr/bin/env python
#
# Script to make a compressed tar archive of the directory 
# the script is living in, excluding CVS directories.
#


import os, sys


script = os.path.join(os.getcwd(), sys.argv[0])
srcdir = os.path.normpath(os.path.dirname(os.path.dirname(script)))
wdir, src = os.path.split(srcdir)

try:
	execfile(os.path.join(srcdir, "Lib", "fontTools", "__init__.py"))
	version  # make sure we now have a variable named "version"
except (IOError, NameError):
	version = None


destdir = None
if sys.argv[1:]:
	destdir = os.path.normpath(os.path.join(os.getcwd(), sys.argv[1]))
	assert os.path.isdir(destdir), "destination is not an existing directory"

os.chdir(wdir)

if version:
	tar = src + "-%s.tgz" % version
else:
	tar = src + ".tgz"

print "source:", src
print "dest:", tar

if sys.platform[:6] == "darwin":
	tool = "gnutar"
else:
	tool = "tar"

os.system('%s --exclude=CVS -czf %s %s/' % (tool, tar, src))

if destdir:
	print "destination directory:", destdir
	os.system('mv %s %s' % (gz, destdir))
