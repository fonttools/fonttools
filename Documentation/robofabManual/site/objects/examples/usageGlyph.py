# robofab manual
#	Glyph object
#	Usage examples
# start using the current font

from robofab.world import CurrentGlyph
g = CurrentGlyph()

# suppose you've done the right imports
# different ways of creating glyphs
# a new empty glyph object
g = robofab.world.RGlyph()

# a new empty fontlab glyph object
g = robofab.objects.objectsFL.RGlyph()

# a new empty robofab glyph object
g = robofab.objects.objectsRF.RGlyph()

# the easiest way to get a new glyph
# is to ask a font to make you one:
g = aFontObject[glyphName]

