# robothon06
# set basic attributes in a glyph

from robofab.world import CurrentFont

font = CurrentFont()
glyph = font['A']
glyph.width = 200
print glyph.width
glyph.leftMargin = 50
print glyph.leftMargin
glyph.rightMargin = 50
print glyph.rightMargin

glyph.unicode = 666
print glyph.unicode

glyph.update()

