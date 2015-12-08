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
        self.lookup_flag_ = 0
        self.language_systems = set()
        self.named_lookups_ = {}
        self.cur_lookup_ = None
        self.cur_lookup_name_ = None
        self.cur_feature_name_ = None
        self.lookups_ = []
        self.features_ = {}  # ('latn', 'DEU ', 'smcp') --> [LookupBuilder*]
        self.parseTree = None
        self.required_features_ = {}  # ('latn', 'DEU ') --> 'scmp'

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
                self.cur_lookup_.lookup_flag == self.lookup_flag_):
            return self.cur_lookup_
        if self.cur_lookup_name_ and self.cur_lookup_:
            raise FeatureLibError(
                "Within a named lookup block, all rules must be of "
                "the same lookup type and flag", location)
        self.cur_lookup_ = builder_class(
            self.font, location, self.lookup_flag_)
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
        gdef.GlyphClassDef.classDefs = {}

        glyphMarkClass = {}  # glyph --> markClass
        for markClass in self.parseTree.markClasses.values():
            for glyph in markClass.anchors.keys():
                if glyph in glyphMarkClass:
                    other = glyphMarkClass[glyph]
                    name1, name2 = sorted([markClass.name, other.name])
                    raise FeatureLibError(
                        'glyph %s cannot be both in markClass @%s and @%s' %
                        (glyph, name1, name2), markClass.location)
                glyphMarkClass[glyph] = markClass
                gdef.GlyphClassDef.classDefs[glyph] = 3
        gdef.AttachList = None
        gdef.LigCaretList = None
        gdef.MarkAttachClassDef = None
        if len(gdef.GlyphClassDef.classDefs) == 0:
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
        self.lookup_flag_ = 0
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

    def add_substitution(self, location, old_prefix, old, old_suffix, new,
                         lookups):
        assert len(new) == 0, new
        lookup = self.get_lookup_(location, ChainContextSubstBuilder)
        lookup.substitutions.append((old_prefix, old, old_suffix,
                                     self.find_lookup_builders_(lookups)))

    def add_alternate_substitution(self, location, glyph, from_class):
        lookup = self.get_lookup_(location, AlternateSubstBuilder)
        if glyph in lookup.alternates:
            raise FeatureLibError(
                'Already defined alternates for glyph "%s"' % glyph,
                location)
        lookup.alternates[glyph] = from_class

    def add_ligature_substitution(self, location, glyphs, replacement):
        lookup = self.get_lookup_(location, LigatureSubstBuilder)
        lookup.ligatures[glyphs] = replacement

    def add_multiple_substitution(self, location, glyph, replacements):
        lookup = self.get_lookup_(location, MultipleSubstBuilder)
        if glyph in lookup.mapping:
            raise FeatureLibError(
                'Already defined substitution for glyph "%s"' % glyph,
                location)
        lookup.mapping[glyph] = replacements

    def add_reverse_chaining_single_substitution(self, location, old_prefix,
                                                 old_suffix, mapping):
        lookup = self.get_lookup_(location, ReverseChainSingleSubstBuilder)
        lookup.substitutions.append((old_prefix, old_suffix, mapping))

    def add_single_substitution(self, location, mapping):
        lookup = self.get_lookup_(location, SingleSubstBuilder)
        for (from_glyph, to_glyph) in mapping.items():
            if from_glyph in lookup.mapping:
                raise FeatureLibError(
                    'Already defined rule for replacing glyph "%s" by "%s"' %
                    (from_glyph, lookup.mapping[from_glyph]),
                    location)
            lookup.mapping[from_glyph] = to_glyph

    def add_cursive_attachment_pos(self, location, glyphclass,
                                   entryAnchor, exitAnchor):
        lookup = self.get_lookup_(location, CursiveAttachmentPosBuilder)
        lookup.add_attachment(
            location, glyphclass,
            makeOpenTypeAnchor(entryAnchor, otTables.EntryAnchor),
            makeOpenTypeAnchor(exitAnchor, otTables.ExitAnchor))

    def add_mark_to_base_attachment_pos(self, location, base, marks):
        lookup = self.get_lookup_(location, MarkToBaseAttachmentPosBuilder)
        # TODO: Implement.

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
    def __init__(self, font, location, table, lookup_type, lookup_flag):
        self.font = font
        self.location = location
        self.table, self.lookup_type = table, lookup_type
        self.lookup_flag = lookup_flag
        self.lookup_index = None  # assigned when making final tables
        assert table in ('GPOS', 'GSUB')

    def equals(self, other):
        return (isinstance(other, self.__class__) and
                self.table == other.table and
                self.lookup_flag == other.lookup_flag)

    def setBacktrackCoverage_(self, prefix, subtable):
        subtable.BacktrackGlyphCount = len(prefix)
        subtable.BacktrackCoverage = []
        for p in reversed(prefix):
            coverage = otTables.BacktrackCoverage()
            coverage.glyphs = sorted(list(p), key=self.font.getGlyphID)
            subtable.BacktrackCoverage.append(coverage)

    def setLookAheadCoverage_(self, suffix, subtable):
        subtable.LookAheadGlyphCount = len(suffix)
        subtable.LookAheadCoverage = []
        for s in suffix:
            coverage = otTables.LookAheadCoverage()
            coverage.glyphs = sorted(list(s), key=self.font.getGlyphID)
            subtable.LookAheadCoverage.append(coverage)

    def setInputCoverage_(self, glyphs, subtable):
        subtable.InputGlyphCount = len(glyphs)
        subtable.InputCoverage = []
        for g in glyphs:
            coverage = otTables.InputCoverage()
            coverage.glyphs = sorted(list(g), key=self.font.getGlyphID)
            subtable.InputCoverage.append(coverage)


class AlternateSubstBuilder(LookupBuilder):
    def __init__(self, font, location, lookup_flag):
        LookupBuilder.__init__(self, font, location, 'GSUB', 3, lookup_flag)
        self.alternates = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.alternates == other.alternates)

    def build(self):
        lookup = otTables.Lookup()
        lookup.SubTable = []
        st = otTables.AlternateSubst()
        st.Format = 1
        st.alternates = self.alternates
        lookup.SubTable.append(st)
        lookup.LookupFlag = self.lookup_flag
        lookup.LookupType = self.lookup_type
        lookup.SubTableCount = len(lookup.SubTable)
        return lookup


class ChainContextSubstBuilder(LookupBuilder):
    def __init__(self, font, location, lookup_flag):
        LookupBuilder.__init__(self, font, location, 'GSUB', 6, lookup_flag)
        self.substitutions = []  # (prefix, input, suffix, lookups)

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.substitutions == other.substitutions)

    def build(self):
        lookup = otTables.Lookup()
        lookup.SubTable = []
        for (prefix, input, suffix, lookups) in self.substitutions:
            st = otTables.ChainContextSubst()
            lookup.SubTable.append(st)
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

        lookup.LookupFlag = self.lookup_flag
        lookup.LookupType = self.lookup_type
        lookup.SubTableCount = len(lookup.SubTable)
        return lookup


class LigatureSubstBuilder(LookupBuilder):
    def __init__(self, font, location, lookup_flag):
        LookupBuilder.__init__(self, font, location, 'GSUB', 4, lookup_flag)
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
        lookup = otTables.Lookup()
        lookup.SubTable = []
        st = otTables.LigatureSubst()
        st.Format = 1
        st.ligatures = {}
        for components in sorted(self.ligatures.keys(), key=self.make_key):
            lig = otTables.Ligature()
            lig.Component = components[1:]
            lig.LigGlyph = self.ligatures[components]
            st.ligatures.setdefault(components[0], []).append(lig)
        lookup.SubTable.append(st)
        lookup.LookupFlag = self.lookup_flag
        lookup.LookupType = self.lookup_type
        lookup.SubTableCount = len(lookup.SubTable)
        return lookup


class MultipleSubstBuilder(LookupBuilder):
    def __init__(self, font, location, lookup_flag):
        LookupBuilder.__init__(self, font, location, 'GSUB', 2, lookup_flag)
        self.mapping = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        lookup = otTables.Lookup()
        lookup.SubTable = []
        st = otTables.MultipleSubst()
        st.mapping = self.mapping
        lookup.SubTable.append(st)
        lookup.LookupFlag = self.lookup_flag
        lookup.LookupType = self.lookup_type
        lookup.SubTableCount = len(lookup.SubTable)
        return lookup


class PairPosBuilder(LookupBuilder):
    def __init__(self, font, location, lookup_flag):
        LookupBuilder.__init__(self, font, location, 'GPOS', 2, lookup_flag)
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
            st.Coverage = otTables.Coverage()
            st.Coverage.glyphs = sorted(p.keys(), key=self.font.getGlyphID)
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

        lookup = otTables.Lookup()
        lookup.SubTable = subtables
        lookup.LookupFlag = self.lookup_flag
        lookup.LookupType = self.lookup_type
        lookup.SubTableCount = len(lookup.SubTable)
        return lookup


class CursiveAttachmentPosBuilder(LookupBuilder):
    def __init__(self, font, location, lookup_flag):
        LookupBuilder.__init__(self, font, location, 'GPOS', 3, lookup_flag)
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
        st.Coverage = otTables.Coverage()
        st.Coverage.glyphs = \
            sorted(self.attachments.keys(), key=self.font.getGlyphID)
        st.EntryExitCount = len(self.attachments)
        st.EntryExitRecord = []
        for glyph in st.Coverage.glyphs:
            location, entryAnchor, exitAnchor = self.attachments[glyph]
            rec = otTables.EntryExitRecord()
            st.EntryExitRecord.append(rec)
            rec.EntryAnchor = entryAnchor
            rec.ExitAnchor = exitAnchor
        subtables = [st]
        lookup = otTables.Lookup()
        lookup.SubTable = subtables
        lookup.LookupFlag = self.lookup_flag
        lookup.LookupType = self.lookup_type
        lookup.SubTableCount = len(lookup.SubTable)
        return lookup


class MarkToBaseAttachmentPosBuilder(LookupBuilder):
    def __init__(self, font, location, lookup_flag):
        LookupBuilder.__init__(self, font, location, 'GPOS', 4, lookup_flag)

    def build(self):
        return None  # TODO: Implement.


class ReverseChainSingleSubstBuilder(LookupBuilder):
    def __init__(self, font, location, lookup_flag):
        LookupBuilder.__init__(self, font, location, 'GSUB', 8, lookup_flag)
        self.substitutions = []  # (prefix, suffix, mapping)

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.substitutions == other.substitutions)

    def build(self):
        lookup = otTables.Lookup()
        lookup.SubTable = []
        for prefix, suffix, mapping in self.substitutions:
            st = otTables.ReverseChainSingleSubst()
            st.Format = 1
            lookup.SubTable.append(st)
            self.setBacktrackCoverage_(prefix, st)
            self.setLookAheadCoverage_(suffix, st)
            coverage = sorted(mapping.keys(), key=self.font.getGlyphID)
            st.Coverage = otTables.Coverage()
            st.Coverage.glyphs = coverage
            st.GlyphCount = len(coverage)
            st.Substitute = [mapping[g] for g in coverage]

        lookup.LookupFlag = self.lookup_flag
        lookup.LookupType = self.lookup_type
        lookup.SubTableCount = len(lookup.SubTable)
        return lookup


class SingleSubstBuilder(LookupBuilder):
    def __init__(self, font, location, lookup_flag):
        LookupBuilder.__init__(self, font, location, 'GSUB', 1, lookup_flag)
        self.mapping = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        lookup = otTables.Lookup()
        lookup.SubTable = []
        st = otTables.SingleSubst()
        st.mapping = self.mapping
        lookup.SubTable.append(st)
        lookup.LookupFlag = self.lookup_flag
        lookup.LookupType = self.lookup_type
        lookup.SubTableCount = len(lookup.SubTable)
        return lookup


class SinglePosBuilder(LookupBuilder):
    def __init__(self, font, location, lookup_flag):
        LookupBuilder.__init__(self, font, location, 'GPOS', 1, lookup_flag)
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
            st.Coverage = otTables.Coverage()
            st.Coverage.glyphs = glyphs
            st.Value, st.ValueFormat = value, valueFormat

        lookup = otTables.Lookup()
        lookup.SubTable = subtables
        lookup.LookupFlag = self.lookup_flag
        lookup.LookupType = self.lookup_type
        lookup.SubTableCount = len(lookup.SubTable)
        return lookup
