# robothon06
# interpolate two glyphs in the same font a bunch of times
from robofab.world import CurrentFont
f = CurrentFont()
for i in range(0, 10):
	factor = i*.1
	name = "result_%f"%factor
	print "interpolating", name
	f[name].interpolate(factor, f["A"], f["B"])
f.update()