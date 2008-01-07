# robofab manual
# 	Segment object
#	usage examples

f = OpenFont()

for c  in f:
	for contour in c:
		for segment in contour:
			print segment
 