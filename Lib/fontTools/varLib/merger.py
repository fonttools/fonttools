"""
Merge OpenType Layout tables (GDEF / GPOS / GSUB).
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import classifyTools
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables import otBase as otBase
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.varLib import builder
from functools import reduce


class Merger(object):

	def __init__(self, font=None):
		self.font = font

	@classmethod
	def merger(celf, clazzes, attrs=(None,)):
		assert celf != Merger, 'Subclass Merger instead.'
		if 'mergers' not in celf.__dict__:
			celf.mergers = {}
		if type(clazzes) == type:
			clazzes = (clazzes,)
		if type(attrs) == str:
			attrs = (attrs,)
		def wrapper(method):
			assert method.__name__ == 'merge'
			done = []
			for clazz in clazzes:
				if clazz in done: continue # Support multiple names of a clazz
				done.append(clazz)
				mergers = celf.mergers.setdefault(clazz, {})
				for attr in attrs:
					assert attr not in mergers, \
						"Oops, class '%s' has merge function for '%s' defined already." % (clazz.__name__, attr)
					mergers[attr] = method
			return None
		return wrapper

	@classmethod
	def mergersFor(celf, thing, _default={}):
		typ = type(thing)

		for celf in celf.mro():

			mergers = getattr(celf, 'mergers', None)
			if mergers is None:
				break;

			m = celf.mergers.get(typ, None)
			if m is not None:
				return m

		return _default

	def mergeObjects(self, out, lst, exclude=()):
		keys = sorted(vars(out).keys())
		assert all(keys == sorted(vars(v).keys()) for v in lst), \
			(keys, [sorted(vars(v).keys()) for v in lst])
		mergers = self.mergersFor(out)
		defaultMerger = mergers.get('*', self.__class__.mergeThings)
		try:
			for key in keys:
				if key in exclude: continue
				value = getattr(out, key)
				values = [getattr(table, key) for table in lst]
				mergerFunc = mergers.get(key, defaultMerger)
				mergerFunc(self, value, values)
		except Exception as e:
			e.args = e.args + ('.'+key,)
			raise

	def mergeLists(self, out, lst):
		count = len(out)
		assert all(count == len(v) for v in lst), (count, [len(v) for v in lst])
		for i,(value,values) in enumerate(zip(out, zip(*lst))):
			try:
				self.mergeThings(value, values)
			except Exception as e:
				e.args = e.args + ('[%d]' % i,)
				raise

	def mergeThings(self, out, lst):
		clazz = type(out)
		try:
			assert all(type(item) == clazz for item in lst), (out, lst)
			mergerFunc = self.mergersFor(out).get(None, None)
			if mergerFunc is not None:
				mergerFunc(self, out, lst)
			elif hasattr(out, '__dict__'):
				self.mergeObjects(out, lst)
			elif isinstance(out, list):
				self.mergeLists(out, lst)
			else:
				assert all(out == v for v in lst), (out, lst)
		except Exception as e:
			e.args = e.args + (clazz.__name__,)
			raise

	def mergeTables(self, font, master_ttfs, axes, base_idx, tables):

		for tag in tables:
			if tag not in font: continue
			print('Merging', tag)
			self.mergeThings(font[tag], [m[tag] for m in master_ttfs])

#
# Aligning merger
#
class AligningMerger(Merger):
	pass

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

def _Lookup_SinglePos_get_effective_value(subtables, glyph):
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

def _Lookup_PairPos_get_effective_value_pair(subtables, firstGlyph, secondGlyph):
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

@AligningMerger.merger(ot.SinglePos)
def merge(merger, self, lst):
	self.ValueFormat = valueFormat = reduce(int.__or__, [l.ValueFormat for l in lst], 0)
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
			v = _Lookup_SinglePos_get_effective_value(merger.lookup_subtables[i], glyph)
			if v is None:
				v = otBase.ValueRecord(valueFormat)
			values[j] = v

	merger.mergeLists(self.Value, padded)

	# Merge everything else; though, there shouldn't be anything else. :)
	merger.mergeObjects(self, lst,
			    exclude=('Format', 'Coverage', 'ValueRecord', 'Value', 'ValueCount'))

@AligningMerger.merger(ot.PairSet)
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
			# Fill in value from other subtables
			v = ot.PairValueRecord()
			v.SecondGlyph = glyph
			if values[j] is not None:
				vpair = values[j]
			else:
				vpair = _Lookup_PairPos_get_effective_value_pair(merger.lookup_subtables[i], self._firstGlyph, glyph)
			if vpair is None:
				v1, v2 = None, None
			else:
				v1, v2 = vpair.Value1, vpair.Value2
			v.Value1 = otBase.ValueRecord(merger.valueFormat1, src=v1) if merger.valueFormat1 else None
			v.Value2 = otBase.ValueRecord(merger.valueFormat2, src=v2) if merger.valueFormat2 else None
			values[j] = v
	del self._firstGlyph

	merger.mergeLists(self.PairValueRecord, padded)

def _PairPosFormat1_merge(self, lst, merger):
	# Merge everything else; makes sure Format is the same.
	merger.mergeObjects(self, lst,
			    exclude=('Coverage',
				     'PairSet', 'PairSetCount'))

	empty = ot.PairSet()
	empty.PairValueRecord = []
	empty.PairValueCount = 0

	# Align them
	glyphs, padded = _merge_GlyphOrders(merger.font,
					    [v.Coverage.glyphs for v in lst],
					    [v.PairSet for v in lst],
					    default=empty)

	self.Coverage.glyphs = glyphs
	self.PairSet = [ot.PairSet() for g in glyphs]
	self.PairSetCount = len(self.PairSet)
	for glyph, ps in zip(glyphs, self.PairSet):
		ps._firstGlyph = glyph

	merger.mergeLists(self.PairSet, padded)

def _ClassDef_invert(self, allGlyphs=None):

	classDefs = self.classDefs if self and self.classDefs else {}
	m = max(classDefs.values()) if classDefs else 0

	ret = []
	for _ in range(m + 1):
		ret.append(set())

	for k,v in classDefs.items():
		ret[v].add(k)

	# Class-0 is special.  It's "everything else".
	if allGlyphs is None:
		ret[0] = None
	else:
		ret[0] = set(allGlyphs)
		for s in ret[1:]:
			ret[0].difference_update(s)

	return ret

def _ClassDef_merge_classify(lst, allGlyphs=None):
	self = ot.ClassDef()
	self.classDefs = classDefs = {}

	classifier = classifyTools.Classifier()
	for l in lst:
		sets = _ClassDef_invert(l, allGlyphs=allGlyphs)
		if allGlyphs is None:
			sets = sets[1:]
		classifier.update(sets)
	classes = classifier.getClasses()

	if allGlyphs is None:
		classes.insert(0, set())

	for i,classSet in enumerate(classes):
		if i == 0:
			continue
		for g in classSet:
			classDefs[g] = i

	return self, classes

def _ClassDef_calculate_Format(self, font):
	fmt = 2
	ranges = self._getClassRanges(font)
	if ranges:
		startGlyph = ranges[0][1]
		endGlyph = ranges[-1][3]
		glyphCount = endGlyph - startGlyph + 1
		if len(ranges) * 3 >= glyphCount + 1:
			# Format 1 is more compact
			fmt = 1
	self.Format = fmt

def _PairPosFormat2_merge(self, lst, merger):
	merger.mergeObjects(self, lst,
			    exclude=('Coverage',
				     'ClassDef1', 'Class1Count',
				     'ClassDef2', 'Class2Count',
				     'Class1Record'))

	# Align coverages
	glyphs, _ = _merge_GlyphOrders(merger.font,
				       [v.Coverage.glyphs for v in lst])
	self.Coverage.glyphs = glyphs
	glyphSet = set(glyphs)

	# Currently, if the coverage of PairPosFormat2 subtables are different,
	# we do NOT bother walking down the subtable list when filling in new
	# rows for alignment.  As such, this is only correct if current subtable
	# is the last subtable in the lookup.  Ensure that.
	#
	# Note that our canonicalization process merges some PairPosFormat2's,
	# so in reality this might not be common.
	#
	# TODO: Remove this requirement
	for l,subtables in zip(lst,merger.lookup_subtables):
		if l.Coverage.glyphs != glyphs:
			assert l == subtables[-1]

	matrices = [l.Class1Record for l in lst]

	# Align first classes
	self.ClassDef1, classes = _ClassDef_merge_classify([l.ClassDef1 for l in lst], allGlyphs=glyphSet)
	_ClassDef_calculate_Format(self.ClassDef1, merger.font)
	self.Class1Count = len(classes)
	new_matrices = []
	for l,matrix in zip(lst, matrices):
		nullRow = None
		coverage = set(l.Coverage.glyphs)
		classDef1 = l.ClassDef1.classDefs
		class1Records = []
		for classSet in classes:
			exemplarGlyph = next(iter(classSet))
			if exemplarGlyph not in coverage:
				if nullRow is None:
					nullRow = ot.Class1Record()
					class2records = nullRow.Class2Record = []
					# TODO: When merger becomes selfless, revert e6125b353e1f54a0280ded5434b8e40d042de69f
					for _ in range(l.Class2Count):
						rec2 = ot.Class2Record()
						rec2.Value1 = otBase.ValueRecord(l.ValueFormat1) if l.ValueFormat1 else None
						rec2.Value2 = otBase.ValueRecord(l.ValueFormat2) if l.ValueFormat2 else None
						class2records.append(rec2)
				rec1 = nullRow
			else:
				klass = classDef1.get(exemplarGlyph, 0)
				rec1 = matrix[klass] # TODO handle out-of-range?
			class1Records.append(rec1)
		new_matrices.append(class1Records)
	matrices = new_matrices
	del new_matrices

	# Align second classes
	self.ClassDef2, classes = _ClassDef_merge_classify([l.ClassDef2 for l in lst])
	_ClassDef_calculate_Format(self.ClassDef2, merger.font)
	self.Class2Count = len(classes)
	new_matrices = []
	for l,matrix in zip(lst, matrices):
		classDef2 = l.ClassDef2.classDefs
		class1Records = []
		for rec1old in matrix:
			oldClass2Records = rec1old.Class2Record
			rec1new = ot.Class1Record()
			class2Records = rec1new.Class2Record = []
			for classSet in classes:
				if not classSet: # class=0
					rec2 = oldClass2Records[0]
				else:
					exemplarGlyph = next(iter(classSet))
					klass = classDef2.get(exemplarGlyph, 0)
					rec2 = oldClass2Records[klass]
				class2Records.append(rec2)
			class1Records.append(rec1new)
		new_matrices.append(class1Records)
	matrices = new_matrices
	del new_matrices

	self.Class1Record = list(matrices[0]) # TODO move merger to be selfless
	merger.mergeLists(self.Class1Record, matrices)

@AligningMerger.merger(ot.PairPos)
def merge(merger, self, lst):
	# TODO Support differing ValueFormats.
	merger.valueFormat1 = self.ValueFormat1
	merger.valueFormat2 = self.ValueFormat2

	if self.Format == 1:
		_PairPosFormat1_merge(self, lst, merger)
	elif self.Format == 2:
		_PairPosFormat2_merge(self, lst, merger)
	else:
		assert 0

	del merger.valueFormat1, merger.valueFormat2

	# Now examine the list of value records, and update to the union of format values,
	# as merge might have created new values.
	vf1 = 0
	vf2 = 0
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


def _PairSet_merge_overlay(lst, font):
	self = ot.PairSet()
	self.Coverage = ot.Coverage()
	self.Coverage.Format = 1

	# Align them
	glyphs, padded = _merge_GlyphOrders(font,
				[[v.SecondGlyph for v in vs.PairValueRecord] for vs in lst],
				[vs.PairValueRecord for vs in lst])

	self.Coverage.glyphs = glyphs
	self.PairValueRecord = pvrs = []
	for values in zip(*padded):
		for v in values:
			if v is not None:
				pvrs.append(v)
				break
		else:
			assert False
	self.PairValueCount = len(self.PairValueRecord)

	return self

def _Lookup_PairPosFormat1_subtables_merge_overlay(lst, font):
	self = ot.PairPos()
	self.Format = 1
	self.Coverage = ot.Coverage()
	self.Coverage.Format = 1
	self.ValueFormat1 = reduce(int.__or__, [l.ValueFormat1 for l in lst], 0)
	self.ValueFormat2 = reduce(int.__or__, [l.ValueFormat2 for l in lst], 0)

	# Align them
	glyphs, padded = _merge_GlyphOrders(font,
					    [v.Coverage.glyphs for v in lst],
					    [v.PairSet for v in lst])

	self.Coverage.glyphs = glyphs
	self.PairSet = [_PairSet_merge_overlay([v for v in values if v is not None], font)
		        for values in zip(*padded)]
	self.PairSetCount = len(self.PairSet)
	return self

def _Lookup_PairPosFormat2_subtables_recombine(a, b, font):
	"""Combine two subtables that have the same general structure already."""
	self = ot.PairPos()
	self.Format = 2
	self.Coverage = ot.Coverage()
	self.Coverage.Format = 1
	glyphs, _ = _merge_GlyphOrders(font,
				       [v.Coverage.glyphs for v in (a, b)])

	self.Coverage.glyphs = glyphs
	self.Class1Count = a.Class1Count + b.Class1Count
	self.ClassDef1 = ot.ClassDef()

	classDefs = ot.ClassDef1.classDefs = {}
	offset = a.Class1Count
	# First subtable overrides any possible shared glyph, so add b first.
	sets = _ClassDef_invert(b.ClassDef1, allGlyphs=b.Coverage.glyphs)
	for i,s in enumerate(sets):
		for g in s:
			classDefs[g] = i + offset
	sets = _ClassDef_invert(a.ClassDef1, allGlyphs=a.Coverage.glyphs)
	assert len(sets) <= offset
	for i,s in enumerate(sets):
		for g in s:
			classDefs[g] = i

	records = self.Class1Record = []
	assert a.Class1Count == len(a.Class1Record)
	assert b.Class1Count == len(b.Class1Record)
	records.extend(a.Class1Record)
	records.extend(b.Class1Record)

	for name in ('Class2Count', 'ClassDef2', 'ValueFormat1', 'ValueFormat2'):
		setattr(self, name, getattr(a, name))

	return self

def _Lookup_PairPos_subtables_canonicalize(lst, font):
	"""Merge multiple Format1 subtables at the beginning of lst,
	and merge multiple consecutive Format2 subtables that have the same
	Class2 (ie. were split because of offset overflows).  Returns new list."""
	head = []
	tail = []
	it = iter(lst)

	for subtable in it:
		if subtable.Format == 1:
			head.append(subtable)
			continue
		tail.append(subtable)
		break
	tail.insert(0, _Lookup_PairPosFormat1_subtables_merge_overlay(head, font))

	for subtable in it:
		oldtable = tail[-1]
		if oldtable.Format == 2 and subtable.Format == 2:
			if (oldtable.Class2Count == subtable.Class2Count and
			    oldtable.ClassDef2.classDefs == subtable.ClassDef2.classDefs and
			    oldtable.ValueFormat1 == subtable.ValueFormat1 and
			    oldtable.ValueFormat2 == subtable.ValueFormat2):
				newtable = _Lookup_PairPosFormat2_subtables_recombine(oldtable, subtable, font)
				tail[-1] = newtable
			continue
		tail.append(subtable)

	return tail

@AligningMerger.merger(ot.Lookup)
def merge(merger, self, lst):
	merger.lookup_subtables = [l.SubTable for l in lst]

	exclude = []
	if self.SubTable and isinstance(self.SubTable[0], ot.PairPos):

		# AFDKO and feaLib sometimes generate two Format1 subtables instead of one.
		# Merge those before continuing.
		# https://github.com/fonttools/fonttools/issues/719
		self.SubTable = _Lookup_PairPos_subtables_canonicalize(self.SubTable, merger.font)
		subtables = [_Lookup_PairPos_subtables_canonicalize(l.SubTable, merger.font) for l in lst]

		merger.lookup_subtables = subtables
		merger.mergeLists(self.SubTable, subtables)

		# If format-1 subtable created during canonicalization is empty, remove it.
		assert len(self.SubTable) >= 1 and self.SubTable[0].Format == 1
		if not self.SubTable[0].Coverage.glyphs:
			self.SubTable.pop(0)

		self.SubTableCount = len(self.SubTable)
		exclude.extend(['SubTable', 'SubTableCount'])

	merger.mergeObjects(self, lst, exclude=exclude)

	del merger.lookup_subtables

#
# InstancerMerger
#
class InstancerMerger(AligningMerger):

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


#
# VariationMerger
#

class VariationMerger(AligningMerger):

	def __init__(self, model, axisTags, font):
		Merger.__init__(self, font)
		self.model = model
		self.store_builder = builder.OnlineVarStoreBuilder(axisTags)
		self.store_builder.setModel(model)

def _all_equal(lst):
	it = iter(lst)
	v0 = next(it)
	for v in it:
		if v0 != v:
			return False
	return True

def buildVarDevTable(store_builder, master_values):
	if _all_equal(master_values):
		return master_values[0], None
	base, varIdx = store_builder.storeMasters(master_values)
	return base, builder.buildVarDevTable(varIdx)

@VariationMerger.merger(ot.Anchor)
def merge(merger, self, lst):
	assert self.Format == 1
	self.XCoordinate, XDeviceTable = buildVarDevTable(merger.store_builder, [a.XCoordinate for a in lst])
	self.YCoordinate, YDeviceTable = buildVarDevTable(merger.store_builder, [a.YCoordinate for a in lst])
	if XDeviceTable or YDeviceTable:
		self.Format = 3
		self.XDeviceTable = XDeviceTable
		self.YDeviceTable = YDeviceTable

@VariationMerger.merger(otBase.ValueRecord)
def merge(merger, self, lst):
	for name, tableName in [('XAdvance','XAdvDevice'),
				('YAdvance','YAdvDevice'),
				('XPlacement','XPlaDevice'),
				('YPlacement','YPlaDevice')]:

		if hasattr(self, name):
			value, deviceTable = buildVarDevTable(merger.store_builder,
							      [getattr(a, name, 0) for a in lst])
			setattr(self, name, value)
			if deviceTable:
				setattr(self, tableName, deviceTable)
