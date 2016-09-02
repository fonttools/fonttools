from __future__ import print_function, division, absolute_import
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot

# VariationStore

def buildVarRegionAxis(axisSupport):
	self = ot.VarRegionAxis()
	self.StartCoord, self.PeakCoord, self.EndCoord = axisSupport
	return self

def buildVarRegion(support, axisTags):
	self = ot.VarRegion()
	self.VarRegionAxis = []
	for tag in axisTags:
		self.VarRegionAxis.append(buildVarRegionAxis(support.get(tag, (0,0,0))))
	self.VarRegionAxisCount = len(self.VarRegionAxis)
	return self

def buildVarRegionList(supports, axisTags):
	self = ot.VarRegionList()
	self.AxisCount = len(axisTags)
	self.VarRegion = []
	for support in supports:
		self.VarRegion.append(buildVarRegion(support, axisTags))
	self.VarRegionCount = len(self.VarRegion)
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
	for item in items:
		assert len(item) == regionCount
		records.append(list(item))
	self.ItemCount = len(self.Item)
	if optimize:
		optimizeVarData(self)
	return self


def buildVarStore(varRegionList, varDataList):
	self = ot.VarStore()
	self.Format = 1
	self.VarRegionList = varRegionList
	self.VarData = list(varDataList)
	self.VarDataCount = len(self.VarData)
	return self


class OnlineVarStoreBuilder(object):

	def __init__(self, axisTags):
		self._regions = buildVarRegionList([], axisTags)
		self._store = buildVarStore(self._regions, [])

	def setModel(self, model):
		self._model = model
		# Store model's regions

	def finish(self, optimize=True):
		self._regions.VarRegionCount = len(self._regions.VarRegion)
		self._store.VarDataCount = len(self._store.VarData)
		for data in self._store.VarData:
			data.ItemCount = len(data.Item)
			if optimize:
				optimizeVarData(data)
		return self._store


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
