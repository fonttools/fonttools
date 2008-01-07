# robofab manual
# 	Anchor object
#	attribute examples

c = CurrentGlyph()
if len(c.anchors) > 0:
	for a in c.anchors:
		print a.position    