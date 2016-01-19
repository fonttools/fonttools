from __future__ import print_function, division, absolute_import
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otBase import ValueRecord, valueRecordFormatDict


def buildCoverage(glyphs, glyphMap):
    self = ot.Coverage()
    self.glyphs = sorted(glyphs, key=glyphMap.__getitem__)
    return self


# GSUB


def buildSingleSubst(mapping):
    self = ot.SingleSubst()
    self.mapping = dict(mapping)
    return self


def buildMultipleSubst(mapping):
    self = ot.MultipleSubst()
    self.mapping = dict(mapping)
    return self


def buildAlternateSubst(mapping):
    self = ot.AlternateSubst()
    self.alternates = dict(mapping)
    return self


def _getLigatureKey(components):
    """Computes a key for ordering ligatures in a GSUB Type-4 lookup.

    When building the OpenType lookup, we need to make sure that
    the longest sequence of components is listed first, so we
    use the negative length as the primary key for sorting.
    To make buildLigatureSubst() deterministic, we use the
    component sequence as the secondary key.

    For example, this will sort (f,f,f) < (f,f,i) < (f,f) < (f,i) < (f,l).
    """
    return (-len(components), components)


def buildLigatureSubst(mapping):
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
        assert self.Format == 1, "Either point, or both of deviceX/deviceY, must be None."
        self.XDeviceTable = deviceX
        self.YDeviceTable = deviceY
        self.Format = 3
    return self


def buildCursivePos(attach, glyphMap):
    """{"alef": (entry, exit)} --> otTables.CursivePos"""
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


def buildDevice(device):
    """[(11, 22), (7, -7), ...] --> otTables.Device"""
    self = ot.Device()
    device = tuple(sorted(device))
    self.StartSize = startSize = device[0][0]
    self.EndSize = endSize = device[-1][0]
    deviceDict = dict(device)
    self.DeltaValue = deltaValues = [
        deviceDict.get(size, 0)
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
