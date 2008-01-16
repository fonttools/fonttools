#FLM: Make Kerning Proof of selection

"""Generate an InDesign 2.0 tagged text file
for every possible glyph combination in the current font."""

from robofab.tools.proof import IDTaggedText
from robofab.world import CurrentFont

f = CurrentFont()

fontSize = 36

id = IDTaggedText(f.info.familyName, f.info.styleName, size=fontSize)

names = f.selection
names.sort()

for l in names:
	left = f[l]
	for r in names:
		right = f[r]
		id.addGlyph(left.index)
		id.addGlyph(right.index)
		id.add(' ')
	print 'finished all pairs starting with', left.name

from robofab.interface.all.dialogs import PutFile
path = PutFile("Save the tagged file:", "KerningProofTags.txt")
if path:
	id.save(path)

