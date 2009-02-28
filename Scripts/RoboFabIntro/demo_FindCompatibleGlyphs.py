#
#
#	make a list of which glyphs in this font could theoretically
#	interpolate with each other.
#
#


from robofab.world import CurrentFont
from robofab.pens.digestPen import DigestPointPen, DigestPointStructurePen

compatibles = {}

f = CurrentFont()
for c in f:
	p = DigestPointStructurePen()
	c.drawPoints(p)
	d = p.getDigest()
	if not compatibles.has_key(d):
		compatibles[d] = []
	compatibles[d].append(c.name)

print
print 'In %s, these glyphs could interpolate:'%(f.info.postscriptFullName)
for d, names in compatibles.items():
	if len(names) > 1:
		print ", ".join(names)