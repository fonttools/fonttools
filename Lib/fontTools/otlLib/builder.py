from collections import namedtuple
from fontTools.misc.fixedTools import fixedToFloat
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otBase import ValueRecord, valueRecordFormatDict


def buildCoverage(glyphs, glyphMap):
    if not glyphs:
        return None
    self = ot.Coverage()
    self.glyphs = sorted(glyphs, key=glyphMap.__getitem__)
    return self


LOOKUP_FLAG_RIGHT_TO_LEFT = 0x0001
LOOKUP_FLAG_IGNORE_BASE_GLYPHS = 0x0002
LOOKUP_FLAG_IGNORE_LIGATURES = 0x0004
LOOKUP_FLAG_IGNORE_MARKS = 0x0008
LOOKUP_FLAG_USE_MARK_FILTERING_SET = 0x0010


def buildLookup(subtables, flags=0, markFilterSet=None):
    if subtables is None:
        return None
    subtables = [st for st in subtables if st is not None]
    if not subtables:
        return None
    assert all(t.LookupType == subtables[0].LookupType for t in subtables), \
        ("all subtables must have the same LookupType; got %s" %
         repr([t.LookupType for t in subtables]))
    self = ot.Lookup()
    self.LookupType = subtables[0].LookupType
    self.LookupFlag = flags
    self.SubTable = subtables
    self.SubTableCount = len(self.SubTable)
    if markFilterSet is not None:
        assert self.LookupFlag & LOOKUP_FLAG_USE_MARK_FILTERING_SET, \
            ("if markFilterSet is not None, flags must set "
             "LOOKUP_FLAG_USE_MARK_FILTERING_SET; flags=0x%04x" % flags)
        assert isinstance(markFilterSet, int), markFilterSet
        self.MarkFilteringSet = markFilterSet
    else:
        assert (self.LookupFlag & LOOKUP_FLAG_USE_MARK_FILTERING_SET) == 0, \
            ("if markFilterSet is None, flags must not set "
             "LOOKUP_FLAG_USE_MARK_FILTERING_SET; flags=0x%04x" % flags)
    return self


# GSUB


def buildSingleSubstSubtable(mapping):
    if not mapping:
        return None
    self = ot.SingleSubst()
    self.mapping = dict(mapping)
    return self


def buildMultipleSubstSubtable(mapping):
    if not mapping:
        return None
    self = ot.MultipleSubst()
    self.mapping = dict(mapping)
    return self


def buildAlternateSubstSubtable(mapping):
    if not mapping:
        return None
    self = ot.AlternateSubst()
    self.alternates = dict(mapping)
    return self


def _getLigatureKey(components):
    """Computes a key for ordering ligatures in a GSUB Type-4 lookup.

    When building the OpenType lookup, we need to make sure that
    the longest sequence of components is listed first, so we
    use the negative length as the primary key for sorting.
    To make buildLigatureSubstSubtable() deterministic, we use the
    component sequence as the secondary key.

    For example, this will sort (f,f,f) < (f,f,i) < (f,f) < (f,i) < (f,l).
    """
    return (-len(components), components)


def buildLigatureSubstSubtable(mapping):
    if not mapping:
        return None
    self = ot.LigatureSubst()
    # The following single line can replace the rest of this function
    # with fontTools >= 3.1:
    # self.ligatures = dict(mapping)
    self.ligatures = {}
    for components in sorted(mapping.keys(), key=_getLigatureKey):
        ligature = ot.Ligature()
        ligature.Component = components[1:]
        ligature.CompCount = len(ligature.Component) + 1
        ligature.LigGlyph = mapping[components]
        firstGlyph = components[0]
        self.ligatures.setdefault(firstGlyph, []).append(ligature)
    return self


# GPOS


def buildAnchor(x, y, point=None, deviceX=None, deviceY=None):
    self = ot.Anchor()
    self.XCoordinate, self.YCoordinate = x, y
    self.Format = 1
    if point is not None:
        self.AnchorPoint = point
        self.Format = 2
    if deviceX is not None or deviceY is not None:
        assert self.Format == 1, \
            "Either point, or both of deviceX/deviceY, must be None."
        self.XDeviceTable = deviceX
        self.YDeviceTable = deviceY
        self.Format = 3
    return self


def buildBaseArray(bases, numMarkClasses, glyphMap):
    self = ot.BaseArray()
    self.BaseRecord = []
    for base in sorted(bases, key=glyphMap.__getitem__):
        b = bases[base]
        anchors = [b.get(markClass) for markClass in range(numMarkClasses)]
        self.BaseRecord.append(buildBaseRecord(anchors))
    self.BaseCount = len(self.BaseRecord)
    return self


def buildBaseRecord(anchors):
    """[otTables.Anchor, otTables.Anchor, ...] --> otTables.BaseRecord"""
    self = ot.BaseRecord()
    self.BaseAnchor = anchors
    return self


def buildComponentRecord(anchors):
    """[otTables.Anchor, otTables.Anchor, ...] --> otTables.ComponentRecord"""
    if not anchors:
        return None
    self = ot.ComponentRecord()
    self.LigatureAnchor = anchors
    return self


def buildCursivePosSubtable(attach, glyphMap):
    """{"alef": (entry, exit)} --> otTables.CursivePos"""
    if not attach:
        return None
    self = ot.CursivePos()
    self.Format = 1
    self.Coverage = buildCoverage(attach.keys(), glyphMap)
    self.EntryExitRecord = []
    for glyph in self.Coverage.glyphs:
        entryAnchor, exitAnchor = attach[glyph]
        rec = ot.EntryExitRecord()
        rec.EntryAnchor = entryAnchor
        rec.ExitAnchor = exitAnchor
        self.EntryExitRecord.append(rec)
    self.EntryExitCount = len(self.EntryExitRecord)
    return self


def buildDevice(deltas):
    """{8:+1, 10:-3, ...} --> otTables.Device"""
    if not deltas:
        return None
    self = ot.Device()
    keys = deltas.keys()
    self.StartSize = startSize = min(keys)
    self.EndSize = endSize = max(keys)
    assert 0 <= startSize <= endSize
    self.DeltaValue = deltaValues = [
        deltas.get(size, 0)
        for size in range(startSize, endSize + 1)]
    maxDelta = max(deltaValues)
    minDelta = min(deltaValues)
    assert minDelta > -129 and maxDelta < 128
    if minDelta > -3 and maxDelta < 2:
        self.DeltaFormat = 1
    elif minDelta > -9 and maxDelta < 8:
        self.DeltaFormat = 2
    else:
        self.DeltaFormat = 3
    return self


def buildLigatureArray(ligs, numMarkClasses, glyphMap):
    self = ot.LigatureArray()
    self.LigatureAttach = []
    for lig in sorted(ligs, key=glyphMap.__getitem__):
        anchors = []
        for component in ligs[lig]:
            anchors.append([component.get(mc) for mc in range(numMarkClasses)])
        self.LigatureAttach.append(buildLigatureAttach(anchors))
    self.LigatureCount = len(self.LigatureAttach)
    return self


def buildLigatureAttach(components):
    """[[Anchor, Anchor], [Anchor, Anchor, Anchor]] --> LigatureAttach"""
    self = ot.LigatureAttach()
    self.ComponentRecord = [buildComponentRecord(c) for c in components]
    self.ComponentCount = len(self.ComponentRecord)
    return self


def buildMarkArray(marks, glyphMap):
    """{"acute": (markClass, otTables.Anchor)} --> otTables.MarkArray"""
    self = ot.MarkArray()
    self.MarkRecord = []
    for mark in sorted(marks.keys(), key=glyphMap.__getitem__):
        markClass, anchor = marks[mark]
        markrec = buildMarkRecord(markClass, anchor)
        self.MarkRecord.append(markrec)
    self.MarkCount = len(self.MarkRecord)
    return self


def buildMarkBasePos(marks, bases, glyphMap):
    """Build a list of MarkBasePos subtables.

    a1, a2, a3, a4, a5 = buildAnchor(500, 100), ...
    marks = {"acute": (0, a1), "grave": (0, a1), "cedilla": (1, a2)}
    bases = {"a": {0: a3, 1: a5}, "b": {0: a4, 1: a5}}
    """
    # TODO: Consider emitting multiple subtables to save space.
    # Partition the marks and bases into disjoint subsets, so that
    # MarkBasePos rules would only access glyphs from a single
    # subset. This would likely lead to smaller mark/base
    # matrices, so we might be able to omit many of the empty
    # anchor tables that we currently produce. Of course, this
    # would only work if the MarkBasePos rules of real-world fonts
    # allow partitioning into multiple subsets. We should find out
    # whether this is the case; if so, implement the optimization.
    # On the other hand, a very large number of subtables could
    # slow down layout engines; so this would need profiling.
    return [buildMarkBasePosSubtable(marks, bases, glyphMap)]


def buildMarkBasePosSubtable(marks, bases, glyphMap):
    """Build a single MarkBasePos subtable.

    a1, a2, a3, a4, a5 = buildAnchor(500, 100), ...
    marks = {"acute": (0, a1), "grave": (0, a1), "cedilla": (1, a2)}
    bases = {"a": {0: a3, 1: a5}, "b": {0: a4, 1: a5}}
    """
    self = ot.MarkBasePos()
    self.Format = 1
    self.MarkCoverage = buildCoverage(marks, glyphMap)
    self.MarkArray = buildMarkArray(marks, glyphMap)
    self.ClassCount = max([mc for mc, _ in marks.values()]) + 1
    self.BaseCoverage = buildCoverage(bases, glyphMap)
    self.BaseArray = buildBaseArray(bases, self.ClassCount, glyphMap)
    return self


def buildMarkLigPos(marks, ligs, glyphMap):
    """Build a list of MarkLigPos subtables.

    a1, a2, a3, a4, a5 = buildAnchor(500, 100), ...
    marks = {"acute": (0, a1), "grave": (0, a1), "cedilla": (1, a2)}
    ligs = {"f_i": [{0: a3, 1: a5},  {0: a4, 1: a5}], "c_t": [{...}, {...}]}
    """
    # TODO: Consider splitting into multiple subtables to save space,
    # as with MarkBasePos, this would be a trade-off that would need
    # profiling. And, depending on how typical fonts are structured,
    # it might not be worth doing at all.
    return [buildMarkLigPosSubtable(marks, ligs, glyphMap)]


def buildMarkLigPosSubtable(marks, ligs, glyphMap):
    """Build a single MarkLigPos subtable.

    a1, a2, a3, a4, a5 = buildAnchor(500, 100), ...
    marks = {"acute": (0, a1), "grave": (0, a1), "cedilla": (1, a2)}
    ligs = {"f_i": [{0: a3, 1: a5},  {0: a4, 1: a5}], "c_t": [{...}, {...}]}
    """
    self = ot.MarkLigPos()
    self.Format = 1
    self.MarkCoverage = buildCoverage(marks, glyphMap)
    self.MarkArray = buildMarkArray(marks, glyphMap)
    self.ClassCount = max([mc for mc, _ in marks.values()]) + 1
    self.LigatureCoverage = buildCoverage(ligs, glyphMap)
    self.LigatureArray = buildLigatureArray(ligs, self.ClassCount, glyphMap)
    return self


def buildMarkRecord(classID, anchor):
    assert isinstance(classID, int)
    assert isinstance(anchor, ot.Anchor)
    self = ot.MarkRecord()
    self.Class = classID
    self.MarkAnchor = anchor
    return self


def buildMark2Record(anchors):
    """[otTables.Anchor, otTables.Anchor, ...] --> otTables.Mark2Record"""
    self = ot.Mark2Record()
    self.Mark2Anchor = anchors
    return self


def _getValueFormat(f, values, i):
    """Helper for buildPairPos{Glyphs|Classes}Subtable."""
    if f is not None:
        return f
    mask = 0
    for value in values:
        if value is not None and value[i] is not None:
            mask |= value[i].getFormat()
    return mask


def buildPairPosClassesSubtable(pairs, glyphMap,
                                valueFormat1=None, valueFormat2=None):
    coverage = set()
    classDef1 = ClassDefBuilder(useClass0=True)
    classDef2 = ClassDefBuilder(useClass0=False)
    for gc1, gc2 in sorted(pairs):
        coverage.update(gc1)
        classDef1.add(gc1)
        classDef2.add(gc2)
    self = ot.PairPos()
    self.Format = 2
    self.ValueFormat1 = _getValueFormat(valueFormat1, pairs.values(), 0)
    self.ValueFormat2 = _getValueFormat(valueFormat2, pairs.values(), 1)
    self.Coverage = buildCoverage(coverage, glyphMap)
    self.ClassDef1 = classDef1.build()
    self.ClassDef2 = classDef2.build()
    classes1 = classDef1.classes()
    classes2 = classDef2.classes()
    self.Class1Record = []
    for c1 in classes1:
        rec1 = ot.Class1Record()
        rec1.Class2Record = []
        self.Class1Record.append(rec1)
        for c2 in classes2:
            rec2 = ot.Class2Record()
            rec2.Value1, rec2.Value2 = pairs.get((c1, c2), (None, None))
            rec1.Class2Record.append(rec2)
    self.Class1Count = len(self.Class1Record)
    self.Class2Count = len(classes2)
    return self


def buildPairPosGlyphs(pairs, glyphMap):
    p = {}  # (formatA, formatB) --> {(glyphA, glyphB): (valA, valB)}
    for (glyphA, glyphB), (valA, valB) in pairs.items():
        formatA = valA.getFormat() if valA is not None else 0
        formatB = valB.getFormat() if valB is not None else 0
        pos = p.setdefault((formatA, formatB), {})
        pos[(glyphA, glyphB)] = (valA, valB)
    return [
        buildPairPosGlyphsSubtable(pos, glyphMap, formatA, formatB)
        for ((formatA, formatB), pos) in sorted(p.items())]


def buildPairPosGlyphsSubtable(pairs, glyphMap,
                               valueFormat1=None, valueFormat2=None):
    self = ot.PairPos()
    self.Format = 1
    self.ValueFormat1 = _getValueFormat(valueFormat1, pairs.values(), 0)
    self.ValueFormat2 = _getValueFormat(valueFormat2, pairs.values(), 1)
    p = {}
    for (glyphA, glyphB), (valA, valB) in pairs.items():
        p.setdefault(glyphA, []).append((glyphB, valA, valB))
    self.Coverage = buildCoverage({g for g, _ in pairs.keys()}, glyphMap)
    self.PairSet = []
    for glyph in self.Coverage.glyphs:
        ps = ot.PairSet()
        ps.PairValueRecord = []
        self.PairSet.append(ps)
        for glyph2, val1, val2 in \
                sorted(p[glyph], key=lambda x: glyphMap[x[0]]):
            pvr = ot.PairValueRecord()
            pvr.SecondGlyph = glyph2
            pvr.Value1 = val1 if val1 and val1.getFormat() != 0 else None
            pvr.Value2 = val2 if val2 and val2.getFormat() != 0 else None
            ps.PairValueRecord.append(pvr)
        ps.PairValueCount = len(ps.PairValueRecord)
    self.PairSetCount = len(self.PairSet)
    return self


def buildSinglePos(mapping, glyphMap):
    """{"glyph": ValueRecord} --> [otTables.SinglePos*]"""
    result, handled = [], set()
    # In SinglePos format 1, the covered glyphs all share the same ValueRecord.
    # In format 2, each glyph has its own ValueRecord, but these records
    # all have the same properties (eg., all have an X but no Y placement).
    coverages, masks, values = {}, {}, {}
    for glyph, value in mapping.items():
        key = _getSinglePosValueKey(value)
        coverages.setdefault(key, []).append(glyph)
        masks.setdefault(key[0], []).append(key)
        values[key] = value

    # If a ValueRecord is shared between multiple glyphs, we generate
    # a SinglePos format 1 subtable; that is the most compact form.
    for key, glyphs in coverages.items():
        # 5 ushorts is the length of introducing another sublookup
        if len(glyphs) * _getSinglePosValueSize(key) > 5:
            format1Mapping = {g: values[key] for g in glyphs}
            result.append(buildSinglePosSubtable(format1Mapping, glyphMap))
            handled.add(key)

    # In the remaining ValueRecords, look for those whose valueFormat
    # (the set of used properties) is shared between multiple records.
    # These will get encoded in format 2.
    for valueFormat, keys in masks.items():
        f2 = [k for k in keys if k not in handled]
        if len(f2) > 1:
            format2Mapping = {}
            for k in f2:
                format2Mapping.update((g, values[k]) for g in coverages[k])
            result.append(buildSinglePosSubtable(format2Mapping, glyphMap))
            handled.update(f2)

    # The remaining ValueRecords are only used by a few glyphs, normally
    # one. We encode these in format 1 again.
    for key, glyphs in coverages.items():
        if key not in handled:
            for g in glyphs:
                st = buildSinglePosSubtable({g: values[key]}, glyphMap)
            result.append(st)

    # When the OpenType layout engine traverses the subtables, it will
    # stop after the first matching subtable.  Therefore, we sort the
    # resulting subtables by decreasing coverage size; this increases
    # the chance that the layout engine can do an early exit. (Of course,
    # this would only be true if all glyphs were equally frequent, which
    # is not really the case; but we do not know their distribution).
    # If two subtables cover the same number of glyphs, we sort them
    # by glyph ID so that our output is deterministic.
    result.sort(key=lambda t: _getSinglePosTableKey(t, glyphMap))
    return result


def buildSinglePosSubtable(values, glyphMap):
    """{glyphName: otBase.ValueRecord} --> otTables.SinglePos"""
    self = ot.SinglePos()
    self.Coverage = buildCoverage(values.keys(), glyphMap)
    valueRecords = [values[g] for g in self.Coverage.glyphs]
    self.ValueFormat = 0
    for v in valueRecords:
        self.ValueFormat |= v.getFormat()
    if all(v == valueRecords[0] for v in valueRecords):
        self.Format = 1
        if self.ValueFormat != 0:
            self.Value = valueRecords[0]
        else:
            self.Value = None
    else:
        self.Format = 2
        self.Value = valueRecords
        self.ValueCount = len(self.Value)
    return self


def _getSinglePosTableKey(subtable, glyphMap):
    assert isinstance(subtable, ot.SinglePos), subtable
    glyphs = subtable.Coverage.glyphs
    return (-len(glyphs), glyphMap[glyphs[0]])


def _getSinglePosValueKey(valueRecord):
    """otBase.ValueRecord --> (2, ("YPlacement": 12))"""
    assert isinstance(valueRecord, ValueRecord), valueRecord
    valueFormat, result = 0, []
    for name, value in valueRecord.__dict__.items():
        if isinstance(value, ot.Device):
            result.append((name, _makeDeviceTuple(value)))
        else:
            result.append((name, value))
        valueFormat |= valueRecordFormatDict[name][0]
    result.sort()
    result.insert(0, valueFormat)
    return tuple(result)


_DeviceTuple = namedtuple("_DeviceTuple", "DeltaFormat StartSize EndSize DeltaValue")


def _makeDeviceTuple(device):
    """otTables.Device --> tuple, for making device tables unique"""
    return _DeviceTuple(
        device.DeltaFormat,
        device.StartSize,
        device.EndSize,
        () if device.DeltaFormat & 0x8000 else tuple(device.DeltaValue)
    )


def _getSinglePosValueSize(valueKey):
    """Returns how many ushorts this valueKey (short form of ValueRecord) takes up"""
    count = 0
    for _, v in valueKey[1:]:
        if isinstance(v, _DeviceTuple):
            count += len(v.DeltaValue) + 3
        else:
            count += 1
    return count

def buildValue(value):
    self = ValueRecord()
    for k, v in value.items():
        setattr(self, k, v)
    return self


# GDEF

def buildAttachList(attachPoints, glyphMap):
    """{"glyphName": [4, 23]} --> otTables.AttachList, or None"""
    if not attachPoints:
        return None
    self = ot.AttachList()
    self.Coverage = buildCoverage(attachPoints.keys(), glyphMap)
    self.AttachPoint = [buildAttachPoint(attachPoints[g])
                        for g in self.Coverage.glyphs]
    self.GlyphCount = len(self.AttachPoint)
    return self


def buildAttachPoint(points):
    """[4, 23, 41] --> otTables.AttachPoint"""
    if not points:
        return None
    self = ot.AttachPoint()
    self.PointIndex = sorted(set(points))
    self.PointCount = len(self.PointIndex)
    return self


def buildCaretValueForCoord(coord):
    """500 --> otTables.CaretValue, format 1"""
    self = ot.CaretValue()
    self.Format = 1
    self.Coordinate = coord
    return self


def buildCaretValueForPoint(point):
    """4 --> otTables.CaretValue, format 2"""
    self = ot.CaretValue()
    self.Format = 2
    self.CaretValuePoint = point
    return self


def buildLigCaretList(coords, points, glyphMap):
    """{"f_f_i":[300,600]}, {"c_t":[28]} --> otTables.LigCaretList, or None"""
    glyphs = set(coords.keys()) if coords else set()
    if points:
        glyphs.update(points.keys())
    carets = {g: buildLigGlyph(coords.get(g), points.get(g)) for g in glyphs}
    carets = {g: c for g, c in carets.items() if c is not None}
    if not carets:
        return None
    self = ot.LigCaretList()
    self.Coverage = buildCoverage(carets.keys(), glyphMap)
    self.LigGlyph = [carets[g] for g in self.Coverage.glyphs]
    self.LigGlyphCount = len(self.LigGlyph)
    return self


def buildLigGlyph(coords, points):
    """([500], [4]) --> otTables.LigGlyph; None for empty coords/points"""
    carets = []
    if coords:
        carets.extend([buildCaretValueForCoord(c) for c in sorted(coords)])
    if points:
        carets.extend([buildCaretValueForPoint(p) for p in sorted(points)])
    if not carets:
        return None
    self = ot.LigGlyph()
    self.CaretValue = carets
    self.CaretCount = len(self.CaretValue)
    return self


def buildMarkGlyphSetsDef(markSets, glyphMap):
    """[{"acute","grave"}, {"caron","grave"}] --> otTables.MarkGlyphSetsDef"""
    if not markSets:
        return None
    self = ot.MarkGlyphSetsDef()
    self.MarkSetTableFormat = 1
    self.Coverage = [buildCoverage(m, glyphMap) for m in markSets]
    self.MarkSetCount = len(self.Coverage)
    return self


class ClassDefBuilder(object):
    """Helper for building ClassDef tables."""
    def __init__(self, useClass0):
        self.classes_ = set()
        self.glyphs_ = {}
        self.useClass0_ = useClass0

    def canAdd(self, glyphs):
        if isinstance(glyphs, (set, frozenset)):
            glyphs = sorted(glyphs)
        glyphs = tuple(glyphs)
        if glyphs in self.classes_:
            return True
        for glyph in glyphs:
            if glyph in self.glyphs_:
                return False
        return True

    def add(self, glyphs):
        if isinstance(glyphs, (set, frozenset)):
            glyphs = sorted(glyphs)
        glyphs = tuple(glyphs)
        if glyphs in self.classes_:
            return
        self.classes_.add(glyphs)
        for glyph in glyphs:
            assert glyph not in self.glyphs_
            self.glyphs_[glyph] = glyphs

    def classes(self):
        # In ClassDef1 tables, class id #0 does not need to be encoded
        # because zero is the default. Therefore, we use id #0 for the
        # glyph class that has the largest number of members. However,
        # in other tables than ClassDef1, 0 means "every other glyph"
        # so we should not use that ID for any real glyph classes;
        # we implement this by inserting an empty set at position 0.
        #
        # TODO: Instead of counting the number of glyphs in each class,
        # we should determine the encoded size. If the glyphs in a large
        # class form a contiguous range, the encoding is actually quite
        # compact, whereas a non-contiguous set might need a lot of bytes
        # in the output file. We don't get this right with the key below.
        result = sorted(self.classes_, key=lambda s: (len(s), s), reverse=True)
        if not self.useClass0_:
            result.insert(0, frozenset())
        return result

    def build(self):
        glyphClasses = {}
        for classID, glyphs in enumerate(self.classes()):
            if classID == 0:
                continue
            for glyph in glyphs:
                glyphClasses[glyph] = classID
        classDef = ot.ClassDef()
        classDef.classDefs = glyphClasses
        return classDef


AXIS_VALUE_NEGATIVE_INFINITY = fixedToFloat(-0x80000000, 16)
AXIS_VALUE_POSITIVE_INFINITY = fixedToFloat(0x7FFFFFFF, 16)


def buildStatTable(ttFont, axes, locations=None, elidedFallbackName=2):
    """Add a 'STAT' table to 'ttFont'.

    'axes' is a list of dictionaries describing axes and their
    values.

    Example:

    axes = [
        dict(
            tag="wght",
            name="Weight",
            ordering=0,  # optional
            values=[
                dict(value=100, name='Thin'),
                dict(value=300, name='Light'),
                dict(value=400, name='Regular', flags=0x2),
                dict(value=900, name='Black'),
            ],
        )
    ]

    Each axis dict must have 'tag' and 'name' items. 'tag' maps
    to the 'AxisTag' field. 'name' can be a name ID (int), a string,
    or a dictionary containing multilingual names (see the
    addMultilingualName() name table method), and will translate to
    the AxisNameID field.

    An axis dict may contain an 'ordering' item that maps to the
    AxisOrdering field. If omitted, the order of the axes list is
    used to calculate AxisOrdering fields.

    The axis dict may contain a 'values' item, which is a list of
    dictionaries describing AxisValue records belonging to this axis.

    Each value dict must have a 'name' item, which can be a name ID
    (int), a string, or a dictionary containing multilingual names,
    like the axis name. It translates to the ValueNameID field.

    Optionally the value dict can contain a 'flags' item. It maps to
    the AxisValue Flags field, and will be 0 when omitted.

    The format of the AxisValue is determined by the remaining contents
    of the value dictionary:

    If the value dict contains a 'value' item, an AxisValue record
    Format 1 is created. If in addition to the 'value' item it contains
    a 'linkedValue' item, an AxisValue record Format 3 is built.

    If the value dict contains a 'nominalValue' item, an AxisValue
    record Format 2 is built. Optionally it may contain 'rangeMinValue'
    and 'rangeMaxValue' items. These map to -Infinity and +Infinity
    respectively if omitted.

    You cannot specify Format 4 AxisValue tables this way, as they are
    not tied to a single axis, and specify a name for a location that
    is defined by multiple axes values. Instead, you need to supply the
    'locations' argument.

    The optional 'locations' argument specifies AxisValue Format 4
    tables. It should be a list of dicts, where each dict has a 'name'
    item, which works just like the value dicts above, an optional
    'flags' item (defaulting to 0x0), and a 'location' dict. A
    location dict key is an axis tag, and the associated value is the
    location on the specified axis. They map to the AxisIndex and Value
    fields of the AxisValueRecord.

    Example:

    locations = [
        dict(name='Regular ABCD', location=dict(wght=300, ABCD=100)),
        dict(name='Bold ABCD XYZ', location=dict(wght=600, ABCD=200)),
    ]

    The optional 'elidedFallbackName' argument can be a name ID (int),
    a string, or a dictionary containing multilingual names. It
    translates to the ElidedFallbackNameID field.

    The 'ttFont' argument must be a TTFont instance that already has a
    'name' table. If a 'STAT' table already exists, it will be
    overwritten by the newly created one.
    """
    ttFont["STAT"] = ttLib.newTable("STAT")
    statTable = ttFont["STAT"].table = ot.STAT()
    nameTable = ttFont["name"]
    statTable.ElidedFallbackNameID = _addName(nameTable, elidedFallbackName)

    # 'locations' contains data for AxisValue Format 4
    axisRecords, axisValues = _buildAxisRecords(axes, nameTable)
    if not locations:
        statTable.Version = 0x00010001
    else:
        # We'll be adding Format 4 AxisValue records, which
        # requires a higher table version
        statTable.Version = 0x00010002
        multiAxisValues = _buildAxisValuesFormat4(locations, axes, nameTable)
        axisValues = multiAxisValues + axisValues

    # Store AxisRecords
    axisRecordArray = ot.AxisRecordArray()
    axisRecordArray.Axis = axisRecords
    # XXX these should not be hard-coded but computed automatically
    statTable.DesignAxisRecordSize = 8
    statTable.DesignAxisRecord = axisRecordArray
    statTable.DesignAxisCount = len(axisRecords)

    if axisValues:
        # Store AxisValueRecords
        axisValueArray = ot.AxisValueArray()
        axisValueArray.AxisValue = axisValues
        statTable.AxisValueArray = axisValueArray
        statTable.AxisValueCount = len(axisValues)


def _buildAxisRecords(axes, nameTable):
    axisRecords = []
    axisValues = []
    for axisRecordIndex, axisDict in enumerate(axes):
        axis = ot.AxisRecord()
        axis.AxisTag = axisDict["tag"]
        axis.AxisNameID = _addName(nameTable, axisDict["name"], 256)
        axis.AxisOrdering = axisDict.get("ordering", axisRecordIndex)
        axisRecords.append(axis)

        for axisVal in axisDict.get("values", ()):
            axisValRec = ot.AxisValue()
            axisValRec.AxisIndex = axisRecordIndex
            axisValRec.Flags = axisVal.get("flags", 0)
            axisValRec.ValueNameID = _addName(nameTable, axisVal['name'])

            if "value" in axisVal:
                axisValRec.Value = axisVal["value"]
                if "linkedValue" in axisVal:
                    axisValRec.Format = 3
                    axisValRec.LinkedValue = axisVal["linkedValue"]
                else:
                    axisValRec.Format = 1
            elif "nominalValue" in axisVal:
                axisValRec.Format = 2
                axisValRec.NominalValue = axisVal["nominalValue"]
                axisValRec.RangeMinValue = axisVal.get("rangeMinValue", AXIS_VALUE_NEGATIVE_INFINITY)
                axisValRec.RangeMaxValue = axisVal.get("rangeMaxValue", AXIS_VALUE_POSITIVE_INFINITY)
            else:
                raise ValueError("Can't determine format for AxisValue")

            axisValues.append(axisValRec)
    return axisRecords, axisValues


def _buildAxisValuesFormat4(locations, axes, nameTable):
    axisTagToIndex = {}
    for axisRecordIndex, axisDict in enumerate(axes):
        axisTagToIndex[axisDict["tag"]] = axisRecordIndex

    axisValues = []
    for axisLocationDict in locations:
        axisValRec = ot.AxisValue()
        axisValRec.Format = 4
        axisValRec.ValueNameID = _addName(nameTable, axisLocationDict['name'])
        axisValRec.Flags = axisLocationDict.get("flags", 0)
        axisValueRecords = []
        for tag, value in axisLocationDict["location"].items():
            avr = ot.AxisValueRecord()
            avr.AxisIndex = axisTagToIndex[tag]
            avr.Value = value
            axisValueRecords.append(avr)
        axisValueRecords.sort(key=lambda avr: avr.AxisIndex)
        axisValRec.AxisCount = len(axisValueRecords)
        axisValRec.AxisValueRecord = axisValueRecords
        axisValues.append(axisValRec)
    return axisValues


def _addName(nameTable, value, minNameID=0):
    if isinstance(value, int):
        # Already a nameID
        return value
    if isinstance(value, str):
        names = dict(en=value)
    elif isinstance(value, dict):
        names = value
    else:
        raise TypeError("value must be int, str or dict")
    return nameTable.addMultilingualName(names, minNameID=minNameID)
