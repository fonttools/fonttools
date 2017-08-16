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
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.ttLib.tables import otTables as ot
from fontTools.varLib import builder, designspace, models
from fontTools.varLib.merger import VariationMerger, _all_equal
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
	leftSideBearing = round(glyph.xMin - leftSideX)
	# XXX Handle vertical
	font["hmtx"].metrics[glyphName] = horizontalAdvanceWidth, leftSideBearing


def _all_interpolatable_in_between(deltas, coords, i, j, tolerance):
	assert j - i >= 2
	from fontTools.varLib.mutator import _iup_segment
	interp = list(_iup_segment(coords[i+1:j], coords[i], deltas[i], coords[j], deltas[j]))
	deltas = deltas[i+1:j]

	assert len(deltas) == len(interp)

	return all(abs(complex(x-p, y-q)) <= tolerance for (x,y),(p,q) in zip(deltas, interp))

def _iup_contour_bound_forced_set(delta, coords, tolerance=0):
	"""The forced set is a conservative set of points on the contour that must be encoded
	explicitly (ie. cannot be interpolated).  Calculating this set allows for significantly
	speeding up the dynamic-programming, as well as resolve circularity in DP.

	The set is precise; that is, if an index is in the returned set, then there is no way
	that IUP can generate delta for that point, given coords and delta.
	"""
	assert len(delta) == len(coords)

	forced = set()
	# Track "last" and "next" points on the contour as we sweep.
	nd, nc = delta[0], coords[0]
	ld, lc = delta[-1], coords[-1]
	for i in range(len(delta)-1, -1, -1):
		d, c = ld, lc
		ld, lc = delta[i-1], coords[i-1]

		for j in (0,1): # For X and for Y
			cj = c[j]
			dj = d[j]
			lcj = lc[j]
			ldj = ld[j]
			ncj = nc[j]
			ndj = nd[j]

			if lcj <= ncj:
				c1, c2 = lcj, ncj
				d1, d2 = ldj, ndj
			else:
				c1, c2 = ncj, lcj
				d1, d2 = ndj, ldj

			# If coordinate for current point is between coordinate of adjacent
			# points on the two sides, but the delta for current point is NOT
			# between delta for those adjacent points (considering tolerance
			# allowance), then there is no way that current point can be IUP-ed.
			# Mark it forced.
			force = False
			if c1 <= cj <= c2:
				if not (min(d1,d2)-tolerance <= dj <= max(d1,d2)+tolerance):
					force = True
			else: # cj < c1 or c2 < cj
				if c1 == c2:
					if d1 == d2:
						if abs(dj - d1) > tolerance:
							force = True
					else:
						if abs(dj) > tolerance:
							# Disabled the following because the "d1 == d2" does
							# check does not take tolerance into consideration...
							pass # force = True
				elif d1 != d2:
					if cj < c1:
						if dj != d1 and ((dj-tolerance < d1) != (d1 < d2)):
							force = True
					else: # c2 < cj
						if d2 != dj and ((d2 < dj+tolerance) != (d1 < d2)):
							force = True

			if force:
				forced.add(i)
				break

		nd, nc = d, c

	return forced

def _iup_contour_optimize_dp(delta, coords, forced={}, tolerance=0, lookback=None):
	"""Straightforward Dynamic-Programming.  For each index i, find least-costly encoding of
	points i to n-1 where i is explicitly encoded.  We find this by considering all next
	explicit points j and check whether interpolation can fill points between i and j.

	Note that solution always encodes last point explicitly.  Higher-level is responsible
	for removing that restriction.

	As major speedup, we stop looking further whenever we see a "forced" point."""

	n = len(delta)
	if lookback is None:
		lookback = n
	costs = {-1:0}
	chain = {-1:None}
	for i in range(0, n):
		best_cost = costs[i-1] + 1

		costs[i] = best_cost
		chain[i] = i - 1

		if i - 1 in forced:
			continue

		for j in range(i-2, max(i-lookback, -2), -1):

			cost = costs[j] + 1

			if cost < best_cost and _all_interpolatable_in_between(delta, coords, j, i, tolerance):
				costs[i] = best_cost = cost
				chain[i] = j

			if j in forced:
				break

	return chain, costs

def _rot_list(l, k):
	"""Rotate list by k items forward.  Ie. item at position 0 will be
	at position k in returned list.  Negative k is allowed."""
	n = len(l)
	k %= n
	if not k: return l
	return l[n-k:] + l[:n-k]

def _rot_set(s, k, n):
	k %= n
	if not k: return s
	return {(v + k) % n for v in s}

def _iup_contour_optimize(delta, coords, tolerance=0.):
	n = len(delta)

	# Get the easy cases out of the way:

	# If all are within tolerance distance of 0, encode nothing:
	if all(abs(complex(*p)) <= tolerance for p in delta):
		return [None] * n

	# If there's exactly one point, return it:
	if n == 1:
		return delta

	# If all deltas are exactly the same, return just one (the first one):
	d0 = delta[0]
	if all(d0 == d for d in delta):
		return [d0] + [None] * (n-1)

	# Else, solve the general problem using Dynamic Programming.

	forced = _iup_contour_bound_forced_set(delta, coords, tolerance)
	# The _iup_contour_optimize_dp() routine returns the optimal encoding
	# solution given the constraint that the last point is always encoded.
	# To remove this constraint, we use two different methods, depending on
	# whether forced set is non-empty or not:

	if forced:
		# Forced set is non-empty: rotate the contour start point
		# such that the last point in the list is a forced point.
		k = (n-1) - max(forced)
		assert k >= 0

		delta  = _rot_list(delta, k)
		coords = _rot_list(coords, k)
		forced = _rot_set(forced, k, n)

		chain, costs = _iup_contour_optimize_dp(delta, coords, forced, tolerance)

		# Assemble solution.
		solution = set()
		i = n - 1
		while i is not None:
			solution.add(i)
			i = chain[i]
		assert forced <= solution, (forced, solution)
		delta = [delta[i] if i in solution else None for i in range(n)]

		delta = _rot_list(delta, -k)
	else:
		# Repeat the contour an extra time, solve the 2*n case, then look for solutions of the
		# circular n-length problem in the solution for 2*n linear case.  I cannot prove that
		# this always produces the optimal solution...
		chain, costs = _iup_contour_optimize_dp(delta+delta, coords+coords, forced, tolerance, n)
		best_sol, best_cost = None, n+1

		for start in range(n-1, 2*n-1):
			# Assemble solution.
			solution = set()
			i = start
			while i > start - n:
				solution.add(i % n)
				i = chain[i]
			if i == start - n:
				cost = costs[start] - costs[start - n]
				if cost <= best_cost:
					best_sol, best_cost = solution, cost

		delta = [delta[i] if i in best_sol else None for i in range(n)]


	return delta

def _iup_delta_optimize(delta, coords, ends, tolerance=0.):
	assert sorted(ends) == ends and len(coords) == (ends[-1]+1 if ends else 0) + 4
	n = len(coords)
	ends = ends + [n-4, n-3, n-2, n-1]
	out = []
	start = 0
	for end in ends:
		contour = _iup_contour_optimize(delta[start:end+1], coords[start:end+1], tolerance)
		assert len(contour) == end - start + 1
		out.extend(contour)
		start = end+1

	return out

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
				delta_opt = _iup_delta_optimize(delta, origCoords, endPts, tolerance=tolerance)

				if None in delta_opt:
					# Use "optimized" version only if smaller...
					var_opt = TupleVariation(support, delta_opt)

					axis_tags = sorted(support.keys()) # Shouldn't matter that this is different from fvar...?
					tupleData, auxData = var.compile(axis_tags, [], None)
					unoptimized_len = len(tupleData) + len(auxData)
					tupleData, auxData = var_opt.compile(axis_tags, [], None)
					optimized_len = len(tupleData) + len(auxData)

					if optimized_len < unoptimized_len:
						var = var_opt

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

_MVAR_entries = {
	'hasc': ('OS/2', 'sTypoAscender'),		 # horizontal ascender
	'hdsc': ('OS/2', 'sTypoDescender'),		 # horizontal descender
	'hlgp': ('OS/2', 'sTypoLineGap'),		 # horizontal line gap
	'hcla': ('OS/2', 'usWinAscent'),		 # horizontal clipping ascent
	'hcld': ('OS/2', 'usWinDescent'),		 # horizontal clipping descent
	'vasc': ('vhea', 'ascent'),			 # vertical ascender
	'vdsc': ('vhea', 'descent'),			 # vertical descender
	'vlgp': ('vhea', 'lineGap'),			 # vertical line gap
	'hcrs': ('hhea', 'caretSlopeRise'),		 # horizontal caret rise
	'hcrn': ('hhea', 'caretSlopeRun'),		 # horizontal caret run
	'hcof': ('hhea', 'caretOffset'),		 # horizontal caret offset
	'vcrs': ('vhea', 'caretSlopeRise'),		 # vertical caret rise
	'vcrn': ('vhea', 'caretSlopeRun'),		 # vertical caret run
	'vcof': ('vhea', 'caretOffset'),		 # vertical caret offset
	'xhgt': ('OS/2', 'sxHeight'),			 # x height
	'cpht': ('OS/2', 'sCapHeight'),			 # cap height
	'sbxs': ('OS/2', 'ySubscriptXSize'),		 # subscript em x size
	'sbys': ('OS/2', 'ySubscriptYSize'),		 # subscript em y size
	'sbxo': ('OS/2', 'ySubscriptXOffset'),		 # subscript em x offset
	'sbyo': ('OS/2', 'ySubscriptYOffset'),		 # subscript em y offset
	'spxs': ('OS/2', 'ySuperscriptXSize'),		 # superscript em x size
	'spys': ('OS/2', 'ySuperscriptYSize'),		 # superscript em y size
	'spxo': ('OS/2', 'ySuperscriptXOffset'),	 # superscript em x offset
	'spyo': ('OS/2', 'ySuperscriptYOffset'),	 # superscript em y offset
	'strs': ('OS/2', 'yStrikeoutSize'),		 # strikeout size
	'stro': ('OS/2', 'yStrikeoutPosition'),		 # strikeout offset
	'unds': ('post', 'underlineThickness'),		 # underline size
	'undo': ('post', 'underlinePosition'),		 # underline offset
	#'gsp0': ('gasp', 'gaspRange[0].rangeMaxPPEM'),	 # gaspRange[0]
	#'gsp1': ('gasp', 'gaspRange[1].rangeMaxPPEM'),	 # gaspRange[1]
	#'gsp2': ('gasp', 'gaspRange[2].rangeMaxPPEM'),	 # gaspRange[2]
	#'gsp3': ('gasp', 'gaspRange[3].rangeMaxPPEM'),	 # gaspRange[3]
	#'gsp4': ('gasp', 'gaspRange[4].rangeMaxPPEM'),	 # gaspRange[4]
	#'gsp5': ('gasp', 'gaspRange[5].rangeMaxPPEM'),	 # gaspRange[5]
	#'gsp6': ('gasp', 'gaspRange[6].rangeMaxPPEM'),	 # gaspRange[6]
	#'gsp7': ('gasp', 'gaspRange[7].rangeMaxPPEM'),	 # gaspRange[7]
	#'gsp8': ('gasp', 'gaspRange[8].rangeMaxPPEM'),	 # gaspRange[8]
	#'gsp9': ('gasp', 'gaspRange[9].rangeMaxPPEM'),	 # gaspRange[9]
}


def _add_MVAR(font, model, master_ttfs, axisTags):

	log.info("Generating MVAR")

	store_builder = builder.OnlineVarStoreBuilder(axisTags)
	store_builder.setModel(model)

	records = []
	lastTableTag = None
	fontTable = None
	tables = None
	for tag, (tableTag, itemName) in sorted(_MVAR_entries.items(), key=lambda kv: kv[1]):
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
		MVAR = font["MVAR"] = newTable('MVAR')
		mvar = MVAR.table = ot.MVAR()
		mvar.Version = 0x00010000
		mvar.Reserved = 0
		mvar.VarStore = store_builder.finish()
		# XXX these should not be hard-coded but computed automatically
		mvar.ValueRecordSize = 8
		mvar.ValueRecordCount = len(records)
		mvar.ValueRecord = sorted(records, key=lambda r: r.ValueTag)


def _merge_OTL(font, model, master_fonts, axisTags):

	log.info("Merging OpenType Layout tables")
	merger = VariationMerger(model, axisTags, font)

	merger.mergeTables(font, master_fonts, ['GPOS'])
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
	class DesignspaceAxis(object):

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

			axis = DesignspaceAxis()
			for item in ['name', 'tag', 'labelname', 'minimum', 'default', 'maximum', 'map']:
				assert item in axis_dict, 'Axis does not have "%s"' % item
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

			axis = DesignspaceAxis()
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


def build(designspace_filename, master_finder=lambda s:s):
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
	_add_avar(vf, axes)
	del instances

	# Map from axis names to axis tags...
	normalized_master_locs = [{axes[k].tag:v for k,v in loc.items()} for loc in normalized_master_locs]
	#del axes
	# From here on, we use fvar axes only
	axisTags = [axis.axisTag for axis in fvar.axes]

	# Assume single-model for now.
	model = models.VariationModel(normalized_master_locs)
	assert 0 == model.mapping[base_idx]

	log.info("Building variations tables")
	_add_MVAR(vf, model, master_fonts, axisTags)
	_add_HVAR(vf, model, master_fonts, axisTags)
	_merge_OTL(vf, model, master_fonts, axisTags)
	if 'glyf' in vf:
		_add_gvar(vf, model, master_fonts)

	return vf, model, master_ttfs


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

	vf, model, master_ttfs = build(designspace_filename, finder)

	log.info("Saving variation font %s", outfile)
	vf.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		sys.exit(main())
	import doctest
	sys.exit(doctest.testmod().failed)
