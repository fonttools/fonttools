#! /usr/bin/env python
#
# Script to make a compressed tar archive of the directory 
# the script is living in, excluding CVS directories and the 
# script itself.
#
# $Id: mktarball.py,v 1.5 1999-12-18 23:28:54 Just Exp $
#


import os, sys

src, self = os.path.split(sys.argv[0])
tar = src + ".tar"
gz = tar + ".gz"
tgz = src + ".tgz"

print "source:", src
print "dest:", tgz

os.system('tar --exclude=CVS --exclude=%s -cf %s %s' % (self, tar, src))
os.system('gzip -9v %s' % tar)
os.rename(gz, tgz)
