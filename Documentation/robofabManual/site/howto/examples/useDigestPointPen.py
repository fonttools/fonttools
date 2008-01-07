# robofab manual
# 	Usepens howto
#	attribute examples


from robofab.world import OpenFont
from robofab.pens.digestPen import DigestPointPen

f = OpenFont()
myPen = DigestPointPen()

f['period'].drawPoints(myPen)
print myPen.getDigest()

