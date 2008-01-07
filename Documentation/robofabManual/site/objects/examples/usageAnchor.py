# robofab manual
# 	Anchor object
#	usage examples

f = CurrentFont()
for c  in f:
	if len(c.anchors) > 0:
		print c, c.anchors