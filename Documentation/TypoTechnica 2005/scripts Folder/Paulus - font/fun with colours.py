#FLM: Fun with colours

from robofab.world import CurrentFont

myFont = CurrentFont()
myColour = 1

while 1:
	for myChar in myFont:
		myChar.mark = myColour
		myColour = myColour + 1
		if myColour == 256:
			myColour = 1
	myFont.update()

# mark: red=1, blue=170, green=80, magenta=210, cyan=130
