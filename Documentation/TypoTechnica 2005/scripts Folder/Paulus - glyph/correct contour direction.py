#FLM: Correct contour directions

from robofab.world import CurrentGlyph

glyph = CurrentGlyph()

glyph.correctDirection()
glyph.update()

print "Done"
