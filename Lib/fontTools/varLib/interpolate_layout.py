"""
Interpolate OpenType Layout tables (GDEF / GPOS / GSUB).
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables import otBase as otBase
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.varLib import designspace, models, builder
from fontTools.varLib.merger import merge_tables, Merger
from functools import reduce
import os.path

class InstancerMerger(Merger):

	def __init__(self, font, model, location):
		Merger.__init__(self, font)
		self.model = model
		self.location = location

@InstancerMerger.merger(ot.Anchor)
def merge(merger, self, lst):
	XCoords = [a.XCoordinate for a in lst]
	YCoords = [a.YCoordinate for a in lst]
	model = merger.model
	location = merger.location
	self.XCoordinate = round(model.interpolateFromMasters(location, XCoords))
	self.YCoordinate = round(model.interpolateFromMasters(location, YCoords))

@InstancerMerger.merger(otBase.ValueRecord)
def merge(merger, self, lst):
	model = merger.model
	location = merger.location
	# TODO Handle differing valueformats
	for name, tableName in [('XAdvance','XAdvDevice'),
				('YAdvance','YAdvDevice'),
				('XPlacement','XPlaDevice'),
				('YPlacement','YPlaDevice')]:

		assert not hasattr(self, tableName)

		if hasattr(self, name):
			values = [getattr(a, name, 0) for a in lst]
			value = round(model.interpolateFromMasters(location, values))
			setattr(self, name, value)

def _SinglePosUpgradeToFormat2(self):
	if self.Format == 2: return self

	ret = ot.SinglePos()
	ret.Format = 2
	ret.Coverage = self.Coverage
	ret.ValueFormat = self.ValueFormat
	ret.Value = [self.Value for g in ret.Coverage.glyphs]
	ret.ValueCount = len(ret.Value)

	return ret

def _merge_GlyphOrders(font, lst, values_lst=None, default=None):
	"""Takes font and list of glyph lists (must be sorted by glyph id), and returns
	two things:
	- Combined glyph list,
	- If values_lst is None, return input glyph lists, but padded with None when a glyph
	  was missing in a list.  Otherwise, return values_lst list-of-list, padded with None
	  to match combined glyph lists.
	"""
	if values_lst is None:
		dict_sets = [set(l) for l in lst]
	else:
		dict_sets = [{g:v for g,v in zip(l,vs)} for l,vs in zip(lst,values_lst)]
	combined = set()
	combined.update(*dict_sets)

	sortKey = font.getReverseGlyphMap().__getitem__
	order = sorted(combined, key=sortKey)
	# Make sure all input glyphsets were in proper order
	assert all(sorted(vs, key=sortKey) == vs for vs in lst)
	del combined

	paddedValues = None
	if values_lst is None:
		padded = [[glyph if glyph in dict_set else default
			   for glyph in order]
			  for dict_set in dict_sets]
	else:
		assert len(lst) == len(values_lst)
		padded = [[dict_set[glyph] if glyph in dict_set else default
			   for glyph in order]
			  for dict_set in dict_sets]
	return order, padded

def _Lookup_SinglePos_get_effective_value(self, glyph):
	if self is None: return None
	subtables = self.SubTable
	for self in subtables:
		if self is None or \
		   type(self) != ot.SinglePos or \
		   self.Coverage is None or \
		   glyph not in self.Coverage.glyphs:
			continue
		if self.Format == 1:
			return self.Value
		elif self.Format == 2:
			return self.Value[self.Coverage.glyphs.index(glyph)]
		else:
			assert 0
	return None

def _Lookup_PairPos_get_effective_value_pair(self, firstGlyph, secondGlyph):
	if self is None: return None
	subtables = self.SubTable
	for self in subtables:
		if self is None or \
		   type(self) != ot.PairPos or \
		   self.Coverage is None or \
		   firstGlyph not in self.Coverage.glyphs:
			continue
		if self.Format == 1:
			ps = self.PairSet[self.Coverage.glyphs.index(firstGlyph)]
			pvr = ps.PairValueRecord
			for rec in pvr: # TODO Speed up
				if rec.SecondGlyph == secondGlyph:
					return rec
			continue
		elif self.Format == 2:
			klass1 = self.ClassDef1.classDefs.get(firstGlyph, 0)
			klass2 = self.ClassDef2.classDefs.get(secondGlyph, 0)
			return self.Class1Record[klass1].Class2Record[klass2]
		else:
			assert 0
	return None

@InstancerMerger.merger(ot.SinglePos)
def merge(merger, self, lst):
	self.ValueFormat = valueFormat = reduce(int.__or__, [l.ValueFormat for l in lst])
	assert valueFormat & ~0xF == 0, valueFormat

	# If all have same coverage table and all are format 1,
	if all(v.Format == 1 for v in lst) and all(self.Coverage.glyphs == v.Coverage.glyphs for v in lst):
		self.Value = otBase.ValueRecord(valueFormat)
		merger.mergeThings(self.Value, [v.Value for v in lst])
		return

	# Upgrade everything to Format=2
	self.Format = 2
	lst = [_SinglePosUpgradeToFormat2(v) for v in lst]

	# Align them
	glyphs, padded = _merge_GlyphOrders(merger.font,
					    [v.Coverage.glyphs for v in lst],
					    [v.Value for v in lst])

	self.Coverage.glyphs = glyphs
	self.Value = [otBase.ValueRecord(valueFormat) for g in glyphs]
	self.ValueCount = len(self.Value)

	for i,values in enumerate(padded):
		for j,glyph in enumerate(glyphs):
			if values[j] is not None: continue
			# Fill in value from other subtables
			v = _Lookup_SinglePos_get_effective_value(merger.lookups[i], glyph)
			if v is None:
				v = otBase.ValueRecord(valueFormat)
			values[j] = v

	merger.mergeLists(self.Value, padded)

	# Merge everything else; though, there shouldn't be anything else. :)
	merger.mergeObjects(self, lst,
			    exclude=('Format', 'Coverage', 'ValueRecord', 'Value', 'ValueCount'))

@InstancerMerger.merger(ot.PairSet)
def merge(merger, self, lst):
	# Align them
	glyphs, padded = _merge_GlyphOrders(merger.font,
				[[v.SecondGlyph for v in vs.PairValueRecord] for vs in lst],
				[vs.PairValueRecord for vs in lst])

	self.PairValueRecord = pvrs = []
	for glyph in glyphs:
		pvr = ot.PairValueRecord()
		pvr.SecondGlyph = glyph
		pvr.Value1 = otBase.ValueRecord(merger.valueFormat1) if merger.valueFormat1 else None
		pvr.Value2 = otBase.ValueRecord(merger.valueFormat2) if merger.valueFormat2 else None
		pvrs.append(pvr)
	self.PairValueCount = len(self.PairValueRecord)

	for i,values in enumerate(padded):
		for j,glyph in enumerate(glyphs):
			if values[j] is not None: continue
			# Fill in value from other subtables
			v = ot.PairValueRecord()
			v.SecondGlyph = glyph
			vpair = _Lookup_PairPos_get_effective_value_pair(merger.lookups[i], self._firstGlyph, glyph)
			if vpair is None:
				v.Value1 = otBase.ValueRecord(merger.valueFormat1) if merger.valueFormat1 else None
				v.Value2 = otBase.ValueRecord(merger.valueFormat2) if merger.valueFormat2 else None
			else:
				v.Value1, v.Value2 = vpair.Value1, vpair.Value2
			values[j] = v
	del self._firstGlyph

	merger.mergeThings(self.PairValueRecord, padded)

@InstancerMerger.merger(ot.PairPos)
def merge(merger, self, lst):
	# TODO Support differing ValueFormats.
	merger.valueFormat1 = self.ValueFormat1
	merger.valueFormat2 = self.ValueFormat2

	if self.Format == 2:
		# Everything must match; we don't support smart merge yet.
		merger.mergeObjects(self, lst)
		del merger.valueFormat1, merger.valueFormat2
		return

	assert self.Format == 1
	# Merge everything else; makes sure Format is the same.
	merger.mergeObjects(self, lst,
			    exclude=('Coverage',
				     'PairSet', 'PairSetCount'))

	# Align them
	glyphs, padded = _merge_GlyphOrders(merger.font,
					    [v.Coverage.glyphs for v in lst],
					    [v.PairSet for v in lst])

	empty = ot.PairSet()
	empty.PairValueRecord = []
	empty.PairValueCount = 0

	for i,values in enumerate(padded):
		for j,glyph in enumerate(glyphs):
			if values[j] is not None: continue
			values[j] = empty

	self.Coverage.glyphs = glyphs
	self.PairSet = [ot.PairSet() for g in glyphs]
	self.PairSetCount = len(self.PairSet)
	for glyph, ps in zip(glyphs, self.PairSet):
		ps._firstGlyph = glyph

	merger.mergeThings(self.PairSet, padded)

	del merger.valueFormat1, merger.valueFormat2

@InstancerMerger.merger(ot.Lookup)
def merge(merger, self, lst):
	merger.lookups = lst
	merger.mergeObjects(self, lst)
	del merger.lookups


def interpolate_layout(designspace_filename, loc, finder):

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
	master_ttfs = [finder(os.path.join(basedir, m['filename'])) for m in masters]
	master_fonts = [TTFont(ttf_path) for ttf_path in master_ttfs]

	#font = master_fonts[base_idx]
	font = TTFont(master_ttfs[base_idx])

	master_locs = [o['location'] for o in masters]

	axis_tags = set(master_locs[0].keys())
	assert all(axis_tags == set(m.keys()) for m in master_locs)

	# Set up axes
	axes = {}
	for tag in axis_tags:
		default = master_locs[base_idx][tag]
		lower = min(m[tag] for m in master_locs)
		upper = max(m[tag] for m in master_locs)
		axes[tag] = (lower, default, upper)
	print("Axes:")
	pprint(axes)

	print("Location:", loc)
	print("Master locations:")
	pprint(master_locs)

	# Normalize locations
	loc = models.normalizeLocation(loc, axes)
	master_locs = [models.normalizeLocation(m, axes) for m in master_locs]

	print("Normalized location:", loc)
	print("Normalized master locations:")
	pprint(master_locs)

	# Assume single-model for now.
	model = models.VariationModel(master_locs)
	assert 0 == model.mapping[base_idx]

	merger = InstancerMerger(font, model, loc)

	print("Building variations tables")
	merge_tables(font, merger, master_fonts, axes, base_idx, ['GPOS'])
	return font


def main(args=None):

	import sys
	if args is None:
		args = sys.argv[1:]

	designspace_filename = args[0]
	locargs = args[1:]
	outfile = os.path.splitext(designspace_filename)[0] + '-instance.ttf'

	finder = lambda s: s.replace('master_ufo', 'master_ttf_interpolatable').replace('.ufo', '.ttf')

	loc = {}
	for arg in locargs:
		tag,val = arg.split('=')
		loc[tag] = float(val)

	font = interpolate_layout(designspace_filename, loc, finder)
	print("Saving font", outfile)
	font.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		main()
		#sys.exit(0)
	import doctest, sys
	sys.exit(doctest.testmod().failed)
