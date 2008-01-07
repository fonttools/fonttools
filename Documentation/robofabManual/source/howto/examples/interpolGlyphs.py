# robofab manual
# 	Interpolate howto
#	Interpolating glyphs examples


from robofab.world import CurrentFont
f = CurrentFont()
g = f.newGlyph("interpolated")
g.interpolate(.5, f["a"], f["b"]
# if you're in fontlab:
g.update()
