#FLM: RoboFab Intro, Font and Glyph Lib

#
#
#	demo of font.lib and glyph.lib
#
#

from robofab.world import CurrentFont, CurrentGlyph

# font.lib and glyph.lib are an idea inherited from RoboFog.
# They are spaces to store custom data. font.lib is for
# font-level custom data, glyph.lib is for glyph-level data.
# They're both Python dictionaries.
#
# Now let's talk about your slice of the lib pie.
# Everyone has their own little address space in the lib object.
# This is done by advising to use a naming convention for the
# top level keys in the lib dictionary.
# Your address is defined by inversing your domain name.
# For example, keys used by RoboFab start with "org.robofab",
# LettError keys start with "com.letterror".
# It's pretty simple, and best of all it avoids the problems
# associated with maintaining a registry. This approach
# to naming was pioneered by Java and has been adopted
# by industry luminaries like Apple and RoboFab.
# What you store in your section is completely up to you.
# Enough of that, let's take a look at how to use the thing.

# Make sure you have a font open.
font = CurrentFont()

# Essentially the lib is a dict object, and it has all properties
# of a dict. So, following the naming scheme above, this is how
# you access your section of the lib (but use your address!):
font.lib['org.robofab'] = 'our address in the lib'
font.lib['org.robofab.keepout'] = 'this also belongs to us'

# Like a dict, you can simply store a string in the dict
font.lib['org.robofab'] = 'Hello World'
print font.lib['org.robofab']

# But that is really boring! Let's store a bunch of stuff.
# Here we can go in two directions: we can either store a
# dict right at our address:
font.lib['org.robofab'] = {'An Int':1, 'A Str':'Howdy!', 'A List':['X', 'Y', 'Z'], 'A Dict':{'Robo':'Fab'}}
# Now because we have a nested dict, and we can access
# it like any other dict let's print the stuff we just stored:
print font.lib['org.robofab']['An Int']
print font.lib['org.robofab']['A Str']
print font.lib['org.robofab']['A List']
print font.lib['org.robofab']['A Dict']

# ...or we can avoid deeper nesting, and use our address as a
# key prefix:
font.lib['org.robofab.A'] = "A"
font.lib['org.robofab.B'] = "B"
font.lib['org.robofab.aList'] = [1, 2, 3]
print font.lib['org.robofab.A']
print font.lib['org.robofab.B']
print font.lib['org.robofab.aList']


# It is all sooo easy!

# Every glyph has it's very own lib as well
# and it works just like the font lib
glyph = CurrentGlyph()
glyph.lib['org.robofab'] = {'My glyph is totally':'Awesome'}
print glyph.lib['org.robofab']['My glyph is totally']

# The type of data that can be stored in lib dictionaries is
# limited. Dictionary keys must be strings (or unicode strings),
# values may be dicts, lists, ints, floats, (unicode) strings and
# booleans. There is also a special type to store arbitrary binary
# data: robofab.plistlib.Data. Don't use plain strings for that!

# So, as you can see, this can be a very powerful thing
# to use and you are only limited by your imagination.
# Have fun!

# A Technical Note:
# You "under the hood" type folks out there may be
# wondering where this data is being stored in the
# FontLab file. Well, in all environments, it's stored
# as a Property List* (.plist), which is a simple XML
# format defined by Apple.
# In FontLab, libs are stored in the font.customdata
# and glyph.customdata fields and it is parsed whenever
# the lib is requested. So, don't try to put anything
# else in those fields, otherwise the lib won't work.
# When using UFO/GLIF, font.lib is stored in a file called
# lib.plist in the .ufo folder, glyph.lib is stored as
# part of the .glif file.
