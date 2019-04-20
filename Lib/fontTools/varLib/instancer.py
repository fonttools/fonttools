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
from fontTools.misc.fixedTools import floatToFixedToFloat
from fontTools.varLib.models import supportScalar, normalizeValue, piecewiseLinearMap
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.varLib import builder
from fontTools.varLib.mvar import MVAR_ENTRIES
from fontTools.varLib.merger import MutatorMerger
import collections
from copy import deepcopy
import logging
import os
import re


log = logging.getLogger("fontTools.varlib.instancer")


def instantiateTupleVariationStore(variations, location, origCoords=None, endPts=None):
    newVariations = collections.OrderedDict()
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

        # compute inferred deltas only for gvar ('origCoords' is None for cvar)
        if origCoords is not None:
            var.calcInferredDeltas(origCoords, endPts)

        var.scaleDeltas(scalar)

        # merge TupleVariations with overlapping "tents"
        axes = tuple(var.axes.items())
        if axes in newVariations:
            newVariations[axes] += var
        else:
            newVariations[axes] = var

    for var in newVariations.values():
        var.roundDeltas()

    # drop TupleVariation if all axes have been pinned (var.axes.items() is empty);
    # its deltas will be added to the default instance's coordinates
    defaultVar = newVariations.pop(tuple(), None)

    variations[:] = list(newVariations.values())

    return defaultVar.coordinates if defaultVar is not None else []


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
            cvt[i] += delta


def instantiateCvar(varfont, location):
    log.info("Instantiating cvt/cvar tables")

    cvar = varfont["cvar"]

    defaultDeltas = instantiateTupleVariationStore(cvar.variations, location)

    if defaultDeltas:
        setCvarDeltas(varfont["cvt "], defaultDeltas)

    if not cvar.variations:
        del varfont["cvar"]


def setMvarDeltas(varfont, deltas):
    mvar = varfont["MVAR"].table
    records = mvar.ValueRecord
    for rec in records:
        mvarTag = rec.ValueTag
        if mvarTag not in MVAR_ENTRIES:
            continue
        tableTag, itemName = MVAR_ENTRIES[mvarTag]
        delta = deltas[rec.VarIdx]
        if delta != 0:
            setattr(
                varfont[tableTag],
                itemName,
                getattr(varfont[tableTag], itemName) + delta,
            )


def instantiateMVAR(varfont, location):
    log.info("Instantiating MVAR table")

    mvar = varfont["MVAR"].table
    fvarAxes = varfont["fvar"].axes
    varStore = mvar.VarStore
    defaultDeltas = instantiateItemVariationStore(varStore, fvarAxes, location)
    setMvarDeltas(varfont, defaultDeltas)

    if varStore.VarRegionList.Region:
        varIndexMapping = varStore.optimize()
        for rec in mvar.ValueRecord:
            rec.VarIdx = varIndexMapping[rec.VarIdx]
    else:
        del varfont["MVAR"]


class _TupleVarStoreAdapter(object):
    def __init__(self, regions, axisOrder, tupleVarData, itemCounts):
        self.regions = regions
        self.axisOrder = axisOrder
        self.tupleVarData = tupleVarData
        self.itemCounts = itemCounts

    @classmethod
    def fromItemVarStore(cls, itemVarStore, fvarAxes):
        axisOrder = [axis.axisTag for axis in fvarAxes]
        regions = [
            region.get_support(fvarAxes) for region in itemVarStore.VarRegionList.Region
        ]
        tupleVarData = []
        itemCounts = []
        for varData in itemVarStore.VarData:
            variations = []
            varDataRegions = (regions[i] for i in varData.VarRegionIndex)
            for axes, coordinates in zip(varDataRegions, zip(*varData.Item)):
                variations.append(TupleVariation(axes, list(coordinates)))
            tupleVarData.append(variations)
            itemCounts.append(varData.ItemCount)
        return cls(regions, axisOrder, tupleVarData, itemCounts)

    def dropAxes(self, axes):
        prunedRegions = (
            frozenset(
                (axisTag, support)
                for axisTag, support in region.items()
                if axisTag not in axes
            )
            for region in self.regions
        )
        # dedup regions while keeping original order
        uniqueRegions = collections.OrderedDict.fromkeys(prunedRegions)
        self.regions = [dict(items) for items in uniqueRegions if items]
        # TODO(anthrotype) uncomment this once we support subsetting fvar axes
        # self.axisOrder = [
        #     axisTag for axisTag in self.axisOrder if axisTag not in axes
        # ]

    def instantiate(self, location):
        defaultDeltaArray = []
        for variations, itemCount in zip(self.tupleVarData, self.itemCounts):
            defaultDeltas = instantiateTupleVariationStore(variations, location)
            if not defaultDeltas:
                defaultDeltas = [0] * itemCount
            defaultDeltaArray.append(defaultDeltas)

        # remove pinned axes from all the regions
        self.dropAxes(location.keys())

        return defaultDeltaArray

    def asItemVarStore(self):
        regionOrder = [frozenset(axes.items()) for axes in self.regions]
        varDatas = []
        for variations, itemCount in zip(self.tupleVarData, self.itemCounts):
            if variations:
                assert len(variations[0].coordinates) == itemCount
                varRegionIndices = [
                    regionOrder.index(frozenset(var.axes.items())) for var in variations
                ]
                varDataItems = list(zip(*(var.coordinates for var in variations)))
                varDatas.append(
                    builder.buildVarData(varRegionIndices, varDataItems, optimize=False)
                )
            else:
                varDatas.append(
                    builder.buildVarData([], [[] for _ in range(itemCount)])
                )
        regionList = builder.buildVarRegionList(self.regions, self.axisOrder)
        itemVarStore = builder.buildVarStore(regionList, varDatas)
        return itemVarStore


def instantiateItemVariationStore(itemVarStore, fvarAxes, location):
    """ Compute deltas at partial location, and update varStore in-place.

    Remove regions in which all axes were instanced, and scale the deltas of
    the remaining regions where only some of the axes were instanced.

    The number of VarData subtables, and the number of items within each, are
    not modified, in order to keep the existing VariationIndex valid.
    One may call VarStore.optimize() method after this to further optimize those.

    Args:
        varStore: An otTables.VarStore object (Item Variation Store)
        fvarAxes: list of fvar's Axis objects
        location: Dict[str, float] mapping axis tags to normalized axis coordinates.
            May not specify coordinates for all the fvar axes.

    Returns:
        defaultDeltas: to be added to the default instance, of type dict of ints keyed
            by VariationIndex compound values: i.e. (outer << 16) + inner.
    """
    tupleVarStore = _TupleVarStoreAdapter.fromItemVarStore(itemVarStore, fvarAxes)
    defaultDeltaArray = tupleVarStore.instantiate(location)
    newItemVarStore = tupleVarStore.asItemVarStore()

    itemVarStore.VarRegionList = newItemVarStore.VarRegionList
    assert itemVarStore.VarDataCount == newItemVarStore.VarDataCount
    itemVarStore.VarData = newItemVarStore.VarData

    defaultDeltas = {
        ((major << 16) + minor): delta
        for major, deltas in enumerate(defaultDeltaArray)
        for minor, delta in enumerate(deltas)
    }
    return defaultDeltas


def instantiateOTL(varfont, location):
    # TODO(anthrotype) Support partial instancing of JSTF and BASE tables

    if "GDEF" not in varfont:
        return

    if "GPOS" in varfont:
        msg = "Instantiating GDEF and GPOS tables"
    else:
        msg = "Instantiating GDEF table"
    log.info(msg)

    gdef = varfont["GDEF"].table
    varStore = gdef.VarStore
    fvarAxes = varfont["fvar"].axes

    defaultDeltas = instantiateItemVariationStore(varStore, fvarAxes, location)

    # When VF are built, big lookups may overflow and be broken into multiple
    # subtables. MutatorMerger (which inherits from AligningMerger) reattaches
    # them upon instancing, in case they can now fit a single subtable (if not,
    # they will be split again upon compilation).
    # This 'merger' also works as a 'visitor' that traverses the OTL tables and
    # calls specific methods when instances of a given type are found.
    # Specifically, it adds default deltas to GPOS Anchors/ValueRecords and GDEF
    # LigatureCarets, and optionally deletes all VariationIndex tables if the
    # VarStore is fully instanced.
    merger = MutatorMerger(
        varfont, defaultDeltas, deleteVariations=(not varStore.VarRegionList.Region)
    )
    merger.mergeTables(varfont, [varfont], ["GDEF", "GPOS"])

    if varStore.VarRegionList.Region:
        varIndexMapping = varStore.optimize()
        gdef.remap_device_varidxes(varIndexMapping)
        if "GPOS" in varfont:
            varfont["GPOS"].table.remap_device_varidxes(varIndexMapping)
    else:
        # Downgrade GDEF.
        del gdef.VarStore
        gdef.Version = 0x00010002
        if gdef.MarkGlyphSetsDef is None:
            del gdef.MarkGlyphSetsDef
            gdef.Version = 0x00010000

        if not (
            gdef.LigCaretList
            or gdef.MarkAttachClassDef
            or gdef.GlyphClassDef
            or gdef.AttachList
            or (gdef.Version >= 0x00010002 and gdef.MarkGlyphSetsDef)
        ):
            del varfont["GDEF"]


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
    # TODO(anthrotype) Remove once we do support partial instancing CFF2
    if "CFF2" in varfont:
        raise NotImplementedError(
            "Instancing CFF2 variable fonts is not supported yet"
        )


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
        instantiateMVAR(varfont, axis_limits)

    instantiateOTL(varfont, axis_limits)

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
