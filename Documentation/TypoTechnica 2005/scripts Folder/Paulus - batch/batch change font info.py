#FLM: Batch change font info

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

myID = 5116478

# main loop
mySource = GetFolder()
if mySource is not None:
	myFiles = collectSources(mySource)
	for myFile in myFiles:
		myrfFont = None
		try:
			myrfFont = OpenFont(myFile)
			myFont = fl.font
			
			# myFont.width="Medium (normal)"
			
			# myFamilyname = myFont.family_name
			# myFont.family_name = myFamilyname
			# myFont.font_name = myFont.family_name + "-" + myFont.style_name
			# myFont.full_name = myFont.family_name + " " + myFont.style_name
			# myFont.menu_name = myFont.family_name
			# myFont.apple_name = myFont.family_name + "-" + myFont.style_name
			
			# myFont.year=1999
			# myFont.copyright="Designed by Paul van der Laan.  Copyright (c) 1999 Type Invaders.  Flex is a trademark of Type Invaders.  Flex is protected by copyright law.  Unauthorized copying or modification of any of its data is illegal. Modified by TEFF for exclusive use by Van Dale Lexicografie bv, 2004."
			# myFont.notice=""
			
			# myFont.designer="Paul van der Laan"
			# myFont.designer_url="http://www.type-invaders.com"
			# myFont.vendor_url="http://www.type-invaders.com"
			
			# myFont.version_major = 0
			# myFont.version_minor = 97
			# myFont.version = "000.970"
			
			# myID = myFont.unique_id
			myFont.unique_id = myID
			myFont.fond_id = int(str(myID)[-4:])
			# myFont.vendor="INVD"
			
			myID = myID + 1
			
			# myFont.panose[0] = 2
			# myFont.panose[1] = 0
			# myFont.panose[2] = 5
			# myFont.panose[3] = 6
			# myFont.panose[4] = 2
			# myFont.panose[5] = 0
			# myFont.panose[6] = 0
			# myFont.panose[7] = 2
			# myFont.panose[8] = 0
			# myFont.panose[9] = 4
			
			# myFont.pcl_id = -1
			# myFont.vp_id = -1
			# myFont.ms_id= 2
			
			# myFont.upm = 1000
			# myFont.ascender[0] = 784
			# myFont.descender[0] = -240
			# myFont.cap_height[0] = 712
			# myFont.x_height[0] = 498
			
			# if myFont.style_name == "Italic":
				# myFont.italic_angle = 12.0
				# myFont.slant_angle = 0.0
			
			# myFont.underline_position=-100
			# myFont.underline_thickness=50
				
			# myFont.ms_charset=0
			# myFont.default_character="bullet"
			
			myrfFont.update()
			myrfFont.save()
		finally:
			if myrfFont is not None:
				myrfFont.close(False)
print "Done"
