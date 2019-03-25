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
from fontTools.varLib.iup import iup_delta
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.varLib.varStore import VarStoreInstancer
from fontTools.varLib.mvar import MVAR_ENTRIES
import collections
from copy import deepcopy
import logging
import os
import re


log = logging.getLogger("fontTools.varlib.instancer")


def instantiateTupleVariationStore(variations, location):
    newVariations = []
    defaultDeltas = []
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
        elif scalar != 1.0:
            var.scaleDeltas(scalar)
        if not var.axes:
            # if no axis is left in the TupleVariation, also drop it; its deltas
            # will be folded into the neutral
            defaultDeltas.append(var.coordinates)
        else:
            # keep the TupleVariation, and round the scaled deltas to integers
            if scalar != 1.0:
                var.roundDeltas()
            newVariations.append(var)
    variations[:] = newVariations
    return defaultDeltas


def setGvarGlyphDeltas(varfont, glyphname, deltasets):
    glyf = varfont["glyf"]
    coordinates = glyf.getCoordinates(glyphname, varfont)
    origCoords = None

    for deltas in deltasets:
        hasUntouchedPoints = None in deltas
        if hasUntouchedPoints:
            if origCoords is None:
                origCoords, g = glyf.getCoordinatesAndControls(glyphname, varfont)
            deltas = iup_delta(deltas, origCoords, g.endPts)
        coordinates += GlyphCoordinates(deltas)

    glyf.setCoordinates(glyphname, coordinates, varfont)


def instantiateGvarGlyph(varfont, glyphname, location):
    gvar = varfont["gvar"]

    defaultDeltas = instantiateTupleVariationStore(gvar.variations[glyphname], location)
    if defaultDeltas:
        setGvarGlyphDeltas(varfont, glyphname, defaultDeltas)

    if not gvar.variations[glyphname]:
        del gvar.variations[glyphname]


def instantiateGvar(varfont, location):
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
        instantiateGvarGlyph(varfont, glyphname, location)

    if not gvar.variations:
        del varfont["gvar"]


def setCvarDeltas(cvt, deltasets):
    # copy cvt values internally represented as array.array("h") to a list,
    # accumulating deltas (that may be float since we scaled them) and only
    # do the rounding to integer once at the end to reduce rounding errors
    values = list(cvt)
    for deltas in deltasets:
        for i, delta in enumerate(deltas):
            if delta is not None:
                values[i] += delta
    for i, v in enumerate(values):
        cvt[i] = otRound(v)


def instantiateCvar(varfont, location):
    log.info("Instantiating cvt/cvar tables")
    cvar = varfont["cvar"]
    cvt = varfont["cvt "]
    defaultDeltas = instantiateTupleVariationStore(cvar.variations, location)
    setCvarDeltas(cvt, defaultDeltas)
    if not cvar.variations:
        del varfont["cvar"]


def setMvarDeltas(varfont, location):
    log.info("Setting MVAR deltas")

    mvar = varfont["MVAR"].table
    fvar = varfont["fvar"]
    varStoreInstancer = VarStoreInstancer(mvar.VarStore, fvar.axes, location)
    records = mvar.ValueRecord
    # accumulate applicable deltas as floats and only round at the end
    deltas = collections.defaultdict(float)
    for rec in records:
        mvarTag = rec.ValueTag
        if mvarTag not in MVAR_ENTRIES:
            continue
        tableTag, itemName = MVAR_ENTRIES[mvarTag]
        deltas[(tableTag, itemName)] += varStoreInstancer[rec.VarIdx]

    for (tableTag, itemName), delta in deltas.items():
        setattr(
            varfont[tableTag],
            itemName,
            getattr(varfont[tableTag], itemName) + otRound(delta),
        )


def instantiateMvar(varfont, location):
    log.info("Instantiating MVAR table")
    # First instantiate to new position without modifying MVAR table
    setMvarDeltas(varfont, location)

    instantiateItemVariationStore(varfont, "MVAR", location)


def instantiateItemVariationStore(varfont, tableName, location):
    log.info("Instantiating ItemVariation store of %s table", tableName)

    table = varfont[tableName].table
    fvar = varfont["fvar"]
    newRegions = []
    regionInfluenceMap = {}
    pinnedAxes = set(location.keys())
    fvarAxisIndices = {
        axis.axisTag: index
        for index, axis in enumerate(fvar.axes)
        if axis.axisTag in pinnedAxes
    }
    for regionIndex, region in enumerate(table.VarStore.VarRegionList.Region):
        # collect set of axisTags which have influence: peak != 0
        regionAxes = set(
            axis
            for axis, (start, peak, end) in region.get_support(fvar.axes).items()
            if peak != 0
        )
        pinnedRegionAxes = regionAxes & pinnedAxes
        if not pinnedRegionAxes:
            # A region where none of the axes having effect are pinned
            newRegions.append(region)
            continue
        if len(pinnedRegionAxes) == len(regionAxes):
            # All the axes having effect in this region are being pinned so
            # remove it
            regionInfluenceMap.update({regionIndex: None})
        else:
            # This region will be retained but the deltas have to be adjusted.
            pinnedSupport = {
                axis: support
                for axis, support in region.get_support(fvar.axes).items()
                if axis in pinnedRegionAxes
            }
            pinnedScalar = supportScalar(location, pinnedSupport)
            regionInfluenceMap.update({regionIndex: pinnedScalar})

            for axis in pinnedRegionAxes:
                # For all pinnedRegionAxes make their influence null by setting
                # PeakCoord to 0.
                index = fvarAxisIndices[axis]
                region.VarRegionAxis[index].PeakCoord = 0

            newRegions.append(region)

    table.VarStore.VarRegionList.Region = newRegions

    if not table.VarStore.VarRegionList.Region:
        # Delete table if no more regions left.
        del varfont[tableName]
        return

    # First apply scalars to deltas then remove deltas in reverse index order
    if regionInfluenceMap:
        regionsToBeRemoved = [
            regionIndex
            for regionIndex, scalar in regionInfluenceMap.items()
            if scalar is None
        ]
        for vardata in table.VarStore.VarData:
            for regionIndex, scalar in regionInfluenceMap.items():
                if scalar is not None:
                    for item in vardata.Item:
                        item[regionIndex] = otRound(item[regionIndex] * scalar)

            for index in sorted(regionsToBeRemoved, reverse=True):
                del vardata.VarRegionIndex[index]
                for item in vardata.Item:
                    del item[index]


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


def instantiateVariableFont(varfont, axis_limits, inplace=False):
    sanityCheckVariableTables(varfont)

    if not inplace:
        varfont = deepcopy(varfont)
    normalizeAxisLimits(varfont, axis_limits)

    log.info("Normalized limits: %s", axis_limits)

    # TODO Remove this check once ranges are supported
    if any(isinstance(v, tuple) for v in axis_limits.values()):
        raise NotImplementedError("Axes range limits are not supported yet")

    if "gvar" in varfont:
        instantiateGvar(varfont, axis_limits)

    if "cvar" in varfont:
        instantiateCvar(varfont, axis_limits)

    if "MVAR" in varfont:
        instantiateMvar(varfont, axis_limits)

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
    return (infile, outfile, axis_limits)


def main(args=None):
    infile, outfile, axis_limits = parseArgs(args)
    log.info("Restricting axes: %s", axis_limits)

    log.info("Loading variable font")
    varfont = TTFont(infile)

    instantiateVariableFont(varfont, axis_limits, inplace=True)

    log.info("Saving partial variable font %s", outfile)
    varfont.save(outfile)


if __name__ == "__main__":
    import sys

    sys.exit(main())
