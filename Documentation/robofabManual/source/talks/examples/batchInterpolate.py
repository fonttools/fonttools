# robothon 2006
# batch interpolate

import os
from robofab.world import SelectFont, NewFont

# ask for two masters to interpolate:
font1 = SelectFont("Select font 1")
font2 = SelectFont("Select font 2")
# these are the interpolation factors:
values = [.3, .6]

for value in values:
	# make a new font
	destination = NewFont()
	# do the interpolation
	destination.interpolate(value, font1, font2, doProgress=True)
	destination.update()
	# make a new path + filename for the new font to be saved at:
	dir = os.path.dirname(font1.path)
	fileName = "Demo_%d.vfb" % (1000 * value)
	# save at this path and close the font 
	destination.save(os.path.join(dir, fileName))
	destination.close()


