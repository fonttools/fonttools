#FLM: RoboFab Intro, Interpolating two fonts

#	Basic interpolation of two fonts. This is clean
#	non-FontLab specific implementation of
#	interpolating. This interpolation is strict: it
#	adds no points to contours, it does not alter
#	the outlines of the extremes in any possible
#	way. Note that this works in FontLab as well as
#	NoneLab.
#
#	In fontlab: select two .vfb files, the result will be a new .vfb
#	In NoneLab: select two .ufo files, the result will be a new .ufo

from robofab.world import OpenFont, RFont, RGlyph
from robofab.pens.pointPen import AbstractPointPen
from robofab.interface.all.dialogs import GetFolder

f = OpenFont(None, "First master")
g = OpenFont(None, "Second master")

factor = .5

d = RFont()
d.interpolate(factor, f, g)

path = GetFolder("Select a place to save this UFO")
if path:
	d.save(path)

print 'done'