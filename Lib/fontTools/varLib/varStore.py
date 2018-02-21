from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.ttLib.tables import otTables as ot
from fontTools.varLib.models import supportScalar
from fontTools.varLib.builder import (buildVarRegionList, buildVarStore,
				      buildVarRegion, buildVarData,
				      VarData_CalculateNumShorts)
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
		if inner == 0xFFFF:
			# Full array. Start new one.
			self.setModel(self._model)
			return self.storeMasters(master_values)
		self._data.Item.append(deltas)
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

	self.prune_regions()

	return varDataMap

ot.VarStore.subset_varidxes = VarStore_subset_varidxes

def VarStore_prune_regions(self):
	"""Remove unused VarRegions."""
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

ot.VarStore.prune_regions = VarStore_prune_regions


def _visit(self, objType, func):
	"""Recurse down from self, if type of an object is objType,
	call func() on it.  Only works for otData-style classes."""

	if type(self) == objType:
		func(self)
		return # We don't recurse down; don't need to.

	if isinstance(self, list):
		for that in self:
			_visit(that, objType, func)

	if hasattr(self, 'getConverters'):
		for conv in self.getConverters():
			that = getattr(self, conv.name, None)
			_visit(that, objType, func)

def _Device_recordVarIdx(self, s):
	"""Add VarIdx in this Device table (if any) to the set s."""
	if self.DeltaFormat == 0x8000:
		s.add((self.StartSize<<16)+self.EndSize)

def Object_collect_device_varidxes(self, varidxes):
	adder = partial(_Device_recordVarIdx, s=varidxes)
	_visit(self, ot.Device, adder)

ot.GDEF.collect_device_varidxes = Object_collect_device_varidxes
ot.GSUB.collect_device_varidxes = Object_collect_device_varidxes
ot.GPOS.collect_device_varidxes = Object_collect_device_varidxes

def _Device_mapVarIdx(self, mapping):
	"""Add VarIdx in this Device table (if any) to the set s."""
	if self.DeltaFormat == 0x8000:
		varIdx = mapping[(self.StartSize<<16)+self.EndSize]
		self.StartSize = varIdx >> 16
		self.EndSize = varIdx & 0xFFFF

def Object_remap_device_varidxes(self, varidxes_map):
	mapper = partial(_Device_mapVarIdx, mapping=varidxes_map)
	_visit(self, ot.Device, mapper)

ot.GDEF.remap_device_varidxes = Object_remap_device_varidxes
ot.GSUB.remap_device_varidxes = Object_remap_device_varidxes
ot.GPOS.remap_device_varidxes = Object_remap_device_varidxes


def VarStore_optimize(self):
	"""Optimize storage. Returns mapping from old VarIdxes to new ones."""

	# TODO
	# Check that no two VarRegions are the same; if they are, fold them.
	# Also that same VarData does not reference same VarRegion more than once...

	mapping = {}

	for major,data in enumerate(self.VarData):
		for minor,row in enumerate(data.Item):
			mapping[(major<<16)+minor] = (major<<16)+minor

	self.prune_regions()

	# Recalculate things and go home.
	self.VarRegionList.RegionCount = len(self.VarRegionList.Region)
	self.VarDataCount = len(self.VarData)
	for data in self.VarData:
		data.ItemCount = len(data.Item)
		VarData_CalculateNumShorts(data)

	return mapping

ot.VarStore.optimize = VarStore_optimize


def main(args=None):
	from argparse import ArgumentParser
	from fontTools import configLogger
	from fontTools.ttLib import TTFont
	from fontTools.ttLib.tables.otBase import OTTableWriter

	parser = ArgumentParser(prog='varLib.varStore')
	parser.add_argument('fontfile')
	parser.add_argument('outfile', nargs='?')
	options = parser.parse_args(args)

	# TODO: allow user to configure logging via command-line options
	configLogger(level="INFO")

	fontfile = options.fontfile
	outfile = options.outfile

	font = TTFont(fontfile)
	gdef = font['GDEF']
	store = gdef.table.VarStore

	#writer = OTTableWriter()
	#store.compile(writer, font)
	#size = len(writer.getAllData())
	#print("Before: %7d bytes" % size)

	store.optimize()

	writer = OTTableWriter()
	store.compile(writer, font)
	size = len(writer.getAllData())
	print("After:  %7d bytes" % size)

	if outfile is not None:
		font.save(outfile)


if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		sys.exit(main())
	import doctest
	sys.exit(doctest.testmod().failed)
