from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.varLib.models import supportScalar
from fontTools.varLib.builder import (buildVarRegionList, buildVarStore,
				      buildVarRegion, buildVarData,
				      VarData_CalculateNumShorts)
from fontTools.ttLib.tables import otTables
from functools import partial


def _getLocationKey(loc):
	return tuple(sorted(loc.items(), key=lambda kv: kv[0]))


class OnlineVarStoreBuilder(object):

	def __init__(self, axisTags):
		self._axisTags = axisTags
		self._regionMap = {}
		self._regionList = buildVarRegionList([], axisTags)
		self._store = buildVarStore(self._regionList, [])

	def setModel(self, model):
		self._model = model

		regionMap = self._regionMap
		regionList = self._regionList

		regions = model.supports[1:]
		regionIndices = []
		for region in regions:
			key = _getLocationKey(region)
			idx = regionMap.get(key)
			if idx is None:
				varRegion = buildVarRegion(region, self._axisTags)
				idx = regionMap[key] = len(regionList.Region)
				regionList.Region.append(varRegion)
			regionIndices.append(idx)

		data = self._data = buildVarData(regionIndices, [], optimize=False)
		self._outer = len(self._store.VarData)
		self._store.VarData.append(data)

	def finish(self, optimize=True):
		self._regionList.RegionCount = len(self._regionList.Region)
		self._store.VarDataCount = len(self._store.VarData)
		for data in self._store.VarData:
			data.ItemCount = len(data.Item)
			VarData_CalculateNumShorts(data, optimize)
		return self._store

	def storeMasters(self, master_values):
		deltas = [round(d) for d in self._model.getDeltas(master_values)]
		base = deltas.pop(0)
		inner = len(self._data.Item)
		self._data.Item.append(deltas)
		# TODO Check for full data array?
		return base, (self._outer << 16) + inner


def VarRegion_get_support(self, fvar_axes):
	return {fvar_axes[i].axisTag: (reg.StartCoord,reg.PeakCoord,reg.EndCoord)
		for i,reg in enumerate(self.VarRegionAxis)}

class VarStoreInstancer(object):

	def __init__(self, varstore, fvar_axes, location={}):
		self.fvar_axes = fvar_axes
		assert varstore is None or varstore.Format == 1
		self._varData = varstore.VarData if varstore else []
		self._regions = varstore.VarRegionList.Region if varstore else []
		self.setLocation(location)

	def setLocation(self, location):
		self.location = dict(location)
		self._clearCaches()

	def _clearCaches(self):
		self._scalars = {}

	def _getScalar(self, regionIdx):
		scalar = self._scalars.get(regionIdx)
		if scalar is None:
			support = VarRegion_get_support(self._regions[regionIdx], self.fvar_axes)
			scalar = supportScalar(self.location, support)
			self._scalars[regionIdx] = scalar
		return scalar

	def __getitem__(self, varidx):

		major, minor = varidx >> 16, varidx & 0xFFFF

		varData = self._varData
		scalars = [self._getScalar(ri) for ri in varData[major].VarRegionIndex]

		deltas = varData[major].Item[minor]
		delta = 0.
		for d,s in zip(deltas, scalars):
			delta += d * s
		return delta


#
# Optimizations
#

def VarStore_subset_varidxes(self, varIdxes, optimize=True):

	# Sort out used varIdxes by major/minor.
	used = {}
	for varIdx in varIdxes:
		major = varIdx >> 16
		minor = varIdx & 0xFFFF
		d = used.get(major)
		if d is None:
			d = used[major] = set()
		d.add(minor)
	del varIdxes

	#
	# Subset VarData
	#

	varData = self.VarData
	newVarData = []
	varDataMap = {}
	for major,data in enumerate(varData):
		usedMinors = used.get(major)
		if usedMinors is None:
			continue
		newMajor = varDataMap[major] = len(newVarData)
		newVarData.append(data)

		items = data.Item
		newItems = []
		for minor in sorted(usedMinors):
			newMinor = len(newItems)
			newItems.append(items[minor])
			varDataMap[(major<<16)+minor] = (newMajor<<16)+newMinor

		data.Item = newItems
		data.ItemCount = len(data.Item)

		if optimize:
			VarData_CalculateNumShorts(data)

	self.VarData = newVarData
	self.VarDataCount = len(self.VarData)

	#
	# Subset VarRegionList
	#

	# Collect.
	usedRegions = set()
	for data in self.VarData:
		usedRegions.update(data.VarRegionIndex)
	# Subset.
	regionList = self.VarRegionList
	regions = regionList.Region
	newRegions = []
	regionMap = {}
	for i in sorted(usedRegions):
		regionMap[i] = len(newRegions)
		newRegions.append(regions[i])
	regionList.Region = newRegions
	regionList.RegionCount = len(regionList.Region)
	# Map.
	for data in self.VarData:
		data.VarRegionIndex = [regionMap[i] for i in data.VarRegionIndex]

	return varDataMap


def Device_recordVarIdx(self, s):
	"""Add VarIdx in this Device table (if any) to the set s."""
	if self.DeltaFormat == 0x8000:
		s.add((self.StartSize<<16)+self.EndSize)

def Device_mapVarIdx(self, mapping):
	"""Add VarIdx in this Device table (if any) to the set s."""
	if self.DeltaFormat == 0x8000:
		varIdx = mapping[(self.StartSize<<16)+self.EndSize]
		self.StartSize = varIdx >> 16
		self.EndSize = varIdx & 0xFFFF


def visit(self, objType, func):
	"""Recurse down from self, if type of an object is objType,
	call func() on it.  Only works for otData-style classes."""

	if type(self) == objType:
		func(self)
		return # We don't recurse down; don't need to.

	if isinstance(self, list):
		for that in self:
			visit(that, objType, func)

	if hasattr(self, 'getConverters'):
		for conv in self.getConverters():
			that = getattr(self, conv.name, None)
			visit(that, objType, func)


def pruneGDEF(font):
	if 'GDEF' not in font: return
	gdef = font['GDEF']
	table = gdef.table
	if not hasattr(table, 'VarStore'): return

	store = table.VarStore
	table.VarStore = None # Disable while we work on it.

	usedVarIdxes = set()

	# Collect.
	adder = partial(Device_recordVarIdx, s=usedVarIdxes)
	visit(table, otTables.Device, adder)
	if 'GSUB' in font:
		visit(font['GSUB'].table, otTables.Device, adder)
	if 'GPOS' in font:
		visit(font['GPOS'].table, otTables.Device, adder)

	# Subset.
	varidx_map = VarStore_subset_varidxes(store, usedVarIdxes)

	# Map.
	mapper = partial(Device_mapVarIdx, mapping=varidx_map)
	visit(table, otTables.Device, mapper)
	if 'GSUB' in font:
		visit(font['GSUB'].table, otTables.Device, mapper)
	if 'GPOS' in font:
		visit(font['GPOS'].table, otTables.Device, mapper)

	table.VarStore = store
