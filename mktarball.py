#! /usr/bin/env python

import os

src = os.getcwd()
tar = src + ".tar"
gz = tar + ".gz"
tgz = src + ".tgz"

os.system("tar --exclude=CVS -cvf %s %s" % (tar, src))
os.system("gzip -9v %s" % tar)
os.rename(gz, tgz)
