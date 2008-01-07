#FLM: Batch win rename Kievit

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

		f.info.fontStyle=64
		myStylename="Regular"
		
		myStyle = f.info.styleName
		if "Italic" in myStyle:
			myStyle = myStyle.replace("Italic", "")
			myStylename = "Italic"
			f.info.fontStyle = 1
		
		myFamilyname = f.info.familyName + myStyle
				
		f.info.familyName = myFamilyname
		f.info.styleName = myStylename
		f.info.fontName = myFamilyname + "-" + myStylename
		f.info.fullName = myFamilyname + " " + myStylename
		f.info.menuName = myFamilyname
		f.info.fondName = myFamilyname
		
		font = fl.font
		font.width = "Medium (normal)"
		font.tt_version = "Version 1.000 2001 initial release"
		font.tt_u_id = "INVD: " + myFamilyname + " " + myStylename + ": 2001"
		font.vendor = "INVD"
		myFont.panose[0] = 2
		myFont.panose[1] = 11
		myFont.panose[2] = 0
		myFont.panose[3] = 0
		myFont.panose[4] = 0
		myFont.panose[5] = 0
		myFont.panose[6] = 0
		myFont.panose[7] = 0
		myFont.panose[8] = 0
		myFont.panose[9] = 0
		font.ms_id = 2
		
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
