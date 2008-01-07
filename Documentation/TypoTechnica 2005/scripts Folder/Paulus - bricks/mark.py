from robofab.world import CurrentFont

myFont = CurrentFont()

mySel = myFont.selection

for myGlyph in mySel:
	myFont[myGlyph].mark = 12
myFont.update()