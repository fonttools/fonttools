# robofab manual
#	Font object
#	Usage examples
# start using the current font
from robofab.world import CurrentFont
f = CurrentFont()

# get a clean, empty new font object,
# appropriate for the current environment
f = robofab.world.RFont()

# get an open dialog and start a new font
f = OpenFont()

# open the font at path
f = OpenFont(path)