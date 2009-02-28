#FLM: RoboFab Intro, Kerning

#
#
#	demo of RoboFab kerning.
#
#

# NOTE: this will mess up the kerning in your test font.

from robofab.world import CurrentFont

# (make sure you have a font with some kerning opened in FontLab)

f = CurrentFont()

# If you are familiar with the way RoboFog handled kerning,
# you will feel right at home with RoboFab's kerning implementation.
# As in RoboFog, the kerning object walks like a dict and talks like a
# dict, but it's not a dict. It is a special object that has some features
# build specifically for working with kerning. Let's have a look!

kerning = f.kerning
# A general note about use the kerning object in FontLab. In FontLab, kerning
# data lives in individual glyphs, so to access it at the font level we must go
# through every glyph, gathering kerning pairs as we go. This process occurs
# each time you call font.kerning. So, to speed thinks up, it is best to reference
# it with an assignment. This will keep it from being generated every time you
# you call and attribute or make a change.

# kerning gives you access to some bits of global data
print "%s has %s kerning pairs"%(f.info.postscriptFullName, len(kerning))
print "the average kerning value is %s"%kerning.getAverage()
min, max = kerning.getExtremes()
print "the largest kerning value is %s"%max
print "the smallest kerning value is %s"%min
# ok, kerning.getExtremes() may be a little silly, but it could have its uses.

# kerning pairs are accesed as if you are working with a dict.
# (left glyph name, right glyph name)
kerning[('V', 'o')] = -14
print '(V, o)', kerning[('V', 'o')]

# if you want to go through all kerning pairs:
for pair in kerning:
	print pair, kerning[pair]

# kerning also has some useful methods.  A few examples:
# scale all kerning!
print 'scaling...'
kerning.scale(100)
print "the average kerning value is %s"%kerning.getAverage()
min, max = kerning.getExtremes()
print "the largest kerning value is %s"%max
print "the smallest kerning value is %s"%min
# get a count of pairs that contian certain glyphs
print 'counting...'
count = kerning.occurrenceCount(['A', 'B', 'C'])
for glyphName in count.keys():
	print "%s: found in %s pairs"%(glyphName, count[glyphName])

# don't forget to update the font after you have made some changes!
f.update()

