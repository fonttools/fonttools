# FLM: Make Cameo Font

"""Make a cameo font. Pretty simple."""

from robofab.world import CurrentFont
from robofab.interface.all.dialogs import Message

buffer = 30
scaleValue = .9

f = CurrentFont()
# clear all kerning
f.kerning.clear()
#determine top and bottom of the box
t = f.info.unitsPerEm + f.info.descender + buffer
b = f.info.descender - buffer
#first decompose any components
for g in f:
	g.decompose()
#then proceed with the cameo operation
for g in f:
	#catch negative sidebearings
	if g.leftMargin < 0:
		g.leftMargin = 0
	if g.rightMargin < 0:
		g.rightMargin = 0
	#scale the glyph and sidebearings
	leftMargin = int(round((g.rightMargin * scaleValue) + buffer))
	rightMargin = int(round((g.rightMargin * scaleValue) + buffer))
	g.scale((scaleValue, scaleValue), (int(round(g.width/2)), 0))
	g.leftMargin = leftMargin
	g.rightMargin = rightMargin
	#determine the left and the right of the box
	l = 0
	r = g.width
	#draw the box using flPen
	p = g.getPen()
	p.moveTo((l, b))
	p.lineTo((l, t))
	p.lineTo((r, t))
	p.lineTo((r, b))
	p.closePath()
	#correct path direction
	g.correctDirection()
	#update the glyph
	g.update()
#update the font
f.update()
#tell me when it is over
Message('The highly complex "Cameo Operation" is now complete. Please examine the results and be thankful that RoboFab is on your side.')