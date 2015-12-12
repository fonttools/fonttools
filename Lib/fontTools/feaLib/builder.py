from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.error import FeatureLibError
from fontTools.feaLib.parser import Parser
from fontTools.ttLib import getTableClass
from fontTools.ttLib.tables import otBase, otTables
import warnings


def addOpenTypeFeatures(featurefile_path, font):
    builder = Builder(featurefile_path, font)
    builder.build()


class Builder(object):
    def __init__(self, featurefile_path, font):
        self.featurefile_path = featurefile_path
        self.font = font
        self.default_language_systems_ = set()
        self.script_ = None
        self.lookupflag_ = 0
        self.lookupflag_markFilterSet_ = None
        self.language_systems = set()
        self.named_lookups_ = {}
        self.cur_lookup_ = None
        self.cur_lookup_name_ = None
        self.cur_feature_name_ = None
        self.lookups_ = []
        self.features_ = {}  # ('latn', 'DEU ', 'smcp') --> [LookupBuilder*]
        self.parseTree = None
        self.required_features_ = {}  # ('latn', 'DEU ') --> 'scmp'
        self.markAttach_ = {}  # "acute" --> (4, (file, line, column))
        self.markAttachClassID_ = {}  # frozenset({"acute", "grave"}) --> 4
        self.markFilterSets_ = {}  # frozenset({"acute", "grave"}) --> 4

    def build(self):
        self.parseTree = Parser(self.featurefile_path).parse()
        self.parseTree.build(self)
        for tag in ('GPOS', 'GSUB'):
            table = self.makeTable(tag)
            if (table.ScriptList.ScriptCount > 0 or
                    table.FeatureList.FeatureCount > 0 or
                    table.LookupList.LookupCount > 0):
                fontTable = self.font[tag] = getTableClass(tag)()
                fontTable.table = table
            elif tag in self.font:
                del self.font[tag]
        gdef = self.makeGDEF()
        if gdef:
            self.font["GDEF"] = gdef
        elif "GDEF" in self.font:
            del self.font["GDEF"]

    def get_lookup_(self, location, builder_class):
        if (self.cur_lookup_ and
            type(self.cur_lookup_) == builder_class and
            self.cur_lookup_.lookupflag == self.lookupflag_ and
            self.cur_lookup_.markFilterSet ==
                self.lookupflag_markFilterSet_):
            return self.cur_lookup_
        if self.cur_lookup_name_ and self.cur_lookup_:
            raise FeatureLibError(
                "Within a named lookup block, all rules must be of "
                "the same lookup type and flag", location)
        self.cur_lookup_ = builder_class(self.font, location)
        self.cur_lookup_.lookupflag = self.lookupflag_
        self.cur_lookup_.markFilterSet = self.lookupflag_markFilterSet_
        self.lookups_.append(self.cur_lookup_)
        if self.cur_lookup_name_:
            # We are starting a lookup rule inside a named lookup block.
            self.named_lookups_[self.cur_lookup_name_] = self.cur_lookup_
        if self.cur_feature_name_:
            # We are starting a lookup rule inside a feature. This includes
            # lookup rules inside named lookups inside features.
            for script, lang in self.language_systems:
                key = (script, lang, self.cur_feature_name_)
                self.features_.setdefault(key, []).append(self.cur_lookup_)
        return self.cur_lookup_

    def makeGDEF(self):
        gdef = otTables.GDEF()
        gdef.Version = 1.0
        gdef.GlyphClassDef = otTables.GlyphClassDef()

        inferredGlyphClass = {}
        for lookup in self.lookups_:
            inferredGlyphClass.update(lookup.inferGlyphClasses())

        marks = {}  # glyph --> markClass
        for markClass in self.parseTree.markClasses.values():
            for markClassDef in markClass.definitions:
                for glyph in markClassDef.glyphSet():
                    other = marks.get(glyph)
                    if other not in (None, markClass):
                        name1, name2 = sorted([markClass.name, other.name])
                        raise FeatureLibError(
                            'Glyph %s cannot be both in '
                            'markClass @%s and @%s' %
                            (glyph, name1, name2), markClassDef.location)
                    marks[glyph] = markClass
                    inferredGlyphClass[glyph] = 3

        gdef.GlyphClassDef.classDefs = inferredGlyphClass
        gdef.AttachList = None
        gdef.LigCaretList = None

        markAttachClass = {g: c for g, (c, _) in self.markAttach_.items()}
        if markAttachClass:
            gdef.MarkAttachClassDef = otTables.MarkAttachClassDef()
            gdef.MarkAttachClassDef.classDefs = markAttachClass
        else:
            gdef.MarkAttachClassDef = None

        if self.markFilterSets_:
            gdef.Version = 0x00010002
            m = gdef.MarkGlyphSetsDef = otTables.MarkGlyphSetsDef()
            m.MarkSetTableFormat = 1
            m.MarkSetCount = len(self.markFilterSets_)
            m.Coverage = []
            filterSets = [(id, glyphs)
                          for (glyphs, id) in self.markFilterSets_.items()]
            for i, glyphs in sorted(filterSets):
                coverage = otTables.Coverage()
                coverage.glyphs = sorted(glyphs, key=self.font.getGlyphID)
                m.Coverage.append(coverage)

        if (len(gdef.GlyphClassDef.classDefs) == 0 and
                gdef.MarkAttachClassDef is None):
            return None
        result = getTableClass("GDEF")()
        result.table = gdef
        return result

    def makeTable(self, tag):
        table = getattr(otTables, tag, None)()
        table.Version = 1.0
        table.ScriptList = otTables.ScriptList()
        table.ScriptList.ScriptRecord = []
        table.FeatureList = otTables.FeatureList()
        table.FeatureList.FeatureRecord = []

        table.LookupList = otTables.LookupList()
        table.LookupList.Lookup = []
        for lookup in self.lookups_:
            lookup.lookup_index = None
        for i, lookup_builder in enumerate(self.lookups_):
            if lookup_builder.table != tag:
                continue
            # If multiple lookup builders would build equivalent lookups,
            # emit them only once. This is quadratic in the number of lookups,
            # but the checks are cheap. If performance ever becomes an issue,
            # we could hash the lookup content and only compare those with
            # the same hash value.
            equivalent_builder = None
            for other_builder in self.lookups_[:i]:
                if lookup_builder.equals(other_builder):
                    equivalent_builder = other_builder
            if equivalent_builder is not None:
                lookup_builder.lookup_index = equivalent_builder.lookup_index
                continue
            lookup_builder.lookup_index = len(table.LookupList.Lookup)
            table.LookupList.Lookup.append(lookup_builder.build())

        # Build a table for mapping (tag, lookup_indices) to feature_index.
        # For example, ('liga', (2,3,7)) --> 23.
        feature_indices = {}
        required_feature_indices = {}  # ('latn', 'DEU') --> 23
        scripts = {}  # 'latn' --> {'DEU': [23, 24]} for feature #23,24
        for key, lookups in sorted(self.features_.items()):
            script, lang, feature_tag = key
            # l.lookup_index will be None when a lookup is not needed
            # for the table under construction. For example, substitution
            # rules will have no lookup_index while building GPOS tables.
            lookup_indices = tuple([l.lookup_index for l in lookups
                                    if l.lookup_index is not None])
            if len(lookup_indices) == 0:
                continue

            feature_key = (feature_tag, lookup_indices)
            feature_index = feature_indices.get(feature_key)
            if feature_index is None:
                feature_index = len(table.FeatureList.FeatureRecord)
                frec = otTables.FeatureRecord()
                frec.FeatureTag = feature_tag
                frec.Feature = otTables.Feature()
                frec.Feature.FeatureParams = None
                frec.Feature.LookupListIndex = lookup_indices
                frec.Feature.LookupCount = len(lookup_indices)
                table.FeatureList.FeatureRecord.append(frec)
                feature_indices[feature_key] = feature_index
            scripts.setdefault(script, {}).setdefault(lang, []).append(
                feature_index)
            if self.required_features_.get((script, lang)) == feature_tag:
                required_feature_indices[(script, lang)] = feature_index

        # Build ScriptList.
        for script, lang_features in sorted(scripts.items()):
            srec = otTables.ScriptRecord()
            srec.ScriptTag = script
            srec.Script = otTables.Script()
            srec.Script.DefaultLangSys = None
            srec.Script.LangSysRecord = []
            for lang, feature_indices in sorted(lang_features.items()):
                langrec = otTables.LangSysRecord()
                langrec.LangSys = otTables.LangSys()
                langrec.LangSys.LookupOrder = None

                req_feature_index = \
                    required_feature_indices.get((script, lang))
                if req_feature_index is None:
                    langrec.LangSys.ReqFeatureIndex = 0xFFFF
                else:
                    langrec.LangSys.ReqFeatureIndex = req_feature_index

                langrec.LangSys.FeatureIndex = [i for i in feature_indices
                                                if i != req_feature_index]
                langrec.LangSys.FeatureCount = \
                    len(langrec.LangSys.FeatureIndex)

                if lang == "dflt":
                    srec.Script.DefaultLangSys = langrec.LangSys
                else:
                    langrec.LangSysTag = lang
                    srec.Script.LangSysRecord.append(langrec)
            srec.Script.LangSysCount = len(srec.Script.LangSysRecord)
            table.ScriptList.ScriptRecord.append(srec)

        table.ScriptList.ScriptCount = len(table.ScriptList.ScriptRecord)
        table.FeatureList.FeatureCount = len(table.FeatureList.FeatureRecord)
        table.LookupList.LookupCount = len(table.LookupList.Lookup)
        return table

    def add_language_system(self, location, script, language):
        # OpenType Feature File Specification, section 4.b.i
        if (script == "DFLT" and language == "dflt" and
                self.default_language_systems_):
            raise FeatureLibError(
                'If "languagesystem DFLT dflt" is present, it must be '
                'the first of the languagesystem statements', location)
        if (script, language) in self.default_language_systems_:
            raise FeatureLibError(
                '"languagesystem %s %s" has already been specified' %
                (script.strip(), language.strip()), location)
        self.default_language_systems_.add((script, language))

    def get_default_language_systems_(self):
        # OpenType Feature File specification, 4.b.i. languagesystem:
        # If no "languagesystem" statement is present, then the
        # implementation must behave exactly as though the following
        # statement were present at the beginning of the feature file:
        # languagesystem DFLT dflt;
        if self.default_language_systems_:
            return frozenset(self.default_language_systems_)
        else:
            return frozenset({('DFLT', 'dflt')})

    def start_feature(self, location, name):
        self.language_systems = self.get_default_language_systems_()
        self.cur_lookup_ = None
        self.cur_feature_name_ = name

    def end_feature(self):
        assert self.cur_feature_name_ is not None
        self.cur_feature_name_ = None
        self.language_systems = None
        self.cur_lookup_ = None

    def start_lookup_block(self, location, name):
        if name in self.named_lookups_:
            raise FeatureLibError(
                'Lookup "%s" has already been defined' % name, location)
        self.cur_lookup_name_ = name
        self.named_lookups_[name] = None
        self.cur_lookup_ = None

    def end_lookup_block(self):
        assert self.cur_lookup_name_ is not None
        self.cur_lookup_name_ = None
        self.cur_lookup_ = None

    def set_language(self, location, language, include_default, required):
        assert(len(language) == 4)
        if self.cur_lookup_name_:
            raise FeatureLibError(
                "Within a named lookup block, it is not allowed "
                "to change the language", location)
        if self.cur_feature_name_ in ('aalt', 'size'):
            raise FeatureLibError(
                "Language statements are not allowed "
                "within \"feature %s\"" % self.cur_feature_name_, location)
        self.cur_lookup_ = None
        if include_default:
            langsys = set(self.get_default_language_systems_())
        else:
            langsys = set()
        langsys.add((self.script_, language))
        self.language_systems = frozenset(langsys)
        if required:
            key = (self.script_, language)
            if key in self.required_features_:
                raise FeatureLibError(
                    "Language %s (script %s) has already "
                    "specified feature %s as its required feature" % (
                        language.strip(), self.script_.strip(),
                        self.required_features_[key].strip()),
                    location)
            self.required_features_[key] = self.cur_feature_name_

    def getMarkAttachClass_(self, location, glyphs):
        id = self.markAttachClassID_.get(glyphs)
        if id is not None:
            return id
        id = len(self.markAttachClassID_) + 1
        self.markAttachClassID_[glyphs] = id
        for glyph in glyphs:
            if glyph in self.markAttach_:
                _, loc = self.markAttach_[glyph]
                raise FeatureLibError(
                    "Glyph %s already has been assigned "
                    "a MarkAttachmentType at %s:%d:%d" % (
                        glyph, loc[0], loc[1], loc[2]),
                    location)
            self.markAttach_[glyph] = (id, location)
        return id

    def getMarkFilterSet_(self, location, glyphs):
        id = self.markFilterSets_.get(glyphs)
        if id is not None:
            return id
        id = len(self.markFilterSets_)
        self.markFilterSets_[glyphs] = id
        return id

    def set_lookup_flag(self, location, value, markAttach, markFilter):
        value = value & 0xFF
        if markAttach:
            markAttachClass = self.getMarkAttachClass_(location, markAttach)
            value = value | (markAttachClass << 8)
        if markFilter:
            markFilterSet = self.getMarkFilterSet_(location, markFilter)
            value = value | 0x10
            self.lookupflag_markFilterSet_ = markFilterSet
        else:
            self.lookupflag_markFilterSet_ = None
        self.lookupflag_ = value

    def set_script(self, location, script):
        if self.cur_lookup_name_:
            raise FeatureLibError(
                "Within a named lookup block, it is not allowed "
                "to change the script", location)
        if self.cur_feature_name_ in ('aalt', 'size'):
            raise FeatureLibError(
                "Script statements are not allowed "
                "within \"feature %s\"" % self.cur_feature_name_, location)
        self.cur_lookup_ = None
        self.script_ = script
        self.lookupflag_ = 0
        self.lookupflag_markFilterSet_ = None
        self.set_language(location, "dflt",
                          include_default=True, required=False)

    def find_lookup_builders_(self, lookups):
        """Helper for building chain contextual substitutions

        Given a list of lookup names, finds the LookupBuilder for each name.
        If an input name is None, it gets mapped to a None LookupBuilder.
        """
        lookup_builders = []
        for lookup in lookups:
            if lookup is not None:
                lookup_builders.append(self.named_lookups_.get(lookup.name))
            else:
                lookup_builders.append(None)
        return lookup_builders

    def add_chain_context_pos(self, location, prefix, glyphs, suffix, lookups):
        lookup = self.get_lookup_(location, ChainContextPosBuilder)
        lookup.rules.append((prefix, glyphs, suffix,
                            self.find_lookup_builders_(lookups)))

    def add_chain_context_subst(self, location,
                                prefix, glyphs, suffix, lookups):
        lookup = self.get_lookup_(location, ChainContextSubstBuilder)
        lookup.substitutions.append((prefix, glyphs, suffix,
                                     self.find_lookup_builders_(lookups)))

    def add_alternate_subst(self, location, glyph, from_class):
        lookup = self.get_lookup_(location, AlternateSubstBuilder)
        if glyph in lookup.alternates:
            raise FeatureLibError(
                'Already defined alternates for glyph "%s"' % glyph,
                location)
        lookup.alternates[glyph] = from_class

    def add_ligature_subst(self, location, glyphs, replacement):
        lookup = self.get_lookup_(location, LigatureSubstBuilder)
        lookup.ligatures[glyphs] = replacement

    def add_multiple_subst(self, location, glyph, replacements):
        lookup = self.get_lookup_(location, MultipleSubstBuilder)
        if glyph in lookup.mapping:
            raise FeatureLibError(
                'Already defined substitution for glyph "%s"' % glyph,
                location)
        lookup.mapping[glyph] = replacements

    def add_reverse_chain_single_subst(self, location, old_prefix,
                                       old_suffix, mapping):
        lookup = self.get_lookup_(location, ReverseChainSingleSubstBuilder)
        lookup.substitutions.append((old_prefix, old_suffix, mapping))

    def add_single_subst(self, location, mapping):
        lookup = self.get_lookup_(location, SingleSubstBuilder)
        for (from_glyph, to_glyph) in mapping.items():
            if from_glyph in lookup.mapping:
                raise FeatureLibError(
                    'Already defined rule for replacing glyph "%s" by "%s"' %
                    (from_glyph, lookup.mapping[from_glyph]),
                    location)
            lookup.mapping[from_glyph] = to_glyph

    def add_cursive_pos(self, location, glyphclass, entryAnchor, exitAnchor):
        lookup = self.get_lookup_(location, CursivePosBuilder)
        lookup.add_attachment(
            location, glyphclass,
            makeOpenTypeAnchor(entryAnchor, otTables.EntryAnchor),
            makeOpenTypeAnchor(exitAnchor, otTables.ExitAnchor))

    def add_marks_(self, location, lookupBuilder, marks):
        """Helper for add_mark_{base,liga,mark}_pos."""
        for _, markClass in marks:
            for markClassDef in markClass.definitions:
                for mark in markClassDef.glyphs.glyphSet():
                    if mark not in lookupBuilder.marks:
                        otMarkAnchor = makeOpenTypeAnchor(markClassDef.anchor,
                                                          otTables.MarkAnchor)
                        lookupBuilder.marks[mark] = (
                            markClass.name, otMarkAnchor)

    def add_mark_base_pos(self, location, bases, marks):
        builder = self.get_lookup_(location, MarkBasePosBuilder)
        self.add_marks_(location, builder, marks)
        for baseAnchor, markClass in marks:
            otBaseAnchor = makeOpenTypeAnchor(baseAnchor, otTables.BaseAnchor)
            for base in bases:
                builder.bases.setdefault(base, {})[markClass.name] = (
                    otBaseAnchor)

    def add_mark_lig_pos(self, location, ligatures, components):
        builder = self.get_lookup_(location, MarkLigPosBuilder)
        componentAnchors = []
        for marks in components:
            anchors = {}
            self.add_marks_(location, builder, marks)
            for ligAnchor, markClass in marks:
                anchors[markClass.name] = (
                    makeOpenTypeAnchor(ligAnchor, otTables.LigatureAnchor))
            componentAnchors.append(anchors)
        for glyph in ligatures:
            builder.ligatures[glyph] = componentAnchors

    def add_mark_mark_pos(self, location, baseMarks, marks):
        builder = self.get_lookup_(location, MarkMarkPosBuilder)
        self.add_marks_(location, builder, marks)
        for baseAnchor, markClass in marks:
            otBaseAnchor = makeOpenTypeAnchor(baseAnchor, otTables.Mark2Anchor)
            for baseMark in baseMarks:
                builder.baseMarks.setdefault(baseMark, {})[markClass.name] = (
                    otBaseAnchor)

    def add_pair_pos(self, location, enumerated,
                     glyphclass1, value1, glyphclass2, value2):
        lookup = self.get_lookup_(location, PairPosBuilder)
        if enumerated:
            for glyph in glyphclass1:
                lookup.add_pair(location, {glyph}, value1, glyphclass2, value2)
        else:
            lookup.add_pair(location, glyphclass1, value1, glyphclass2, value2)

    def add_single_pos(self, location, glyph, valuerecord):
        lookup = self.get_lookup_(location, SinglePosBuilder)
        curValue = lookup.mapping.get(glyph)
        if curValue is not None and curValue != valuerecord:
            otherLoc = valuerecord.location
            raise FeatureLibError(
                'Already defined different position for glyph "%s" at %s:%d:%d'
                % (glyph, otherLoc[0], otherLoc[1], otherLoc[2]),
                location)
        lookup.mapping[glyph] = valuerecord


def _makeOpenTypeDeviceTable(deviceTable, device):
    device = tuple(sorted(device))
    deviceTable.StartSize = startSize = device[0][0]
    deviceTable.EndSize = endSize = device[-1][0]
    deviceDict = dict(device)
    deviceTable.DeltaValue = deltaValues = [
        deviceDict.get(size, 0)
        for size in range(startSize, endSize + 1)]
    maxDelta = max(deltaValues)
    minDelta = min(deltaValues)
    assert minDelta > -129 and maxDelta < 128
    if minDelta > -3 and maxDelta < 2:
        deviceTable.DeltaFormat = 1
    elif minDelta > -9 and maxDelta < 8:
        deviceTable.DeltaFormat = 2
    else:
        deviceTable.DeltaFormat = 3


def makeOpenTypeAnchor(anchor, anchorClass):
    """ast.Anchor --> otTables.Anchor"""
    if anchor is None:
        return None
    anch = anchorClass()
    anch.Format = 1
    anch.XCoordinate, anch.YCoordinate = anchor.x, anchor.y
    if anchor.contourpoint is not None:
        anch.AnchorPoint = anchor.contourpoint
        anch.Format = 2
    if anchor.xDeviceTable is not None:
        anch.XDeviceTable = otTables.XDeviceTable()
        _makeOpenTypeDeviceTable(anch.XDeviceTable, anchor.xDeviceTable)
        anch.Format = 3
    if anchor.yDeviceTable is not None:
        anch.YDeviceTable = otTables.YDeviceTable()
        _makeOpenTypeDeviceTable(anch.YDeviceTable, anchor.yDeviceTable)
        anch.Format = 3
    return anch


def makeOpenTypeValueRecord(v):
    """ast.ValueRecord --> (otBase.ValueRecord, int ValueFormat)"""
    if v is None:
        return None, 0
    vr = otBase.ValueRecord()
    if v.xPlacement:
        vr.XPlacement = v.xPlacement
    if v.yPlacement:
        vr.YPlacement = v.yPlacement
    if v.xAdvance:
        vr.XAdvance = v.xAdvance
    if v.yAdvance:
        vr.YAdvance = v.yAdvance

    if v.xPlaDevice:
        vr.XPlaDevice = otTables.XPlaDevice()
        _makeOpenTypeDeviceTable(vr.XPlaDevice, v.xPlaDevice)
    if v.yPlaDevice:
        vr.YPlaDevice = otTables.YPlaDevice()
        _makeOpenTypeDeviceTable(vr.YPlaDevice, v.yPlaDevice)
    if v.xAdvDevice:
        vr.XAdvDevice = otTables.XAdvDevice()
        _makeOpenTypeDeviceTable(vr.XAdvDevice, v.xAdvDevice)
    if v.yAdvDevice:
        vr.YAdvDevice = otTables.YAdvDevice()
        _makeOpenTypeDeviceTable(vr.YAdvDevice, v.yAdvDevice)

    vrMask = 0
    for mask, name, _, _ in otBase.valueRecordFormat:
        if getattr(vr, name, 0) != 0:
            vrMask |= mask

    if vrMask == 0:
        return None, 0
    else:
        return vr, vrMask


class LookupBuilder(object):
    def __init__(self, font, location, table, lookup_type):
        self.font = font
        self.location = location
        self.table, self.lookup_type = table, lookup_type
        self.lookupflag = 0
        self.markFilterSet = None
        self.lookup_index = None  # assigned when making final tables
        assert table in ('GPOS', 'GSUB')

    def equals(self, other):
        return (isinstance(other, self.__class__) and
                self.table == other.table and
                self.lookupflag == other.lookupflag and
                self.markFilterSet == other.markFilterSet)

    def inferGlyphClasses(self):
        """Infers glyph glasses for the GDEF table, such as {"cedilla":3}."""
        return {}

    def buildCoverage_(self, glyphs, tableClass=otTables.Coverage):
        coverage = tableClass()
        coverage.glyphs = sorted(glyphs, key=self.font.getGlyphID)
        return coverage

    def buildLookup_(self, subtables):
        lookup = otTables.Lookup()
        lookup.LookupFlag = self.lookupflag
        lookup.LookupType = self.lookup_type
        lookup.SubTable = subtables
        lookup.SubTableCount = len(subtables)
        if self.markFilterSet is not None:
            lookup.MarkFilteringSet = self.markFilterSet
        return lookup

    def buildMarkClasses_(self, marks):
        """{"cedilla": ("BOTTOM", ast.Anchor), ...} --> {"BOTTOM":0, "TOP":1}

        Helper for MarkBasePostBuilder, MarkLigPosBuilder, and
        MarkMarkPosBuilder. Seems to return the same numeric IDs
        for mark classes as the AFDKO makeotf tool.
        """
        ids = {}
        for mark in sorted(marks.keys(), key=self.font.getGlyphID):
            markClassName, _markAnchor = marks[mark]
            if markClassName not in ids:
                ids[markClassName] = len(ids)
        return ids

    def setBacktrackCoverage_(self, prefix, subtable):
        subtable.BacktrackGlyphCount = len(prefix)
        subtable.BacktrackCoverage = []
        for p in reversed(prefix):
            coverage = self.buildCoverage_(p, otTables.BacktrackCoverage)
            subtable.BacktrackCoverage.append(coverage)

    def setLookAheadCoverage_(self, suffix, subtable):
        subtable.LookAheadGlyphCount = len(suffix)
        subtable.LookAheadCoverage = []
        for s in suffix:
            coverage = self.buildCoverage_(s, otTables.LookAheadCoverage)
            subtable.LookAheadCoverage.append(coverage)

    def setInputCoverage_(self, glyphs, subtable):
        subtable.InputGlyphCount = len(glyphs)
        subtable.InputCoverage = []
        for g in glyphs:
            coverage = self.buildCoverage_(g, otTables.InputCoverage)
            subtable.InputCoverage.append(coverage)

    def setMarkArray_(self, marks, markClassIDs, subtable):
        """Helper for MarkBasePosBuilder and MarkLigPosBuilder."""
        subtable.MarkArray = otTables.MarkArray()
        subtable.MarkArray.MarkCount = len(marks)
        subtable.MarkArray.MarkRecord = []
        for mark in subtable.MarkCoverage.glyphs:
            markClassName, markAnchor = self.marks[mark]
            markrec = otTables.MarkRecord()
            markrec.Class = markClassIDs[markClassName]
            markrec.MarkAnchor = markAnchor
            subtable.MarkArray.MarkRecord.append(markrec)

    def setMark1Array_(self, marks, markClassIDs, subtable):
        """Helper for MarkMarkPosBuilder."""
        subtable.Mark1Array = otTables.Mark1Array()
        subtable.Mark1Array.MarkCount = len(marks)
        subtable.Mark1Array.MarkRecord = []
        for mark in subtable.Mark1Coverage.glyphs:
            markClassName, markAnchor = self.marks[mark]
            markrec = otTables.MarkRecord()
            markrec.Class = markClassIDs[markClassName]
            markrec.MarkAnchor = markAnchor
            subtable.Mark1Array.MarkRecord.append(markrec)


class AlternateSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 3)
        self.alternates = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.alternates == other.alternates)

    def build(self):
        subtable = otTables.AlternateSubst()
        subtable.Format = 1
        subtable.alternates = self.alternates
        return self.buildLookup_([subtable])


class ChainContextPosBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 8)
        self.rules = []  # (prefix, input, suffix, lookups)

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.rules == other.rules)

    def build(self):
        subtables = []
        for (prefix, glyphs, suffix, lookups) in self.rules:
            st = otTables.ChainContextPos()
            subtables.append(st)
            st.Format = 3
            self.setBacktrackCoverage_(prefix, st)
            self.setLookAheadCoverage_(suffix, st)
            self.setInputCoverage_(glyphs, st)

            st.PosCount = len([l for l in lookups if l is not None])
            st.PosLookupRecord = []
            for sequenceIndex, l in enumerate(lookups):
                if l is not None:
                    rec = otTables.PosLookupRecord()
                    rec.SequenceIndex = sequenceIndex
                    rec.LookupListIndex = l.lookup_index
                    st.PosLookupRecord.append(rec)
        return self.buildLookup_(subtables)


class ChainContextSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 6)
        self.substitutions = []  # (prefix, input, suffix, lookups)

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.substitutions == other.substitutions)

    def build(self):
        subtables = []
        for (prefix, input, suffix, lookups) in self.substitutions:
            st = otTables.ChainContextSubst()
            subtables.append(st)
            st.Format = 3
            self.setBacktrackCoverage_(prefix, st)
            self.setLookAheadCoverage_(suffix, st)
            self.setInputCoverage_(input, st)

            st.SubstCount = len([l for l in lookups if l is not None])
            st.SubstLookupRecord = []
            for sequenceIndex, l in enumerate(lookups):
                if l is not None:
                    rec = otTables.SubstLookupRecord()
                    rec.SequenceIndex = sequenceIndex
                    rec.LookupListIndex = l.lookup_index
                    st.SubstLookupRecord.append(rec)
        return self.buildLookup_(subtables)


class LigatureSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 4)
        self.ligatures = {}  # {('f','f','i'): 'f_f_i'}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.ligatures == other.ligatures)

    @staticmethod
    def make_key(components):
        """Computes a key for ordering ligatures in a GSUB Type-4 lookup.

        When building the OpenType lookup, we need to make sure that
        the longest sequence of components is listed first, so we
        use the negative length as the primary key for sorting.
        To make the tables easier to read, we use the component
        sequence as the secondary key.

        For example, this will sort (f,f,f) < (f,f,i) < (f,f) < (f,i) < (f,l).
        """
        return (-len(components), components)

    def build(self):
        subtable = otTables.LigatureSubst()
        subtable.Format = 1
        subtable.ligatures = {}
        for components in sorted(self.ligatures.keys(), key=self.make_key):
            lig = otTables.Ligature()
            lig.Component = components[1:]
            lig.LigGlyph = self.ligatures[components]
            subtable.ligatures.setdefault(components[0], []).append(lig)
        return self.buildLookup_([subtable])


class MultipleSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 2)
        self.mapping = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        subtable = otTables.MultipleSubst()
        subtable.mapping = self.mapping
        return self.buildLookup_([subtable])


class PairPosBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 2)
        self.pairs = {}  # (gc1, gc2) -> (location, value1, value2)

    def add_pair(self, location, glyphclass1, value1, glyphclass2, value2):
        gc1 = tuple(sorted(glyphclass1, key=self.font.getGlyphID))
        gc2 = tuple(sorted(glyphclass2, key=self.font.getGlyphID))
        oldValue = self.pairs.get((gc1, gc2), None)
        if oldValue is not None:
            otherLoc, _, _ = oldValue
            raise FeatureLibError(
                'Already defined position for pair [%s] [%s] at %s:%d:%d'
                % (' '.join(gc1), ' '.join(gc2),
                   otherLoc[0], otherLoc[1], otherLoc[2]),
                location)
        self.pairs[(gc1, gc2)] = (location, value1, value2)

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.pairs == other.pairs)

    def build(self):
        subtables = []

        # (valueFormat1, valueFormat2) --> [(glyph1, glyph2, value1, value2)*]
        format1 = {}
        for (gc1, gc2), (location, value1, value2) in self.pairs.items():
            if len(gc1) == 1 and len(gc2) == 1:
                val1, valFormat1 = makeOpenTypeValueRecord(value1)
                val2, valFormat2 = makeOpenTypeValueRecord(value2)
                format1.setdefault(((valFormat1, valFormat2)), []).append(
                    (gc1[0], gc2[0], val1, val2))
        for (vf1, vf2), pairs in sorted(format1.items()):
            p = {}
            for glyph1, glyph2, val1, val2 in pairs:
                p.setdefault(glyph1, []).append((glyph2, val1, val2))
            st = otTables.PairPos()
            subtables.append(st)
            st.Format = 1
            st.ValueFormat1, st.ValueFormat2 = vf1, vf2
            st.Coverage = self.buildCoverage_(p)
            st.PairSet = []
            for glyph in st.Coverage.glyphs:
                ps = otTables.PairSet()
                ps.PairValueRecord = []
                st.PairSet.append(ps)
                for glyph2, val1, val2 in sorted(
                        p[glyph], key=lambda x: self.font.getGlyphID(x[0])):
                    pvr = otTables.PairValueRecord()
                    pvr.SecondGlyph = glyph2
                    pvr.Value1, pvr.Value2 = val1, val2
                    ps.PairValueRecord.append(pvr)
                ps.PairValueCount = len(ps.PairValueRecord)
            st.PairSetCount = len(st.PairSet)
        return self.buildLookup_(subtables)


class CursivePosBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 3)
        self.attachments = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.attachments == other.attachments)

    def add_attachment(self, location, glyphs, entryAnchor, exitAnchor):
        for glyph in glyphs:
            self.attachments[glyph] = (location, entryAnchor, exitAnchor)

    def build(self):
        st = otTables.CursivePos()
        st.Format = 1
        st.Coverage = self.buildCoverage_(self.attachments.keys())
        st.EntryExitCount = len(self.attachments)
        st.EntryExitRecord = []
        for glyph in st.Coverage.glyphs:
            location, entryAnchor, exitAnchor = self.attachments[glyph]
            rec = otTables.EntryExitRecord()
            st.EntryExitRecord.append(rec)
            rec.EntryAnchor = entryAnchor
            rec.ExitAnchor = exitAnchor
        return self.buildLookup_([st])


class MarkBasePosBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 4)
        self.marks = {}  # glyphName -> (markClassName, anchor)
        self.bases = {}  # glyphName -> {markClassName: anchor}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.marks == other.marks and
                self.bases == other.bases)

    def inferGlyphClasses(self):
        result = {glyph: 1 for glyph in self.bases}
        result.update({glyph: 3 for glyph in self.marks})
        return result

    def build(self):
        # TODO: Consider emitting multiple subtables to save space.
        # Partition the marks and bases into disjoint subsets, so that
        # MarkBasePos rules would only access glyphs from a single
        # subset. This would likely lead to smaller mark/base
        # matrices, so we might be able to omit many of the empty
        # anchor tables that we currently produce. Of course, this
        # would only work if the MarkBasePos rules of real-world fonts
        # allow partitioning into multiple subsets. We should find out
        # whether this is the case; if so, implement the optimization.

        st = otTables.MarkBasePos()
        st.Format = 1
        st.MarkCoverage = \
            self.buildCoverage_(self.marks, otTables.MarkCoverage)
        markClasses = self.buildMarkClasses_(self.marks)
        st.ClassCount = len(markClasses)
        self.setMarkArray_(self.marks, markClasses, st)

        st.BaseCoverage = \
            self.buildCoverage_(self.bases, otTables.BaseCoverage)
        st.BaseArray = otTables.BaseArray()
        st.BaseArray.BaseCount = len(st.BaseCoverage.glyphs)
        st.BaseArray.BaseRecord = []
        for base in st.BaseCoverage.glyphs:
            baserec = otTables.BaseRecord()
            st.BaseArray.BaseRecord.append(baserec)
            baserec.BaseAnchor = []
            for markClass in sorted(markClasses.keys(), key=markClasses.get):
                baserec.BaseAnchor.append(self.bases[base].get(markClass))

        return self.buildLookup_([st])


class MarkLigPosBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 5)
        self.marks = {}  # glyphName -> (markClassName, anchor)
        self.ligatures = {}  # glyphName -> [{markClassName: anchor}, ...]

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.marks == other.marks and
                self.ligatures == other.ligatures)

    def inferGlyphClasses(self):
        result = {glyph: 2 for glyph in self.ligatures}
        result.update({glyph: 3 for glyph in self.marks})
        return result

    def build(self):
        st = otTables.MarkLigPos()
        st.Format = 1
        st.MarkCoverage = \
            self.buildCoverage_(self.marks, otTables.MarkCoverage)
        markClasses = self.buildMarkClasses_(self.marks)
        st.ClassCount = len(markClasses)
        self.setMarkArray_(self.marks, markClasses, st)

        st.LigatureCoverage = \
            self.buildCoverage_(self.ligatures, otTables.LigatureCoverage)
        st.LigatureArray = otTables.LigatureArray()
        st.LigatureArray.LigatureCount = len(self.ligatures)
        st.LigatureArray.LigatureAttach = []
        for lig in st.LigatureCoverage.glyphs:
            components = self.ligatures[lig]
            attach = otTables.LigatureAttach()
            attach.ComponentCount = len(components)
            attach.ComponentRecord = []
            for component in components:
                crec = otTables.ComponentRecord()
                attach.ComponentRecord.append(crec)
                crec.LigatureAnchor = []
                for markClass in sorted(markClasses.keys(),
                                        key=markClasses.get):
                    crec.LigatureAnchor.append(component.get(markClass))
            st.LigatureArray.LigatureAttach.append(attach)

        return self.buildLookup_([st])


class MarkMarkPosBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 6)
        self.marks = {}      # glyphName -> (markClassName, anchor)
        self.baseMarks = {}  # glyphName -> {markClassName: anchor}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.marks == other.marks and
                self.baseMarks == other.baseMarks)

    def inferGlyphClasses(self):
        result = {glyph: 3 for glyph in self.baseMarks}
        result.update({glyph: 3 for glyph in self.marks})
        return result

    def build(self):
        st = otTables.MarkMarkPos()
        st.Format = 1
        st.Mark1Coverage = \
            self.buildCoverage_(self.marks, otTables.Mark1Coverage)
        markClasses = self.buildMarkClasses_(self.marks)
        st.ClassCount = len(markClasses)
        self.setMark1Array_(self.marks, markClasses, st)

        st.Mark2Coverage = \
            self.buildCoverage_(self.baseMarks, otTables.Mark2Coverage)
        st.Mark2Array = otTables.Mark2Array()
        st.Mark2Array.Mark2Count = len(st.Mark2Coverage.glyphs)
        st.Mark2Array.Mark2Record = []
        for base in st.Mark2Coverage.glyphs:
            baserec = otTables.Mark2Record()
            st.Mark2Array.Mark2Record.append(baserec)
            baserec.Mark2Anchor = []
            for markClass in sorted(markClasses.keys(), key=markClasses.get):
                baserec.Mark2Anchor.append(self.baseMarks[base].get(markClass))

        return self.buildLookup_([st])


class ReverseChainSingleSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 8)
        self.substitutions = []  # (prefix, suffix, mapping)

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.substitutions == other.substitutions)

    def build(self):
        subtables = []
        for prefix, suffix, mapping in self.substitutions:
            st = otTables.ReverseChainSingleSubst()
            st.Format = 1
            self.setBacktrackCoverage_(prefix, st)
            self.setLookAheadCoverage_(suffix, st)
            st.Coverage = self.buildCoverage_(mapping.keys())
            st.GlyphCount = len(mapping)
            st.Substitute = [mapping[g] for g in st.Coverage.glyphs]
            subtables.append(st)
        return self.buildLookup_(subtables)


class SingleSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 1)
        self.mapping = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        subtable = otTables.SingleSubst()
        subtable.mapping = self.mapping
        return self.buildLookup_([subtable])


class SinglePosBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 1)
        self.mapping = {}  # glyph -> ast.ValueRecord

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        subtables = []

        # If multiple glyphs have the same ValueRecord, they can go into
        # the same subtable which saves space. Therefore, we first build
        # a reverse mapping from ValueRecord to glyph coverage.
        values = {}
        for glyph, valuerecord in self.mapping.items():
            values.setdefault(valuerecord, []).append(glyph)

        # For compliance with the OpenType specification,
        # we sort the glyph coverage by glyph ID.
        for glyphs in values.values():
            glyphs.sort(key=self.font.getGlyphID)

        # Make a list of (glyphs, (otBase.ValueRecord, int valueFormat)).
        # Glyphs with the same otBase.ValueRecord are grouped into one item.
        values = [(glyphs, makeOpenTypeValueRecord(valrec))
                  for valrec, glyphs in values.items()]

        # Find out which glyphs should be encoded as SinglePos format 2.
        # Format 2 is more compact than format 1 when multiple glyphs
        # have different values but share the same integer valueFormat.
        format2 = {}  # valueFormat --> [(glyph, value), (glyph, value), ...]
        for glyphs, (value, valueFormat) in values:
            if len(glyphs) == 1:
                glyph = glyphs[0]
                format2.setdefault(valueFormat, []).append((glyph, value))

        # Only use format 2 if multiple glyphs share the same valueFormat.
        # Otherwise, format 1 is more compact.
        format2 = [(valueFormat, valueList)
                   for valueFormat, valueList in format2.items()
                   if len(valueList) > 1]
        format2.sort()
        format2Glyphs = set()  # {"A", "B", "C"}
        for _, valueList in format2:
            for (glyph, _) in valueList:
                format2Glyphs.add(glyph)
        for valueFormat, valueList in format2:
            valueList.sort(key=lambda x: self.font.getGlyphID(x[0]))
            st = otTables.SinglePos()
            subtables.append(st)
            st.Format = 2
            st.ValueFormat = valueFormat
            st.Coverage = otTables.Coverage()
            st.Coverage.glyphs = [glyph for glyph, _value in valueList]
            st.ValueCount = len(valueList)
            st.Value = [value for _glyph, value in valueList]

        # To make the ordering of our subtables deterministic,
        # we sort subtables by the first glyph ID in their coverage.
        # Not doing this would be OK for OpenType, but testing the
        # compiler would be harder with non-deterministic output.
        values.sort(key=lambda x: self.font.getGlyphID(x[0][0]))

        for glyphs, (value, valueFormat) in values:
            if len(glyphs) == 1 and glyphs[0] in format2Glyphs:
                continue  # already emitted as part of a format 2 subtable
            st = otTables.SinglePos()
            subtables.append(st)
            st.Format = 1
            st.Coverage = self.buildCoverage_(glyphs)
            st.Value, st.ValueFormat = value, valueFormat

        return self.buildLookup_(subtables)
