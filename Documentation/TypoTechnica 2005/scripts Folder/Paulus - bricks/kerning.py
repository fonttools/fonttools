from robofab.world import CurrentFont

myFont = CurrentFont()
myKerning = myFont.kerning

for myPair in myKerning:
	myComb = str(myPair).split()
	myComb = "%s %s" %(myComb[0][2:-2], myComb[1][1:-2])
	print myComb,myKerning[myPair]
