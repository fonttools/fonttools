# robofab manual
# Font object
#	attribute examples

# Most useful attributes of RFont are
# actually stored in <a href="objects/info.html">RFont.info</a>
f = CurrentFont()
print f.info.unitsPerEm

# kerning data is available in the kerning object:
print f.kerning

# len() gives you the "length" of the font, i.e. the number of glyphs
print "glyphs in this font:", len(f)

# treat a font object as a dictionary to get to the glyphs
print f["A"]
