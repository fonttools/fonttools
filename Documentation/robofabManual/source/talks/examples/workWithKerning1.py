# robothon06
# work with kerning 1

from robofab.world import CurrentFont
font = CurrentFont()

# now the kerning object is generated once
kerning = font.kerning

# and ready for your instructions.
print kerning
print len(kerning)
print kerning.keys()

# proceed to work with the myKerning object
# this happens in the following examples too.