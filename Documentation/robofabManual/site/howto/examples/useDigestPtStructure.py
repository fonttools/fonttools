# robofab manual
# 	Usepens howto
#	DigestPointStructurePen examples


from robofab.world import OpenFont
from robofab.pens.digestPen import DigestPointStructurePen

f = OpenFont()
myPen = DigestPointStructurePen()

f['period'].drawPoints(myPen)
print myPen.getDigest()
