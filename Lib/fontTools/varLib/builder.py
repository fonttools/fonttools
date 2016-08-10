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

def buildVarData(varRegionIndices, items):
	self = ot.VarData()
	self.VarRegionIndex = list(varRegionIndices)
	regionCount = self.VarRegionCount = len(self.VarRegionIndex)
	records = self.Item = []
	for item in items:
		assert len(item) == regionCount
		records.append(list(item))
	self.ItemCount = len(self.Item)
	self.NumShorts = self.VarRegionCount # XXX
	return self

def buildVarStore(varTupleList, varDataList):
	self = ot.VarStore()
	self.Format = 1
	self.Reserved = 0
	self.VarRegionList = varTupleList
	self.VarData = list(varDataList)
	self.VarDataCount = len(self.VarData)
	return self

# Variation helpers

def buildVarIdxMap(varIdxes):
	self = ot.VarIdxMap()
	self.mapping = list(varIdxes)
	return self
