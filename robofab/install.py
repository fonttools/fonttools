"""Install script for the RoboFab Package.

This script installs a _link_ to the current location
of RoboFab. It does not copy anything. It also means that
if you move your RoboFab folder, you'll have to run the
install script again.
"""


from distutils.sysconfig import get_python_lib
import os, sys


def install(srcDir, pathFileName):
	sitePackDir = get_python_lib()
	fileName = os.path.join(sitePackDir, pathFileName + ".pth")
	print "Installing RoboFab: about to write a path to %r in %r..." % (srcDir, fileName)
	f = open(fileName, 'w')
	f.write(srcDir)
	f.close()
	return fileName

dir = os.path.join(os.path.dirname(os.path.normpath(os.path.abspath(sys.argv[0]))), "Lib")

p = install(dir, "robofab")

print "Robofab is now installed."
print "(Note that you have to run the install script again if you move your RoboFab folder)"
