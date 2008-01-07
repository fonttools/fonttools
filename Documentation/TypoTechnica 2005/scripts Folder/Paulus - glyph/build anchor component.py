#FLM: Build anchor for components

from robofab.world import CurrentGlyph

myGlyph=CurrentGlyph()

#if len(myGlyph.anchors) == 0:
#	myGlyph.appendAnchor("nieuw", (50, 50))

myGlyph.appendAnchor("nieuw", (50, 50))

myGlyph.anchors[-1].name = "bottom"
myGlyph.anchors[-1].x = (myGlyph.box[2]+myGlyph.box[0])/2
myGlyph.anchors[-1].y = 0
myGlyph.update()