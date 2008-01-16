#FLM: RoboFab Intro, Font Groups

#
#
#	demo of RoboFab font groups
#
#

# RoboFab font objects have several objects associated with them
# kerning, info, groups, etc. Let's talk about groups. Groups are,
# well groups of glyph names. These can be useful for lots of things
# like kerning and OpenType features. The number of uses for
# groups is only limited by your imagination. Enough of this
# silly pep talk. Let's check it out.


from robofab.world import CurrentFont
# gString has lots of glyph lists, these two will be useful for this demo
from robofab.gString import uppercase_plain, lowercase_plain

# (you will need t have a font open in FontLab for this demo)
font = CurrentFont()

# First off, let's gather up some glyph names.
# gString's uppercase_plain and lowercase_plain
# lists will do for now. Let's go through these lists
# and see if they contain any glyphs that are in this font.
uppercase = []
lowercase = []
for glyphName in uppercase_plain:
	if font.has_key(glyphName):
		uppercase.append(glyphName)
for glyphName in lowercase_plain:
	if font.has_key(glyphName):
		lowercase.append(glyphName)
uppercase.sort()
lowercase.sort()

# And, we'll combine the uppercase glyph names and
# lowercase glyph names that we found into one list
both = uppercase + lowercase
both.sort()

# Just for kicks, let's get the list of glyphs
# that you have selected in the font window as well
selected = font.selection

# Ok, now that we have these lists, what do we do with them?
# Well, we'll store them in font.groups. That object is
# essentially a dictionary that has a few special tricks.
# The dictionary is keyed by the name of the group, and
# the value is the list of the glyphs. Pretty simple.
# Now, let's store these lists away.
groups = font.groups
groups['uppercase'] = uppercase
groups['lowercase'] = lowercase
groups['uppercaseAndLowercase'] = both
groups['selected'] = both
font.update()

# In FontLab the group info is visible in the classes panel.
# if you look there now, you'll (hopefully) see these new
# groups. Wow! Exciting! Amazing! But, what if you want to
# get these lists back? Easy:
groups = font.groups
print 'uppercase:'
print groups['uppercase']
print
print 'lowercase:'
print groups['lowercase']
print
print 'upper and lowercase:'
print groups['uppercaseAndLowercase']
print
print 'selected:'
print groups['selected']
print

# You can even search the groups for the names of groups
# that contain a certain glyph name. It works like this:
groups = font.groups
found = groups.findGlyph('a')
print '"a" is in these groups: %s'%str(found)

# Oh yeah, don't forget to update the font.
font.update()

# Super easy, huh? Now get to it!
