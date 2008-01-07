# robofab manual
# 	Usepens howto
#	usage examples


from robofab.world import CurrentFont
f = CurrentFont()
newGlyph = f.newGlyph('demoDrawGlyph', clear=True)
newGlyph.width = 1000

# hey, what's this:
pen = newGlyph.getPen()
# ha! a sneaky way to get a pen object!

pen.moveTo((100, 100))
pen.lineTo((800, 100))
pen.curveTo((1000, 300), (1000, 600), (800, 800))
pen.lineTo((100, 800))
pen.lineTo((100, 100))
pen.closePath()

newGlyph.update()
f.update()
