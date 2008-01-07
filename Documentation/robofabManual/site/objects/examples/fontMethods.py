# robofab manual
# 	Font object
#	method examples
from robofab.world import CurrentFont
f = CurrentFont()

# the keys() method returns a list of glyphnames:
print f.keys()

# find unicodes for each glyph by using the postscript name:
f.autoUnicodes()
