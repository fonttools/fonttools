#! /usr/bin/env python

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
