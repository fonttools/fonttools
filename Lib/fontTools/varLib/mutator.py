"""
Instantiate a variation font.  Run, eg:

$ python mutator.py ./NotoSansArabic-VF.ttf wght=140 wdth=85
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinatesDelta
from fontTools.varLib import _GetCoordinates, _SetCoordinates
from fontTools.varLib.models import VariationModel, supportScalar, normalizeLocation
import os.path

def main(args=None):

	if args is None:
		import sys
		args = sys.argv[1:]

	varfilename = args[0]
	locargs = args[1:]
	outfile = os.path.splitext(varfilename)[0] + '-instance.ttf'

	loc = {}
	for arg in locargs:
		tag,val = arg.split('=')
		assert len(tag) <= 4
		loc[tag.ljust(4)] = float(val)
	print("Location:", loc)

	print("Loading variable font")
	varfont = TTFont(varfilename)

	fvar = varfont['fvar']
	axes = {a.axisTag:(a.minValue,a.defaultValue,a.maxValue) for a in fvar.axes}
	# TODO Apply avar
	# TODO Round to F2Dot14?
	loc = normalizeLocation(loc, axes)
	# Location is normalized now
	print("Normalized location:", loc)

	gvar = varfont['gvar']
	glyf = varfont['glyf']
	# get list of glyph names in gvar sorted by component depth
	glyphnames = sorted(
		gvar.variations.keys(),
		key=lambda name: (
			glyf[name].getCompositeMaxpValues(glyf).maxComponentDepth
			if glyf[name].isComposite() else 0,
			name))
	for glyphname in glyphnames:
		variations = gvar.variations[glyphname]
		coordinates,control = _GetCoordinates(varfont, glyphname)
		for var in variations:
			scalar = supportScalar(loc, var.axes)
			if not scalar: continue
			delta_coords = GlyphCoordinatesDelta(var.coordinates)
			delta_coords *= scalar
			coordinates.applyDeltas(delta_coords, control)
		_SetCoordinates(varfont, glyphname, coordinates)

	print("Removing variable tables")
	for tag in ('avar','cvar','fvar','gvar','HVAR','MVAR','VVAR','STAT'):
		if tag in varfont:
			del varfont[tag]

	print("Saving instance font", outfile)
	varfont.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		sys.exit(main())
	import doctest
	sys.exit(doctest.testmod().failed)
