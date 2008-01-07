# robofab manual
#	Glyph object
#	method examples

# get a glyph object from a font
f = CurrentFont()
g = f["A"]
print g

# move the glyph 10 units to the right, and 200 units up:
g = f["a"]
g.move((10, 200))
