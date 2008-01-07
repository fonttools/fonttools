#FLM: Batch font report

from robofab.interface.all.dialogs import GetFolder
from robofab.world import OpenFont, CurrentFont
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
myFolder = GetFolder()
myPath = myFolder + ":fontreport.txt"


myRecord = ["Filename", "Glyphs", "Kerning pairs", "Family name", "Weight", "Weight code", "Width", "Style", "Style name", "Font name", "Full name", "Menu name", "FOND name", "OT Family name", "OT Style name" ,"OT Mac name", "Year", "Copyright", "Trademark", "Notice", "Designer", "Designer URL", "Vendor URL", "Version", "Revision", "Version", "TrueType version", "TrueType unique ID", "Type 1 unique ID", "TrueType vendor", "PANOSE", "PCL ID", "VP ID", "MS ID", "UPM", "Ascender", "Descender", "Cap height", "X height", "Italic angle", "Slant angle", "Underline", "Thickness", "Monospaced", "MS Charset", "Default char", "Mac FOND ID", "Blue fuzz", "Blue scale", "Blue shift", "Blue values", "Other blues", "Family blues", "Other family blues", "Force bold", "Horizontal stems", "Vertical stems"]

myLen=len(myRecord)

myFile = open(myPath, "w")
for myItem in myRecord:
	myFile.write(str(myItem + "\t"))
myFile.write("\r")
myFile.close()

if myFolder is not None:
	myFiles = collectSources(myFolder)
	
	for mySourcefile in myFiles:
		myflFont = None
		try:
			myrfFont = OpenFont(mySourcefile)
			myflFont = fl.font
			
			for x in range(myLen):
				myRecord[x]=""

			if myflFont.file_name:
				myFilename = str(myflFont.file_name).split(":")
				myRecord[0] = myFilename[-1]
			myRecord[1] = str(len(myflFont))
			myRecord[2] = str(len(myrfFont.kerning.keys()))
			
			if myflFont.family_name: myRecord[3] = str(myflFont.family_name)
			if myflFont.weight: myRecord[4] = str(myflFont.weight)	
			myRecord[5] = str(myflFont.weight_code)	
			if myflFont.width: myRecord[6] = str(myflFont.width)
			myRecord[7] = str(myflFont.font_style)
				# 1=italic, 32=bold, 64=regular
			if myflFont.style_name: myRecord[8] = str(myflFont.style_name)	
			if myflFont.font_name: myRecord[9] = str(myflFont.font_name)
			if myflFont.full_name: myRecord[10] = str(myflFont.full_name)
			if myflFont.menu_name: myRecord[11] = str(myflFont.menu_name)
			if myflFont.apple_name: myRecord[12] = str(myflFont.apple_name)
			
			if myflFont.pref_family_name: myRecord[13] = str(myflFont.pref_family_name)
			if myflFont.pref_style_name: myRecord[14] = str(myflFont.pref_style_name)
			if myflFont.mac_compatible: myRecord[15] = str(myflFont.mac_compatible)
			
			myRecord[16] = str(myflFont.year)
			if myflFont.copyright: myRecord[17] = str(myflFont.copyright)
			if myflFont.trademark: myRecord[18] = str(myflFont.trademark)
			if myflFont.notice: myRecord[19] = str(myflFont.notice)
			
			if myflFont.designer: myRecord[20] = str(myflFont.designer)
			if myflFont.designer_url: myRecord[21] = str(myflFont.designer_url)
			if myflFont.vendor_url: myRecord[22] = str(myflFont.vendor_url)
			
			myRecord[23] = str(myflFont.version_major)
			myRecord[24] = str(myflFont.version_minor)
			if myflFont.version: myRecord[25] = str(myflFont.version)
			if myflFont.tt_version: myRecord[26] = str(myflFont.tt_version)
			
			if myflFont.tt_u_id: myRecord[27] = str(myflFont.tt_u_id)
			myRecord[28] = str(myflFont.unique_id)
			if myflFont.vendor: myRecord[29] = str(myflFont.vendor)
			
			if myflFont.panose: myRecord[30] = str(myflFont.panose)
			
			myRecord[31] = str(myflFont.pcl_id)
			myRecord[32] = str(myflFont.vp_id)
			myRecord[33] = str(myflFont.ms_id)
			
			myRecord[34] = str(myflFont.upm)
			
			myRecord[35] = str(myflFont.ascender[0])
			myRecord[36] = str(myflFont.descender[0])
			myRecord[37] = str(myflFont.cap_height[0])
			myRecord[38] = str(myflFont.x_height[0])
			myRecord[39] = str(myflFont.italic_angle)
			myRecord[40] = str(myflFont.slant_angle)
			myRecord[41] = str(myflFont.underline_position)
			myRecord[42] = str(myflFont.underline_thickness)
			myRecord[43] = str(myflFont.is_fixed_pitch)
			
			myRecord[44] = str(myflFont.ms_charset)
			if myflFont.default_character: myRecord[45] = str(myflFont.default_character)
			myRecord[46] = str(myflFont.fond_id)
			
			myRecord[47] = str(myflFont.blue_fuzz[0])
			myRecord[48] = str(myflFont.blue_scale[0])
			myRecord[49] = str(myflFont.blue_shift[0])
			myRecord[50] = str(myflFont.blue_values[0])
			myRecord[51] = str(myflFont.other_blues[0])
			myRecord[52] = str(myflFont.family_blues[0])
			myRecord[53] = str(myflFont.family_other_blues[0])
			myRecord[54] = str(myflFont.force_bold[0])
			myRecord[55] = str(myflFont.stem_snap_h[0])
			myRecord[56] = str(myflFont.stem_snap_v[0])
			
			myFile = open(myPath, "r+")
			myFile.seek(0,2)
			for myItem in myRecord:
				myFile.write(str(myItem + "\t"))
			myFile.write("\r")
			myFile.close()

		finally:
			if myrfFont is not None:
				myrfFont.close(False)

print "Done"
