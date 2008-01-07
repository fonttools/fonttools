# robothon06
# interpolate two glyphs in the same font
from robofab.world import CurrentFont
f = CurrentFont()
factor = 0.5
f["C"].interpolate(factor, f["A"], f["B"])
f["C"].update()
