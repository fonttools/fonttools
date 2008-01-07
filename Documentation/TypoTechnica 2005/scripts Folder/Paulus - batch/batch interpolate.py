#FLM: Batch interpolate

# Paul van der Laan, 2004/08/11

from robofab.world import SelectFont, CurrentFont
from robofab.interface.all.dialogs import ProgressBar, GetFolder

myFolder = GetFolder()
# myPars = ((.21, "ExtraLight", 200), (.55, "Light", 300)) # Kievit factor, weight, weightcode
myPars = ((.36, "Medium", 500), (.63, "Bold", 700)) # Flex factor, weight, weightcode


myMin = SelectFont('Select source font one:')
if myMin:
	myMax = SelectFont('Select source font two:')
	if myMax:
	
		for myInterpol in myPars:
		
			myFactor = myInterpol[0]
			myWeight = myInterpol[1]
			myWeightcode = myInterpol[2]
			myFamilyname = myMin.info.familyName # "Flex"
			
			fl.CallCommand(fl_cmd.FileNew)
			myDest = CurrentFont()
			bar = ProgressBar('Interpolating...', len(myMin))
			for myChar in myMin:
				myCharname = myChar.name
				myNewglyph = myDest.newGlyph(myCharname)
				myNewglyph.interpolate(myFactor, myMin[myCharname], myMax[myCharname])
				# myDest[myCharname].mark = 26
				bar.tick()
			bar.close()
			myDest.update()
			
			myMinkern = myMin.kerning
			myMaxkern = myMax.kerning
			myDestkern = myDest.kerning
			myDestkern.interpolate(myMinkern,myMaxkern,myFactor,clearExisting=True)
			
			myDest.info.familyName = myFamilyname
			fl.font.weight = myWeight
			fl.font.weight_code = myWeightcode
			myStylename = myWeight + myMin.info.styleName[-3:]
			myDest.info.styleName = myStylename
			myDest.info.fontName = myMin.info.familyName + "-" + myStylename
			myDest.info.fullName = myMin.info.familyName + " " + myStylename
			myDest.info.menuName = myMin.info.familyName
			myDest.info.fondName = myMin.info.familyName + "-" + myStylename
	
			myDest.info.year = 1999
			# myDest.info.copyright = u"2001 Mike Abbink. Produced by Type Invaders"
			myDest.info.designer = "Paul van der Laan"
			
			fl.font.upm = 1000
			fl.font.ascender[0] = 730
			fl.font.descender[0] = -270
			fl.font.x_height[0] = 480
			fl.font.cap_height[0] = 616
			fl.font.default_character = "bullet"
			
			myEncoding= os.path.join(fl.path, r"Encoding", r"MACROMAN.ENC")
			fl.font.encoding.Load(myEncoding)
			
			myDest.update()
			
			myPath = myFolder + ":" + myFamilyname + "-" + myStylename + ".vfb"
			fl.font.Save(myPath)
			print myFamilyname + "-" + myStylename
			myDest.close(False)


print "Done"
