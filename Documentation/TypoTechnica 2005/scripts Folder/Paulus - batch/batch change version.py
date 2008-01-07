#FLM: Batch version change

#	Paul van der Laan, 2004/10/25


from robofab.interface.all.dialogs import GetFolder
from robofab.world import RFont, OpenFont, CurrentFont
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

# main loop
mySource = GetFolder()
if mySource is not None:
	myFiles = collectSources(mySource)
	for myFile in myFiles:
		myrfFont = None
		try:
			myrfFont = OpenFont(myFile)

			myFamilyname = myrfFont.info.familyName
			myStylename = myrfFont.info.styleName
			myFamilyname = myFamilyname.replace("V01", "V02")

			myrfFont.info.familyName = myFamilyname
			myrfFont.info.fontName = myFamilyname + "-" + myStylename
			myrfFont.info.fullName = myFamilyname + " " + myStylename
			myrfFont.info.menuName = myFamilyname
			myrfFont.info.fondName = myFamilyname + "-" + myStylename
			
			print myFamilyname + "-" + myStylename
			
			myrfFont.update()
			myrfFont.save()
		finally:
			if myrfFont is not None:
				myrfFont.close(False)
print "Done"
