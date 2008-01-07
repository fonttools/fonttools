#FLM: Batch generate Mac, Win & Unix

# Generates three formats at once:
#   Macintosh PS Type 1
#   Windows PS Type 1
#   Unix PS Type 1

from robofab.interface.all.dialogs import GetFolder
from robofab.world import RFont, OpenFont
import os

# Een functie om een map met files door te zoeken op vfb files
def collectSources(root):
	files = []
	ext = ['.vfb']
	names = os.listdir(root)
	for n in names:
		if os.path.splitext(n)[1] in ext:
			files.append(os.path.join(root, n))
	return files

# A little function for making folders. we'll need it later.
def makeFolder(path):
	#if the path doesn't exist, make it!
	if not os.path.exists(path):
		os.makedirs(path)

# maak verschillende mapjes aan voor de fontformaten
def makeDestination(root):
	basePath = os.path.join(root, 'Generated',)
	macPath = os.path.join(root, 'Generated', 'mac ps type 1')
	makeFolder(macPath)
	winPath = os.path.join(root, 'Generated', 'win ps type 1')
	makeFolder(winPath)
	unixPath = os.path.join(root, 'Generated', 'unix ps type 1')
	makeFolder(unixPath)
	return basePath

# genereer de drie formaten
def generateOne(f, dstDir):
	dstMac = os.path.join(dstDir, 'mac ps type 1')
	f.generate('mactype1', dstMac)
	dstWin = os.path.join(dstDir, 'win ps type 1')
	f.generate('pctype1', dstWin)
	dstUnix = os.path.join(dstDir, 'unix ps type 1')
	f.generate('pctype1ascii', dstUnix)
	print "%s  -  %s"%(f.info.uniqueID, f.info.fullName)
	# print unique ID en naam in het output window

# dialog voor het selecteren van een folder
f = GetFolder()

if f is not None:
	paths = collectSources(f)
	dstDir = makeDestination(f)

	print 'UniqueID    Full fontname'
	print '-------------------------------------------'
	
	for f in paths:
		font = None
		try:
			font = OpenFont(f)
			generateOne(font, dstDir)

		finally:
			if font is not None:
				fl.font.modified = 0
				font.close(False)

	print 'done'
