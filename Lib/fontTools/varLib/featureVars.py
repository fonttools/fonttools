"""Module to build FeatureVariation tables:
https://docs.microsoft.com/en-us/typography/opentype/spec/chapter2#featurevariations-table

NOTE: The API is experimental and subject to change.
"""
from __future__ import print_function, absolute_import, division

from fontTools.ttLib import newTable
from fontTools.ttLib.tables import otTables as ot
from fontTools.otlLib.builder import buildLookup, buildSingleSubstSubtable
import itertools


def addFeatureVariations(font, conditionalSubstitutions):
    """Add conditional substitutions to a Variable Font.

    The `conditionalSubstitutions` argument is a list of (Region, Substitutions)
    tuples.

    A Region is a list of Spaces. A Space is a dict mapping axisTags to
    (minValue, maxValue) tuples. Irrelevant axes may be omitted.
    A Space represents a 'rectangular' subset of an N-dimensional design space.
    A Region represents a more complex subset of an N-dimensional design space,
    ie. the union of all the Spaces in the Region.
    For efficiency, Spaces within a Region should ideally not overlap, but
    functionality is not compromised if they do.

    The minimum and maximum values are expressed in normalized coordinates.

    A Substitution is a dict mapping source glyph names to substitute glyph names.
    """

    # Example:
    #
    #     >>> f = TTFont(srcPath)
    #     >>> condSubst = [
    #     ...     # A list of (Region, Substitution) tuples.
    #     ...     ([{"wght": (0.5, 1.0)}], {"dollar": "dollar.rvrn"}),
    #     ...     ([{"wdth": (0.5, 1.0)}], {"cent": "cent.rvrn"}),
    #     ... ]
    #     >>> addFeatureVariations(f, condSubst)
    #     >>> f.save(dstPath)

    # Since the FeatureVariations table will only ever match one rule at a time,
    # we will make new rules for all possible combinations of our input, so we
    # can indirectly support overlapping rules.
    explodedConditionalSubstitutions = []
    for combination in iterAllCombinations(len(conditionalSubstitutions)):
        regions = []
        lookups = []
        for index in combination:
            regions.append(conditionalSubstitutions[index][0])
            lookups.append(conditionalSubstitutions[index][1])
        if not regions:
            continue
        intersection = regions[0]
        for region in regions[1:]:
            intersection = intersectRegions(intersection, region)
        for space in intersection:
            # Remove default values, so we don't generate redundant ConditionSets
            space = cleanupSpace(space)
            if space:
                explodedConditionalSubstitutions.append((space, lookups))

    addFeatureVariationsRaw(font, explodedConditionalSubstitutions)


def iterAllCombinations(numRules):
    """Given a number of rules, yield all the combinations of indices, sorted
    by decreasing length, so we get the most specialized rules first.

        >>> list(iterAllCombinations(0))
        []
        >>> list(iterAllCombinations(1))
        [(0,)]
        >>> list(iterAllCombinations(2))
        [(0, 1), (0,), (1,)]
        >>> list(iterAllCombinations(3))
        [(0, 1, 2), (0, 1), (0, 2), (1, 2), (0,), (1,), (2,)]
    """
    indices = range(numRules)
    for length in range(numRules, 0, -1):
        for combinations in itertools.combinations(indices, length):
            yield combinations


#
# Region and Space support
#
# Terminology:
#
# A 'Space' is a dict representing a "rectangular" bit of N-dimensional space.
# The keys in the dict are axis tags, the values are (minValue, maxValue) tuples.
# Missing dimensions (keys) are substituted by the default min and max values
# from the corresponding axes.
#
# A 'Region' is a list of Space dicts, representing the union of the Spaces,
# therefore representing a more complex subset of design space.
#

def intersectRegions(region1, region2):
    """Return the region intersecting `region1` and `region2`.

        >>> intersectRegions([], [])
        []
        >>> intersectRegions([{'wdth': (0.0, 1.0)}], [])
        []
        >>> expected = [{'wdth': (0.0, 1.0), 'wght': (-1.0, 0.0)}]
        >>> expected == intersectRegions([{'wdth': (0.0, 1.0)}], [{'wght': (-1.0, 0.0)}])
        True
        >>> expected = [{'wdth': (0.0, 1.0), 'wght': (-0.5, 0.0)}]
        >>> expected == intersectRegions([{'wdth': (0.0, 1.0), 'wght': (-0.5, 0.5)}], [{'wght': (-1.0, 0.0)}])
        True
        >>> intersectRegions(
        ...     [{'wdth': (0.0, 1.0), 'wght': (-0.5, 0.5)}],
        ...     [{'wdth': (-1.0, 0.0), 'wght': (-1.0, 0.0)}])
        []

    """
    region = []
    for space1 in region1:
        for space2 in region2:
            space = intersectSpaces(space1, space2)
            if space is not None:
                region.append(space)
    return region


def intersectSpaces(space1, space2):
    """Return the space intersected by `space1` and `space2`, or None if there
    is no intersection.

        >>> intersectSpaces({}, {})
        {}
        >>> intersectSpaces({'wdth': (-0.5, 0.5)}, {})
        {'wdth': (-0.5, 0.5)}
        >>> intersectSpaces({'wdth': (-0.5, 0.5)}, {'wdth': (0.0, 1.0)})
        {'wdth': (0.0, 0.5)}
        >>> expected = {'wdth': (0.0, 0.5), 'wght': (0.25, 0.5)}
        >>> expected == intersectSpaces({'wdth': (-0.5, 0.5), 'wght': (0.0, 0.5)}, {'wdth': (0.0, 1.0), 'wght': (0.25, 0.75)})
        True
        >>> expected = {'wdth': (-0.5, 0.5), 'wght': (0.0, 1.0)}
        >>> expected == intersectSpaces({'wdth': (-0.5, 0.5)}, {'wght': (0.0, 1.0)})
        True
        >>> intersectSpaces({'wdth': (-0.5, 0)}, {'wdth': (0.1, 0.5)})

    """
    space = {}
    space.update(space1)
    space.update(space2)
    for axisTag in set(space1) & set(space2):
        min1, max1 = space1[axisTag]
        min2, max2 = space2[axisTag]
        minimum = max(min1, min2)
        maximum = min(max1, max2)
        if not minimum < maximum:
            return None
        space[axisTag] = minimum, maximum
    return space


def cleanupSpace(space):
    """Return a sparse copy of `space`, without redundant (default) values.

        >>> cleanupSpace({})
        {}
        >>> cleanupSpace({'wdth': (0.0, 1.0)})
        {'wdth': (0.0, 1.0)}
        >>> cleanupSpace({'wdth': (-1.0, 1.0)})
        {}

    """
    return {tag: limit for tag, limit in space.items() if limit != (-1.0, 1.0)}


#
# Low level implementation
#

def addFeatureVariationsRaw(font, conditionalSubstitutions):
    """Low level implementation of addFeatureVariations that directly
    models the possibilities of the FeatureVariations table."""

    #
    # assert there is no 'rvrn' feature
    # make dummy 'rvrn' feature with no lookups
    # sort features, get 'rvrn' feature index
    # add 'rvrn' feature to all scripts
    # make lookups
    # add feature variations
    #

    if "GSUB" not in font:
        font["GSUB"] = buildGSUB()

    gsub = font["GSUB"].table

    if gsub.Version < 0x00010001:
        gsub.Version = 0x00010001  # allow gsub.FeatureVariations

    gsub.FeatureVariations = None  # delete any existing FeatureVariations

    for feature in gsub.FeatureList.FeatureRecord:
        assert feature.FeatureTag != 'rvrn'

    rvrnFeature = buildFeatureRecord('rvrn', [])
    gsub.FeatureList.FeatureRecord.append(rvrnFeature)

    sortFeatureList(gsub)
    rvrnFeatureIndex = gsub.FeatureList.FeatureRecord.index(rvrnFeature)

    for scriptRecord in gsub.ScriptList.ScriptRecord:
        for langSys in [scriptRecord.Script.DefaultLangSys] + scriptRecord.Script.LangSysRecord:
            langSys.FeatureIndex.append(rvrnFeatureIndex)

    # setup lookups

    # turn substitution dicts into tuples of tuples, so they are hashable
    conditionalSubstitutions, allSubstitutions = makeSubstitutionsHashable(conditionalSubstitutions)

    lookupMap = buildSubstitutionLookups(gsub, allSubstitutions)

    axisIndices = {axis.axisTag: axisIndex for axisIndex, axis in enumerate(font["fvar"].axes)}

    featureVariationRecords = []
    for conditionSet, substitutions in conditionalSubstitutions:
        conditionTable = []
        for axisTag, (minValue, maxValue) in sorted(conditionSet.items()):
            assert minValue < maxValue
            ct = buildConditionTable(axisIndices[axisTag], minValue, maxValue)
            conditionTable.append(ct)

        lookupIndices = [lookupMap[subst] for subst in substitutions]
        record = buildFeatureTableSubstitutionRecord(rvrnFeatureIndex, lookupIndices)
        featureVariationRecords.append(buildFeatureVariationRecord(conditionTable, [record]))

    gsub.FeatureVariations = buildFeatureVariations(featureVariationRecords)


#
# Building GSUB/FeatureVariations internals
#

def buildGSUB():
    """Build a GSUB table from scratch."""
    fontTable = newTable("GSUB")
    gsub = fontTable.table = ot.GSUB()
    gsub.Version = 0x00010001  # allow gsub.FeatureVariations

    gsub.ScriptList = ot.ScriptList()
    gsub.ScriptList.ScriptRecord = []
    gsub.FeatureList = ot.FeatureList()
    gsub.FeatureList.FeatureRecord = []
    gsub.LookupList = ot.LookupList()
    gsub.LookupList.Lookup = []

    srec = ot.ScriptRecord()
    srec.ScriptTag = 'DFLT'
    srec.Script = ot.Script()
    srec.Script.DefaultLangSys = None
    srec.Script.LangSysRecord = []

    langrec = ot.LangSysRecord()
    langrec.LangSys = ot.LangSys()
    langrec.LangSys.ReqFeatureIndex = 0xFFFF
    langrec.LangSys.FeatureIndex = [0]
    srec.Script.DefaultLangSys = langrec.LangSys

    gsub.ScriptList.ScriptRecord.append(srec)
    gsub.FeatureVariations = None

    return fontTable


def makeSubstitutionsHashable(conditionalSubstitutions):
    """Turn all the substitution dictionaries in sorted tuples of tuples so
    they are hashable, to detect duplicates so we don't write out redundant
    data."""
    allSubstitutions = set()
    condSubst = []
    for conditionSet, substitutionMaps in conditionalSubstitutions:
        substitutions = []
        for substitutionMap in substitutionMaps:
            subst = tuple(sorted(substitutionMap.items()))
            substitutions.append(subst)
            allSubstitutions.add(subst)
        condSubst.append((conditionSet, substitutions))
    return condSubst, sorted(allSubstitutions)


def buildSubstitutionLookups(gsub, allSubstitutions):
    """Build the lookups for the glyph substitutions, return a dict mapping
    the substitution to lookup indices."""
    firstIndex = len(gsub.LookupList.Lookup)
    lookupMap = {}
    for i, substitutionMap in enumerate(allSubstitutions):
        lookupMap[substitutionMap] = i + firstIndex

    for subst in allSubstitutions:
        substMap = dict(subst)
        lookup = buildLookup([buildSingleSubstSubtable(substMap)])
        gsub.LookupList.Lookup.append(lookup)
        assert gsub.LookupList.Lookup[lookupMap[subst]] is lookup
    return lookupMap


def buildFeatureVariations(featureVariationRecords):
    """Build the FeatureVariations subtable."""
    fv = ot.FeatureVariations()
    fv.Version = 0x00010000
    fv.FeatureVariationRecord = featureVariationRecords
    return fv


def buildFeatureRecord(featureTag, lookupListIndices):
    """Build a FeatureRecord."""
    fr = ot.FeatureRecord()
    fr.FeatureTag = featureTag
    fr.Feature = ot.Feature()
    fr.Feature.LookupListIndex = lookupListIndices
    return fr


def buildFeatureVariationRecord(conditionTable, substitutionRecords):
    """Build a FeatureVariationRecord."""
    fvr = ot.FeatureVariationRecord()
    fvr.ConditionSet = ot.ConditionSet()
    fvr.ConditionSet.ConditionTable = conditionTable
    fvr.FeatureTableSubstitution = ot.FeatureTableSubstitution()
    fvr.FeatureTableSubstitution.Version = 0x00010001
    fvr.FeatureTableSubstitution.SubstitutionRecord = substitutionRecords
    return fvr


def buildFeatureTableSubstitutionRecord(featureIndex, lookupListIndices):
    """Build a FeatureTableSubstitutionRecord."""
    ftsr = ot.FeatureTableSubstitutionRecord()
    ftsr.FeatureIndex = featureIndex
    ftsr.Feature = ot.Feature()
    ftsr.Feature.LookupListIndex = lookupListIndices
    return ftsr


def buildConditionTable(axisIndex, filterRangeMinValue, filterRangeMaxValue):
    """Build a ConditionTable."""
    ct = ot.ConditionTable()
    ct.Format = 1
    ct.AxisIndex = axisIndex
    ct.FilterRangeMinValue = filterRangeMinValue
    ct.FilterRangeMaxValue = filterRangeMaxValue
    return ct


def sortFeatureList(table):
    """Sort the feature list by feature tag, and remap the feature indices
    elsewhere. This is needed after the feature list has been modified.
    """
    # decorate, sort, undecorate, because we need to make an index remapping table
    tagIndexFea = [(fea.FeatureTag, index, fea) for index, fea in enumerate(table.FeatureList.FeatureRecord)]
    tagIndexFea.sort()
    table.FeatureList.FeatureRecord = [fea for tag, index, fea in tagIndexFea]
    featureRemap = dict(zip([index for tag, index, fea in tagIndexFea], range(len(tagIndexFea))))

    # Remap the feature indices
    remapFeatures(table, featureRemap)


def remapFeatures(table, featureRemap):
    """Go through the scripts list, and remap feature indices."""
    for scriptIndex, script in enumerate(table.ScriptList.ScriptRecord):
        defaultLangSys = script.Script.DefaultLangSys
        if defaultLangSys is not None:
            _remapLangSys(defaultLangSys, featureRemap)
        for langSysRecordIndex, langSysRec in enumerate(script.Script.LangSysRecord):
            langSys = langSysRec.LangSys
            _remapLangSys(langSys, featureRemap)

    if hasattr(table, "FeatureVariations") and table.FeatureVariations is not None:
        for fvr in table.FeatureVariations.FeatureVariationRecord:
            for ftsr in fvr.FeatureTableSubstitution.SubstitutionRecord:
                ftsr.FeatureIndex = featureRemap[ftsr.FeatureIndex]


def _remapLangSys(langSys, featureRemap):
    if langSys.ReqFeatureIndex != 0xffff:
        langSys.ReqFeatureIndex = featureRemap[langSys.ReqFeatureIndex]
    langSys.FeatureIndex = [featureRemap[index] for index in langSys.FeatureIndex]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
