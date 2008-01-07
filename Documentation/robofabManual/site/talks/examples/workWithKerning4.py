# robothon06
# work with kerning 4
from robofab.world import CurrentFont
font = CurrentFont()
kerning = font.kerning
for left, right in kerning.keys():
	if left == "acircumflex":
		print left, right, kerning[(left, right)]

