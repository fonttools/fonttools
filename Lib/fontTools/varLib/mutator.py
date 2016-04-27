"""
Module for dealing with 'gvar'-style font variations, also known as run-time
interpolation.

The ideas here are very similar to MutatorMath.  There is even code to read
MutatorMath .designspace files.

For now, if you run this file on a designspace file, it tries to find
ttf-interpolatable files for the masters and build a GX variation font from
them.  Such ttf-interpolatable and designspace files can be generated from
a Glyphs source, eg., using noto-source as an example:

  $ fontmake -o ttf-interpolatable -g NotoSansArabic-MM.glyphs

Then you can make a GX font this way:

  $ python fonttools/Lib/fontTools/varLib/__init__.py master_ufo/NotoSansArabic.designspace

API *will* change in near future.
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.varLib import VariationModel, supportScalar, _GetCoordinates, _SetCoordinates
import os.path

def main(args=None):

	import sys
	if args is None:
		args = sys.argv[1:]

	varfilename = args[0]
	locargs = args[1:]
	outfile = os.path.splitext(varfilename)[0] + '-instance.ttf'

	loc = {}
	for arg in locargs:
		tag,valstr = arg.split('=')
		assert len(tag) == 4
		loc[tag] = float(valstr)
	print("Location:", loc)

	print("Loading GX font")
	varfont = TTFont(varfilename)

	fvar = varfont['fvar']
	for axis in fvar.axes:
		lower, default, upper = axis.minValue, axis.defaultValue, axis.maxValue
		v = loc.get(axis.axisTag, default)
		if v < lower: v = lower
		if v > upper: v = upper
		if v == default:
			v = 0
		elif v < default:
			v = (v - default) / (default - lower)
		else:
			v = (v - default) / (upper - default)
		loc[axis.axisTag] = v
	# Location is normalized now
	print("Normalized location:", loc)

	gvar = varfont['gvar']
	for glyphname,variations in gvar.variations.items():
		coordinates,_ = _GetCoordinates(varfont, glyphname)
		for var in variations:
			scalar = supportScalar(loc, var.axes)
			if not scalar: continue
			coordinates += GlyphCoordinates(var.coordinates) * scalar
		_SetCoordinates(varfont, glyphname, coordinates)

	print("Removing GX tables")
	for tag in ('fvar','avar','gvar'):
		if tag in varfont:
			del varfont[tag]

	print("Saving instance font", outfile)
	varfont.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		main()
		#sys.exit(0)
	import doctest, sys
	sys.exit(doctest.testmod().failed)
