""" Partially instantiate a variable font.

The module exports an `instantiateVariableFont` function and CLI that allow to
create full instances (i.e. static fonts) from variable fonts, as well as "partial"
variable fonts that only contain a subset of the original variation space.

For example, if you wish to pin the width axis to a given location while keeping
the rest of the axes, you can do:

$ fonttools varLib.instancer ./NotoSans-VF.ttf wdth=85

See `fonttools varLib.instancer --help` for more info on the CLI options.

The module's entry point is the `instantiateVariableFont` function, which takes
a TTFont object and a dict specifying a location along either some or all the axes,
and returns a new TTFont representing respectively a partial or a full instance.

E.g. here's how to pin the wght axis at a given location in a wght+wdth variable
font, keeping only the deltas associated with the wdth axis:

| >>> from fontTools import ttLib
| >>> from fontTools.varLib import instancer
| >>> varfont = ttLib.TTFont("path/to/MyVariableFont.ttf")
| >>> [a.axisTag for a in partial["fvar"].axes]  # the varfont's current axes
| ['wght', 'wdth']
| >>> partial = instancer.instantiateVariableFont(varfont, {"wght": 300})
| >>> [a.axisTag for a in partial["fvar"].axes]  # axes left after pinning 'wght'
| ['wdth']

If the input location specifies all the axes, the resulting instance is no longer
'variable' (same as using fontools varLib.mutator):

| >>> instance = instancer.instantiateVariableFont(
| ...     varfont, {"wght": 700, "wdth": 67.5}
| ... )
| >>> "fvar" not in instance
| True

If one just want to drop an axis at the default location, without knowing in
advance what the default value for that axis is, one can pass a `None` value:

| >>> instance = instancer.instantiateVariableFont(varfont, {"wght": None})
| >>> len(varfont["fvar"].axes)
| 1

From the console script, this is equivalent to passing `wght=drop` as input.

This module is similar to fontTools.varLib.mutator, which it's intended to supersede.
Note that, unlike varLib.mutator, when an axis is not mentioned in the input
location, the varLib.instancer will keep the axis and the corresponding deltas,
whereas mutator implicitly drops the axis at its default coordinate.

The module currently supports only the first two "levels" of partial instancing,
with the rest planned to be implemented in the future, namely:
L1) dropping one or more axes while leaving the default tables unmodified;
L2) dropping one or more axes while pinning them at non-default locations;
L3) restricting the range of variation of one or more axes, by setting either
    a new minimum or maximum, potentially -- though not necessarily -- dropping
    entire regions of variations that fall completely outside this new range.
L4) moving the default location of an axis.

Currently only TrueType-flavored variable fonts (i.e. containing 'glyf' table)
are supported, but support for CFF2 variable fonts will be added soon.

The discussion and implementation of these features are tracked at
https://github.com/fonttools/fonttools/issues/1537
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.fixedTools import floatToFixedToFloat, otRound
from fontTools.varLib.models import supportScalar, normalizeValue, piecewiseLinearMap
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.ttLib.tables import _g_l_y_f
from fontTools import varLib

# we import the `subset` module because we use the `prune_lookups` method on the GSUB
# table class, and that method is only defined dynamically upon importing `subset`
from fontTools import subset  # noqa: F401
from fontTools.varLib import builder
from fontTools.varLib.mvar import MVAR_ENTRIES
from fontTools.varLib.merger import MutatorMerger
from contextlib import contextmanager
import collections
from copy import deepcopy
import logging
from itertools import islice
import os
import re


log = logging.getLogger("fontTools.varLib.instancer")


def instantiateTupleVariationStore(variations, location, origCoords=None, endPts=None):
    """Instantiate TupleVariation list at the given location.

    The 'variations' list of TupleVariation objects is modified in-place.
    The input location can describe either a full instance (all the axes are assigned an
    explicit coordinate) or partial (some of the axes are omitted).
    Tuples that do not participate are kept as they are. Those that have 0 influence
    at the given location are removed from the variation store.
    Those that are fully instantiated (i.e. all their axes are being pinned) are also
    removed from the variation store, their scaled deltas accummulated and returned, so
    that they can be added by the caller to the default instance's coordinates.
    Tuples that are only partially instantiated (i.e. not all the axes that they
    participate in are being pinned) are kept in the store, and their deltas multiplied
    by the scalar support of the axes to be pinned at the desired location.

    Args:
        variations: List[TupleVariation] from either 'gvar' or 'cvar'.
        location: Dict[str, float]: axes coordinates for the full or partial instance.
        origCoords: GlyphCoordinates: default instance's coordinates for computing 'gvar'
            inferred points (cf. table__g_l_y_f.getCoordinatesAndControls).
        endPts: List[int]: indices of contour end points, for inferring 'gvar' deltas.

    Returns:
        List[float]: the overall delta adjustment after applicable deltas were summed.
    """
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

    # drop TupleVariation if all axes have been pinned (var.axes.items() is empty);
    # its deltas will be added to the default instance's coordinates
    defaultVar = newVariations.pop(tuple(), None)

    for var in newVariations.values():
        var.roundDeltas()
    variations[:] = list(newVariations.values())

    return defaultVar.coordinates if defaultVar is not None else []


def instantiateGvarGlyph(varfont, glyphname, location, optimize=True):
    glyf = varfont["glyf"]
    coordinates, ctrl = glyf.getCoordinatesAndControls(glyphname, varfont)
    endPts = ctrl.endPts

    gvar = varfont["gvar"]
    # when exporting to TTX, a glyph with no variations is omitted; thus when loading
    # a TTFont from TTX, a glyph that's present in glyf table may be missing from gvar.
    tupleVarStore = gvar.variations.get(glyphname)

    if tupleVarStore:
        defaultDeltas = instantiateTupleVariationStore(
            tupleVarStore, location, coordinates, endPts
        )

        if defaultDeltas:
            coordinates += _g_l_y_f.GlyphCoordinates(defaultDeltas)

    # setCoordinates also sets the hmtx/vmtx advance widths and sidebearings from
    # the four phantom points and glyph bounding boxes.
    # We call it unconditionally even if a glyph has no variations or no deltas are
    # applied at this location, in case the glyph's xMin and in turn its sidebearing
    # have changed. E.g. a composite glyph has no deltas for the component's (x, y)
    # offset nor for the 4 phantom points (e.g. it's monospaced). Thus its entry in
    # gvar table is empty; however, the composite's base glyph may have deltas
    # applied, hence the composite's bbox and left/top sidebearings may need updating
    # in the instanced font.
    glyf.setCoordinates(glyphname, coordinates, varfont)

    if not tupleVarStore:
        if glyphname in gvar.variations:
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
    # Get list of glyph names sorted by component depth.
    # If a composite glyph is processed before its base glyph, the bounds may
    # be calculated incorrectly because deltas haven't been applied to the
    # base glyph yet.
    glyphnames = sorted(
        glyf.glyphOrder,
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
        if delta:
            cvt[i] += otRound(delta)


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
                getattr(varfont[tableTag], itemName) + otRound(delta),
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


def _remapVarIdxMap(table, attrName, varIndexMapping, glyphOrder):
    oldMapping = getattr(table, attrName).mapping
    newMapping = [varIndexMapping[oldMapping[glyphName]] for glyphName in glyphOrder]
    setattr(table, attrName, builder.buildVarIdxMap(newMapping, glyphOrder))


# TODO(anthrotype) Add support for HVAR/VVAR in CFF2
def _instantiateVHVAR(varfont, location, tableFields):
    tableTag = tableFields.tableTag
    fvarAxes = varfont["fvar"].axes
    # Deltas from gvar table have already been applied to the hmtx/vmtx. For full
    # instances (i.e. all axes pinned), we can simply drop HVAR/VVAR and return
    if set(location).issuperset(axis.axisTag for axis in fvarAxes):
        log.info("Dropping %s table", tableTag)
        del varfont[tableTag]
        return

    log.info("Instantiating %s table", tableTag)
    vhvar = varfont[tableTag].table
    varStore = vhvar.VarStore
    # since deltas were already applied, the return value here is ignored
    instantiateItemVariationStore(varStore, fvarAxes, location)

    if varStore.VarRegionList.Region:
        # Only re-optimize VarStore if the HVAR/VVAR already uses indirect AdvWidthMap
        # or AdvHeightMap. If a direct, implicit glyphID->VariationIndex mapping is
        # used for advances, skip re-optimizing and maintain original VariationIndex.
        if getattr(vhvar, tableFields.advMapping):
            varIndexMapping = varStore.optimize()
            glyphOrder = varfont.getGlyphOrder()
            _remapVarIdxMap(vhvar, tableFields.advMapping, varIndexMapping, glyphOrder)
            if getattr(vhvar, tableFields.sb1):  # left or top sidebearings
                _remapVarIdxMap(vhvar, tableFields.sb1, varIndexMapping, glyphOrder)
            if getattr(vhvar, tableFields.sb2):  # right or bottom sidebearings
                _remapVarIdxMap(vhvar, tableFields.sb2, varIndexMapping, glyphOrder)
            if tableTag == "VVAR" and getattr(vhvar, tableFields.vOrigMapping):
                _remapVarIdxMap(
                    vhvar, tableFields.vOrigMapping, varIndexMapping, glyphOrder
                )
    else:
        del varfont[tableTag]


def instantiateHVAR(varfont, location):
    return _instantiateVHVAR(varfont, location, varLib.HVAR_FIELDS)


def instantiateVVAR(varfont, location):
    return _instantiateVHVAR(varfont, location, varLib.VVAR_FIELDS)


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
        self.axisOrder = [axisTag for axisTag in self.axisOrder if axisTag not in axes]

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
        # remove unused regions from VarRegionList
        itemVarStore.prune_regions()
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
        defaultDeltas: to be added to the default instance, of type dict of floats
            keyed by VariationIndex compound values: i.e. (outer << 16) + inner.
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

    if (
        "GDEF" not in varfont
        or varfont["GDEF"].table.Version < 0x00010003
        or not varfont["GDEF"].table.VarStore
    ):
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
        # remove unreferenced lookups
        varfont[tableTag].prune_lookups()


def _featureVariationRecordIsUnique(rec, seen):
    conditionSet = []
    for cond in rec.ConditionSet.ConditionTable:
        if cond.Format != 1:
            # can't tell whether this is duplicate, assume is unique
            return True
        conditionSet.append(
            (cond.AxisIndex, cond.FilterRangeMinValue, cond.FilterRangeMaxValue)
        )
    # besides the set of conditions, we also include the FeatureTableSubstitution
    # version to identify unique FeatureVariationRecords, even though only one
    # version is currently defined. It's theoretically possible that multiple
    # records with same conditions but different substitution table version be
    # present in the same font for backward compatibility.
    recordKey = frozenset([rec.FeatureTableSubstitution.Version] + conditionSet)
    if recordKey in seen:
        return False
    else:
        seen.add(recordKey)  # side effect
        return True


def _instantiateFeatureVariationRecord(
    record, recIdx, location, fvarAxes, axisIndexMap
):
    shouldKeep = False
    applies = True
    newConditions = []
    for i, condition in enumerate(record.ConditionSet.ConditionTable):
        if condition.Format == 1:
            axisIdx = condition.AxisIndex
            axisTag = fvarAxes[axisIdx].axisTag
            if axisTag in location:
                minValue = condition.FilterRangeMinValue
                maxValue = condition.FilterRangeMaxValue
                v = location[axisTag]
                if not (minValue <= v <= maxValue):
                    # condition not met so remove entire record
                    applies = False
                    newConditions = None
                    break
            else:
                # axis not pinned, keep condition with remapped axis index
                applies = False
                condition.AxisIndex = axisIndexMap[axisTag]
                newConditions.append(condition)
        else:
            log.warning(
                "Condition table {0} of FeatureVariationRecord {1} has "
                "unsupported format ({2}); ignored".format(i, recIdx, condition.Format)
            )
            applies = False
            newConditions.append(condition)

    if newConditions:
        record.ConditionSet.ConditionTable = newConditions
        shouldKeep = True

    return applies, shouldKeep


def _instantiateFeatureVariations(table, fvarAxes, location):
    pinnedAxes = set(location.keys())
    axisOrder = [axis.axisTag for axis in fvarAxes if axis.axisTag not in pinnedAxes]
    axisIndexMap = {axisTag: axisOrder.index(axisTag) for axisTag in axisOrder}

    featureVariationApplied = False
    uniqueRecords = set()
    newRecords = []

    for i, record in enumerate(table.FeatureVariations.FeatureVariationRecord):
        applies, shouldKeep = _instantiateFeatureVariationRecord(
            record, i, location, fvarAxes, axisIndexMap
        )
        if shouldKeep:
            if _featureVariationRecordIsUnique(record, uniqueRecords):
                newRecords.append(record)

        if applies and not featureVariationApplied:
            assert record.FeatureTableSubstitution.Version == 0x00010000
            for rec in record.FeatureTableSubstitution.SubstitutionRecord:
                table.FeatureList.FeatureRecord[rec.FeatureIndex].Feature = rec.Feature
            # Set variations only once
            featureVariationApplied = True

    if newRecords:
        table.FeatureVariations.FeatureVariationRecord = newRecords
        table.FeatureVariations.FeatureVariationCount = len(newRecords)
    else:
        del table.FeatureVariations


def instantiateAvar(varfont, location):
    segments = varfont["avar"].segments

    # drop table if we instantiate all the axes
    if set(location).issuperset(segments):
        log.info("Dropping avar table")
        del varfont["avar"]
        return

    log.info("Instantiating avar table")
    for axis in location:
        if axis in segments:
            del segments[axis]


def instantiateFvar(varfont, location):
    # 'location' dict must contain user-space (non-normalized) coordinates

    fvar = varfont["fvar"]

    # drop table if we instantiate all the axes
    if set(location).issuperset(axis.axisTag for axis in fvar.axes):
        log.info("Dropping fvar table")
        del varfont["fvar"]
        return

    log.info("Instantiating fvar table")

    fvar.axes = [axis for axis in fvar.axes if axis.axisTag not in location]

    # only keep NamedInstances whose coordinates == pinned axis location
    instances = []
    for instance in fvar.instances:
        if any(instance.coordinates[axis] != value for axis, value in location.items()):
            continue
        for axis in location:
            del instance.coordinates[axis]
        instances.append(instance)
    fvar.instances = instances


def instantiateSTAT(varfont, location):
    pinnedAxes = set(location.keys())

    stat = varfont["STAT"].table
    if not stat.DesignAxisRecord:
        return  # skip empty STAT table

    designAxes = stat.DesignAxisRecord.Axis
    pinnedAxisIndices = {
        i for i, axis in enumerate(designAxes) if axis.AxisTag in pinnedAxes
    }

    if len(pinnedAxisIndices) == len(designAxes):
        log.info("Dropping STAT table")
        del varfont["STAT"]
        return

    log.info("Instantiating STAT table")

    # only keep DesignAxis that were not instanced, and build a mapping from old
    # to new axis indices
    newDesignAxes = []
    axisIndexMap = {}
    for i, axis in enumerate(designAxes):
        if i not in pinnedAxisIndices:
            axisIndexMap[i] = len(newDesignAxes)
            newDesignAxes.append(axis)

    if stat.AxisValueArray and stat.AxisValueArray.AxisValue:
        # drop all AxisValue tables that reference any of the pinned axes
        newAxisValueTables = []
        for axisValueTable in stat.AxisValueArray.AxisValue:
            if axisValueTable.Format in (1, 2, 3):
                if axisValueTable.AxisIndex in pinnedAxisIndices:
                    continue
                axisValueTable.AxisIndex = axisIndexMap[axisValueTable.AxisIndex]
                newAxisValueTables.append(axisValueTable)
            elif axisValueTable.Format == 4:
                if any(
                    rec.AxisIndex in pinnedAxisIndices
                    for rec in axisValueTable.AxisValueRecord
                ):
                    continue
                for rec in axisValueTable.AxisValueRecord:
                    rec.AxisIndex = axisIndexMap[rec.AxisIndex]
                newAxisValueTables.append(axisValueTable)
            else:
                raise NotImplementedError(axisValueTable.Format)
        stat.AxisValueArray.AxisValue = newAxisValueTables
        stat.AxisValueCount = len(stat.AxisValueArray.AxisValue)

    stat.DesignAxisRecord.Axis[:] = newDesignAxes
    stat.DesignAxisCount = len(stat.DesignAxisRecord.Axis)


def getVariationNameIDs(varfont):
    used = []
    if "fvar" in varfont:
        fvar = varfont["fvar"]
        for axis in fvar.axes:
            used.append(axis.axisNameID)
        for instance in fvar.instances:
            used.append(instance.subfamilyNameID)
            if instance.postscriptNameID != 0xFFFF:
                used.append(instance.postscriptNameID)
    if "STAT" in varfont:
        stat = varfont["STAT"].table
        for axis in stat.DesignAxisRecord.Axis if stat.DesignAxisRecord else ():
            used.append(axis.AxisNameID)
        for value in stat.AxisValueArray.AxisValue if stat.AxisValueArray else ():
            used.append(value.ValueNameID)
    # nameIDs <= 255 are reserved by OT spec so we don't touch them
    return {nameID for nameID in used if nameID > 255}


@contextmanager
def pruningUnusedNames(varfont):
    origNameIDs = getVariationNameIDs(varfont)

    yield

    log.info("Pruning name table")
    exclude = origNameIDs - getVariationNameIDs(varfont)
    varfont["name"].names[:] = [
        record for record in varfont["name"].names if record.nameID not in exclude
    ]
    if "ltag" in varfont:
        # Drop the whole 'ltag' table if all the language-dependent Unicode name
        # records that reference it have been dropped.
        # TODO: Only prune unused ltag tags, renumerating langIDs accordingly.
        # Note ltag can also be used by feat or morx tables, so check those too.
        if not any(
            record
            for record in varfont["name"].names
            if record.platformID == 0 and record.langID != 0xFFFF
        ):
            del varfont["ltag"]


def setMacOverlapFlags(glyfTable):
    flagOverlapCompound = _g_l_y_f.OVERLAP_COMPOUND
    flagOverlapSimple = _g_l_y_f.flagOverlapSimple
    for glyphName in glyfTable.keys():
        glyph = glyfTable[glyphName]
        # Set OVERLAP_COMPOUND bit for compound glyphs
        if glyph.isComposite():
            glyph.components[0].flags |= flagOverlapCompound
        # Set OVERLAP_SIMPLE bit for simple glyphs
        elif glyph.numberOfContours > 0:
            glyph.flags[0] |= flagOverlapSimple


def normalize(value, triple, avarMapping):
    value = normalizeValue(value, triple)
    if avarMapping:
        value = piecewiseLinearMap(value, avarMapping)
    # Quantize to F2Dot14, to avoid surprise interpolations.
    return floatToFixedToFloat(value, 14)


def normalizeAxisLimits(varfont, axisLimits):
    fvar = varfont["fvar"]
    badLimits = set(axisLimits.keys()).difference(a.axisTag for a in fvar.axes)
    if badLimits:
        raise ValueError("Cannot limit: {} not present in fvar".format(badLimits))

    axes = {
        a.axisTag: (a.minValue, a.defaultValue, a.maxValue)
        for a in fvar.axes
        if a.axisTag in axisLimits
    }

    avarSegments = {}
    if "avar" in varfont:
        avarSegments = varfont["avar"].segments
    normalizedLimits = {}
    for axis_tag, triple in axes.items():
        avarMapping = avarSegments.get(axis_tag, None)
        value = axisLimits[axis_tag]
        if isinstance(value, tuple):
            normalizedLimits[axis_tag] = tuple(
                normalize(v, triple, avarMapping) for v in axisLimits[axis_tag]
            )
        else:
            normalizedLimits[axis_tag] = normalize(value, triple, avarMapping)
    return normalizedLimits


def sanityCheckVariableTables(varfont):
    if "fvar" not in varfont:
        raise ValueError("Missing required table fvar")
    if "gvar" in varfont:
        if "glyf" not in varfont:
            raise ValueError("Can't have gvar without glyf")
    # TODO(anthrotype) Remove once we do support partial instancing CFF2
    if "CFF2" in varfont:
        raise NotImplementedError("Instancing CFF2 variable fonts is not supported yet")


def populateAxisDefaults(varfont, axisLimits):
    if any(value is None for value in axisLimits.values()):
        fvar = varfont["fvar"]
        defaultValues = {a.axisTag: a.defaultValue for a in fvar.axes}
        return {
            axisTag: defaultValues[axisTag] if value is None else value
            for axisTag, value in axisLimits.items()
        }
    return axisLimits


def instantiateVariableFont(
    varfont, axisLimits, inplace=False, optimize=True, overlap=True
):
    """ Instantiate variable font, either fully or partially.

    Depending on whether the `axisLimits` dictionary references all or some of the
    input varfont's axes, the output font will either be a full instance (static
    font) or a variable font with possibly less variation data.

    Args:
        varfont: a TTFont instance, which must contain at least an 'fvar' table.
            Note that variable fonts with 'CFF2' table are not supported yet.
        axisLimits: a dict keyed by axis tags (str) containing the coordinates (float)
            along one or more axes where the desired instance will be located.
            If the value is `None`, the default coordinate as per 'fvar' table for
            that axis is used.
            The limit values can also be (min, max) tuples for restricting an
            axis's variation range, but this is not implemented yet.
        inplace (bool): whether to modify input TTFont object in-place instead of
            returning a distinct object.
        optimize (bool): if False, do not perform IUP-delta optimization on the
            remaining 'gvar' table's deltas. Possibly faster, and might work around
            rendering issues in some buggy environments, at the cost of a slightly
            larger file size.
        overlap (bool): variable fonts usually contain overlapping contours, and some
            font rendering engines on Apple platforms require that the `OVERLAP_SIMPLE`
            and `OVERLAP_COMPOUND` flags in the 'glyf' table be set to force rendering
            using a non-zero fill rule. Thus we always set these flags on all glyphs
            to maximise cross-compatibility of the generated instance. You can disable
            this by setting `overalap` to False.
    """
    sanityCheckVariableTables(varfont)

    if not inplace:
        varfont = deepcopy(varfont)

    axisLimits = populateAxisDefaults(varfont, axisLimits)

    normalizedLimits = normalizeAxisLimits(varfont, axisLimits)

    log.info("Normalized limits: %s", normalizedLimits)

    # TODO Remove this check once ranges are supported
    if any(isinstance(v, tuple) for v in axisLimits.values()):
        raise NotImplementedError("Axes range limits are not supported yet")

    if "gvar" in varfont:
        instantiateGvar(varfont, normalizedLimits, optimize=optimize)

    if "cvar" in varfont:
        instantiateCvar(varfont, normalizedLimits)

    if "MVAR" in varfont:
        instantiateMVAR(varfont, normalizedLimits)

    if "HVAR" in varfont:
        instantiateHVAR(varfont, normalizedLimits)

    if "VVAR" in varfont:
        instantiateVVAR(varfont, normalizedLimits)

    instantiateOTL(varfont, normalizedLimits)

    instantiateFeatureVariations(varfont, normalizedLimits)

    if "avar" in varfont:
        instantiateAvar(varfont, normalizedLimits)

    with pruningUnusedNames(varfont):
        if "STAT" in varfont:
            instantiateSTAT(varfont, axisLimits)

        instantiateFvar(varfont, axisLimits)

    if "fvar" not in varfont:
        if "glyf" in varfont and overlap:
            setMacOverlapFlags(varfont["glyf"])

    varLib.set_default_weight_width_slant(
        varfont,
        location={
            axisTag: limit
            for axisTag, limit in axisLimits.items()
            if not isinstance(limit, tuple)
        },
    )

    return varfont


def parseLimits(limits):
    result = {}
    for limitString in limits:
        match = re.match(r"^(\w{1,4})=(?:(drop)|(?:([^:]+)(?:[:](.+))?))$", limitString)
        if not match:
            raise ValueError("invalid location format: %r" % limitString)
        tag = match.group(1).ljust(4)
        if match.group(2):  # 'drop'
            lbound = None
        else:
            lbound = float(match.group(3))
        ubound = lbound
        if match.group(4):
            ubound = float(match.group(4))
        if lbound != ubound:
            result[tag] = (lbound, ubound)
        else:
            result[tag] = lbound
    return result


def parseArgs(args):
    """Parse argv.

    Returns:
        3-tuple (infile, axisLimits, options)
        axisLimits is either a Dict[str, Optional[float]], for pinning variation axes
        to specific coordinates along those axes (with `None` as a placeholder for an
        axis' default value); or a Dict[str, Tuple(float, float)], meaning limit this
        axis to min/max range.
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
        "the tag of a variation axis, followed by '=' and one of number, "
        "number:number or the literal string 'drop'. "
        "E.g.: wdth=100 or wght=75.0:125.0 or wght=drop",
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
        help="Don't perform IUP optimization on the remaining gvar TupleVariations",
    )
    parser.add_argument(
        "--no-overlap-flag",
        dest="overlap",
        action="store_false",
        help="Don't set OVERLAP_SIMPLE/OVERLAP_COMPOUND glyf flags (only applicable "
        "when generating a full instance)",
    )
    loggingGroup = parser.add_mutually_exclusive_group(required=False)
    loggingGroup.add_argument(
        "-v", "--verbose", action="store_true", help="Run more verbosely."
    )
    loggingGroup.add_argument(
        "-q", "--quiet", action="store_true", help="Turn verbosity off."
    )
    options = parser.parse_args(args)

    infile = options.input
    if not os.path.isfile(infile):
        parser.error("No such file '{}'".format(infile))

    configLogger(
        level=("DEBUG" if options.verbose else "ERROR" if options.quiet else "INFO")
    )

    try:
        axisLimits = parseLimits(options.locargs)
    except ValueError as e:
        parser.error(e)

    if len(axisLimits) != len(options.locargs):
        parser.error("Specified multiple limits for the same axis")

    return (infile, axisLimits, options)


def main(args=None):
    infile, axisLimits, options = parseArgs(args)
    log.info("Restricting axes: %s", axisLimits)

    log.info("Loading variable font")
    varfont = TTFont(infile)

    isFullInstance = {
        axisTag for axisTag, limit in axisLimits.items() if not isinstance(limit, tuple)
    }.issuperset(axis.axisTag for axis in varfont["fvar"].axes)

    instantiateVariableFont(
        varfont,
        axisLimits,
        inplace=True,
        optimize=options.optimize,
        overlap=options.overlap,
    )

    outfile = (
        os.path.splitext(infile)[0]
        + "-{}.ttf".format("instance" if isFullInstance else "partial")
        if not options.output
        else options.output
    )

    log.info(
        "Saving %s font %s",
        "instance" if isFullInstance else "partial variable",
        outfile,
    )
    varfont.save(outfile)


if __name__ == "__main__":
    import sys

    sys.exit(main())
