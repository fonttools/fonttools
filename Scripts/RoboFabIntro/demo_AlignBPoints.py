#FLM: Align Two Nodes

"""Align bPoints horizontally, vertically or both."""

from robofab.world import CurrentGlyph
from robofab.interface.all.dialogs import TwoChecks

glyph = CurrentGlyph()

sel = []

#gather selected bPoints
for contour in glyph.contours:
	if contour.selected:
		for bPoint in contour.bPoints:
			if bPoint.selected:
				sel.append(bPoint)
				
if len(sel) != 0:
	xL = []
	yL = []
	
	#store up all coordinates for use later
	for bPoint in sel:
		x, y = bPoint.anchor
		xL.append(x)
		yL.append(y)
	
	if len(xL) > 1:
		w = TwoChecks("Horizontal", "Vertical", 0, 0)
		if w == None or w == 0:
			#the user doesn't want to align anything
			pass
		else:
			#find the center among all those bPoints
			minX = min(xL)
			maxX = max(xL)
			minY = min(yL)
			maxY = max(yL)
			cX = int(round((minX + maxX)/2))
			cY = int(round((minY + maxY)/2))
			
			#set the undo
			fl.SetUndo()
			
			#determine what the user wants to do
			noY = False
			noX = False
			if w == 1:
				#the user wants to align y
				noX = True
			elif w == 2:
				#the user wants to align x
				noY = True
			elif w == 3:
				#the user wants to align x and y
				pass
			
			
			for bPoint in sel:
				#get the move value for the bPoint
				aX, aY = bPoint.anchor
				mX = cX - aX
				mY = cY - aY
				if noY:
					#don't move the y
					mY = 0
				if noX:
					#don't move the x
					mX = 0
				bPoint.move((mX, mY))
			glyph.update()
