"""
Module for dealing with 'gvar'-style font variations, also known as run-time
interpolation.

The ideas here are very similar to MutatorMath.  There is even code to read
MutatorMath .designspace files in the varLib.designspace module.

For now, if you run this file on a designspace file, it tries to find
ttf-interpolatable files for the masters and build a variable-font from
them.  Such ttf-interpolatable and designspace files can be generated from
a Glyphs source, eg., using noto-source as an example:

  $ fontmake -o ttf-interpolatable -g NotoSansArabic-MM.glyphs

Then you can make a variable-font this way:

  $ fonttools varLib master_ufo/NotoSansArabic.designspace

API *will* change in near future.
"""
from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from fontTools.ttLib.tables._f_v_a_r import Axis, NamedInstance
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables._g_v_a_r import TupleVariation
from fontTools.ttLib.tables import otTables as ot
from fontTools.varLib import builder, designspace, models
from fontTools.varLib.merger import VariationMerger
import collections
import warnings
import os.path
import logging
from pprint import pformat

log = logging.getLogger("fontTools.varLib")

VarAxis = collections.namedtuple(
	"VarAxis",
	"key, tag, name, "
	"minLocation, defaultLocation, maxLocation, "  # in MutatorMath space
	"minValue, defaultValue, maxValue, "  # in fvar user space, eg 100..900
	"mapping")  # MutatorMath->fvar user space, eg {26:100, 90:400, 190:900}

#
# Creation routines
#

def _add_fvar(font, axes, instances):
	"""
	Add 'fvar' table to font.

	axes is a list of VarAxis namedtuples with tag, name, etc.

	instances is list of dictionary objects with 'location', 'stylename',
	and possibly 'postscriptfontname' entries.
	"""
	assert "fvar" not in font
	font['fvar'] = fvar = newTable('fvar')
	nameTable = font['name']
	for a in axes:
		axis = Axis()
		axis.axisTag = a.tag
		axis.minValue, axis.maxValue = a.minValue, a.maxValue
		axis.defaultValue = a.defaultValue
		axisName = tounicode(a.name)
		axis.axisNameID = nameTable.addName(axisName)
		fvar.axes.append(axis)
	for instance in instances:
		location = instance['location']
		name = tounicode(instance['stylename'])
		psname = instance.get('postscriptfontname')
		inst = NamedInstance()
		inst.subfamilyNameID = nameTable.addName(name)
		if psname is not None:
			psname = tounicode(psname)
			inst.postscriptNameID = nameTable.addName(psname)
		inst.coordinates = {a.tag: _map_fvar_value(a, location[a.key])
		                    for a in axes}
		fvar.instances.append(inst)
	return fvar


def _map_fvar_value(axis, value):
	# linear interpolation on axis.mapping, for example
	# [(26.0, 300), (90.0, 400.0), (151.0, 600.0), (190.0, 700.0)]
	m = axis.mapping
	assert len(m) > 0, axis
	assert value >= m[0][0], (axis, value, m)
	assert value <= m[-1][0], (axis, value, m)
	for i, (start, startVal) in enumerate(m[:-1]):
		limit, limitVal = m[i + 1]
		if value == start:
			return startVal
		elif value == limit:
			return limitVal
		elif value >= start and value <= limit:
			fraction = (value - start) / (limit - start)
			return startVal + fraction * (limitVal - startVal)
	assert False, "no value found; axis: %s; value: %s" % (axis, value)


def _add_avar(font, axes, locAxes, valAxes):
        defaultLocation = {a.key: a.defaultLocation for a in axes}
        defaultValue = {a.key: a.defaultValue for a in axes}
        avar = newTable('avar')
	for axis in axes:
                axisLocation = defaultLocation.copy()
                axisValue = defaultValue.copy()
                curve = avar.segments[axis.tag] = {}
                for loc, val in axis.mapping:
                        axisLocation[axis.key] = loc
                        axisValue[axis.key] = val
                        normLoc = models.normalizeLocation(axisLocation, locAxes)
                        normVal = models.normalizeLocation(axisValue, valAxes)
                        curve[normLoc[axis.key]] = normVal[axis.key]
        interesting = False
        for tag, curve in  avar.segments.items():
                if curve != {-1.0: -1.0, 0.0: 0.0, 1.0:1.0}:
                        interesting = True
                        break
        if not interesting:
                return None
        font['avar'] = avar
        return avar


# TODO Move to glyf or gvar table proper
def _GetCoordinates(font, glyphName):
	"""font, glyphName --> glyph coordinates as expected by "gvar" table

	The result includes four "phantom points" for the glyph metrics,
	as mandated by the "gvar" spec.
	"""
	glyf = font["glyf"]
	if glyphName not in glyf.glyphs: return None
	glyph = glyf[glyphName]
	if glyph.isComposite():
		coord = GlyphCoordinates([(getattr(c, 'x', 0),getattr(c, 'y', 0)) for c in glyph.components])
		control = [c.glyphName for c in glyph.components]
	else:
		allData = glyph.getCoordinates(glyf)
		coord = allData[0]
		control = allData[1:]

	# Add phantom points for (left, right, top, bottom) positions.
	horizontalAdvanceWidth, leftSideBearing = font["hmtx"].metrics[glyphName]
	if not hasattr(glyph, 'xMin'):
		glyph.recalcBounds(glyf)
	leftSideX = glyph.xMin - leftSideBearing
	rightSideX = leftSideX + horizontalAdvanceWidth
	# XXX these are incorrect.  Load vmtx and fix.
	topSideY = glyph.yMax
	bottomSideY = -glyph.yMin
	coord = coord.copy()
	coord.extend([(leftSideX, 0),
	              (rightSideX, 0),
	              (0, topSideY),
	              (0, bottomSideY)])

	return coord, control

# TODO Move to glyf or gvar table proper
def _SetCoordinates(font, glyphName, coord):
	glyf = font["glyf"]
	assert glyphName in glyf.glyphs
	glyph = glyf[glyphName]

	# Handle phantom points for (left, right, top, bottom) positions.
	assert len(coord) >= 4
	if not hasattr(glyph, 'xMin'):
		glyph.recalcBounds(glyf)
	leftSideX = coord[-4][0]
	rightSideX = coord[-3][0]
	topSideY = coord[-2][1]
	bottomSideY = coord[-1][1]

	for _ in range(4):
		del coord[-1]

	if glyph.isComposite():
		assert len(coord) == len(glyph.components)
		for p,comp in zip(coord, glyph.components):
			if hasattr(comp, 'x'):
				comp.x,comp.y = p
	elif glyph.numberOfContours is 0:
		assert len(coord) == 0
	else:
		assert len(coord) == len(glyph.coordinates)
		glyph.coordinates = coord

	glyph.recalcBounds(glyf)

	horizontalAdvanceWidth = rightSideX - leftSideX
	leftSideBearing = glyph.xMin - leftSideX
	# XXX Handle vertical
	# XXX Remove the round when https://github.com/behdad/fonttools/issues/593 is fixed
	font["hmtx"].metrics[glyphName] = int(round(horizontalAdvanceWidth)), int(round(leftSideBearing))


# TODO: Double-check that this mapping matches the spec for OS/2.usWidthClass.
_OS2_WIDTH_CLASSES = {
        1: 50.0,
        2: 65.0,
        3: 70.0,
        4: 85.0,
        5: 100.0,
        6: 125.0,
        7: 150.0,
        8: 175.0,
        9: 200.0,
}


def _get_axis_value(font, axisTag, defaultValue):
	if 'STAT' in font:
		# TODO: This code has not been tested; there might be typos.
		stat = font['STAT']
		for axisValue in stat.DesignAxisValueArray:
			axis = stat.DesignAxisRecord[axisValue.AxisIndex]
			if axis.AxisTag == axisTag:
				return axisValue.Value
	if axisTag == 'wdth':
		return _OS2_WIDTH_CLASSES[font['OS/2'].usWidthClass]
	elif axisTag == 'wght':
		return float(font['OS/2'].usWeightClass)
	# TODO: Should we really take MutatorMath locations as OpenType
	# axis values? Or bail out?
	return defaultValue


def _get_axes(masters, master_fonts, base_idx, axis_map):
	master_locs = [m['location'] for m in masters]
	used_keys = sorted(set(master_locs[base_idx].keys()))
	assert all(used_keys == sorted(set(loc.keys())) for loc in master_locs)
	axes = []
	for key in used_keys:
		tag, name, instanceMapping = axis_map[key]
		tag = Tag(tag)
		locs = [loc[key] for loc in master_locs]
		values = [_get_axis_value(font, tag, loc)
		          for loc, font in zip(locs, master_fonts)]
		minValue, maxValue = min(values), max(values)
		defaultValue = values[base_idx]
		if minValue == maxValue == defaultValue:
			continue
		upper = max(m[key] for m in master_locs)

		mapping = dict(zip(locs, values))  # from masters
		mapping.update(instanceMapping)    # from instances
		mapping = sorted(mapping.items())
		axes.append(VarAxis(key=key, tag=tag, name=name,
		                    minValue=minValue,
		                    defaultValue=defaultValue,
		                    maxValue=maxValue,
                                    minLocation=min(m[key] for m in master_locs),
                                    defaultLocation=master_locs[base_idx][key],
                                    maxLocation=max(m[key] for m in master_locs),
		                    mapping=mapping))

	# TODO: Sort axes by ordering specified in masters STAT table.
	return axes


def _add_gvar(font, model, master_ttfs):

	log.info("Generating gvar")
	assert "gvar" not in font
	gvar = font["gvar"] = newTable('gvar')
	gvar.version = 1
	gvar.reserved = 0
	gvar.variations = {}

	for glyph in font.getGlyphOrder():

		allData = [_GetCoordinates(m, glyph) for m in master_ttfs]
		allCoords = [d[0] for d in allData]
		allControls = [d[1] for d in allData]
		control = allControls[0]
		if (any(c != control for c in allControls)):
			warnings.warn("glyph %s has incompatible masters; skipping" % glyph)
			continue
		del allControls

		# Update gvar
		gvar.variations[glyph] = []
		deltas = model.getDeltas(allCoords)
		supports = model.supports
		assert len(deltas) == len(supports)
		for i,(delta,support) in enumerate(zip(deltas[1:], supports[1:])):
			var = TupleVariation(support, delta)
			gvar.variations[glyph].append(var)

def _add_HVAR(font, model, master_ttfs, axisTags):

	log.info("Generating HVAR")

	hAdvanceDeltas = {}
	metricses = [m["hmtx"].metrics for m in master_ttfs]
	for glyph in font.getGlyphOrder():
		hAdvances = [metrics[glyph][0] for metrics in metricses]
		# TODO move round somewhere else?
		hAdvanceDeltas[glyph] = tuple(round(d) for d in model.getDeltas(hAdvances)[1:])

	# We only support the direct mapping right now.

	supports = model.supports[1:]
	varTupleList = builder.buildVarRegionList(supports, axisTags)
	varTupleIndexes = list(range(len(supports)))
	n = len(supports)
	items = []
	zeroes = [0]*n
	for glyphName in font.getGlyphOrder():
		items.append(hAdvanceDeltas.get(glyphName, zeroes))
	while items and items[-1] is zeroes:
		del items[-1]

	advanceMapping = None
	# Add indirect mapping to save on duplicates
	uniq = set(items)
	# TODO Improve heuristic
	if (len(items) - len(uniq)) * len(varTupleIndexes) > len(items):
		newItems = sorted(uniq)
		mapper = {v:i for i,v in enumerate(newItems)}
		mapping = [mapper[item] for item in items]
		while len(mapping) > 1 and mapping[-1] == mapping[-2]:
			del mapping[-1]
		advanceMapping = builder.buildVarIdxMap(mapping)
		items = newItems
		del mapper, mapping, newItems
	del uniq

	varData = builder.buildVarData(varTupleIndexes, items)
	varStore = builder.buildVarStore(varTupleList, [varData])

	assert "HVAR" not in font
	HVAR = font["HVAR"] = newTable('HVAR')
	hvar = HVAR.table = ot.HVAR()
	hvar.Version = 0x00010000
	hvar.VarStore = varStore
	hvar.AdvWidthMap = advanceMapping
	hvar.LsbMap = hvar.RsbMap = None


def _merge_OTL(font, model, master_fonts, axisTags, base_idx):

	log.info("Merging OpenType Layout tables")
	merger = VariationMerger(model, axisTags, font)

	merger.mergeTables(font, master_fonts, axisTags, base_idx, ['GPOS'])
	store = merger.store_builder.finish()
	try:
		GDEF = font['GDEF'].table
		assert GDEF.Version <= 0x00010002
	except KeyError:
		font['GDEF']= newTable('GDEF')
		GDEFTable = font["GDEF"] = newTable('GDEF')
		GDEF = GDEFTable.table = ot.GDEF()
	GDEF.Version = 0x00010003
	GDEF.VarStore = store


def build(designspace_filename, master_finder=lambda s:s, axisMap=None):
	"""
	Build variation font from a designspace file.

	If master_finder is set, it should be a callable that takes master
	filename as found in designspace file and map it to master font
	binary as to be opened (eg. .ttf or .otf).

	If axisMap is set, it should be dictionary mapping axis-id to
	(axis-tag, axis-name, {interpolation-value: fvar-value}}).
	"""

	masters, instances = designspace.load(designspace_filename)
	base_idx = None
	for i,m in enumerate(masters):
		if 'info' in m and m['info']['copy']:
			assert base_idx is None
			base_idx = i
	assert base_idx is not None, "Cannot find 'base' master; Add <info> element to one of the masters in the .designspace document."

	log.info("Index of base master: %s", base_idx)

	log.info("Building variable font")
	log.info("Loading TTF masters")
	basedir = os.path.dirname(designspace_filename)
	master_ttfs = [master_finder(os.path.join(basedir, m['filename'])) for m in masters]
	master_fonts = [TTFont(ttf_path) for ttf_path in master_ttfs]

	standard_axis_map = {
		'weight':  ('wght', 'Weight', {}),
		'width':   ('wdth', 'Width', {}),
		'slant':   ('slnt', 'Slant', {}),
		'optical': ('opsz', 'Optical Size', {}),
		'custom':  ('xxxx', 'Custom', {}),
	}

	axis_map = standard_axis_map
	if axisMap:
		axis_map = axis_map.copy()
		axis_map.update(axisMap)

        axes = _get_axes(masters, master_fonts, base_idx, axis_map)
	master_locs = [o['location'] for o in masters]
	axis_keys = set(master_locs[base_idx].keys())
	assert all(axis_keys == set(m.keys()) for m in master_locs)

	log.info("Axes:\n%s", pformat(axes))
	log.info("Master locations:\n%s", pformat(master_locs))

	# We can use the base font straight, but it's faster to load it again since
	# then we won't be recompiling the existing ('glyf', 'hmtx', ...) tables.
	#gx = master_fonts[base_idx]
	gx = TTFont(master_ttfs[base_idx])

        locAxes, valAxes = {}, {}
        for a in axes:
                locAxes[a.key] = (a.minLocation, a.defaultLocation, a.maxLocation)
                valAxes[a.key] = (a.minValue, a.defaultValue, a.maxValue)

	fvar = _add_fvar(gx, axes, instances)
	avar = _add_avar(gx, axes, locAxes, valAxes)

	master_locs = [models.normalizeLocation(m, locAxes) for m in master_locs]
	log.info("Normalized master locations:\n%s", pformat(master_locs))

	# TODO Clean this up.
	del instances
	master_locs = [{axis_map[k][0]:v for k,v in loc.items()} for loc in master_locs]
	axisTags = [axis.axisTag for axis in fvar.axes]

	# Assume single-model for now.
	model = models.VariationModel(master_locs)
	assert 0 == model.mapping[base_idx]

	log.info("Building variations tables")
	if 'glyf' in gx:
		_add_gvar(gx, model, master_fonts)
	_add_HVAR(gx, model, master_fonts, axisTags)
	_merge_OTL(gx, model, master_fonts, axisTags, base_idx)

	return gx, model, master_ttfs


def main(args=None):
	from argparse import ArgumentParser
	from fontTools import configLogger

	parser = ArgumentParser(prog='varLib')
	parser.add_argument('designspace')
	options = parser.parse_args(args)

	# TODO: allow user to configure logging via command-line options
	configLogger(level="INFO")

	designspace_filename = options.designspace
	finder = lambda s: s.replace('master_ufo', 'master_ttf_interpolatable').replace('.ufo', '.ttf')
	outfile = os.path.splitext(designspace_filename)[0] + '-VF.ttf'

        # TODO: Find out if this information can be passed as part of the
        # designspace. If not, change fontmake to pass this structure.
        # These parameters are those for NotoSansArabic-MM.glyphs.
        axisMap = {
                'width':  ('wdth', 'Width', {
                        70.0: 70.0,
                        79.0: 80.0,
                        89.0: 90.0,
                        100.0: 100.0
                }),
                'weight':  ('wght', 'Weight', {
                        26.0: 100.0,
                        39.0: 200.0,
                        58.0: 300.0,
                        90.0: 400.0,
                        108.0: 500.0,
                        128.0: 600.0,
                        151.0: 700.0,
                        169.0: 800.0,
                        190.0: 900.0,
                })
        }

	gx, model, master_ttfs = build(designspace_filename, finder, axisMap)

	log.info("Saving variation font %s", outfile)
	gx.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		sys.exit(main())
	import doctest, sys
	sys.exit(doctest.testmod().failed)
