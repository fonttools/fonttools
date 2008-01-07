# robofab manual
# Buildingaccents howto
#	attribute examples


# a script to generate all necessary accented characters.
# this assumes all anchor points are set correctly.
# including doublelayer accents. so, add anchorpoints 
# on the accents too!
# (c) evb

from robofab.world import CurrentFont
from robofab.tools.toolsAll import readGlyphConstructions

f = CurrentFont()

import string

theList = [
	# caps
	'AEacute',
	'AEmacron',
	'Aacute',
	'Abreve',
	# add all the accents you want in this list
]


con = readGlyphConstructions()
theList.sort()

def accentify(f, preflight=False):
	print 'start accentification', f.info.fullName
	slots = con.keys()
	slots.sort()
	for k in theList:
		if k[-3:] in [".sc"]:
			isSpecial = True
			tag = k[-3:]
			name = k[:-3]
		else:
			isSpecial = False
			tag = ""
			name = k
		parts = con.get(name, None)
		if parts is None:
			print k, "not defined?"
			continue
		base = parts[0]
		accents = parts[1:]
		f.generateGlyph(k, preflight=preflight)
		f[k].mark = 100 + randint(-20, 20)
		f[k].autoUnicodes()
		f[k].update()
	f.update()

accentify(f)
print 'done'

