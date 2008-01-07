#FLM: Interpolate in current font

# Interpolate selected glyphs in the current font 
# Paul van der Laan, 2004/08/12

from robofab.world import SelectFont, CurrentFont
from robofab.interface.all.dialogs import ProgressBar

factor = 1.37
myFont = CurrentFont()
myGlyphs = myFont.selection

myMin = SelectFont('Select source font one:')
if myMin:
	myMax = SelectFont('Select source font two:')
	if myMax:
		bar = ProgressBar('Interpolating...', len(myGlyphs))
		for myChar in myGlyphs:
			myFont.removeGlyph(myChar)
			myNewglyph = myFont.newGlyph(myChar)
			myNewglyph.interpolate(factor, myMin[myChar], myMax[myChar])
			myFont[myChar].mark = 26
			bar.tick()

		bar.close()
		myFont.update()
