"""
Instantiate a variation font.  Run, eg:

$ fonttools varLib.mutator ./NotoSansArabic-VF.ttf wght=140 wdth=85
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.fixedTools import floatToFixedToFloat, otRound
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.varLib import _GetCoordinates, _SetCoordinates
from fontTools.varLib.models import (
	supportScalar, normalizeLocation, piecewiseLinearMap
)
from fontTools.varLib.merger import MutatorMerger
from fontTools.varLib.varStore import VarStoreInstancer
from fontTools.varLib.mvar import MVAR_ENTRIES
from fontTools.varLib.iup import iup_delta
import os.path
import logging


log = logging.getLogger("fontTools.varlib.mutator")

# map 'wdth' axis (1..200) to OS/2.usWidthClass (1..9), rounding to closest
OS2_WIDTH_CLASS_VALUES = {}
percents = [50.0, 62.5, 75.0, 87.5, 100.0, 112.5, 125.0, 150.0, 200.0]
for i, (prev, curr) in enumerate(zip(percents[:-1], percents[1:]), start=1):
	half = (prev + curr) / 2
	OS2_WIDTH_CLASS_VALUES[half] = i


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
	loc = normalizeLocation(location, axes)
	if 'avar' in varfont:
		maps = varfont['avar'].segments
		loc = {k: piecewiseLinearMap(v, maps[k]) for k,v in loc.items()}
	# Quantize to F2Dot14, to avoid surprise interpolations.
	loc = {k:floatToFixedToFloat(v, 14) for k,v in loc.items()}
	# Location is normalized now
	log.info("Normalized location: %s", loc)

	log.info("Mutating glyf/gvar tables")
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
		log.info("Mutating cvt/cvar tables")
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
			cvt[i] += otRound(delta)

	if 'MVAR' in varfont:
		log.info("Mutating MVAR table")
		mvar = varfont['MVAR'].table
		varStoreInstancer = VarStoreInstancer(mvar.VarStore, fvar.axes, loc)
		records = mvar.ValueRecord
		for rec in records:
			mvarTag = rec.ValueTag
			if mvarTag not in MVAR_ENTRIES:
				continue
			tableTag, itemName = MVAR_ENTRIES[mvarTag]
			delta = otRound(varStoreInstancer[rec.VarIdx])
			if not delta:
				continue
			setattr(varfont[tableTag], itemName,
				getattr(varfont[tableTag], itemName) + delta)

	if 'GDEF' in varfont:
		log.info("Mutating GDEF/GPOS/GSUB tables")
		merger = MutatorMerger(varfont, loc)

		log.info("Building interpolated tables")
		merger.instantiate()

	if 'name' in varfont:
		log.info("Pruning name table")
		exclude = {a.axisNameID for a in fvar.axes}
		for i in fvar.instances:
			exclude.add(i.subfamilyNameID)
			exclude.add(i.postscriptNameID)
		varfont['name'].names[:] = [
			n for n in varfont['name'].names
			if n.nameID not in exclude
		]

	if "wght" in location and "OS/2" in varfont:
		varfont["OS/2"].usWeightClass = otRound(
			max(1, min(location["wght"], 1000))
		)
	if "wdth" in location:
		wdth = location["wdth"]
		for percent, widthClass in sorted(OS2_WIDTH_CLASS_VALUES.items()):
			if wdth < percent:
				varfont["OS/2"].usWidthClass = widthClass
				break
		else:
			varfont["OS/2"].usWidthClass = 9
	if "slnt" in location and "post" in varfont:
		varfont["post"].italicAngle = max(-90, min(location["slnt"], 90))

	log.info("Removing variable tables")
	for tag in ('avar','cvar','fvar','gvar','HVAR','MVAR','VVAR','STAT'):
		if tag in varfont:
			del varfont[tag]

	return varfont


def main(args=None):
	from fontTools import configLogger
	import argparse

	parser = argparse.ArgumentParser(
		"fonttools varLib.mutator", description="Instantiate a variable font")
	parser.add_argument(
		"input", metavar="INPUT.ttf", help="Input variable TTF file.")
	parser.add_argument(
		"locargs", metavar="AXIS=LOC", nargs="*",
		help="List of space separated locations. A location consist in "
		"the name of a variation axis, followed by '=' and a number. E.g.: "
		" wght=700 wdth=80. The default is the location of the base master.")
	parser.add_argument(
		"-o", "--output", metavar="OUTPUT.ttf", default=None,
		help="Output instance TTF file (default: INPUT-instance.ttf).")
	logging_group = parser.add_mutually_exclusive_group(required=False)
	logging_group.add_argument(
		"-v", "--verbose", action="store_true", help="Run more verbosely.")
	logging_group.add_argument(
		"-q", "--quiet", action="store_true", help="Turn verbosity off.")
	options = parser.parse_args(args)

	varfilename = options.input
	outfile = (
		os.path.splitext(varfilename)[0] + '-instance.ttf'
		if not options.output else options.output)
	configLogger(level=(
		"DEBUG" if options.verbose else
		"ERROR" if options.quiet else
		"INFO"))

	loc = {}
	for arg in options.locargs:
		try:
			tag, val = arg.split('=')
			assert len(tag) <= 4
			loc[tag.ljust(4)] = float(val)
		except (ValueError, AssertionError):
			parser.error("invalid location argument format: %r" % arg)
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
