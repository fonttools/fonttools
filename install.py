#! /usr/bin/env python

import sys, os

ttlibdir = os.path.join(os.getcwd(), "Lib")

if sys.platform not in ('win32', 'mac'):
    libdir = os.path.join(sys.exec_prefix, 
                          'lib',
                          'python' + sys.version[:3],
                          'site-packages')
else:
    libdir = sys.exec_prefix
pth_path = os.path.join(libdir, "FontTools.pth")
pth_file = open(pth_path, "w")
pth_file.write(ttlibdir + '\n')
pth_file.close()
