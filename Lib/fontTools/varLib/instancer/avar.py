from fontTools.varLib.varStore import VarStoreInstancer, NO_VARIATION_INDEX
from fontTools.ttLib.tables.otTables import VarStore
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.varLib import instancer


def VarStore_getExtremes(
    self, varIdx, identityAxisIndex=None, nullAxes=set(), cache=None
):

    if varIdx == NO_VARIATION_INDEX:
        if identityAxisIndex is None:
            return 0, 0
        else:
            return -16384, 16384

    if cache is None:
        cache = {}

    key = frozenset(nullAxes)
    if key in cache:
        return cache[key]

    regionList = self.VarRegionList

    if not hasattr(self, "_fvar_axes"):
        self._fvar_axes = []
        for i in range(regionList.RegionAxisCount):
            axis = Axis()
            axis.axisTag = str(i)
            axis.minValue = -1.0
            axis.defaultValue = 0.0
            axis.maxValue = 1.0
            self._fvar_axes.append(axis)

    major = varIdx >> 16
    minor = varIdx & 0xFFFF
    varData = self.VarData[major]
    regionIndices = varData.VarRegionIndex

    minV = 0
    maxV = 0
    for regionIndex in regionIndices:
        location = {}
        region = regionList.Region[regionIndex]
        skip = False
        thisAxes = set()
        for i, regionAxis in enumerate(region.VarRegionAxis):
            peak = regionAxis.PeakCoord
            if peak == 0:
                continue
            if i in nullAxes:
                skip = True
                break
            thisAxes.add(i)
            location[str(i)] = peak
        if skip:
            continue

        locs = [None]
        if identityAxisIndex in thisAxes:
            locs = []
            locs.append(-1)
            locs.append(region.VarRegionAxis[identityAxisIndex].StartCoord)
            locs.append(region.VarRegionAxis[identityAxisIndex].PeakCoord)
            locs.append(region.VarRegionAxis[identityAxisIndex].EndCoord)
            locs.append(+1)

        for loc in locs:
            if loc is not None:
                location[str(identityAxisIndex)] = loc

            varStoreInstancer = VarStoreInstancer(varStore, self._fvar_axes, location)
            v = varStoreInstancer[varIdx] + (0 if loc is None else round(loc * 16384))

            assert thisAxes, "Empty region in VarStore!"
            minOther, maxOther = self.getExtremes(
                varIdx, identityAxisIndex, nullAxes | thisAxes, cache
            )

            minV = min(minV, v + minOther)
            maxV = max(maxV, v + maxOther)

    cache[key] = (minV, maxV)

    return minV, maxV


VarStore.getExtremes = VarStore_getExtremes


if __name__ == "__main__":
    import sys
    from fontTools.ttLib import TTFont

    font = TTFont(sys.argv[1])

    limits = sys.argv[2:]
    limits = instancer.parseLimits(limits)
    limits = instancer.AxisLimits(limits).limitAxesAndPopulateDefaults(font)
    limits = limits.normalize(font, usingAvar=True)
    print(limits)

    fvar = font["fvar"]
    avar = font["avar"]

    varIdxMap = avar.table.VarIdxMap
    varStore = avar.table.VarStore

    defaultDeltas = instancer.instantiateItemVariationStore(varStore, fvar.axes, limits)

    for axisIdx, axis in enumerate(fvar.axes):
        varIdx = axisIdx
        if varIdxMap is not None:
            varIdx = varIdxMap[varIdx]
        # Only for public axes
        identityAxisIndex = None if axis.flags & 0x1 else axisIdx
        minV, maxV = varStore.getExtremes(varIdx, identityAxisIndex)
        print(axis.axisTag, defaultDeltas[varIdx] / 16384, (minV / 16384, maxV / 16384))
