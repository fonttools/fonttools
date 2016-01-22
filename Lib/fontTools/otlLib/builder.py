from __future__ import print_function, division, absolute_import
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
    self.SubTableCount = len(subtables)
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
        ligature.CompCount = len(components)
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
    self.BaseCount = len(bases)
    self.BaseRecord = []
    for base in sorted(bases, key=glyphMap.__getitem__):
        b = bases[base]
        anchors = [b.get(markClass) for markClass in range(numMarkClasses)]
        self.BaseRecord.append(buildBaseRecord(anchors))
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
    self.LigatureCount = len(ligs)
    self.LigatureAttach = []
    for lig in sorted(ligs, key=glyphMap.__getitem__):
        anchors = []
        for component in ligs[lig]:
            anchors.append([component.get(mc) for mc in range(numMarkClasses)])
        self.LigatureAttach.append(buildLigatureAttach(anchors))
    return self


def buildLigatureAttach(components):
    """[[Anchor, Anchor], [Anchor, Anchor, Anchor]] --> LigatureAttach"""
    self = ot.LigatureAttach()
    self.ComponentCount = len(components)
    self.ComponentRecord = [buildComponentRecord(c) for c in components]
    return self


def buildMarkArray(marks, glyphMap):
    """{"acute": (markClass, otTables.Anchor)} --> otTables.MarkArray"""
    self = ot.MarkArray()
    self.MarkCount = len(marks)
    self.MarkRecord = []
    for mark in sorted(marks.keys(), key=glyphMap.__getitem__):
        markClass, anchor = marks[mark]
        markrec = buildMarkRecord(markClass, anchor)
        self.MarkRecord.append(markrec)
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
        if len(glyphs) > 1:
            format1Mapping = {g: values[key] for g in glyphs}
            result.append(buildSinglePosSubtable(format1Mapping, glyphMap))
            handled.add(key)

    # In the remaining ValueRecords, look for those whose valueFormat
    # (the set of used properties) is shared between multiple records.
    # These will get encoded in format 2.
    for valueFormat, keys in masks.items():
        f2 = [k for k in keys if k not in handled]
        if len(f2) > 1:
            format2Mapping = {coverages[k][0]: values[k] for k in f2}
            result.append(buildSinglePosSubtable(format2Mapping, glyphMap))
            handled.update(f2)

    # The remaining ValueRecords are singletons in the sense that
    # they are only used by a single glyph, and their valueFormat
    # is unique as well. We encode these in format 1 again.
    for key, glyphs in coverages.items():
        if key not in handled:
            assert len(glyphs) == 1, glyphs
            st = buildSinglePosSubtable({glyphs[0]: values[key]}, glyphMap)
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


def _makeDeviceTuple(device):
    """otTables.Device --> tuple, for making device tables unique"""
    return (device.DeltaFormat, device.StartSize, device.EndSize,
            tuple(device.DeltaValue))


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
    self = ot.AttachPoint()
    self.PointIndex = sorted(points)
    self.PointCount = len(points)
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
    self.CaretCount = len(carets)
    self.CaretValue = carets
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
