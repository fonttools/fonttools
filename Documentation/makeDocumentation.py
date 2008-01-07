#FLM: Generate RoboFab Documentation

"""This script will generate up to date documentation for RoboFab.
Provided you have installed RoboFab correctly and you're using
python 2.1 or higher.

This script will make a bunch of HTML files in robofab/Documentation/robofabDoc/

It collects all docstrings, shows classes, methods and functions. 
This script uses pydoc.

The results of this script depend on the environment you run it in
As RoboFab does different things in different places, you can't generate
documentation for (for instance) ObjectsFL when you're running
this script in the Python IDE: it's impossible to load all the necessary
modules.

Run this script in the Python IDE first, then run it again as a macro in FontLab,
that will give you a fairly complete set of descriptions.
"""

print 'Generating RoboFab documentation, just a moment...'

import robofab
import fontTools
import os
from pydoc import  writedocs, ispackage, writedoc, inspect
from robofab.world import world


def myWritedocs(dir, pkgpath='', done=None):
	"""Write out HTML documentation for all modules in a directory tree."""
	if done is None: done = {}
	for file in os.listdir(dir):
		path = os.path.join(dir, file)
		if ispackage(path):
			writedocs(path, pkgpath + file + '.', done)
		elif os.path.isfile(path):
			modname = inspect.getmodulename(path)
			if modname:
				if modname == '__init__':
					modname = pkgpath[:-1] # remove trailing period
				else:
					modname = pkgpath + modname
				if modname not in done:
					done[modname] = 1
					try:
						writedoc(modname)
					except:
						print 'failed to document', modname


robofabDir = os.path.dirname(os.path.dirname(robofab.__file__))
fontToolsDir = os.path.dirname(os.path.dirname(fontTools.__file__))
roboFabDocoDir = ['Documentation', 'robofabDocs']
fontToolsDocoDir = ['Documentation', 'fontToolsDocs']

currentDir = os.getcwd()

# robofab
bits = robofabDir.split(os.sep)[:-1] + roboFabDocoDir
htmlDir = os.sep.join(bits)

try:
	os.makedirs(htmlDir)
except OSError:
	pass
os.chdir(htmlDir)

if world.inFontLab:
	print "- generating documentation for FontLab specific modules"
	print "- make sure to run this script in the IDE as well!"
	
	# this is a list of FontLab specific modules that need to be documented
	import robofab.objects.objectsFL
	import robofab.tools.toolsFL
	import robofab.pens.flPen
	import robofab.tools.otFeatures
	mods = [	robofab.objects.objectsFL,
			 robofab.tools.toolsFL,
			robofab.pens.flPen,
			robofab.tools.otFeatures,
			]
	for m in mods:
		writedoc(m)
else:
	print "- generating documentation for generic modules"
	print "- make sure to run this script in FontLab as well (if you want that documented)."
	myWritedocs(robofabDir)

os.chdir(currentDir)

# fonttools
bits = robofabDir.split(os.sep)[:-1] + fontToolsDocoDir
htmlDir = os.sep.join(bits)
try:
	os.makedirs(htmlDir)
except OSError:
	pass
os.chdir(htmlDir)

if world.inFontLab:
	pass
else:
	print "- generating documentation for generic modules"
	print "- make sure to run this script in FontLab as well (if you want that documented)."
	myWritedocs(fontToolsDir)

os.chdir(currentDir)

print 'done'
print 'The documentation is in', htmlDir
	
	
