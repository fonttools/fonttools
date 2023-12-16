from fontTools.misc.roundTools import noRound, otRound
from fontTools.misc.intTools import bit_count
from fontTools.ttLib.tables import otTables as ot
from fontTools.varLib.models import supportScalar
from fontTools.varLib.builder import (
    buildVarRegionList,
    buildVarRegion,
    buildMultiVarStore,
    buildMultiVarData,
)
from functools import partial
from collections import defaultdict
from heapq import heappush, heappop


NO_VARIATION_INDEX = ot.NO_VARIATION_INDEX
ot.MultiVarStore.NO_VARIATION_INDEX = NO_VARIATION_INDEX


def _getLocationKey(loc):
    return tuple(sorted(loc.items(), key=lambda kv: kv[0]))


class OnlineMultiVarStoreBuilder(object):
    def __init__(self, axisTags):
        self._axisTags = axisTags
        self._regionMap = {}
        self._regionList = buildVarRegionList([], axisTags)
        self._store = buildMultiVarStore(self._regionList, [])
        self._data = None
        self._model = None
        self._supports = None
        self._varDataIndices = {}
        self._varDataCaches = {}
        self._cache = None

    def setModel(self, model):
        self.setSupports(model.supports)
        self._model = model

    def setSupports(self, supports):
        self._model = None
        self._supports = list(supports)
        if not self._supports[0]:
            del self._supports[0]  # Drop base master support
        self._cache = None
        self._data = None

    def finish(self, optimize=True):
        self._regionList.RegionCount = len(self._regionList.Region)
        self._store.MultiVarDataCount = len(self._store.MultiVarData)
        return self._store

    def _add_MultiVarData(self):
        regionMap = self._regionMap
        regionList = self._regionList

        regions = self._supports
        regionIndices = []
        for region in regions:
            key = _getLocationKey(region)
            idx = regionMap.get(key)
            if idx is None:
                varRegion = buildVarRegion(region, self._axisTags)
                idx = regionMap[key] = len(regionList.Region)
                regionList.Region.append(varRegion)
            regionIndices.append(idx)

        # Check if we have one already...
        key = tuple(regionIndices)
        varDataIdx = self._varDataIndices.get(key)
        if varDataIdx is not None:
            self._outer = varDataIdx
            self._data = self._store.MultiVarData[varDataIdx]
            self._cache = self._varDataCaches[key]
            if len(self._data.Item) == 0xFFFF:
                # This is full.  Need new one.
                varDataIdx = None

        if varDataIdx is None:
            self._data = buildMultiVarData(regionIndices, [])
            self._outer = len(self._store.MultiVarData)
            self._store.MultiVarData.append(self._data)
            self._varDataIndices[key] = self._outer
            if key not in self._varDataCaches:
                self._varDataCaches[key] = {}
            self._cache = self._varDataCaches[key]

    def storeMasters(self, master_values, *, round=round):
        deltas = self._model.getDeltas(master_values, round=round)
        base = deltas.pop(0)
        return base, self.storeDeltas(deltas, round=noRound)

    def storeDeltas(self, deltas, *, round=round):
        deltas = tuple(round(d) for d in deltas)
        deltas_tuple = tuple(tuple(d) for d in deltas)

        if not self._data:
            self._add_MultiVarData()

        varIdx = self._cache.get(deltas_tuple)
        if varIdx is not None:
            return varIdx

        inner = len(self._data.Item)
        if inner == 0xFFFF:
            # Full array. Start new one.
            self._add_MultiVarData()
            return self.storeDeltas(deltas, round=noRound)
        self._data.addItem(deltas, round=noRound)

        varIdx = (self._outer << 16) + inner
        self._cache[deltas_tuple] = varIdx
        return varIdx


def MultiVarData_addItem(self, deltas, *, round=round):
    deltas = tuple(round(d) for d in deltas)

    assert len(deltas) == self.VarRegionCount

    values = []
    for d in deltas:
        values.extend(d)

    values = ot.CvarEncodedValues(values)

    self.Item.append(values)
    self.ItemCount = len(self.Item)


ot.MultiVarData.addItem = MultiVarData_addItem


def MultiVarStore___bool__(self):
    return bool(self.MultiVarData)


ot.MultiVarStore.__bool__ = MultiVarStore___bool__
