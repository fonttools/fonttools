""" Partially instantiate a variable font.

This is similar to fontTools.varLib.mutator, but instead of creating full
instances (i.e. static fonts) from variable fonts, it creates "partial"
variable fonts, only containing a subset of the variation space.
For example, if you wish to pin the width axis to a given location while
keeping the rest of the axes, you can do:

$ fonttools varLib.instancer ./NotoSans-VF.ttf wdth=85

NOTE: The module is experimental and both the API and the CLI *will* change.
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.fixedTools import floatToFixedToFloat, otRound
from fontTools.varLib.models import supportScalar, normalizeValue, piecewiseLinearMap
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.varLib.mvar import MVAR_ENTRIES
import collections
from copy import deepcopy
import logging
import os
import re


log = logging.getLogger("fontTools.varlib.instancer")


def instantiateTupleVariationStore(variations, location, origCoords=None, endPts=None):
    varGroups = collections.OrderedDict()
    for var in variations:
        # Compute the scalar support of the axes to be pinned at the desired location,
        # excluding any axes that we are not pinning.
        # If a TupleVariation doesn't mention an axis, it implies that the axis peak
        # is 0 (i.e. the axis does not participate).
        support = {axis: var.axes.pop(axis, (-1, 0, +1)) for axis in location}
        scalar = supportScalar(location, support)
        if scalar == 0.0:
            # no influence, drop the TupleVariation
            continue

        var.scaleDeltas(scalar)

        # group TupleVariations by overlapping "tents" (can be empty if all the axes
        # were instanced)
        axes = tuple(var.axes.items())
        if axes in varGroups:
            varGroups[axes].append(var)
        else:
            varGroups[axes] = [var]

    defaultDeltas = None
    newVariations = []
    for axes, varGroup in varGroups.items():
        var = varGroup.pop(0)

        # merge TupleVariations having the same (or none) axes
        if varGroup:
            var.sumDeltas(varGroup, origCoords, endPts)

        if axes is ():
            # if no axis is left in the TupleVariation, we drop it and its deltas
            # will be later added to the default instance; we need to interpolate
            # any inferred (i.e. None) deltas to be able to sum the coordinates
            if origCoords is not None:
                var.calcInferredDeltas(origCoords, endPts)
            defaultDeltas = var.coordinates
        else:
            var.roundDeltas()
            newVariations.append(var)

    variations[:] = newVariations
    return defaultDeltas or []


def instantiateGvarGlyph(varfont, glyphname, location, optimize=True):
    glyf = varfont["glyf"]
    coordinates, ctrl = glyf.getCoordinatesAndControls(glyphname, varfont)
    endPts = ctrl.endPts

    gvar = varfont["gvar"]
    tupleVarStore = gvar.variations[glyphname]

    defaultDeltas = instantiateTupleVariationStore(
        tupleVarStore, location, coordinates, endPts
    )

    if defaultDeltas:
        coordinates += GlyphCoordinates(defaultDeltas)
        # this will also set the hmtx advance widths and sidebearings from
        # the fourth-last and third-last phantom points (and glyph.xMin)
        glyf.setCoordinates(glyphname, coordinates, varfont)

    if not tupleVarStore:
        del gvar.variations[glyphname]
        return

    if optimize:
        isComposite = glyf[glyphname].isComposite()
        for var in tupleVarStore:
            var.optimize(coordinates, endPts, isComposite)


def instantiateGvar(varfont, location, optimize=True):
    log.info("Instantiating glyf/gvar tables")

    gvar = varfont["gvar"]
    glyf = varfont["glyf"]
    # Get list of glyph names in gvar sorted by component depth.
    # If a composite glyph is processed before its base glyph, the bounds may
    # be calculated incorrectly because deltas haven't been applied to the
    # base glyph yet.
    glyphnames = sorted(
        gvar.variations.keys(),
        key=lambda name: (
            glyf[name].getCompositeMaxpValues(glyf).maxComponentDepth
            if glyf[name].isComposite()
            else 0,
            name,
        ),
    )
    for glyphname in glyphnames:
        instantiateGvarGlyph(varfont, glyphname, location, optimize=optimize)

    if not gvar.variations:
        del varfont["gvar"]


def setCvarDeltas(cvt, deltas):
    for i, delta in enumerate(deltas):
        if delta is not None:
            cvt[i] += otRound(delta)


def instantiateCvar(varfont, location):
    log.info("Instantiating cvt/cvar tables")

    cvar = varfont["cvar"]

    defaultDeltas = instantiateTupleVariationStore(cvar.variations, location)

    if defaultDeltas:
        setCvarDeltas(varfont["cvt "], defaultDeltas)

    if not cvar.variations:
        del varfont["cvar"]


def setMvarDeltas(varfont, deltaArray):
    log.info("Setting MVAR deltas")

    mvar = varfont["MVAR"].table
    records = mvar.ValueRecord
    for rec in records:
        mvarTag = rec.ValueTag
        if mvarTag not in MVAR_ENTRIES:
            continue
        tableTag, itemName = MVAR_ENTRIES[mvarTag]
        varDataIndex = rec.VarIdx >> 16
        itemIndex = rec.VarIdx & 0xFFFF
        deltaRow = deltaArray[varDataIndex][itemIndex]
        delta = sum(deltaRow)
        if delta != 0:
            setattr(
                varfont[tableTag],
                itemName,
                getattr(varfont[tableTag], itemName) + otRound(delta),
            )


def instantiateMvar(varfont, location):
    log.info("Instantiating MVAR table")

    varStore = varfont["MVAR"].table.VarStore
    fvarAxes = varfont["fvar"].axes
    defaultDeltas = instantiateItemVariationStore(varStore, fvarAxes, location)
    setMvarDeltas(varfont, defaultDeltas)

    if not varStore.VarRegionList.Region:
        # Delete table if no more regions left.
        del varfont["MVAR"]


def _getVarRegionAxes(region, fvarAxes):
    # map fvar axes tags to VarRegionAxis in VarStore region, excluding axes that
    # don't participate (peak == 0)
    axes = {}
    assert len(fvarAxes) == len(region.VarRegionAxis)
    for fvarAxis, regionAxis in zip(fvarAxes, region.VarRegionAxis):
        if regionAxis.PeakCoord != 0:
            axes[fvarAxis.axisTag] = regionAxis
    return axes


def _getVarRegionScalar(location, regionAxes):
    # compute partial product of per-axis scalars at location, excluding the axes
    # that are not pinned
    pinnedAxes = {
        axisTag: (axis.StartCoord, axis.PeakCoord, axis.EndCoord)
        for axisTag, axis in regionAxes.items()
        if axisTag in location
    }
    return supportScalar(location, pinnedAxes)


def _scaleVarDataDeltas(varData, regionScalars):
    # multiply all varData deltas in-place by the corresponding region scalar
    varRegionCount = len(varData.VarRegionIndex)
    scalars = [regionScalars[regionIndex] for regionIndex in varData.VarRegionIndex]
    for item in varData.Item:
        assert len(item) == varRegionCount
        item[:] = [delta * scalar for delta, scalar in zip(item, scalars)]


def _getVarDataDeltasForRegions(varData, regionIndices, rounded=False):
    # Get only the deltas that correspond to the given regions (optionally, rounded).
    # Returns: list of lists of float
    varRegionIndices = varData.VarRegionIndex
    deltaSets = []
    for item in varData.Item:
        deltaSets.append(
            [
                delta if not rounded else otRound(delta)
                for regionIndex, delta in zip(varRegionIndices, item)
                if regionIndex in regionIndices
            ]
        )
    return deltaSets


def _subsetVarStoreRegions(varStore, regionIndices):
    # drop regions not in regionIndices
    newVarDatas = []
    for varData in varStore.VarData:
        if regionIndices.isdisjoint(varData.VarRegionIndex):
            # drop VarData subtable if we remove all the regions referenced by it
            continue

        # only retain delta-set columns that correspond to the given regions
        varData.Item = _getVarDataDeltasForRegions(varData, regionIndices, rounded=True)
        varData.VarRegionIndex = [
            ri for ri in varData.VarRegionIndex if ri in regionIndices
        ]
        varData.VarRegionCount = len(varData.VarRegionIndex)

        # recalculate NumShorts, reordering columns as necessary
        varData.optimize()
        newVarDatas.append(varData)

    varStore.VarData = newVarDatas
    varStore.VarDataCount = len(varStore.VarData)
    # remove unused regions from VarRegionList
    varStore.prune_regions()


def instantiateItemVariationStore(varStore, fvarAxes, location):
    regions = [
        _getVarRegionAxes(reg, fvarAxes) for reg in varStore.VarRegionList.Region
    ]
    # for each region, compute the scalar support of the axes to be pinned at the
    # desired location, and scale the deltas accordingly
    regionScalars = [_getVarRegionScalar(location, axes) for axes in regions]
    for varData in varStore.VarData:
        _scaleVarDataDeltas(varData, regionScalars)

    # disable the pinned axes by setting PeakCoord to 0
    for axes in regions:
        for axisTag, axis in axes.items():
            if axisTag in location:
                axis.StartCoord, axis.PeakCoord, axis.EndCoord = (0, 0, 0)
    # If all axes in a region are pinned, its deltas are added to the default instance
    defaultRegionIndices = {
        regionIndex
        for regionIndex, axes in enumerate(regions)
        if all(axis.PeakCoord == 0 for axis in axes.values())
    }
    # Collect the default deltas into a two-dimension array, with outer/inner indices
    # corresponding to a VarData subtable and a deltaset row within that table.
    defaultDeltaArray = [
        _getVarDataDeltasForRegions(varData, defaultRegionIndices)
        for varData in varStore.VarData
    ]

    # drop default regions, or those whose influence at the pinned location is 0
    newRegionIndices = {
        regionIndex
        for regionIndex in range(len(varStore.VarRegionList.Region))
        if regionIndex not in defaultRegionIndices and regionScalars[regionIndex] != 0
    }
    _subsetVarStoreRegions(varStore, newRegionIndices)

    return defaultDeltaArray


def instantiateFeatureVariations(varfont, location):
    for tableTag in ("GPOS", "GSUB"):
        if tableTag not in varfont or not hasattr(
            varfont[tableTag].table, "FeatureVariations"
        ):
            continue
        log.info("Instantiating FeatureVariations of %s table", tableTag)
        _instantiateFeatureVariations(
            varfont[tableTag].table, varfont["fvar"].axes, location
        )


def _instantiateFeatureVariations(table, fvarAxes, location):
    newRecords = []
    pinnedAxes = set(location.keys())
    featureVariationApplied = False
    for record in table.FeatureVariations.FeatureVariationRecord:
        retainRecord = True
        applies = True
        newConditions = []
        for condition in record.ConditionSet.ConditionTable:
            axisIdx = condition.AxisIndex
            axisTag = fvarAxes[axisIdx].axisTag
            if condition.Format == 1 and axisTag in pinnedAxes:
                minValue = condition.FilterRangeMinValue
                maxValue = condition.FilterRangeMaxValue
                v = location[axisTag]
                if not (minValue <= v <= maxValue):
                    # condition not met so remove entire record
                    retainRecord = False
                    break
            else:
                applies = False
                newConditions.append(condition)

        if retainRecord and newConditions:
            record.ConditionSet.ConditionTable = newConditions
            newRecords.append(record)

        if applies and not featureVariationApplied:
            assert record.FeatureTableSubstitution.Version == 0x00010000
            for rec in record.FeatureTableSubstitution.SubstitutionRecord:
                table.FeatureList.FeatureRecord[rec.FeatureIndex].Feature = rec.Feature
            # Set variations only once
            featureVariationApplied = True

    if newRecords:
        table.FeatureVariations.FeatureVariationRecord = newRecords
    else:
        del table.FeatureVariations


def normalize(value, triple, avar_mapping):
    value = normalizeValue(value, triple)
    if avar_mapping:
        value = piecewiseLinearMap(value, avar_mapping)
    # Quantize to F2Dot14, to avoid surprise interpolations.
    return floatToFixedToFloat(value, 14)


def normalizeAxisLimits(varfont, axis_limits):
    fvar = varfont["fvar"]
    bad_limits = axis_limits.keys() - {a.axisTag for a in fvar.axes}
    if bad_limits:
        raise ValueError("Cannot limit: {} not present in fvar".format(bad_limits))

    axes = {
        a.axisTag: (a.minValue, a.defaultValue, a.maxValue)
        for a in fvar.axes
        if a.axisTag in axis_limits
    }

    avar_segments = {}
    if "avar" in varfont:
        avar_segments = varfont["avar"].segments
    for axis_tag, triple in axes.items():
        avar_mapping = avar_segments.get(axis_tag, None)
        value = axis_limits[axis_tag]
        if isinstance(value, tuple):
            axis_limits[axis_tag] = tuple(
                normalize(v, triple, avar_mapping) for v in axis_limits[axis_tag]
            )
        else:
            axis_limits[axis_tag] = normalize(value, triple, avar_mapping)


def sanityCheckVariableTables(varfont):
    if "fvar" not in varfont:
        raise ValueError("Missing required table fvar")
    if "gvar" in varfont:
        if "glyf" not in varfont:
            raise ValueError("Can't have gvar without glyf")


def instantiateVariableFont(varfont, axis_limits, inplace=False, optimize=True):
    sanityCheckVariableTables(varfont)

    if not inplace:
        varfont = deepcopy(varfont)
    normalizeAxisLimits(varfont, axis_limits)

    log.info("Normalized limits: %s", axis_limits)

    # TODO Remove this check once ranges are supported
    if any(isinstance(v, tuple) for v in axis_limits.values()):
        raise NotImplementedError("Axes range limits are not supported yet")

    if "gvar" in varfont:
        instantiateGvar(varfont, axis_limits, optimize=optimize)

    if "cvar" in varfont:
        instantiateCvar(varfont, axis_limits)

    if "MVAR" in varfont:
        instantiateMvar(varfont, axis_limits)

    instantiateFeatureVariations(varfont, axis_limits)

    # TODO: actually process HVAR instead of dropping it
    del varfont["HVAR"]

    return varfont


def parseLimits(limits):
    result = {}
    for limit_string in limits:
        match = re.match(r"^(\w{1,4})=([^:]+)(?:[:](.+))?$", limit_string)
        if not match:
            raise ValueError("invalid location format: %r" % limit_string)
        tag = match.group(1).ljust(4)
        lbound = float(match.group(2))
        ubound = lbound
        if match.group(3):
            ubound = float(match.group(3))
        if lbound != ubound:
            result[tag] = (lbound, ubound)
        else:
            result[tag] = lbound
    return result


def parseArgs(args):
    """Parse argv.

    Returns:
        3-tuple (infile, outfile, axis_limits)
        axis_limits is either a Dict[str, int], for pinning variation axes to specific
        coordinates along those axes; or a Dict[str, Tuple(int, int)], meaning limit
        this axis to min/max range.
        Axes locations are in user-space coordinates, as defined in the "fvar" table.
    """
    from fontTools import configLogger
    import argparse

    parser = argparse.ArgumentParser(
        "fonttools varLib.instancer",
        description="Partially instantiate a variable font",
    )
    parser.add_argument("input", metavar="INPUT.ttf", help="Input variable TTF file.")
    parser.add_argument(
        "locargs",
        metavar="AXIS=LOC",
        nargs="*",
        help="List of space separated locations. A location consist in "
        "the tag of a variation axis, followed by '=' and a number or"
        "number:number. E.g.: wdth=100 or wght=75.0:125.0",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT.ttf",
        default=None,
        help="Output instance TTF file (default: INPUT-instance.ttf).",
    )
    parser.add_argument(
        "--no-optimize",
        dest="optimize",
        action="store_false",
        help="do not perform IUP optimization on the remaining gvar TupleVariations",
    )
    logging_group = parser.add_mutually_exclusive_group(required=False)
    logging_group.add_argument(
        "-v", "--verbose", action="store_true", help="Run more verbosely."
    )
    logging_group.add_argument(
        "-q", "--quiet", action="store_true", help="Turn verbosity off."
    )
    options = parser.parse_args(args)

    infile = options.input
    outfile = (
        os.path.splitext(infile)[0] + "-instance.ttf"
        if not options.output
        else options.output
    )
    configLogger(
        level=("DEBUG" if options.verbose else "ERROR" if options.quiet else "INFO")
    )

    axis_limits = parseLimits(options.locargs)
    if len(axis_limits) != len(options.locargs):
        raise ValueError("Specified multiple limits for the same axis")
    return (infile, outfile, axis_limits, options)


def main(args=None):
    infile, outfile, axis_limits, options = parseArgs(args)
    log.info("Restricting axes: %s", axis_limits)

    log.info("Loading variable font")
    varfont = TTFont(infile)

    instantiateVariableFont(
        varfont, axis_limits, inplace=True, optimize=options.optimize
    )

    log.info("Saving partial variable font %s", outfile)
    varfont.save(outfile)


if __name__ == "__main__":
    import sys

    sys.exit(main())
