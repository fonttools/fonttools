# robofab manual
# Font object
#	method examples, available in FontLab
from robofab.world import CurrentFont
f = CurrentFont()

# the keys() method returns a list of glyphnames:
print f.selection

# generate font binaries
f.generate('otfcff')