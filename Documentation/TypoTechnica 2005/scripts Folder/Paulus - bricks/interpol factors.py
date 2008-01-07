stems = [85, 106, 133,152]

minstem = 73.0
maxstem = 180.0

print ""
for stem in stems:
	print 100/(maxstem-minstem) * (stem-minstem)
print ""