# robothon06
# iterate through a glyph's contours

from robofab.world import CurrentFont

font = CurrentFont()

glyph = font["A"]
print glyph.getParent()

