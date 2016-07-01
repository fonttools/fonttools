from __future__ import print_function, division, absolute_import
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot

# VariationStore

def buildVarAxis(axisTag, axisSupport):
	self = ot.VarAxis()
	self.VarAxisID = axisTag
	self.StartCoord, self.PeakCoord, self.EndCoord = axisSupport
	return self

def buildVarTuple(support):
	self = ot.VarTuple()
	self.VarAxis = []
	for axisTag in sorted(support.keys()): # TODO order by axisIdx instead of tag?!
		self.VarAxis.append(buildVarAxis(axisTag, support[axisTag]))
	self.VarAxisCount = len(self.VarAxis)
	return self

def buildVarTupleList(supports):
	self = ot.VarTupleList()
	self.VarTuple = []
	for support in supports:
		self.VarTuple.append(buildVarTuple(support))
	self.VarTupleCount = len(self.VarTuple)
	return self

def buildVarDeltas(varTupleIndexes, items):
	self = ot.VarDeltas()
	self.Format = 1 if all(all(128 <= delta <= 127 for delta in item) for item in items) else 2
	self.VarTupleIndex = list(varTupleIndexes)
	tupleCount = self.VarTupleCount = len(self.VarTupleIndex)
	records = self.Item = []
	for item in items:
		assert len(item) == tupleCount
		record = ot.VarItemByteRecord() if self.Format == 1 else ot.VarItemShortRecord()
		record.Deltas = list(item)
		records.append(record)
	self.ItemCount = len(self.Item)
	return self

def buildVarStore(varTupleList, varDeltasList):
	self = ot.VarStore()
	self.Format = 1
	self.VarTupleList = varTupleList
	self.VarDeltas = list(varDeltasList)
	self.VarDeltasCount = len(self.VarDeltas)
	return self

# Variation helpers

def buildVarIdxMap(varIdxes):
	self = ot.VarIdxMap()
	self.VarIdx = varIdxes = list(varIdxes)
	self.VarIdxCount = len(self.VarIdx)
	self.Format = 1 if all(x <= 0xFFFF for x in varIdxes) else 2
	return self
