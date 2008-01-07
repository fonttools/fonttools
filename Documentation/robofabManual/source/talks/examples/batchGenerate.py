# robothon 2006
# batch generate

from robofab.world import AllFonts

for font in AllFonts():
	font.generate('otfcff')
