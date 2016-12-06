"""
Module for dealing with 'gvar'-style font variations, also known as run-time
interpolation.

The ideas here are very similar to MutatorMath.  There is even code to read
MutatorMath .designspace files in the varLib.designspace module.

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
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from fontTools.ttLib.tables._f_v_a_r import Axis, NamedInstance
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables._g_v_a_r import GlyphVariation
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables import otBase as otBase
from fontTools.varLib import designspace, models, builder
from fontTools.varLib.merger import merge_tables, Merger
import warnings
import os.path
from argparse import ArgumentParser

#
# Creation routines
#

# Move to fvar table proper?
# TODO how to provide axis order?
def _add_fvar(font, axes, instances, axis_map):
	"""
	Add 'fvar' table to font.

	axes is a dictionary mapping axis-id to axis (min,default,max)
	coordinate values.

	instances is list of dictionary objects with 'location', 'stylename',
	and possibly 'postscriptfontname' entries.

	axisMap is dictionary mapping axis-id to (axis-tag, axis-name).
	"""

	assert "fvar" not in font
	font['fvar'] = fvar = newTable('fvar')
	nameTable = font['name']

	for iden in sorted(axes.keys(), key=lambda k: axis_map[k][0]):
		axis = Axis()
		axis.axisTag = Tag(axis_map[iden][0])
		axis.minValue, axis.defaultValue, axis.maxValue = axes[iden]
		axisName = tounicode(axis_map[iden][1])
		axis.axisNameID = nameTable.addName(axisName)
		fvar.axes.append(axis)

	for instance in instances:
		coordinates = instance['location']
		name = tounicode(instance['stylename'])
		psname = instance.get('postscriptfontname')

		inst = NamedInstance()
		inst.subfamilyNameID = nameTable.addName(name)
		if psname is not None:
			psname = tounicode(psname)
			inst.postscriptNameID = nameTable.addName(psname)
		inst.coordinates = {axis_map[k][0]:v for k,v in coordinates.items()}
		fvar.instances.append(inst)

	return fvar

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


def _add_gvar(font, model, master_ttfs):

	print("Generating gvar")
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
			var = GlyphVariation(support, delta)
			gvar.variations[glyph].append(var)

def _add_HVAR(font, model, master_ttfs, axisTags):

	print("Generating HVAR")

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


def _all_equal(lst):
	it = iter(lst)
	v0 = next(it)
	for v in it:
		if v0 != v:
			return False
	return True

def buildVarDevTable(store_builder, master_values):
	if _all_equal(master_values):
		return None
	varIdx = store_builder.storeMasters(master_values)
	return builder.buildVarDevTable(varIdx)

class VariationMerger(Merger):

	def __init__(self, model, axisTags, font):
		Merger.__init__(self, font)
		self.model = model
		self.store_builder = builder.OnlineVarStoreBuilder(axisTags)
		self.store_builder.setModel(model)

@VariationMerger.merger(ot.Anchor)
def merge(merger, self, lst):
	assert self.Format == 1
	XDeviceTable = buildVarDevTable(merger.store_builder, [a.XCoordinate for a in lst])
	YDeviceTable = buildVarDevTable(merger.store_builder, [a.YCoordinate for a in lst])
	if XDeviceTable or YDeviceTable:
		self.Format = 3
		self.XDeviceTable = XDeviceTable
		self.YDeviceTable = YDeviceTable

@VariationMerger.merger(ot.PairPos)
def merge(merger, self, lst):
	# We need to interecept the merger processing of the object tree here so
	# that we can change the PairPos value formats after the ValueRecords are
	# changed.
	merger.mergeObjects(self, lst)
	# Now examine the list of value records, and update to the union of format values.
	vf1 = self.ValueFormat1
	vf2 = self.ValueFormat2
	if self.Format == 1:
		for pairSet in self.PairSet:
			for pairValueRecord in pairSet.PairValueRecord:
				pv1 = pairValueRecord.Value1
				if pv1 is not None:
					vf1 |= pv1.getFormat()
				pv2 = pairValueRecord.Value2
				if pv2 is not None:
					vf2 |= pv2.getFormat()
	elif self.Format == 2:
		for class1Record in self.Class1Record:
			for class2Record in class1Record.Class2Record:
				pv1 = class2Record.Value1
				if pv1 is not None:
					vf1 |= pv1.getFormat()
				pv2 = class2Record.Value2
				if pv2 is not None:
					vf2 |= pv2.getFormat()
	self.ValueFormat1 = vf1
	self.ValueFormat2 = vf2

@VariationMerger.merger(otBase.ValueRecord)
def merge(merger, self, lst):
	for name, tableName in [('XAdvance','XAdvDevice'),
				('YAdvance','YAdvDevice'),
				('XPlacement','XPlaDevice'),
				('YPlacement','YPlaDevice')]:

		if hasattr(self, name):
			deviceTable = buildVarDevTable(merger.store_builder,
						       [getattr(a, name, 0) for a in lst])
			if deviceTable:
				setattr(self, tableName, deviceTable)


def _merge_OTL(font, model, master_fonts, axisTags, base_idx):

	print("Merging OpenType Layout tables")
	merger = VariationMerger(model, axisTags, font)

	merge_tables(font, merger, master_fonts, axisTags, base_idx, ['GPOS'])
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


def build(designspace_filename, master_finder=lambda s:s, axisMap=None, build_HVAR=False):
	"""
	Build variation font from a designspace file.

	If master_finder is set, it should be a callable that takes master
	filename as found in designspace file and map it to master font
	binary as to be opened (eg. .ttf or .otf).

	If axisMap is set, it should be dictionary mapping axis-id to
	(axis-tag, axis-name).
	"""

	masters, instances = designspace.load(designspace_filename)
	base_idx = None
	for i,m in enumerate(masters):
		if 'info' in m and m['info']['copy']:
			assert base_idx is None
			base_idx = i
	assert base_idx is not None, "Cannot find 'base' master; Add <info> element to one of the masters in the .designspace document."

	from pprint import pprint
	print("Index of base master:", base_idx)

	print("Building GX")
	print("Loading TTF masters")
	basedir = os.path.dirname(designspace_filename)
	master_ttfs = [master_finder(os.path.join(basedir, m['filename'])) for m in masters]
	master_fonts = [TTFont(ttf_path) for ttf_path in master_ttfs]

	standard_axis_map = {
		'weight':  ('wght', 'Weight'),
		'width':   ('wdth', 'Width'),
		'slant':   ('slnt', 'Slant'),
		'optical': ('opsz', 'Optical Size'),
		'custom':  ('xxxx', 'Custom'),
	}

	axis_map = standard_axis_map
	if axisMap:
		axis_map = axis_map.copy()
		axis_map.update(axisMap)

	# TODO: For weight & width, use OS/2 values and setup 'avar' mapping.

	master_locs = [o['location'] for o in masters]

	axis_tags = set(master_locs[0].keys())
	assert all(axis_tags == set(m.keys()) for m in master_locs)

	# Set up axes
	axes = {}
	for tag in axis_tags:
		default = master_locs[base_idx][tag]
		lower = min(m[tag] for m in master_locs)
		upper = max(m[tag] for m in master_locs)
		if default == lower == upper:
			continue
		axes[tag] = (lower, default, upper)
	print("Axes:")
	pprint(axes)

	print("Master locations:")
	pprint(master_locs)

	# We can use the base font straight, but it's faster to load it again since
	# then we won't be recompiling the existing ('glyf', 'hmtx', ...) tables.
	#gx = master_fonts[base_idx]
	gx = TTFont(master_ttfs[base_idx])

	# TODO append masters as named-instances as well; needs .designspace change.
	fvar = _add_fvar(gx, axes, instances, axis_map)


	# Normalize master locations
	master_locs = [models.normalizeLocation(m, axes) for m in master_locs]

	print("Normalized master locations:")
	pprint(master_locs)

	# TODO Clean this up.
	del instances
	del axes
	master_locs = [{axis_map[k][0]:v for k,v in loc.items()} for loc in master_locs]
	#instance_locs = [{axis_map[k][0]:v for k,v in loc.items()} for loc in instance_locs]
	axisTags = [axis.axisTag for axis in fvar.axes]

	# Assume single-model for now.
	model = models.VariationModel(master_locs)
	assert 0 == model.mapping[base_idx]

	print("Building variations tables")
	if 'glyf' in gx:
		_add_gvar(gx, model, master_fonts)
	if build_HVAR or 'glyf' not in gx:
		# HVAR generation is currently disabled for TTF because of
		# https://github.com/fonttools/fonttools/issues/705
		_add_HVAR(gx, model, master_fonts, axisTags)
	_merge_OTL(gx, model, master_fonts, axisTags, base_idx)

	return gx, model, master_ttfs


def main(args=None):

	parser = ArgumentParser(prog='varLib')
	parser.add_argument('designspace')
	parser.add_argument('--build-HVAR', action='store_true')
	options = parser.parse_args(args)

	designspace_filename = options.designspace
	finder = lambda s: s.replace('master_ufo', 'master_ttf_interpolatable').replace('.ufo', '.ttf')
	outfile = os.path.splitext(designspace_filename)[0] + '-GX.ttf'

	gx, model, master_ttfs = build(designspace_filename, finder, build_HVAR=options.build_HVAR)

	print("Saving variation font", outfile)
	gx.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		main()
		#sys.exit(0)
	import doctest, sys
	sys.exit(doctest.testmod().failed)
