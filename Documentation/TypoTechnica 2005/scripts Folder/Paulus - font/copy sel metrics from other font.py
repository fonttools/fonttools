#FLM: Copy selected sidebearings from other font

from robofab.world import CurrentFont, SelectFont
from robofab.interface.all.dialogs import ProgressBar

myDestination = CurrentFont()
myGlyphs = myDestination.selection

myFont = SelectFont("Select source font")

if myFont is not None:
	bar = ProgressBar('Copying sidebearings...', len(myGlyphs))
	for myChar in myGlyphs:
		if myFont.has_key(myChar):
			myDestination[myChar].leftMargin = myFont[myChar].leftMargin
			myDestination[myChar].rightMargin = myFont[myChar].rightMargin
			# myDestination[myChar].width = myFont[myChar].width
			myDestination[myChar].mark = 26
			bar.tick()
			
	myDestination.update()
	bar.close()
