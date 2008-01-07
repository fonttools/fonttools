#FLM: Export glyphs naar tagged text OT

from robofab.world import CurrentFont
from robofab.interface.all.dialogs import GetFolder, ProgressBar

mySize = 44.0
myLeading = 48.0

myFont = CurrentFont()
myFontfam = myFont.info.otFamilyName
myFontstyle = myFont.info.otStyleName

myPagebreak = ""
myPath = GetFolder()

if myPath:
	myPath += ":" + myFontfam + "-" + myFontstyle + ".txt"

	myFile = open(myPath, "w")
	try:
		myFile.write("<ASCII-MAC>" + chr(10))
		myFile.write("<vsn:2.000000><fset:InDesign-Roman><ctable:=<Black:COLOR:CMYK:Process:0.000000,0.000000,0.000000,1.000000>>" + chr(10))
		
		myLine = myPagebreak + "<pstyle:><ct:Regular><cs:6.000000><cl:12.000000><cf:Andale Mono>" + myFontfam + "-" + myFontstyle + " glyph overview, generated 26 10 2004<cf:><cl:><cs:><ct:>" + chr(10) + "<pstyle:><ct:Regular><cs:6.000000><cl:12.000000><cf:Andale Mono>Version " + str(myFont.info.versionMajor) + "." + str(myFont.info.versionMinor) + ", designed by " + myFont.info.designer + ", " + str(myFont.info.year) + ".<cf:><cl:><cs:><ct:>" + chr(10) + "<pstyle:><ct:Regular><cs:9.000000><cl:14.000000><cf:Andale Mono><cf:><cl:><cs:><ct:>"  + chr(10) + "<pstyle:><cs:" + str(mySize) + "><cl:" + str(myLeading) + "><cf:TEFF><ct:Pi> | <ct:><cf:>"
		myFile.write(myLine)
		
		myBar = ProgressBar('Exporting glyphs...', len(myFont))
		for myGlyph in range(1,len(myFont)):
			myLine = "<cf:" + myFontfam + "><ct:" + myFontstyle + "><pSG:" + str(myGlyph) + "><0xFFFD><pSG:><ct:><cf:><cf:TEFF><ct:Pi>| |<ct:><cf:>"
			myFile.write(myLine)
			myBar.tick()
		myFile.write("<cl:><cs:>")
		myPagebreak = "<cnxc:Page>"
		myFile.close()
		myBar.close()
		print "Generated glyph overview for", myFontfam + "-" + myFontstyle
	except:
		myFile.close()
		print "An error occurred"
print "Done"
