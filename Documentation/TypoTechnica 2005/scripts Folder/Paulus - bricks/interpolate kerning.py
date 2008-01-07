from robofab.world import SelectFont, CurrentFont
from robofab.interface.all.dialogs import ProgressBar

myFactor = .36

myMin = SelectFont('Select source font one:')
if myMin:
	myMax = SelectFont('Select source font two:')
	if myMax:
		myDest = SelectFont('Select destination font:')
		if myDest:
			myMinkern = myMin.kerning
			myMaxkern = myMax.kerning
			myDestkern = myDest.kerning
			
			myDestkern.interpolate(myMinkern,myMaxkern,myFactor,clearExisting=True)
	
			myDest.update()
			
print "Done"
