#FLM: Export kerning naar tagged text OT

from robofab.world import CurrentFont
from robofab.interface.all.dialogs import GetFolder, ProgressBar

myFont = CurrentFont()
myKerning = myFont.kerning
myFontfam = myFont.info.familyName
myFontstyle = myFont.info.styleName

myPath = GetFolder()

if myPath:
	myPath += ":" + myFontfam + "-" + myFontstyle + "_kern.txt"
		
	myFile = open(myPath, "w")
	myFile.write("<ASCII-MAC>" + chr(10))
	myFile.write("<vsn:2.000000><fset:InDesign-Roman><ctable:=<Black:COLOR:CMYK:Process:0.000000,0.000000,0.000000,1.000000>>" + chr(10))
	
	myBar = ProgressBar('Exporting kerning...', len(myKerning))
	for myPair in myKerning:
		myComb = str(myPair).split()
		myLeft=myComb[0][2:-2]
		myRight=myComb[1][1:-2]
		myLeftid = myFont[myLeft].index
		myRightid = myFont[myRight].index
		
		myLine = "<pstyle:><pga:BaseLine><ct:" + myFontstyle + "><cs:11.000000><cl:14.100000><cf:" + myFontfam + "><pSG:" + str(myLeftid) + "><0xFFFD><pSG:><pSG:" + str(myRightid) + "><0xFFFD><pSG:><ct:><cs:><cl:><cf:><ct:Regular><cs:5.000000><cl:14.100000><cf:Andale Mono>  " + str(myKerning[myPair]) + chr(10) + "<ct:><cs:><cl:><cf:><pga:>"
		myFile.write(myLine)
		myBar.tick()
	myFile.close()
	myBar.close()
	print "Generated kerning file for", myFontfam, myFontstyle
print "Done"
