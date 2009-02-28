from robofab.world import AllFonts

print "Compare all fonts in the  AllFonts list with each other:"


af = AllFonts()

results = []
line = []
for n in af:
	line.append(`n.info.postscriptFullName`)
results.append(line)

for i in range(len(af)):
	one = af[i]
	line = []
	line.append(af[i].info.postscriptFullName)
	for j in range(len(af)):
		other = af[j]
		line.append(`one==other`)
		if one == other:
			print "same: ", one.path, other.path
	results.append(line)

for n in results:
	print n
	
	