#FLM: Copy sidebearings to other font

from robofab.world import SelectFont
from robofab.interface.all.dialogs import ProgressBar

mySource = SelectFont("Select source font")
myDestination = SelectFont("Select destination font")

if mySource is not None and myDestination is not None:
	bar = ProgressBar('Copying sidebearings...', len(mySource))
	for myChar in mySource:
		myCharname = myChar.name
		if myDestination.has_key(myCharname):
			myDestination[myCharname].leftMargin = myChar.leftMargin
			myDestination[myCharname].rightMargin = myChar.rightMargin
			myDestination[myCharname].mark = 26
			bar.tick()
			
	myDestination.update()
	bar.close()
