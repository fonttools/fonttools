# a more robust batch generator that only has one font open at the time.

from robofab.interface.all.dialogs import GetFolder
from robofab.world import RFont, OpenFont
import os

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

def makeDestination(root):
	macPath = os.path.join(root, 'FabFonts', 'ForMac')
	makeFolder(macPath)
	return macPath

def generateOne(f, dstDir):
	print "generating %s"%f.info.postscriptFullName
	f.generate('mactype1',  dstDir)
	

f = GetFolder()

if f is not None:
	paths = collectSources(f)
	dstDir = makeDestination(f)

	for f in paths:
		font = None
		try:
			font = OpenFont(f)
			generateOne(font, dstDir)

		finally:
			if font is not None:
				font.close(False)


	print 'done'