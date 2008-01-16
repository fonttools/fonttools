#FLM: RoboFab Intro, Building Accented Glyphs

#
#
#	demo building accented glyphs with robofab
#
#

# RoboFab sports very simple, yet very simple automatic
# accented glyph compiling. The accentBuilder module has
# several tools that handle these operations splendidly.
# Why don't we have a look?

# (you will need to have a font open in FontLab)
from robofab.world import CurrentFont

# accentBuilder lives in robofab.tools
from robofab.tools.accentBuilder import AccentTools

font = CurrentFont()

# The first thing that you need is a list of accented glyphs
# that you want to compile. This is a very short one for
# demonstration purposes. There are some more extensive
# lists located in robofab.gString
myList = ['aacute', 'agrave', 'acircumflex', 'adieresis', 'atilde', 'aring']

# AccentTools is the class that contains the most important methods.
# It takes a font and the list of accented glyphs as arguments. 
accentTool = AccentTools(font, myList)

# These accented glyphs are compiled using anchors. Anchors are
# simple reference points in the glyph. These anchors are used
# to align the various components when the accented glyph is compiled.
# AccentTools looks at the glyph names in your list of accented glyphs
# and references an internal glyph construction database to determine
# where the anchors need to be placed. So, we need to tell AccentTools
# to position the anchors appropriately. We have very flexible control
# of how the anchors are positioned in relation to the glyph.
# So, build the needed anchors!
accentTool.buildAnchors(ucXOffset=30, ucYOffset=70, lcXOffset=20, lcYOffset=50, doProgress=True)

# AccentTools may encounter some problems, for example if some
# necessary glyphs are not present, when adding the anchors.
# We can print these errors by calling:
accentTool.printAnchorErrors()

# Now that we have the anchors in place, we can compile the glyphs.
accentTool.buildAccents(doProgress=True)

# It may also run into some problems, for example if necessary
# anchors are not prest. You can print these errors out as well.
accentTool.printAccentErrors()

# That's it! Now, update the font.
font.update()

# See how easy that is? And, this is just the tip of the iceburg
# with AccentTools. Read the source!

