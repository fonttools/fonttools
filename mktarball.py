#! /usr/bin/env python

import os, sys

src = os.path.basename(sys.argv[0])
print src

xxxxxx

tar = src + ".tar"
gz = tar + ".gz"
tgz = src + ".tgz"

os.system("tar --exclude="CVS|mktarball.py" -cvf %s %s" % (tar, src))
os.system("gzip -9v %s" % tar)
os.rename(gz, tgz)
