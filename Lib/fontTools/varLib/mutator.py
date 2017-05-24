"""
Instantiate a variation font.  Run, eg:

$ python mutator.py ./NotoSansArabic-VF.ttf wght=140 wdth=85
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.varLib import _GetCoordinates, _SetCoordinates
from fontTools.varLib.models import VariationModel, supportScalar, normalizeLocation
import os.path


def _iup_segment(coords, rc1, rd1, rc2, rd2):
	# rc1 = reference coord 1
	# rd1 = reference delta 1
	out_arrays = [None, None]
	for j in 0,1:
		out_arrays[j] = out = []
		x1, x2, d1, d2 = rc1[j], rc2[j], rd1[j], rd2[j]


		if x1 == x2:
			n = len(coords)
			if d1 == d2:
				out.extend([d1]*n)
			else:
				out.extend([0]*n)
			continue

		if x1 > x2:
			x1, x2 = x2, x1
			d1, d2 = d2, d1

		# x1 < x2
		scale = (d2 - d1) / (x2 - x1)
		for pair in coords:
			x = pair[j]

			if x <= x1:
				d = d1
			elif x >= x2:
				d = d2
			else:
				# Interpolate
				d = d1 + (x - x1) * scale

			out.append(d)

	return zip(*out_arrays)

def _iup_contour(delta, coords):
	assert len(delta) == len(coords)
	if None not in delta:
		return delta

	n = len(delta)
	# indices of points with explicit deltas
	indices = [i for i,v in enumerate(delta) if v is not None]
	if not indices:
		# All deltas are None.  Return 0,0 for all.
		return [(0,0)]*n

	out = []
	it = iter(indices)
	start = next(it)
	if start != 0:
		# Initial segment that wraps around
		i1, i2, ri1, ri2 = 0, start, start, indices[-1]
		out.extend(_iup_segment(coords[i1:i2], coords[ri1], delta[ri1], coords[ri2], delta[ri2]))
	out.append(delta[start])
	for end in it:
		if end - start > 1:
			i1, i2, ri1, ri2 = start+1, end, start, end
			out.extend(_iup_segment(coords[i1:i2], coords[ri1], delta[ri1], coords[ri2], delta[ri2]))
		out.append(delta[end])
		start = end
	if start != n-1:
		# Final segment that wraps around
		i1, i2, ri1, ri2 = start+1, n, start, indices[0]
		out.extend(_iup_segment(coords[i1:i2], coords[ri1], delta[ri1], coords[ri2], delta[ri2]))

	assert len(delta) == len(out), (len(delta), len(out))
	return out

def _iup_delta(delta, coords, ends):
	assert sorted(ends) == ends and len(coords) == (ends[-1]+1 if ends else 0) + 4
	n = len(coords)
	ends = ends + [n-4, n-3, n-2, n-1]
	out = []
	start = 0
	for end in ends:
		end += 1
		contour = _iup_contour(delta[start:end], coords[start:end])
		out.extend(contour)
		start = end

	return out


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
		coordinates,_ = _GetCoordinates(varfont, glyphname)
		origCoords, endPts = None, None
		for var in variations:
			scalar = supportScalar(loc, var.axes)
			if not scalar: continue
			delta = var.coordinates
			if None in delta:
				if origCoords is None:
					origCoords,control = _GetCoordinates(varfont, glyphname)
					endPts = control[1] if control[0] >= 1 else list(range(len(control[1])))
				delta = _iup_delta(delta, origCoords, endPts)
				# TODO Do IUP / handle None items
			coordinates += GlyphCoordinates(delta) * scalar
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
