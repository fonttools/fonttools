#! /usr/bin/env python
#
# Script to make a compressed tar archive of the directory 
# the script is living in, excluding CVS directories and the 
# script itself.
#
# $Id: mktarball.py,v 1.7 2000-02-13 17:36:44 just Exp $
#


import os, sys

program = os.path.normpath(sys.argv[0])
script = os.path.join(os.getcwd(), program)
srcdir, scriptname = os.path.split(script)
wdir, src = os.path.split(srcdir)

destdir = None
if sys.argv[1:]:
	destdir = os.path.normpath(os.path.join(os.getcwd(), sys.argv[1]))
	assert os.path.isdir(destdir), "destination is not an existing directory"

os.chdir(wdir)

tar = src + ".tar"
gz = tar + ".gz"

print "source:", src
print "dest:", gz

os.system('tar --exclude=CVS --exclude=%s -cf %s %s' % (scriptname, tar, src))
os.system('gzip -9v %s' % tar)

if destdir:
	print "destination directory:", destdir
	os.system('mv %s %s' % (gz, destdir))

