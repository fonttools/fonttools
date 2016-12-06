from __future__ import print_function, division, absolute_import
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot

# VariationStore

def buildVarRegionAxis(axisSupport):
	self = ot.VarRegionAxis()
	self.StartCoord, self.PeakCoord, self.EndCoord = axisSupport
	return self

def buildVarRegion(support, axisTags):
	assert all(tag in axisTags for tag in support.keys()), ("Unknown axis tag found.", support, axisTags)
	self = ot.VarRegion()
	self.VarRegionAxis = []
	for tag in axisTags:
		self.VarRegionAxis.append(buildVarRegionAxis(support.get(tag, (0,0,0))))
	self.VarRegionAxisCount = len(self.VarRegionAxis)
	return self

def buildVarRegionList(supports, axisTags):
	self = ot.VarRegionList()
	self.AxisCount = len(axisTags)
	self.Region = []
	for support in supports:
		self.Region.append(buildVarRegion(support, axisTags))
	self.RegionCount = len(self.Region)
	return self


def _reorderItem(lst, narrows):
	out = []
	count = len(lst)
	for i in range(count):
		if i not in narrows:
			out.append(lst[i])
	for i in range(count):
		if i in narrows:
			out.append(lst[i])
	return out

def optimizeVarData(self):
	# Reorder columns such that all SHORT columns come before UINT8
	count = self.VarRegionCount
	items = self.Item
	narrows = set(range(count))
	for item in items:
		for i in narrows:
			if not (-128 <= item[i] <= 127):
				narrows.remove(i)
				break
		if not narrows:
			break

	self.VarRegionIndex = _reorderItem(self.VarRegionIndex, narrows)
	for i in range(self.ItemCount):
		items[i] = _reorderItem(items[i], narrows)

	return self

def buildVarData(varRegionIndices, items, optimize=True):
	self = ot.VarData()
	self.VarRegionIndex = list(varRegionIndices)
	regionCount = self.VarRegionCount = len(self.VarRegionIndex)
	records = self.Item = []
	if items:
		for item in items:
			assert len(item) == regionCount
			records.append(list(item))
	self.ItemCount = len(self.Item)
	if items and optimize:
		optimizeVarData(self)
	return self


def buildVarStore(varRegionList, varDataList):
	self = ot.VarStore()
	self.Format = 1
	self.VarRegionList = varRegionList
	self.VarData = list(varDataList)
	self.VarDataCount = len(self.VarData)
	return self


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
			if optimize:
				optimizeVarData(data)
		return self._store

	def storeMasters(self, master_values):
		deltas = [int(round(d)) for d in self._model.getDeltas(master_values)[1:]]
		inner = len(self._data.Item)
		self._data.Item.append(deltas)
		# TODO Check for full data array?
		return (self._outer << 16) + inner



# Variation helpers

def buildVarIdxMap(varIdxes):
	# TODO Change VarIdxMap mapping to hold separate outer,inner indices
	self = ot.VarIdxMap()
	self.mapping = list(varIdxes)
	return self

def buildVarDevTable(varIdx):
	self = ot.Device()
	self.DeltaFormat = 0x8000
	self.StartSize = varIdx >> 16
	self.EndSize = varIdx & 0xFFFF
	return self
