#FLM: Copy selected sidebearings to other font

from robofab.world import CurrentFont, SelectFont
from robofab.interface.all.dialogs import ProgressBar

myFont = CurrentFont()
myGlyphs = myFont.selection

myDestination = SelectFont("Select destination font")

if myDestination is not None:
	bar = ProgressBar('Copying sidebearings...', len(myGlyphs))
	for myChar in myGlyphs:
		if myDestination.has_key(myChar):
			myDestination[myChar].leftMargin = myFont[myChar].leftMargin
			# myDestination[myChar].rightMargin = myFont[myChar].rightMargin
			myDestination[myChar].width = myFont[myChar].width
			myDestination[myChar].mark = 26
			bar.tick()
			
	myDestination.update()
	bar.close()
