#FLM: Batch remove glyphs

#	Paul van der Laan, 2004/10/25


from robofab.interface.all.dialogs import GetFolder
from robofab.world import RFont, OpenFont, CurrentFont
import os

myBlacklist = ("nbspace", ".notdef", ".null")


# Een functie om een map met files door te zoeken op vfb files
def collectSources(root):
	files = []
	ext = ['.vfb']
	names = os.listdir(root)
	for n in names:
		if os.path.splitext(n)[1] in ext:
			files.append(os.path.join(root, n))
	return files

# main loop
mySource = GetFolder()
if mySource is not None:
	myFiles = collectSources(mySource)
	for myFile in myFiles:
		myrfFont = None
		try:
			myrfFont = OpenFont(myFile)
			for myGlyph in myBlacklist:
				if myrfFont.has_key(myGlyph):
					myrfFont.removeGlyph(myGlyph)
					print myGlyph, "removed from", myrfFont.info.familyName + "-" + myrfFont.info.styleName
			myrfFont.update()
			myrfFont.save()
		finally:
			if myrfFont is not None:
				myrfFont.close(False)
print "Done"
