#FLM: Interpolate in a new font

# Paul van der Laan, 2004/08/11

from robofab.world import SelectFont, CurrentFont, NewFont
from robofab.interface.all.dialogs import ProgressBar
import os.path

factor = .50

myMin = SelectFont('Select source font one:')
if myMin:
	myMax = SelectFont('Select source font two:')
	if myMax:
		# fl.CallCommand(fl_cmd.FileNew)
		myDest = NewFont()
		bar = ProgressBar('Interpolating...', len(myMin))
		for n in range (0,len(myMin)):
			myCharname = myMin[n].name
			myNewglyph = myDest.newGlyph(myCharname)
			myNewglyph.interpolate(factor, myMin[myCharname], myMax[myCharname])
			myDest[myCharname].mark = myMin[myCharname].mark
			myDest[myCharname].unicode = myMin[myCharname].unicode
			bar.tick()

		bar.close()
		myDest.update()
		
		myMinkern = myMin.kerning
		myMaxkern = myMax.kerning
		myDestkern = myDest.kerning
		myDestkern.interpolate(myMinkern,myMaxkern,factor,clearExisting=True)
		
		myNotice = `int(factor * 100)` + "% interpolatie van " + myMin.info.fontName + " en " + myMax.info.fontName
		myDest.info.notice=myNotice
		
		myDest.info.familyName = myMin.info.familyName
		myDest.info.styleName = "Interpol"
		myDest.info.fontName = myMin.info.familyName + "-Interpol"
		myDest.info.fullName = myMin.info.familyName + " Interpol"
		myDest.info.menuName = myMin.info.familyName
		myDest.info.fondName = myMin.info.familyName + "-Interpol"

		# myFont = fl.font
		# myEncoding= os.path.join(fl.path, r"Encoding", r"MACROMAN.ENC")
		# myFont.encoding.Load(myEncoding)

		myDest.update()
		
		print `int(factor * 100)` + "% interpolation of " + myMin.info.fontName + " and " + myMax.info.fontName
