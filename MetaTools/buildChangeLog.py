#! /usr/bin/env python

import os, sys

fontToolsDir = os.path.dirname(os.path.dirname(os.path.normpath(
		os.path.join(os.getcwd(), sys.argv[0]))))

os.chdir(fontToolsDir)
os.system("git2cl > Doc/ChangeLog")
print("done.")
