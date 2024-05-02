from fontTools.varLib.varStore import VarStoreInstancer, NO_VARIATION_INDEX
from fontTools.ttLib.tables.otTables import VarStore
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.varLib import instancer


def VarStore_getExtremes(
    self,
    varIdx,
    fvarAxes,
    axisLimits,
    identityAxisIndex=None,
    nullAxes=set(),
    cache=None,
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
            location[fvarAxes[i].axisTag] = peak
        if skip:
            continue
        assert thisAxes, "Empty region in VarStore!"

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
                location[fvarAxes[identityAxisIndex].axisTag] = loc

            scalar = 1
            for j, regionAxis in enumerate(region.VarRegionAxis):
                peak = regionAxis.PeakCoord
                if peak == 0:
                    continue
                axis = fvarAxes[j]
                try:
                    limits = axisLimits[axis.axisTag]
                    if peak > 0:
                        scalar *= limits[2] - limits[1]
                    else:
                        scalar *= limits[1] - limits[0]
                except KeyError:
                    pass

            varStoreInstancer = VarStoreInstancer(varStore, fvarAxes, location)
            v = varStoreInstancer[varIdx] + (0 if loc is None else round(loc * 16384))

            minOther, maxOther = self.getExtremes(
                varIdx,
                fvarAxes,
                axisLimits,
                identityAxisIndex,
                nullAxes | thisAxes,
                cache,
            )

            minV = min(minV, (v + minOther) * scalar)
            maxV = max(maxV, (v + maxOther) * scalar)

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

    pinnedAxes = limits.pinnedLocation()
    unpinnedAxes = [axis for axis in fvar.axes if axis.axisTag not in pinnedAxes]

    for axis in fvar.axes:
        if axis.axisTag in limits:
            continue
        private = axis.flags & 0x1
        if not private:
            continue
        # if private, pin at default
        limits[axis.axisTag] = instancer.NormalizedAxisTripleAndDistances(0, 0, 0)

    defaultDeltas = instancer.instantiateItemVariationStore(varStore, fvar.axes, limits)

    for axisIdx, axis in enumerate(fvar.axes):
        if axis.axisTag in pinnedAxes:
            limits[axis.axisTag] = instancer.NormalizedAxisTripleAndDistances(0, 0, 0)
            continue
        varIdx = axisIdx
        if varIdxMap is not None:
            varIdx = varIdxMap[varIdx]
        # Only for public axes
        private = axis.flags & 0x1
        identityAxisIndex = None if private else axisIdx
        minV, maxV = varStore.getExtremes(
            varIdx, unpinnedAxes, limits, identityAxisIndex
        )
        limits[axis.axisTag] = instancer.NormalizedAxisTripleAndDistances(
            max(-1, min(minV / 16384, +1)),
            0,
            max(-1, min(maxV / 16384, +1)),
        )
        print(
            "%s%s" % (axis.axisTag, "*" if private else ""),
            defaultDeltas[varIdx] / 16384,
            (minV / 16384, maxV / 16384),
        )

    defaultDeltas = instancer.instantiateItemVariationStore(
        varStore, unpinnedAxes, limits
    )
    print(defaultDeltas)
