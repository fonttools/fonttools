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
from fontTools.misc.arrayTools import Vector
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from fontTools.ttLib.tables._f_v_a_r import Axis, NamedInstance
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.ttLib.tables.ttProgram import Program
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otBase import OTTableWriter
from fontTools.varLib import builder, designspace, models, varStore
from fontTools.varLib.merger import VariationMerger, _all_equal
from fontTools.varLib.mvar import MVAR_ENTRIES
from fontTools.varLib.iup import iup_delta_optimize
from collections import OrderedDict
import os.path
import logging
from pprint import pformat

log = logging.getLogger("fontTools.varLib")


class VarLibError(Exception):
	pass

#
# Creation routines
#

def _add_fvar(font, axes, instances):
	"""
	Add 'fvar' table to font.

	axes is an ordered dictionary of DesignspaceAxis objects.

	instances is list of dictionary objects with 'location', 'stylename',
	and possibly 'postscriptfontname' entries.
	"""

	assert axes
	assert isinstance(axes, OrderedDict)

	log.info("Generating fvar")

	fvar = newTable('fvar')
	nameTable = font['name']

	for a in axes.values():
		axis = Axis()
		axis.axisTag = Tag(a.tag)
		# TODO Skip axes that have no variation.
		axis.minValue, axis.defaultValue, axis.maxValue = a.minimum, a.default, a.maximum
		axis.axisNameID = nameTable.addName(tounicode(a.labelname['en']))
		# TODO:
		# Replace previous line with the following when the following issues are resolved:
		# https://github.com/fonttools/fonttools/issues/930
		# https://github.com/fonttools/fonttools/issues/931
		# axis.axisNameID = nameTable.addMultilingualName(a.labelname, font)
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
		inst.coordinates = {axes[k].tag:axes[k].map_backward(v) for k,v in coordinates.items()}
		#inst.coordinates = {axes[k].tag:v for k,v in coordinates.items()}
		fvar.instances.append(inst)

	assert "fvar" not in font
	font['fvar'] = fvar

	return fvar

def _add_avar(font, axes):
	"""
	Add 'avar' table to font.

	axes is an ordered dictionary of DesignspaceAxis objects.
	"""

	assert axes
	assert isinstance(axes, OrderedDict)

	log.info("Generating avar")

	avar = newTable('avar')

	interesting = False
	for axis in axes.values():
		# Currently, some rasterizers require that the default value maps
		# (-1 to -1, 0 to 0, and 1 to 1) be present for all the segment
		# maps, even when the default normalization mapping for the axis
		# was not modified.
		# https://github.com/googlei18n/fontmake/issues/295
		# https://github.com/fonttools/fonttools/issues/1011
		# TODO(anthrotype) revert this (and 19c4b37) when issue is fixed
		curve = avar.segments[axis.tag] = {-1.0: -1.0, 0.0: 0.0, 1.0: 1.0}
		if not axis.map:
			continue

		items = sorted(axis.map.items())
		keys = [item[0] for item in items]
		vals = [item[1] for item in items]

		# Current avar requirements.  We don't have to enforce
		# these on the designer and can deduce some ourselves,
		# but for now just enforce them.
		assert axis.minimum == min(keys)
		assert axis.maximum == max(keys)
		assert axis.default in keys
		# No duplicates
		assert len(set(keys)) == len(keys)
		assert len(set(vals)) == len(vals)
		# Ascending values
		assert sorted(vals) == vals

		keys_triple = (axis.minimum, axis.default, axis.maximum)
		vals_triple = tuple(axis.map_forward(v) for v in keys_triple)

		keys = [models.normalizeValue(v, keys_triple) for v in keys]
		vals = [models.normalizeValue(v, vals_triple) for v in vals]

		if all(k == v for k, v in zip(keys, vals)):
			continue
		interesting = True

		curve.update(zip(keys, vals))

		assert 0.0 in curve and curve[0.0] == 0.0
		assert -1.0 not in curve or curve[-1.0] == -1.0
		assert +1.0 not in curve or curve[+1.0] == +1.0
		# curve.update({-1.0: -1.0, 0.0: 0.0, 1.0: 1.0})

	assert "avar" not in font
	if not interesting:
		log.info("No need for avar")
		avar = None
	else:
		font['avar'] = avar

	return avar

def _add_stat(font, axes):

	if "STAT" in font:
            return

	nameTable = font['name']

	STAT = font["STAT"] = newTable('STAT')
	stat = STAT.table = ot.STAT()
	stat.Version = 0x00010000

	axisRecords = []
	for i,a in enumerate(axes.values()):
		axis = ot.AxisRecord()
		axis.AxisTag = Tag(a.tag)
		# Meh. Reuse fvar nameID!
		axis.AxisNameID = nameTable.addName(tounicode(a.labelname['en']))
		axis.AxisOrdering = i
		axisRecords.append(axis)

	axisRecordArray = ot.AxisRecordArray()
	axisRecordArray.Axis = axisRecords
	# XXX these should not be hard-coded but computed automatically
	stat.DesignAxisRecordSize = 8
	stat.DesignAxisCount = len(axisRecords)
	stat.DesignAxisRecord = axisRecordArray

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
		control = (glyph.numberOfContours,[c.glyphName for c in glyph.components])
	else:
		allData = glyph.getCoordinates(glyf)
		coord = allData[0]
		control = (glyph.numberOfContours,)+allData[1:]

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

	horizontalAdvanceWidth = round(rightSideX - leftSideX)
	if horizontalAdvanceWidth < 0:
		# unlikely, but it can happen, see:
		# https://github.com/fonttools/fonttools/pull/1198
		horizontalAdvanceWidth = 0
	leftSideBearing = round(glyph.xMin - leftSideX)
	# XXX Handle vertical
	font["hmtx"].metrics[glyphName] = horizontalAdvanceWidth, leftSideBearing

def _add_gvar(font, model, master_ttfs, tolerance=0.5, optimize=True):

	assert tolerance >= 0

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
			log.warning("glyph %s has incompatible masters; skipping" % glyph)
			continue
		del allControls

		# Update gvar
		gvar.variations[glyph] = []
		deltas = model.getDeltas(allCoords)
		supports = model.supports
		assert len(deltas) == len(supports)

		# Prepare for IUP optimization
		origCoords = deltas[0]
		endPts = control[1] if control[0] >= 1 else list(range(len(control[1])))

		for i,(delta,support) in enumerate(zip(deltas[1:], supports[1:])):
			if all(abs(v) <= tolerance for v in delta.array):
				continue
			var = TupleVariation(support, delta)
			if optimize:
				delta_opt = iup_delta_optimize(delta, origCoords, endPts, tolerance=tolerance)

				if None in delta_opt:
					# Use "optimized" version only if smaller...
					var_opt = TupleVariation(support, delta_opt)

					axis_tags = sorted(support.keys()) # Shouldn't matter that this is different from fvar...?
					tupleData, auxData, _ = var.compile(axis_tags, [], None)
					unoptimized_len = len(tupleData) + len(auxData)
					tupleData, auxData, _ = var_opt.compile(axis_tags, [], None)
					optimized_len = len(tupleData) + len(auxData)

					if optimized_len < unoptimized_len:
						var = var_opt

			gvar.variations[glyph].append(var)

def _remove_TTHinting(font):
	for tag in ("cvar", "cvt ", "fpgm", "prep"):
		if tag in font:
			del font[tag]
	for attr in ("maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs", "maxStackElements", "maxSizeOfInstructions"):
		setattr(font["maxp"], attr, 0)
	font["maxp"].maxZones = 1
	font["glyf"].removeHinting()
	# TODO: Modify gasp table to deactivate gridfitting for all ranges?

def _merge_TTHinting(font, model, master_ttfs, tolerance=0.5):

	log.info("Merging TT hinting")
	assert "cvar" not in font

	# Check that the existing hinting is compatible

	# fpgm and prep table

	for tag in ("fpgm", "prep"):
		all_pgms = [m[tag].program for m in master_ttfs if tag in m]
		if len(all_pgms) == 0:
			continue
		if tag in font:
			font_pgm = font[tag].program
		else:
			font_pgm = Program()
		if any(pgm != font_pgm for pgm in all_pgms):
			log.warning("Masters have incompatible %s tables, hinting is discarded." % tag)
			_remove_TTHinting(font)
			return

	# glyf table

	for name, glyph in font["glyf"].glyphs.items():
		all_pgms = [
			m["glyf"][name].program
			for m in master_ttfs
			if hasattr(m["glyf"][name], "program")
		]
		if not any(all_pgms):
			continue
		glyph.expand(font["glyf"])
		if hasattr(glyph, "program"):
			font_pgm = glyph.program
		else:
			font_pgm = Program()
		if any(pgm != font_pgm for pgm in all_pgms if pgm):
			log.warning("Masters have incompatible glyph programs in glyph '%s', hinting is discarded." % name)
			_remove_TTHinting(font)
			return

	# cvt table

	all_cvs = [Vector(m["cvt "].values) for m in master_ttfs if "cvt " in m]
	
	if len(all_cvs) == 0:
		# There is no cvt table to make a cvar table from, we're done here.
		return

	if len(all_cvs) != len(master_ttfs):
		log.warning("Some masters have no cvt table, hinting is discarded.")
		_remove_TTHinting(font)
		return

	num_cvt0 = len(all_cvs[0])
	if (any(len(c) != num_cvt0 for c in all_cvs)):
		log.warning("Masters have incompatible cvt tables, hinting is discarded.")
		_remove_TTHinting(font)
		return

	# We can build the cvar table now.

	cvar = font["cvar"] = newTable('cvar')
	cvar.version = 1
	cvar.variations = []

	deltas = model.getDeltas(all_cvs)
	supports = model.supports
	for i,(delta,support) in enumerate(zip(deltas[1:], supports[1:])):
		delta = [round(d) for d in delta]
		if all(abs(v) <= tolerance for v in delta):
			continue
		var = TupleVariation(support, delta)
		cvar.variations.append(var)

def _add_HVAR(font, model, master_ttfs, axisTags):

	log.info("Generating HVAR")

	hAdvanceDeltas = {}
	metricses = [m["hmtx"].metrics for m in master_ttfs]
	for glyph in font.getGlyphOrder():
		hAdvances = [metrics[glyph][0] for metrics in metricses]
		# TODO move round somewhere else?
		hAdvanceDeltas[glyph] = tuple(round(d) for d in model.getDeltas(hAdvances)[1:])

	# Direct mapping
	supports = model.supports[1:]
	varTupleList = builder.buildVarRegionList(supports, axisTags)
	varTupleIndexes = list(range(len(supports)))
	n = len(supports)
	items = []
	for glyphName in font.getGlyphOrder():
		items.append(hAdvanceDeltas[glyphName])

	# Build indirect mapping to save on duplicates, compare both sizes
	uniq = list(set(items))
	mapper = {v:i for i,v in enumerate(uniq)}
	mapping = [mapper[item] for item in items]
	advanceMapping = builder.buildVarIdxMap(mapping, font.getGlyphOrder())

	# Direct
	varData = builder.buildVarData(varTupleIndexes, items)
	directStore = builder.buildVarStore(varTupleList, [varData])

	# Indirect
	varData = builder.buildVarData(varTupleIndexes, uniq)
	indirectStore = builder.buildVarStore(varTupleList, [varData])
	mapping = indirectStore.optimize()
	advanceMapping.mapping = {k:mapping[v] for k,v in advanceMapping.mapping.items()}

	# Compile both, see which is more compact

	writer = OTTableWriter()
	directStore.compile(writer, font)
	directSize = len(writer.getAllData())

	writer = OTTableWriter()
	indirectStore.compile(writer, font)
	advanceMapping.compile(writer, font)
	indirectSize = len(writer.getAllData())

	use_direct = directSize < indirectSize

	# Done; put it all together.
	assert "HVAR" not in font
	HVAR = font["HVAR"] = newTable('HVAR')
	hvar = HVAR.table = ot.HVAR()
	hvar.Version = 0x00010000
	hvar.LsbMap = hvar.RsbMap = None
	if use_direct:
		hvar.VarStore = directStore
		hvar.AdvWidthMap = None
	else:
		hvar.VarStore = indirectStore
		hvar.AdvWidthMap = advanceMapping

def _add_MVAR(font, model, master_ttfs, axisTags):

	log.info("Generating MVAR")

	store_builder = varStore.OnlineVarStoreBuilder(axisTags)
	store_builder.setModel(model)

	records = []
	lastTableTag = None
	fontTable = None
	tables = None
	for tag, (tableTag, itemName) in sorted(MVAR_ENTRIES.items(), key=lambda kv: kv[1]):
		if tableTag != lastTableTag:
			tables = fontTable = None
			if tableTag in font:
				# TODO Check all masters have same table set?
				fontTable = font[tableTag]
				tables = [master[tableTag] for master in master_ttfs]
			lastTableTag = tableTag
		if tables is None:
			continue

		# TODO support gasp entries

		master_values = [getattr(table, itemName) for table in tables]
		if _all_equal(master_values):
			base, varIdx = master_values[0], None
		else:
			base, varIdx = store_builder.storeMasters(master_values)
		setattr(fontTable, itemName, base)

		if varIdx is None:
			continue
		log.info('	%s: %s.%s	%s', tag, tableTag, itemName, master_values)
		rec = ot.MetricsValueRecord()
		rec.ValueTag = tag
		rec.VarIdx = varIdx
		records.append(rec)

	assert "MVAR" not in font
	if records:
		store = store_builder.finish()
		# Optimize
		mapping = store.optimize()
		for rec in records:
			rec.VarIdx = mapping[rec.VarIdx]

		MVAR = font["MVAR"] = newTable('MVAR')
		mvar = MVAR.table = ot.MVAR()
		mvar.Version = 0x00010000
		mvar.Reserved = 0
		mvar.VarStore = store
		# XXX these should not be hard-coded but computed automatically
		mvar.ValueRecordSize = 8
		mvar.ValueRecordCount = len(records)
		mvar.ValueRecord = sorted(records, key=lambda r: r.ValueTag)


def _merge_OTL(font, model, master_fonts, axisTags):

	log.info("Merging OpenType Layout tables")
	merger = VariationMerger(model, axisTags, font)

	merger.mergeTables(font, master_fonts, ['GPOS'])
	# TODO Merge GSUB
	# TODO Merge GDEF itself!
	store = merger.store_builder.finish()
	if not store.VarData:
		return
	try:
		GDEF = font['GDEF'].table
		assert GDEF.Version <= 0x00010002
	except KeyError:
		font['GDEF']= newTable('GDEF')
		GDEFTable = font["GDEF"] = newTable('GDEF')
		GDEF = GDEFTable.table = ot.GDEF()
	GDEF.Version = 0x00010003
	GDEF.VarStore = store

	# Optimize
	varidx_map = store.optimize()
	GDEF.remap_device_varidxes(varidx_map)
	if 'GPOS' in font:
		font['GPOS'].table.remap_device_varidxes(varidx_map)



# Pretty much all of this file should be redesigned and moved inot submodules...
# Such a mess right now, but kludging along...
class _DesignspaceAxis(object):

	def __repr__(self):
		return repr(self.__dict__)

	@staticmethod
	def _map(v, map):
		keys = map.keys()
		if not keys:
			return v
		if v in keys:
			return map[v]
		k = min(keys)
		if v < k:
			return v + map[k] - k
		k = max(keys)
		if v > k:
			return v + map[k] - k
		# Interpolate
		a = max(k for k in keys if k < v)
		b = min(k for k in keys if k > v)
		va = map[a]
		vb = map[b]
		return va + (vb - va) * (v - a) / (b - a)

	def map_forward(self, v):
		if self.map is None: return v
		return self._map(v, self.map)

	def map_backward(self, v):
		if self.map is None: return v
		map = {v:k for k,v in self.map.items()}
		return self._map(v, map)


def load_designspace(designspace_filename):

	ds = designspace.load(designspace_filename)
	axes = ds.get('axes')
	masters = ds.get('sources')
	if not masters:
		raise VarLibError("no sources found in .designspace")
	instances = ds.get('instances', [])

	standard_axis_map = OrderedDict([
		('weight',  ('wght', {'en':'Weight'})),
		('width',   ('wdth', {'en':'Width'})),
		('slant',   ('slnt', {'en':'Slant'})),
		('optical', ('opsz', {'en':'Optical Size'})),
		])


	# Setup axes
	axis_objects = OrderedDict()
	if axes is not None:
		for axis_dict in axes:
			axis_name = axis_dict.get('name')
			if not axis_name:
				axis_name = axis_dict['name'] = axis_dict['tag']
			if 'map' not in axis_dict:
				axis_dict['map'] = None
			else:
				axis_dict['map'] = {m['input']:m['output'] for m in axis_dict['map']}

			if axis_name in standard_axis_map:
				if 'tag' not in axis_dict:
					axis_dict['tag'] = standard_axis_map[axis_name][0]
				if 'labelname' not in axis_dict:
					axis_dict['labelname'] = standard_axis_map[axis_name][1].copy()

			axis = _DesignspaceAxis()
			for item in ['name', 'tag', 'minimum', 'default', 'maximum', 'map']:
				assert item in axis_dict, 'Axis does not have "%s"' % item
			if 'labelname' not in axis_dict:
				axis_dict['labelname'] = {'en': axis_name}
			axis.__dict__ = axis_dict
			axis_objects[axis_name] = axis
	else:
		# No <axes> element. Guess things...
		base_idx = None
		for i,m in enumerate(masters):
			if 'info' in m and m['info']['copy']:
				assert base_idx is None
				base_idx = i
		assert base_idx is not None, "Cannot find 'base' master; Either add <axes> element to .designspace document, or add <info> element to one of the sources in the .designspace document."

		master_locs = [o['location'] for o in masters]
		base_loc = master_locs[base_idx]
		axis_names = set(base_loc.keys())
		assert all(name in standard_axis_map for name in axis_names), "Non-standard axis found and there exist no <axes> element."

		for name,(tag,labelname) in standard_axis_map.items():
			if name not in axis_names:
				continue

			axis = _DesignspaceAxis()
			axis.name = name
			axis.tag = tag
			axis.labelname = labelname.copy()
			axis.default = base_loc[name]
			axis.minimum = min(m[name] for m in master_locs if name in m)
			axis.maximum = max(m[name] for m in master_locs if name in m)
			axis.map = None
			# TODO Fill in weight / width mapping from OS/2 table? Need loading fonts...
			axis_objects[name] = axis
		del base_idx, base_loc, axis_names, master_locs
	axes = axis_objects
	del axis_objects
	log.info("Axes:\n%s", pformat(axes))


	# Check all master and instance locations are valid and fill in defaults
	for obj in masters+instances:
		obj_name = obj.get('name', obj.get('stylename', ''))
		loc = obj['location']
		for axis_name in loc.keys():
			assert axis_name in axes, "Location axis '%s' unknown for '%s'." % (axis_name, obj_name)
		for axis_name,axis in axes.items():
			if axis_name not in loc:
				loc[axis_name] = axis.default
			else:
				v = axis.map_backward(loc[axis_name])
				assert axis.minimum <= v <= axis.maximum, "Location for axis '%s' (mapped to %s) out of range for '%s' [%s..%s]" % (axis_name, v, obj_name, axis.minimum, axis.maximum)


	# Normalize master locations

	normalized_master_locs = [o['location'] for o in masters]
	log.info("Internal master locations:\n%s", pformat(normalized_master_locs))

	# TODO This mapping should ideally be moved closer to logic in _add_fvar/avar
	internal_axis_supports = {}
	for axis in axes.values():
		triple = (axis.minimum, axis.default, axis.maximum)
		internal_axis_supports[axis.name] = [axis.map_forward(v) for v in triple]
	log.info("Internal axis supports:\n%s", pformat(internal_axis_supports))

	normalized_master_locs = [models.normalizeLocation(m, internal_axis_supports) for m in normalized_master_locs]
	log.info("Normalized master locations:\n%s", pformat(normalized_master_locs))


	# Find base master
	base_idx = None
	for i,m in enumerate(normalized_master_locs):
		if all(v == 0 for v in m.values()):
			assert base_idx is None
			base_idx = i
	assert base_idx is not None, "Base master not found; no master at default location?"
	log.info("Index of base master: %s", base_idx)

	return axes, internal_axis_supports, base_idx, normalized_master_locs, masters, instances


def build(designspace_filename, master_finder=lambda s:s, exclude=[], optimize=True):
	"""
	Build variation font from a designspace file.

	If master_finder is set, it should be a callable that takes master
	filename as found in designspace file and map it to master font
	binary as to be opened (eg. .ttf or .otf).
	"""

	axes, internal_axis_supports, base_idx, normalized_master_locs, masters, instances = load_designspace(designspace_filename)

	log.info("Building variable font")
	log.info("Loading master fonts")
	basedir = os.path.dirname(designspace_filename)
	master_ttfs = [master_finder(os.path.join(basedir, m['filename'])) for m in masters]
	master_fonts = [TTFont(ttf_path) for ttf_path in master_ttfs]
	# Reload base font as target font
	vf = TTFont(master_ttfs[base_idx])

	# TODO append masters as named-instances as well; needs .designspace change.
	fvar = _add_fvar(vf, axes, instances)
	if 'STAT' not in exclude:
		_add_stat(vf, axes)
	if 'avar' not in exclude:
		_add_avar(vf, axes)
	del instances

	# Map from axis names to axis tags...
	normalized_master_locs = [{axes[k].tag:v for k,v in loc.items()} for loc in normalized_master_locs]
	#del axes
	# From here on, we use fvar axes only
	axisTags = [axis.axisTag for axis in fvar.axes]

	# Assume single-model for now.
	model = models.VariationModel(normalized_master_locs, axisOrder=axisTags)
	assert 0 == model.mapping[base_idx]

	log.info("Building variations tables")
	if 'MVAR' not in exclude:
		_add_MVAR(vf, model, master_fonts, axisTags)
	if 'HVAR' not in exclude:
		_add_HVAR(vf, model, master_fonts, axisTags)
	if 'GDEF' not in exclude or 'GPOS' not in exclude:
		_merge_OTL(vf, model, master_fonts, axisTags)
	if 'gvar' not in exclude and 'glyf' in vf:
		_add_gvar(vf, model, master_fonts, optimize=optimize)
	if 'cvar' not in exclude:
		_merge_TTHinting(vf, model, master_fonts)

	for tag in exclude:
		if tag in vf:
			del vf[tag]

	return vf, model, master_ttfs


def main(args=None):
	from argparse import ArgumentParser
	from fontTools import configLogger

	parser = ArgumentParser(prog='varLib')
	parser.add_argument('designspace')
	parser.add_argument('-o', metavar='OUTPUTFILE', dest='outfile', default=None, help='output file')
	parser.add_argument('-x', metavar='TAG', dest='exclude', action='append', default=[], help='exclude table')
	parser.add_argument('--disable-iup', dest='optimize', action='store_false', help='do not perform IUP optimization')
	options = parser.parse_args(args)

	# TODO: allow user to configure logging via command-line options
	configLogger(level="INFO")

	designspace_filename = options.designspace
	finder = lambda s: s.replace('master_ufo', 'master_ttf_interpolatable').replace('.ufo', '.ttf')
	outfile = options.outfile
	if outfile is None:
		outfile = os.path.splitext(designspace_filename)[0] + '-VF.ttf'

	vf, model, master_ttfs = build(designspace_filename, finder, exclude=options.exclude, optimize=options.optimize)

	log.info("Saving variation font %s", outfile)
	vf.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		sys.exit(main())
	import doctest
	sys.exit(doctest.testmod().failed)
