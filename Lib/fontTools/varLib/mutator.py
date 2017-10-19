"""
Instantiate a variation font.  Run, eg:

$ python mutator.py ./NotoSansArabic-VF.ttf wght=140 wdth=85
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.varLib import _GetCoordinates, _SetCoordinates
from fontTools.varLib.models import supportScalar, normalizeLocation
from fontTools.varLib.mvar import MVAR_entries
from fontTools.varLib.iup import iup_delta
import os.path
import logging


log = logging.getLogger("fontTools.varlib.mutator")


def instantiateVariableFont(varfont, location, inplace=False):
	""" Generate a static instance from a variable TTFont and a dictionary
	defining the desired location along the variable font's axes.
	The location values must be specified as user-space coordinates, e.g.:

		{'wght': 400, 'wdth': 100}

	By default, a new TTFont object is returned. If ``inplace`` is True, the
	input varfont is modified and reduced to a static font.
	"""
	if not inplace:
		# make a copy to leave input varfont unmodified
		stream = BytesIO()
		varfont.save(stream)
		stream.seek(0)
		varfont = TTFont(stream)

	fvar = varfont['fvar']
	axes = {a.axisTag:(a.minValue,a.defaultValue,a.maxValue) for a in fvar.axes}
	# TODO Apply avar
	# TODO Round to F2Dot14?
	loc = normalizeLocation(location, axes)
	# Location is normalized now
	log.info("Normalized location: %s", loc)

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
				delta = iup_delta(delta, origCoords, endPts)
			coordinates += GlyphCoordinates(delta) * scalar
		_SetCoordinates(varfont, glyphname, coordinates)

	if 'cvar' in varfont:
		cvar = varfont['cvar']
		cvt = varfont['cvt ']
		deltas = {}
		for var in cvar.variations:
			scalar = supportScalar(loc, var.axes)
			if not scalar: continue
			for i, c in enumerate(var.coordinates):
				if c is not None:
					deltas[i] = deltas.get(i, 0) + scalar * c
		for i, delta in deltas.items():
			cvt[i] += int(round(delta))

	if 'MVAR' in varfont:
		mvar = varfont['MVAR'].table
		varstore = mvar.VarStore
		records = mvar.ValueRecord
		for rec in records:
			mvarTag = rec.ValueTag
			if mvarTag not in MVAR_entries:
				continue
			tableTag, itemName = MVAR_entries[mvarTag]

			varIdx = rec.VarIdx
			major,minor = varIdx >> 16, varIdx & 0xFFFF

			assert varstore.Format == 1
			deltas = varstore.VarData[major].Item[minor]
			def VarRegion_get_support(self, fvar):
				axes = fvar.axes
				return {axes[i].axisTag: (reg.StartCoord,reg.PeakCoord,reg.EndCoord)
					for i,reg in enumerate(self.VarRegionAxis)}
			supports = [VarRegion_get_support(varstore.VarRegionList.Region[ri], fvar)
				    for ri in varstore.VarData[major].VarRegionIndex]
			delta = 0.
			for d,s in zip(deltas, supports):
				if not d: continue
				scalar = supportScalar(loc, s)
				delta += d * scalar
			delta = int(round(delta))
			if not delta:
				continue
			setattr(varfont[tableTag], itemName, getattr(varfont[tableTag], itemName) + delta)

	log.info("Removing variable tables")
	for tag in ('avar','cvar','fvar','gvar','HVAR','MVAR','VVAR','STAT'):
		if tag in varfont:
			del varfont[tag]

	return varfont


def main(args=None):
	from fontTools import configLogger

	if args is None:
		import sys
		args = sys.argv[1:]

	varfilename = args[0]
	locargs = args[1:]
	outfile = os.path.splitext(varfilename)[0] + '-instance.ttf'

	# TODO Allow to specify logging verbosity as command line option
	configLogger(level=logging.INFO)

	loc = {}
	for arg in locargs:
		tag,val = arg.split('=')
		assert len(tag) <= 4
		loc[tag.ljust(4)] = float(val)
	log.info("Location: %s", loc)

	log.info("Loading variable font")
	varfont = TTFont(varfilename)

	instantiateVariableFont(varfont, loc, inplace=True)

	log.info("Saving instance font %s", outfile)
	varfont.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		sys.exit(main())
	import doctest
	sys.exit(doctest.testmod().failed)
