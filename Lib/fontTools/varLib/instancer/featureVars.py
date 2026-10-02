from fontTools.ttLib.tables import otTables as ot
from fontTools.misc.fixedTools import otRound
from copy import deepcopy
import logging

log = logging.getLogger("fontTools.varLib.instancer")

_LOOKUP_CONDITION_FALSE = 0
_LOOKUP_CONDITION_TRUE = 1
_LOOKUP_CONDITION_KEEP = 2


def _featureVariationRecordIsUnique(rec, seen):
    conditionSet = []
    conditionSets = (
        rec.ConditionSet.ConditionTable if rec.ConditionSet is not None else []
    )
    for cond in conditionSets:
        if cond is None:
            continue
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


def _limitFeatureVariationConditionRange(condition, axisLimit):
    minValue = condition.FilterRangeMinValue
    maxValue = condition.FilterRangeMaxValue

    if (
        minValue > maxValue
        or minValue > axisLimit.maximum
        or maxValue < axisLimit.minimum
    ):
        # condition invalid or out of range
        return

    return tuple(
        axisLimit.renormalizeValue(v, extrapolate=False) for v in (minValue, maxValue)
    )


def _conditionAppliesAtDefault(condition, axisLimits, fvarAxes, depth=64):
    if condition is None:
        return True
    if not depth:
        return False
    if condition.Format == 1:
        if condition.AxisIndex >= len(fvarAxes):
            return False
        axisTag = fvarAxes[condition.AxisIndex].axisTag
        default = axisLimits[axisTag].default if axisTag in axisLimits else 0
        return condition.FilterRangeMinValue <= default <= condition.FilterRangeMaxValue
    if condition.Format == 2:
        # instantiateOTL has already moved the default deltas into DefaultValue.
        return condition.DefaultValue > 0
    if condition.Format in (3, 4):
        values = (
            _conditionAppliesAtDefault(child, axisLimits, fvarAxes, depth - 1)
            for child in condition.ConditionTable
        )
        return all(values) if condition.Format == 3 else any(values)
    if condition.Format == 5:
        return not _conditionAppliesAtDefault(
            condition.ConditionTable, axisLimits, fvarAxes, depth - 1
        )
    return False


def _instantiateFeatureVariationRecord(
    record, recIdx, axisLimits, fvarAxes, axisIndexMap
):
    applies = True
    shouldKeep = False
    newConditions = []
    from fontTools.varLib.instancer import NormalizedAxisTripleAndDistances

    default_triple = NormalizedAxisTripleAndDistances(-1, 0, +1)
    if record.ConditionSet is None:
        record.ConditionSet = ot.ConditionSet()
        record.ConditionSet.ConditionTable = []
        record.ConditionSet.ConditionCount = 0
    for i, condition in enumerate(record.ConditionSet.ConditionTable):
        if condition is None:
            continue
        if condition.Format == 1:
            axisIdx = condition.AxisIndex
            axisTag = fvarAxes[axisIdx].axisTag

            minValue = condition.FilterRangeMinValue
            maxValue = condition.FilterRangeMaxValue
            triple = axisLimits.get(axisTag, default_triple)

            if not (minValue <= triple.default <= maxValue):
                applies = False

            # if condition not met, remove entire record
            if triple.minimum > maxValue or triple.maximum < minValue:
                newConditions = None
                break

            if axisTag in axisIndexMap:
                # remap axis index
                condition.AxisIndex = axisIndexMap[axisTag]

                # remap condition limits
                newRange = _limitFeatureVariationConditionRange(condition, triple)
                if newRange:
                    # keep condition with updated limits
                    minimum, maximum = newRange
                    condition.FilterRangeMinValue = minimum
                    condition.FilterRangeMaxValue = maximum
                    shouldKeep = True
                    if minimum != -1 or maximum != +1:
                        newConditions.append(condition)
                else:
                    # condition out of range, remove entire record
                    newConditions = None
                    break

        elif condition.Format in (2, 3, 4, 5):
            applies &= _conditionAppliesAtDefault(condition, axisLimits, fvarAxes)
            result = _instantiateLookupCondition(
                condition, axisLimits, fvarAxes, axisIndexMap
            )
            if result == _LOOKUP_CONDITION_FALSE:
                newConditions = None
                applies = False
                break
            if result == _LOOKUP_CONDITION_KEEP:
                newConditions.append(condition)
                shouldKeep = True
            elif axisIndexMap:
                shouldKeep = True
        else:
            log.warning(
                "Condition table {0} of FeatureVariationRecord {1} has "
                "unsupported format ({2}); ignored".format(i, recIdx, condition.Format)
            )
            applies = False
            newConditions.append(condition)

    if newConditions is not None and shouldKeep:
        record.ConditionSet.ConditionTable = newConditions
        if not newConditions:
            record.ConditionSet = None
        shouldKeep = True
    else:
        shouldKeep = False

    # Does this *always* apply?
    universal = shouldKeep and not newConditions

    return applies, shouldKeep, universal


def _trueLookupCondition():
    condition = ot.ConditionTable()
    condition.Format = 2
    condition.DefaultValue = 1
    condition.VarIdx = ot.NO_VARIATION_INDEX
    return condition


def _instantiateLookupCondition(
    condition, axisLimits, fvarAxes, axisIndexMap, depth=64
):
    if condition is None:
        return _LOOKUP_CONDITION_TRUE

    if not depth:
        log.warning("LookupVariationRecord condition nesting is too deep; ignored")
        return _LOOKUP_CONDITION_KEEP

    if condition.Format == 1:
        axisIdx = condition.AxisIndex
        if axisIdx >= len(fvarAxes):
            log.warning(
                "LookupVariationRecord condition has invalid axis index %d; ignored",
                axisIdx,
            )
            return _LOOKUP_CONDITION_KEEP

        axisTag = fvarAxes[axisIdx].axisTag
        from fontTools.varLib.instancer import NormalizedAxisTripleAndDistances

        triple = axisLimits.get(axisTag, NormalizedAxisTripleAndDistances(-1, 0, +1))
        minimum = condition.FilterRangeMinValue
        maximum = condition.FilterRangeMaxValue
        if minimum > maximum or triple.minimum > maximum or triple.maximum < minimum:
            return _LOOKUP_CONDITION_FALSE
        if triple.minimum == triple.maximum:
            return (
                _LOOKUP_CONDITION_TRUE
                if minimum <= triple.default <= maximum
                else _LOOKUP_CONDITION_FALSE
            )

        newRange = _limitFeatureVariationConditionRange(condition, triple)
        if newRange is None or axisTag not in axisIndexMap:
            return _LOOKUP_CONDITION_FALSE

        condition.AxisIndex = axisIndexMap[axisTag]
        condition.FilterRangeMinValue, condition.FilterRangeMaxValue = newRange
        if newRange[0] <= -1 and newRange[1] >= 1:
            return _LOOKUP_CONDITION_TRUE
        return _LOOKUP_CONDITION_KEEP

    if condition.Format == 2:
        if condition.VarIdx != ot.NO_VARIATION_INDEX:
            return _LOOKUP_CONDITION_KEEP
        return (
            _LOOKUP_CONDITION_TRUE
            if condition.DefaultValue > 0
            else _LOOKUP_CONDITION_FALSE
        )

    if condition.Format in (3, 4):
        newConditions = []
        for child in condition.ConditionTable:
            result = _instantiateLookupCondition(
                child, axisLimits, fvarAxes, axisIndexMap, depth - 1
            )
            if condition.Format == 3 and result == _LOOKUP_CONDITION_FALSE:
                return _LOOKUP_CONDITION_FALSE
            if condition.Format == 4 and result == _LOOKUP_CONDITION_TRUE:
                return _LOOKUP_CONDITION_TRUE
            if result == _LOOKUP_CONDITION_KEEP:
                newConditions.append(child)

        condition.ConditionTable = newConditions
        condition.ConditionCount = len(newConditions)
        if newConditions:
            return _LOOKUP_CONDITION_KEEP
        return (
            _LOOKUP_CONDITION_TRUE if condition.Format == 3 else _LOOKUP_CONDITION_FALSE
        )

    if condition.Format == 5:
        result = _instantiateLookupCondition(
            condition.ConditionTable,
            axisLimits,
            fvarAxes,
            axisIndexMap,
            depth - 1,
        )
        if result == _LOOKUP_CONDITION_TRUE:
            return _LOOKUP_CONDITION_FALSE
        if result == _LOOKUP_CONDITION_FALSE:
            return _LOOKUP_CONDITION_TRUE
        return _LOOKUP_CONDITION_KEEP

    log.warning(
        "LookupVariationRecord condition has unsupported format %d; ignored",
        condition.Format,
    )
    return _LOOKUP_CONDITION_KEEP


def _instantiateLookupVariations(table, fvarAxes, axisLimits, axisIndexMap):
    variations = table.FeatureVariations
    records = getattr(variations, "LookupVariationRecord", [])
    if not records:
        return

    fullyInstanced = not axisIndexMap
    newRecords = []
    for record in records:
        featureLookups = record.FeatureLookupsTable
        selectedLookups = []
        newConditionRecords = []
        canBake = fullyInstanced

        for conditionRecord in featureLookups.LookupConditionRecord:
            result = _instantiateLookupCondition(
                conditionRecord.ConditionTable,
                axisLimits,
                fvarAxes,
                axisIndexMap,
            )
            if result == _LOOKUP_CONDITION_FALSE:
                continue
            if result == _LOOKUP_CONDITION_TRUE:
                selectedLookups.extend(conditionRecord.LookupIndexList.LookupIndex)
                if not fullyInstanced:
                    conditionRecord.ConditionTable = _trueLookupCondition()
                    newConditionRecords.append(conditionRecord)
                continue

            canBake = False
            newConditionRecords.append(conditionRecord)

        if canBake and table.FeatureList is not None:
            featureRecord = table.FeatureList.FeatureRecord[record.FeatureIndex]
            feature = deepcopy(featureRecord.Feature)
            lookupIndices = (
                list(feature.LookupListIndex) if featureLookups.Flags & 1 else []
            )
            lookupIndices.extend(selectedLookups)
            feature.LookupListIndex = sorted(set(lookupIndices))
            feature.LookupCount = len(feature.LookupListIndex)
            featureRecord.Feature = feature
        else:
            featureLookups.LookupConditionRecord = newConditionRecords
            featureLookups.LookupConditionCount = len(newConditionRecords)
            newRecords.append(record)

    variations.LookupVariationRecord = newRecords
    variations.LookupVariationCount = len(newRecords)


def instantiateLookupVariationConditionValues(
    varfont, defaultDeltas=None, varIndexMapping=None
):
    conditions = []
    for tableTag in ("GSUB", "GPOS"):
        if tableTag not in varfont:
            continue
        variations = getattr(varfont[tableTag].table, "FeatureVariations", None)
        for record in getattr(variations, "FeatureVariationRecord", []):
            if record.ConditionSet is not None:
                conditions.extend(record.ConditionSet.ConditionTable)
        for record in getattr(variations, "LookupVariationRecord", []):
            conditions.extend(
                conditionRecord.ConditionTable
                for conditionRecord in record.FeatureLookupsTable.LookupConditionRecord
            )

    seen = set()
    while conditions:
        condition = conditions.pop()
        if condition is None:
            continue
        if id(condition) in seen:
            continue
        seen.add(id(condition))

        if condition.Format == 2:
            varIdx = condition.VarIdx
            if defaultDeltas is not None:
                condition.DefaultValue += otRound(defaultDeltas.get(varIdx, 0))
            if varIndexMapping is not None:
                condition.VarIdx = varIndexMapping.get(varIdx, ot.NO_VARIATION_INDEX)
        elif condition.Format in (3, 4):
            conditions.extend(condition.ConditionTable)
        elif condition.Format == 5:
            conditions.append(condition.ConditionTable)


def _instantiateFeatureVariations(table, fvarAxes, axisLimits):
    pinnedAxes = set(axisLimits.pinnedLocation())
    axisOrder = [axis.axisTag for axis in fvarAxes if axis.axisTag not in pinnedAxes]
    axisIndexMap = {axisTag: axisOrder.index(axisTag) for axisTag in axisOrder}

    featureVariationApplied = False
    uniqueRecords = set()
    newRecords = []
    defaultsSubsts = None

    for i, record in enumerate(table.FeatureVariations.FeatureVariationRecord):
        applies, shouldKeep, universal = _instantiateFeatureVariationRecord(
            record, i, axisLimits, fvarAxes, axisIndexMap
        )

        if shouldKeep and _featureVariationRecordIsUnique(record, uniqueRecords):
            newRecords.append(record)

        if applies and not featureVariationApplied:
            assert record.FeatureTableSubstitution.Version == 0x00010000
            defaultsSubsts = deepcopy(record.FeatureTableSubstitution)
            for default, rec in zip(
                defaultsSubsts.SubstitutionRecord,
                record.FeatureTableSubstitution.SubstitutionRecord,
            ):
                default.Feature = deepcopy(
                    table.FeatureList.FeatureRecord[rec.FeatureIndex].Feature
                )
                table.FeatureList.FeatureRecord[rec.FeatureIndex].Feature = deepcopy(
                    rec.Feature
                )
            # Set variations only once
            featureVariationApplied = True

        # Further records don't have a chance to apply after a universal record
        if universal:
            break

    # Insert a catch-all record to reinstate the old features if necessary
    if featureVariationApplied and newRecords and not universal:
        defaultRecord = ot.FeatureVariationRecord()
        defaultRecord.ConditionSet = ot.ConditionSet()
        defaultRecord.ConditionSet.ConditionTable = []
        defaultRecord.ConditionSet.ConditionCount = 0
        defaultRecord.FeatureTableSubstitution = defaultsSubsts

        newRecords.append(defaultRecord)

    variations = table.FeatureVariations
    variations.FeatureVariationRecord = newRecords
    variations.FeatureVariationCount = len(newRecords)

    _instantiateLookupVariations(table, fvarAxes, axisLimits, axisIndexMap)

    if not (
        variations.FeatureVariationCount
        or getattr(variations, "LookupVariationCount", 0)
    ):
        del table.FeatureVariations
        # downgrade table version if there are no FeatureVariations left
        table.Version = 0x00010000


def instantiateFeatureVariations(varfont, axisLimits):
    for tableTag in ("GPOS", "GSUB"):
        if tableTag not in varfont or not getattr(
            varfont[tableTag].table, "FeatureVariations", None
        ):
            continue
        log.info("Instantiating FeatureVariations of %s table", tableTag)
        _instantiateFeatureVariations(
            varfont[tableTag].table, varfont["fvar"].axes, axisLimits
        )
        # remove unreferenced lookups
        varfont[tableTag].prune_lookups()
