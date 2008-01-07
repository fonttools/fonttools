# glyphmath example, using glyphs in math
# in the test font: two interpolatable, different glyphs
# on positions A and B.

from robofab.world import CurrentFont
f = CurrentFont()

# glyphmath
a = f["A"]
b = f["B"]

# multiply works as scaling up
d = a * 2
#or
d = 2 * a
f.insertGlyph(d, as="A.A_times_2")

# division works as scaling down
d = a / 2
f.insertGlyph(d, as="A.A_divide_2")

# addition: add coordinates of each point
d = a + b
f.insertGlyph(d, as="A.A_plus_B")

# subtraction: subtract coordinates of each point
d = a - b
f.insertGlyph(d, as="A.A_minus_B")

# combination: interpolation!
d = a + .5 * (b-a)
f.insertGlyph(d, as="A.A_interpolate_B")

f.update()