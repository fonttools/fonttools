#! /usr/bin/env python

import os, sys

fontToolsDir = os.path.dirname(os.path.dirname(os.path.normpath(
		os.path.join(os.getcwd(), sys.argv[0]))))

os.chdir(fontToolsDir)
os.system("cvs log | ./MetaTools/logmerge.py > Doc/ChangeLog.txt")
print "done."
