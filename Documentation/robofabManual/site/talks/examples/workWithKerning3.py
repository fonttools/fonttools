# robothon06
# work with kerning 3
# print a specific set of pairs

from robofab.world import CurrentFont
font = CurrentFont()
kerning = font.kerning
for left, right in kerning.keys():
	if kerning[(left, right)] < -100:
		print left, right, kerning[(left, right)]
