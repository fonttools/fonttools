# robofab manual
# 	Generatefonts howto
#	usage examples


import os.path
from robofab.world import CurrentFont

font = CurrentFont()
path = font.path
dir, fileName = os.path.split(path)
path = os.sep.join([dir, font.info.fullName])
font.generate('mactype1', path)
