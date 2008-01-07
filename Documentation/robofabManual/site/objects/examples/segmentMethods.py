# robofab manual
# 	Segment object
#	method examples

f = OpenFont()

for c  in f:
	for contour in c:
		for segment in contour:
			segment.move((50, 25))