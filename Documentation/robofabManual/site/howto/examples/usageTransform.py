# robofab manual
# 	Usetransformations howto
#	usage examples


from fontTools.misc.transform import Identity
from robofab.world import CurrentFont

m = Identity
print m

m = m.rotate(math.radians(20))
print m

f = CurrentFont()
for c in f:
	c.transform(m)
	c.update()