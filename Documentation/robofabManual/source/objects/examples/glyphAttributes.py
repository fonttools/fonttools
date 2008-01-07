# robofab manual
#	Glyph object
#	attribute examples

from robofab.world import CurrentFont, CurrentGlyph
f = CurrentFont()

# create a glyph object by asking the font
g = f["Adieresis"]

# alternatively, create a glyph object for the current glyph
g = CurrentGlyph()

# get the width
print g.width

# get the name
print g.name

# a  list of unicode values for this glyph. Can be more than 1!
print g.unicodes

# set the width
g.width = 1000
print g.width

# get the number of contours in a glyph
# by getting  its length
print len(g)
