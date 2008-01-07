#FLM: Batch win rename Lexicon

#	Paul van der Laan, 2004/09/13



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



# Rename
def renameFont(f, myDest):
	if f.info.fontName:
		myMenuname = f.info.menuName
	
		myFamilyname = myMenuname[:11]
		myStylename = myMenuname[11:]
		if myStylename == "Sc":
			myStylename = "SC"
		
		if f.info.styleName:
			if f.info.styleName == "Regular":
				myStylename = "Roman" + myStylename
				myFontstyle = 64
			else:
				myStylename = f.info.styleName + myStylename
				myFontstyle = 1
		
		f.info.familyName = myFamilyname
		f.info.fontStyle = myFontstyle
		f.info.styleName = myStylename
		f.info.fontName = myFamilyname + "-" + myStylename
		f.info.fullName = myFamilyname + " " + myStylename
		f.info.menuName = myFamilyname
		f.info.fondName = myFamilyname
		
		font = fl.font
		font.weight = "Regular"
		font.weight_code = 400
		font.width = "Medium (normal)"
	
		f.update()
		
		myPath = myDest + ":" + myFamilyname + "-" + myStylename + ".vfb"
		fl.font.Save(myPath)
		print myFamilyname + "-" + myStylename


	
# main loop
mySource = GetFolder()
myDest = GetFolder()

if mySource is not None:
	myFiles = collectSources(mySource)
	
	for myFile in myFiles:
		myFont = None
		try:
			myFont = OpenFont(myFile)
			renameFont(myFont, myDest)
			
		finally:
			if myFont is not None:
				myFont.close(False)

print "Done"
