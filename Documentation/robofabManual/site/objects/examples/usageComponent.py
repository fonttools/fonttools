# the easiest way to get to a component
# is to get one from a glyph
from robofab.world import CurrentFont
f = CurrentFont()
g = f['adieresis']
for c in g.components:
	print c