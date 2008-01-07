# robofab manual
#	Glyph object
#	method examples

#	In FontLab the baseglyph of a component can't be changed easily.
#	This assumes that there will only be
#	one component that needs to be remapped.

def remapComponent(glyph, oldBaseGlyph, newBaseGlyph):
	foundComponent = None
	for component in glyph.components:
		if component.baseGlyph = oldBaseGlyph:
			foundComponent = component
			break
	if foundComponent is None:
		return
	offset = foundComponent.offset
	scale = foundComponent.scale
	glyph.removeComponent(component)
	glyph.appendComponent(newBaseGlyph, offset=offset, scale=scale)

