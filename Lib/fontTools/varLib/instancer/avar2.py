from fontTools.varLib.varStore import VarStoreInstancer, NO_VARIATION_INDEX
from fontTools.ttLib.tables.otTables import VarStore
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.varLib import instancer


if __name__ == "__main__":
    import sys
    from fontTools.ttLib import TTFont

    font = TTFont(sys.argv[1])

    limits = sys.argv[2:]
    limits = instancer.parseLimits(limits)
    limits = instancer.AxisLimits(limits).limitAxesAndPopulateDefaults(font)
    limits = limits.normalize(font, usingAvar=False)
    print(limits)

    fvar = font["fvar"]
    avar = font.get("avar", None)

    varIdxMap = None
    varStore = None
    if avar and hasattr(avar, "table"):
        varIdxMap = getattr(avar.table, "VarIdxMap", None)
        varStore = getattr(avar.table, "VarStore", None)

    pinnedAxes = limits.pinnedLocation()
    unpinnedAxes = [axis for axis in fvar.axes if axis.axisTag not in pinnedAxes]

    if avar:
        limits = avar.renormalizeAxisLimits(limits, font)

    for axisIdx, axis in enumerate(fvar.axes):
        varIdx = axisIdx
        if varIdxMap is not None:
            varIdx = varIdxMap[varIdx]
        private = axis.flags & 0x1
        print(
            "%s%s" % (axis.axisTag, "*" if private else ""),
            limits.get(axis.axisTag, (0, 0, 0) if private else (-1, 0, +1)),
        )
