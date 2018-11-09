"""Module to build FeatureVariation tables:
https://docs.microsoft.com/en-us/typography/opentype/spec/chapter2#featurevariations-table

NOTE: The API is experimental and subject to change.
"""
from __future__ import print_function, absolute_import, division

from fontTools.ttLib import newTable
from fontTools.ttLib.tables import otTables as ot
from fontTools.otlLib.builder import buildLookup, buildSingleSubstSubtable
from collections import OrderedDict


# https://stackoverflow.com/questions/1151658/python-hashable-dicts
class hashdict(dict):
    """
    hashable dict implementation, suitable for use as a key into
    other dicts.

        >>> h1 = hashdict({"apples": 1, "bananas":2})
        >>> h2 = hashdict({"bananas": 3, "mangoes": 5})
        >>> h1+h2
        hashdict(apples=1, bananas=3, mangoes=5)
        >>> d1 = {}
        >>> d1[h1] = "salad"
        >>> d1[h1]
        'salad'
        >>> d1[h2]
        Traceback (most recent call last):
        ...
        KeyError: hashdict(bananas=3, mangoes=5)

    based on answers from
       http://stackoverflow.com/questions/1151658/python-hashable-dicts

    """
    def __key(self):
        return tuple(sorted(self.items()))
    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__,
            ", ".join("{0}={1}".format(
                    str(i[0]),repr(i[1])) for i in self.__key()))

    def __hash__(self):
        return hash(self.__key())
    def __setitem__(self, key, value):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))
    def __delitem__(self, key):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))
    def clear(self):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))
    def pop(self, *args, **kwargs):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))
    def popitem(self, *args, **kwargs):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))
    def setdefault(self, *args, **kwargs):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))
    def update(self, *args, **kwargs):
        raise TypeError("{0} does not support item assignment"
                         .format(self.__class__.__name__))
    # update is not ok because it mutates the object
    # __add__ is ok because it creates a new object
    # while the new object is under construction, it's ok to mutate it
    def __add__(self, right):
        result = hashdict(self)
        dict.update(result, right)
        return result

def popCount(v):
    # TODO Speed up
    i = 0
    while v:
        if v & 1:
            i += 1
        v = v >> 1
    return i


def addFeatureVariations(font, conditionalSubstitutions):
    """Add conditional substitutions to a Variable Font.

    The `conditionalSubstitutions` argument is a list of (Region, Substitutions)
    tuples.

    A Region is a list of Boxes. A Box is a dict mapping axisTags to
    (minValue, maxValue) tuples. Irrelevant axes may be omitted and they are
    interpretted as extending to end of axis in each direction.  A Box represents
    an orthogonal 'rectangular' subset of an N-dimensional design space.
    A Region represents a more complex subset of an N-dimensional design space,
    ie. the union of all the Boxes in the Region.
    For efficiency, Boxes within a Region should ideally not overlap, but
    functionality is not compromised if they do.

    The minimum and maximum values are expressed in normalized coordinates.

    A Substitution is a dict mapping source glyph names to substitute glyph names.

    Example:

    # >>> f = TTFont(srcPath)
    # >>> condSubst = [
    # ...     # A list of (Region, Substitution) tuples.
    # ...     ([{"wdth": (0.5, 1.0)}], {"cent": "cent.rvrn"}),
    # ...     ([{"wght": (0.5, 1.0)}], {"dollar": "dollar.rvrn"}),
    # ... ]
    # >>> addFeatureVariations(f, condSubst)
    # >>> f.save(dstPath)
    """

    addFeatureVariationsRaw(font,
                            overlayFeatureVariations(conditionalSubstitutions))

def overlayFeatureVariations(conditionalSubstitutions):
    """Compute overlaps between all conditional substitutions.

    The `conditionalSubstitutions` argument is a list of (Region, Substitutions)
    tuples.

    A Region is a list of Boxes. A Box is a dict mapping axisTags to
    (minValue, maxValue) tuples. Irrelevant axes may be omitted and they are
    interpretted as extending to end of axis in each direction.  A Box represents
    an orthogonal 'rectangular' subset of an N-dimensional design space.
    A Region represents a more complex subset of an N-dimensional design space,
    ie. the union of all the Boxes in the Region.
    For efficiency, Boxes within a Region should ideally not overlap, but
    functionality is not compromised if they do.

    The minimum and maximum values are expressed in normalized coordinates.

    A Substitution is a dict mapping source glyph names to substitute glyph names.

    Returns data is in similar but different format.  Overlaps of distinct
    substitution Boxes (*not* Regions) are explicitly listed as distinct rules,
    and rules with the same Box merged.  The more specific rules appear earlier
    in the resulting list.  Moreover, instead of just a dictionary of substitutions,
    a list of dictionaries is returned for substitutions corresponding to each
    uniq space, with each dictionary being identical to one of the input
    substitution dictionaries.  These dictionaries are not merged to allow data
    sharing when they are converted into font tables.

    Example:
    >>> condSubst = [
    ...     # A list of (Region, Substitution) tuples.
    ...     ([{"wght": (0.5, 1.0)}], {"dollar": "dollar.rvrn"}),
    ...     ([{"wdth": (0.5, 1.0)}], {"cent": "cent.rvrn"}),
    ... ]
    >>> from pprint import pprint
    >>> pprint(overlayFeatureVariations(condSubst))
    [({'wdth': (0.5, 1.0), 'wght': (0.5, 1.0)},
      [{'dollar': 'dollar.rvrn'}, {'cent': 'cent.rvrn'}]),
     ({'wdth': (0.5, 1.0)}, [{'cent': 'cent.rvrn'}]),
     ({'wght': (0.5, 1.0)}, [{'dollar': 'dollar.rvrn'}])]
    """

    # Merge duplicate region rules before intersecting, as this is much cheaper.
    # Also convert boxes to hashdict()
    #
    # Reversing is such that earlier entries win in case of conflicting substitution
    # rules for the same region.
    merged = OrderedDict()
    for key,value in reversed(conditionalSubstitutions):
        key = tuple(sorted(hashdict(cleanupBox(k)) for k in key))
        if key in merged:
            merged[key].update(value)
        else:
            merged[key] = dict(value)
    conditionalSubstitutions = list(reversed(merged.items()))
    del merged

    # Overlay
    #
    # Rank is the bit-set of the index of all contributing layers.
    initMapInit = ((hashdict(),0),) # Initializer representing the entire space
    boxMap = OrderedDict(initMapInit) # Map from Box to Rank
    for i,(currRegion,_) in enumerate(conditionalSubstitutions):
        newMap = OrderedDict(initMapInit)
        currRank = 1<<i
        for box,rank in boxMap.items():
            for currBox in currRegion:
                intersection, remainder = overlayBox(currBox, box)
                if intersection is not None:
                    intersection = hashdict(intersection)
                    newMap[intersection] = newMap.get(intersection, 0) | rank|currRank
                if remainder is not None:
                    remainder = hashdict(remainder)
                    newMap[remainder] = newMap.get(remainder, 0) | rank
        boxMap = newMap
    del boxMap[hashdict()]

    # Generate output
    items = []
    for box,rank in sorted(boxMap.items(),
                           key=(lambda BoxAndRank: -popCount(BoxAndRank[1]))):
        substsList = []
        i = 0
        while rank:
          if rank & 1:
              substsList.append(conditionalSubstitutions[i][1])
          rank >>= 1
          i += 1
        items.append((dict(box),substsList))
    return items


#
# Terminology:
#
# A 'Box' is a dict representing an orthogonal "rectangular" bit of N-dimensional space.
# The keys in the dict are axis tags, the values are (minValue, maxValue) tuples.
# Missing dimensions (keys) are substituted by the default min and max values
# from the corresponding axes.
#

def intersectBoxes(box1, box2):
    """Return the box intersected by `box1` and `box2`, or None if there
    is no intersection.

        >>> intersectBoxes({}, {})
        {}
        >>> intersectBoxes({'wdth': (-0.5, 0.5)}, {})
        {'wdth': (-0.5, 0.5)}
        >>> intersectBoxes({'wdth': (-0.5, 0.5)}, {'wdth': (0.0, 1.0)})
        {'wdth': (0.0, 0.5)}
        >>> expected = {'wdth': (0.0, 0.5), 'wght': (0.25, 0.5)}
        >>> expected == intersectBoxes({'wdth': (-0.5, 0.5), 'wght': (0.0, 0.5)}, {'wdth': (0.0, 1.0), 'wght': (0.25, 0.75)})
        True
        >>> expected = {'wdth': (-0.5, 0.5), 'wght': (0.0, 1.0)}
        >>> expected == intersectBoxes({'wdth': (-0.5, 0.5)}, {'wght': (0.0, 1.0)})
        True
        >>> intersectBoxes({'wdth': (-0.5, 0)}, {'wdth': (0.1, 0.5)})

    """
    box = {}
    box.update(box1)
    box.update(box2)
    for axisTag in set(box1) & set(box2):
        min1, max1 = box1[axisTag]
        min2, max2 = box2[axisTag]
        minimum = max(min1, min2)
        maximum = min(max1, max2)
        if not minimum < maximum:
            return None
        box[axisTag] = minimum, maximum
    return box

def overlayBox(top, bot):
    """Overlays `top` box on top of `bot` box.

    Returns two items:
    - Box for intersection of `top` and `bot`, or None if they don't intersect.
    - Box for remainder of `bot`.  Remainder box might not be exact (since the
      remainder might not be a simple box), but is inclusive of the exact
      remainder.
    """

    # Intersection
    intersection = {}
    intersection.update(top)
    intersection.update(bot)
    for axisTag in set(top) & set(bot):
        min1, max1 = top[axisTag]
        min2, max2 = bot[axisTag]
        minimum = max(min1, min2)
        maximum = min(max1, max2)
        if not minimum < maximum:
            return None, bot # Do not intersect
        intersection[axisTag] = minimum, maximum

    # Remainder
    remainder = bot

    return intersection, remainder

def cleanupBox(box):
    """Return a sparse copy of `box`, without redundant (default) values.

        >>> cleanupBox({})
        {}
        >>> cleanupBox({'wdth': (0.0, 1.0)})
        {'wdth': (0.0, 1.0)}
        >>> cleanupBox({'wdth': (-1.0, 1.0)})
        {}

    """
    return {tag: limit for tag, limit in box.items() if limit != (-1.0, 1.0)}


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
        langSystems = [lsr.LangSys for lsr in scriptRecord.Script.LangSysRecord]
        for langSys in [scriptRecord.Script.DefaultLangSys] + langSystems:
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
    import doctest, sys
    sys.exit(doctest.testmod().failed)
