#FLM: Batch save as font info name

#	Paul van der Laan, 2005/01/10



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
		myFont = None
		try:
			myFont = OpenFont(myFile)
			myFamilyname = myFont.info.familyName
			myStylename = myFont.info.styleName
			myPath = mySource + ":" + myFamilyname + "-" + myStylename + ".vfb"
			fl.font.Save(myPath)
			print myFamilyname + "-" + myStylename
			
		finally:
			if myFont is not None:
				myFont.close(False)

print "Done"
