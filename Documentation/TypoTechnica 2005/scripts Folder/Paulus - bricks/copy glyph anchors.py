
from robofab.world import SelectFont, CurrentFont
from robofab.interface.all.dialogs import ProgressBar

mySource = SelectFont('Select source font:')
if mySource:
	myDest = SelectFont('Select destination font:')
	if myDest:
		for myGlyph in mySource:
			myGlyphname=myGlyph.name
			if len(mySource[myGlyphname].anchors) > 0:
				myDestglyph = myDest[myGlyphname]
				if len(myDestglyph.anchors) == 0:
					myDestglyph.appendAnchor("nieuw", (50, 50))
				myDestglyph.anchors[0].name = myGlyph.anchors[0].name
				myDestglyph.anchors[0].x = myGlyph.anchors[0].x
				myDestglyph.anchors[0].y = myGlyph.anchors[0].y
				myDestglyph.mark = 26
				myDestglyph.update()