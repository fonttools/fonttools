#! /usr/bin/env python
#
# Script to make a compressed tar archive of the directory 
# the script is living in, excluding CVS directories and the 
# script itself.
#
# $Id: mktarball.py,v 1.6 1999-12-18 23:56:14 just Exp $
#


import os, sys

script = os.path.join(os.getcwd(), sys.argv[0])
srcdir, scriptname = os.path.split(script)
wdir, src = os.path.split(srcdir)
os.chdir(wdir)

tar = src + ".tar"
gz = tar + ".gz"
tgz = src + ".tgz"

print "source:", src
print "dest:", tgz

os.system('tar --exclude=CVS --exclude=%s -cf %s %s' % (scriptname, tar, src))
os.system('gzip -9v %s' % tar)
os.rename(gz, tgz)
