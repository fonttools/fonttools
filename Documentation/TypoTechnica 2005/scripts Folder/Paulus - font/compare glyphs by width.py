#FLM: Compare glyphs by width

from robofab.world import SelectFont, CurrentFont
from robofab.interface.all.dialogs import ProgressBar

myFont = CurrentFont()
myComparison = SelectFont("Select comparison font")

if myComparison is not None:
	bar = ProgressBar('Comparing fonts...', len(myFont))
	for myChar in myFont:
		myCharname = myChar.name
		if myComparison.has_key(myCharname):
			if myChar.width <> myComparison[myCharname].width:
				myFont[myCharname].mark = 26
	bar.tick()
	
	myFont.update()
	bar.close()

# mark: red=1, blue=170, green=80, magenta=210, cyan=130
