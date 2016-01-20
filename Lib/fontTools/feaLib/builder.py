from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.error import FeatureLibError
from fontTools.feaLib.parser import Parser
from fontTools.otlLib import builder as otl
from fontTools.ttLib import getTableClass
from fontTools.ttLib.tables import otBase, otTables
import itertools
import warnings


def addOpenTypeFeatures(featurefile_path, font):
    builder = Builder(featurefile_path, font)
    builder.build()


class Builder(object):
    def __init__(self, featurefile_path, font):
        self.featurefile_path = featurefile_path
        self.font = font
        self.glyphMap = font.getReverseGlyphMap()
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
        # for feature 'aalt'
        self.aalt_features_ = []  # [(location, featureName)*], for 'aalt'
        self.aalt_location_ = None
        # for table 'head'
        self.fontRevision_ = None  # 2.71
        # for table 'GDEF'
        self.attachPoints_ = {}  # "a" --> {3, 7}
        self.ligCaretCoords_ = {}  # "f_f_i" --> {300, 600}
        self.ligCaretPoints_ = {}  # "f_f_i" --> {3, 7}
        self.glyphClassDefs_ = {}  # "fi" --> (2, (file, line, column))
        self.markAttach_ = {}  # "acute" --> (4, (file, line, column))
        self.markAttachClassID_ = {}  # frozenset({"acute", "grave"}) --> 4
        self.markFilterSets_ = {}  # frozenset({"acute", "grave"}) --> 4

    def build(self):
        self.parseTree = Parser(self.featurefile_path).parse()
        self.parseTree.build(self)
        self.build_feature_aalt_()
        self.build_head()
        for tag in ('GPOS', 'GSUB'):
            table = self.makeTable(tag)
            if (table.ScriptList.ScriptCount > 0 or
                    table.FeatureList.FeatureCount > 0 or
                    table.LookupList.LookupCount > 0):
                fontTable = self.font[tag] = getTableClass(tag)()
                fontTable.table = table
            elif tag in self.font:
                del self.font[tag]
        gdef = self.buildGDEF()
        if gdef:
            self.font["GDEF"] = gdef
        elif "GDEF" in self.font:
            del self.font["GDEF"]

    def get_chained_lookup_(self, location, builder_class):
        result = builder_class(self.font, location)
        result.lookupflag = self.lookupflag_
        result.markFilterSet = self.lookupflag_markFilterSet_
        self.lookups_.append(result)
        return result

    def add_lookup_to_feature_(self, lookup, feature_name):
        for script, lang in self.language_systems:
            key = (script, lang, feature_name)
            self.features_.setdefault(key, []).append(lookup)

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
            self.add_lookup_to_feature_(self.cur_lookup_,
                                        self.cur_feature_name_)
        return self.cur_lookup_

    def build_feature_aalt_(self):
        if not self.aalt_features_:
            return
        alternates = {}  # glyph --> {glyph.alt1, glyph.alt2, ...}
        for location, name in self.aalt_features_ + [(None, "aalt")]:
            feature = [(script, lang, feature, lookups)
                       for (script, lang, feature), lookups
                       in self.features_.items()
                       if feature == name]
            # "aalt" does not have to specify its own lookups, but it might.
            if not feature and name != "aalt":
                raise FeatureLibError("Feature %s has not been defined" % name,
                                      location)
            for script, lang, feature, lookups in feature:
                for lookup in lookups:
                    for glyph, alts in lookup.getAlternateGlyphs().items():
                        alternates.setdefault(glyph, set()).update(alts)
        single = {glyph: list(repl)[0] for glyph, repl in alternates.items()
                  if len(repl) == 1}
        multi = {glyph: sorted(repl, key=self.font.getGlyphID)
                 for glyph, repl in alternates.items()
                 if len(repl) > 1}
        if not single and not multi:
            return
        aalt_lookups = []
        for (script, lang, feature), lookups in self.features_.items():
            if feature == "aalt":
                aalt_lookups.extend(lookups)
        self.features_ = {(script, lang, feature): lookups
                          for (script, lang, feature), lookups
                          in self.features_.items()
                          if feature != "aalt"}
        old_lookups = self.lookups_
        self.lookups_ = []
        self.start_feature(self.aalt_location_, "aalt")
        if single:
            self.add_single_subst(
                self.aalt_location_, prefix=None, suffix=None, mapping=single)
        for glyph, repl in multi.items():
            self.add_multiple_subst(
                self.aalt_location_, prefix=None, glyph=glyph, suffix=None,
                replacements=repl)
        self.end_feature()
        self.lookups_.extend(old_lookups)

    def build_head(self):
        if not self.fontRevision_:
            return
        table = self.font.get("head")
        if not table:  # this only happens for unit tests
            table = self.font["head"] = getTableClass("head")()
            table.decompile(b"\0" * 54, self.font)
            table.tableVersion = 1.0
            table.created = table.modified = 3406620153  # 2011-12-13 11:22:33
        table.fontRevision = self.fontRevision_

    def buildGDEF(self):
        gdef = otTables.GDEF()
        gdef.GlyphClassDef = self.buildGDEFGlyphClassDef_()
        gdef.AttachList = \
            otl.buildAttachList(self.attachPoints_, self.glyphMap)
        gdef.LigCaretList = \
            otl.buildLigCaretList(self.ligCaretCoords_, self.ligCaretPoints_,
                                  self.glyphMap)
        gdef.MarkAttachClassDef = self.buildGDEFMarkAttachClassDef_()
        gdef.MarkGlyphSetsDef = self.buildGDEFMarkGlyphSetsDef_()
        gdef.Version = 0x00010002 if gdef.MarkGlyphSetsDef else 1.0
        if any((gdef.GlyphClassDef, gdef.AttachList, gdef.LigCaretList,
                gdef.MarkAttachClassDef, gdef.MarkGlyphSetsDef)):
            result = getTableClass("GDEF")()
            result.table = gdef
            return result
        else:
            return None

    def buildGDEFGlyphClassDef_(self):
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
        if self.glyphClassDefs_:
            classes = {g: c for (g, (c, _)) in self.glyphClassDefs_.items()}
        else:
            classes = inferredGlyphClass
        if classes:
            result = otTables.GlyphClassDef()
            result.classDefs = classes
            return result
        else:
            return None

    def buildGDEFMarkAttachClassDef_(self):
        classDefs = {g: c for g, (c, _) in self.markAttach_.items()}
        if not classDefs:
            return None
        result = otTables.MarkAttachClassDef()
        result.classDefs = classDefs
        return result

    def buildGDEFMarkGlyphSetsDef_(self):
        if not self.markFilterSets_:
            return None
        m = otTables.MarkGlyphSetsDef()
        m.MarkSetTableFormat = 1
        m.MarkSetCount = len(self.markFilterSets_)
        m.Coverage = []
        filterSets = [(id, glyphs)
                      for (glyphs, id) in self.markFilterSets_.items()]
        for i, glyphs in sorted(filterSets):
            coverage = otTables.Coverage()
            coverage.glyphs = sorted(glyphs, key=self.font.getGlyphID)
            m.Coverage.append(coverage)
        return m

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
        if name == "aalt":
            self.aalt_location_ = location

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

    def add_lookup_call(self, lookup_name):
        assert lookup_name in self.named_lookups_, lookup_name
        self.cur_lookup_ = None
        lookup = self.named_lookups_[lookup_name]
        self.add_lookup_to_feature_(lookup, self.cur_feature_name_)

    def set_font_revision(self, location, revision):
        self.fontRevision_ = revision

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

    def add_attach_points(self, location, glyphs, contourPoints):
        for glyph in glyphs:
            self.attachPoints_.setdefault(glyph, set()).update(contourPoints)

    def add_chain_context_pos(self, location, prefix, glyphs, suffix, lookups):
        lookup = self.get_lookup_(location, ChainContextPosBuilder)
        lookup.rules.append((prefix, glyphs, suffix,
                            self.find_lookup_builders_(lookups)))

    def add_chain_context_subst(self, location,
                                prefix, glyphs, suffix, lookups):
        lookup = self.get_lookup_(location, ChainContextSubstBuilder)
        lookup.substitutions.append((prefix, glyphs, suffix,
                                     self.find_lookup_builders_(lookups)))

    def add_alternate_subst(self, location,
                            prefix, glyph, suffix, replacement):
        if prefix or suffix:
            lookup = self.get_chained_lookup_(location, AlternateSubstBuilder)
            chain = self.get_lookup_(location, ChainContextSubstBuilder)
            chain.substitutions.append((prefix, [glyph], suffix, [lookup]))
        else:
            lookup = self.get_lookup_(location, AlternateSubstBuilder)
        if glyph in lookup.alternates:
            raise FeatureLibError(
                'Already defined alternates for glyph "%s"' % glyph,
                location)
        lookup.alternates[glyph] = replacement

    def add_feature_reference(self, location, featureName):
        if self.cur_feature_name_ != "aalt":
            raise FeatureLibError(
                'Feature references are only allowed inside "feature aalt"',
                location)
        self.aalt_features_.append((location, featureName))

    def add_ligature_subst(self, location,
                           prefix, glyphs, suffix, replacement):
        if prefix or suffix:
            lookup = self.get_chained_lookup_(location, LigatureSubstBuilder)
            chain = self.get_lookup_(location, ChainContextSubstBuilder)
            chain.substitutions.append((prefix, glyphs, suffix, [lookup]))
        else:
            lookup = self.get_lookup_(location, LigatureSubstBuilder)

        # OpenType feature file syntax, section 5.d, "Ligature substitution":
        # "Since the OpenType specification does not allow ligature
        # substitutions to be specified on target sequences that contain
        # glyph classes, the implementation software will enumerate
        # all specific glyph sequences if glyph classes are detected"
        for g in sorted(itertools.product(*glyphs)):
            lookup.ligatures[g] = replacement

    def add_multiple_subst(self, location,
                           prefix, glyph, suffix, replacements):
        if prefix or suffix:
            sub = self.get_chained_lookup_(location, MultipleSubstBuilder)
            sub.mapping[glyph] = replacements
            lookup = self.get_lookup_(location, ChainContextSubstBuilder)
            lookup.substitutions.append((prefix, [{glyph}], suffix, [sub]))
            return
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

    def add_single_subst(self, location, prefix, suffix, mapping):
        if prefix or suffix:
            sub = self.get_chained_lookup_(location, SingleSubstBuilder)
            sub.mapping.update(mapping)
            lookup = self.get_lookup_(location, ChainContextSubstBuilder)
            lookup.substitutions.append(
                (prefix, [mapping.keys()], suffix, [sub]))
            return
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
            makeOpenTypeAnchor(entryAnchor),
            makeOpenTypeAnchor(exitAnchor))

    def add_marks_(self, location, lookupBuilder, marks):
        """Helper for add_mark_{base,liga,mark}_pos."""
        for _, markClass in marks:
            for markClassDef in markClass.definitions:
                for mark in markClassDef.glyphs.glyphSet():
                    if mark not in lookupBuilder.marks:
                        otMarkAnchor = makeOpenTypeAnchor(markClassDef.anchor)
                        lookupBuilder.marks[mark] = (
                            markClass.name, otMarkAnchor)

    def add_mark_base_pos(self, location, bases, marks):
        builder = self.get_lookup_(location, MarkBasePosBuilder)
        self.add_marks_(location, builder, marks)
        for baseAnchor, markClass in marks:
            otBaseAnchor = makeOpenTypeAnchor(baseAnchor)
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
                anchors[markClass.name] = makeOpenTypeAnchor(ligAnchor)
            componentAnchors.append(anchors)
        for glyph in ligatures:
            builder.ligatures[glyph] = componentAnchors

    def add_mark_mark_pos(self, location, baseMarks, marks):
        builder = self.get_lookup_(location, MarkMarkPosBuilder)
        self.add_marks_(location, builder, marks)
        for baseAnchor, markClass in marks:
            otBaseAnchor = makeOpenTypeAnchor(baseAnchor)
            for baseMark in baseMarks:
                builder.baseMarks.setdefault(baseMark, {})[markClass.name] = (
                    otBaseAnchor)

    def add_class_pair_pos(self, location, glyphclass1, value1,
                           glyphclass2, value2):
        lookup = self.get_lookup_(location, ClassPairPosBuilder)
        lookup.add_pair(location, glyphclass1, value1, glyphclass2, value2)

    def add_specific_pair_pos(self, location, glyph1, value1, glyph2, value2):
        lookup = self.get_lookup_(location, SpecificPairPosBuilder)
        lookup.add_pair(location, glyph1, value1, glyph2, value2)

    def add_single_pos(self, location, glyph, valuerecord):
        lookup = self.get_lookup_(location, SinglePosBuilder)
        lookup.add_pos(location, glyph, valuerecord)

    def setGlyphClass_(self, location, glyph, glyphClass):
        oldClass, oldLocation = self.glyphClassDefs_.get(glyph, (None, None))
        if oldClass and oldClass != glyphClass:
            raise FeatureLibError(
                "Glyph %s was assigned to a different class at %s:%s:%s" %
                (glyph, oldLocation[0], oldLocation[1], oldLocation[2]),
                location)
        self.glyphClassDefs_[glyph] = (glyphClass, location)

    def add_glyphClassDef(self, location, baseGlyphs, ligatureGlyphs,
                          markGlyphs, componentGlyphs):
        for glyph in baseGlyphs:
            self.setGlyphClass_(location, glyph, 1)
        for glyph in ligatureGlyphs:
            self.setGlyphClass_(location, glyph, 2)
        for glyph in markGlyphs:
            self.setGlyphClass_(location, glyph, 3)
        for glyph in componentGlyphs:
            self.setGlyphClass_(location, glyph, 4)

    def add_ligatureCaretByIndex_(self, location, glyphs, carets):
        for glyph in glyphs:
            self.ligCaretPoints_.setdefault(glyph, set()).update(carets)

    def add_ligatureCaretByPos_(self, location, glyphs, carets):
        for glyph in glyphs:
            self.ligCaretCoords_.setdefault(glyph, set()).update(carets)


def makeOpenTypeAnchor(anchor):
    """ast.Anchor --> otTables.Anchor"""
    if anchor is None:
        return None
    deviceX, deviceY = None, None
    if anchor.xDeviceTable is not None:
        deviceX = otl.buildDevice(anchor.xDeviceTable)
    if anchor.yDeviceTable is not None:
        deviceY = otl.buildDevice(anchor.yDeviceTable)
    return otl.buildAnchor(anchor.x, anchor.y, anchor.contourpoint,
                           deviceX, deviceY)


_VALUEREC_ATTRS = {
    name[0].lower() + name[1:]: (name, isDevice)
    for _, name, isDevice, _ in otBase.valueRecordFormat
    if not name.startswith("Reserved")
}


def makeOpenTypeValueRecord(v):
    """ast.ValueRecord --> (otBase.ValueRecord, int ValueFormat)"""
    if v is None:
        return None, 0

    vr = {}
    for astName, (otName, isDevice) in _VALUEREC_ATTRS.items():
        val = getattr(v, astName, None)
        if val:
            vr[otName] = otl.buildDevice(val) if isDevice else val

    valRec = otl.buildValue(vr)
    return valRec, valRec.getFormat()


class LookupBuilder(object):
    def __init__(self, font, location, table, lookup_type):
        self.font = font
        self.glyphMap = font.getReverseGlyphMap()
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

    def getAlternateGlyphs(self):
        """Helper for building 'aalt' features."""
        return {}

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
            coverage = otl.buildCoverage(p, self.glyphMap)
            subtable.BacktrackCoverage.append(coverage)

    def setLookAheadCoverage_(self, suffix, subtable):
        subtable.LookAheadGlyphCount = len(suffix)
        subtable.LookAheadCoverage = []
        for s in suffix:
            coverage = otl.buildCoverage(s, self.glyphMap)
            subtable.LookAheadCoverage.append(coverage)

    def setInputCoverage_(self, glyphs, subtable):
        subtable.InputGlyphCount = len(glyphs)
        subtable.InputCoverage = []
        for g in glyphs:
            coverage = otl.buildCoverage(g, self.glyphMap)
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
        subtable = otl.buildAlternateSubst(self.alternates)
        return self.buildLookup_([subtable])

    def getAlternateGlyphs(self):
        return self.alternates


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

    def getAlternateGlyphs(self):
        result = {}
        for (_prefix, _input, _suffix, lookups) in self.substitutions:
            for lookup in lookups:
                alts = lookup.getAlternateGlyphs()
                for glyph, replacements in alts.items():
                    result.setdefault(glyph, set()).update(replacements)
        return result


class LigatureSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 4)
        self.ligatures = {}  # {('f','f','i'): 'f_f_i'}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.ligatures == other.ligatures)

    def build(self):
        subtable = otl.buildLigatureSubst(self.ligatures)
        return self.buildLookup_([subtable])


class MultipleSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 2)
        self.mapping = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        subtable = otl.buildMultipleSubst(self.mapping)
        return self.buildLookup_([subtable])


class SpecificPairPosBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 2)
        self.pairs = {}  # (gc1, gc2) -> (location, value1, value2)

    def add_pair(self, location, glyph1, value1, glyph2, value2):
        oldValue = self.pairs.get((glyph1, glyph2), None)
        if oldValue is not None:
            otherLoc, _, _ = oldValue
            raise FeatureLibError(
                'Already defined position for pair %s %s at %s:%d:%d'
                % (glyph1, glyph2, otherLoc[0], otherLoc[1], otherLoc[2]),
                location)
        self.pairs[(glyph1, glyph2)] = (location, value1, value2)

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.pairs == other.pairs)

    def build(self):
        subtables = []

        # (valueFormat1, valueFormat2) --> [(glyph1, glyph2, value1, value2)*]
        format1 = {}
        for (glyph1, glyph2), (location, value1, value2) in self.pairs.items():
            val1, valFormat1 = makeOpenTypeValueRecord(value1)
            val2, valFormat2 = makeOpenTypeValueRecord(value2)
            format1.setdefault(((valFormat1, valFormat2)), []).append(
                (glyph1, glyph2, val1, val2))
        for (vf1, vf2), pairs in sorted(format1.items()):
            p = {}
            for glyph1, glyph2, val1, val2 in pairs:
                p.setdefault(glyph1, []).append((glyph2, val1, val2))
            st = otTables.PairPos()
            subtables.append(st)
            st.Format = 1
            st.ValueFormat1, st.ValueFormat2 = vf1, vf2
            st.Coverage = otl.buildCoverage(p, self.glyphMap)
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
            self.attachments[glyph] = (entryAnchor, exitAnchor)

    def build(self):
        st = otl.buildCursivePos(self.attachments, self.glyphMap)
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
        st.MarkCoverage = otl.buildCoverage(self.marks, self.glyphMap)
        markClasses = self.buildMarkClasses_(self.marks)
        st.ClassCount = len(markClasses)
        self.setMarkArray_(self.marks, markClasses, st)

        st.BaseCoverage = otl.buildCoverage(self.bases, self.glyphMap)
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
        st.MarkCoverage = otl.buildCoverage(self.marks, self.glyphMap)
        markClasses = self.buildMarkClasses_(self.marks)
        st.ClassCount = len(markClasses)
        self.setMarkArray_(self.marks, markClasses, st)

        st.LigatureCoverage = otl.buildCoverage(self.ligatures, self.glyphMap)
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
        st.Mark1Coverage = otl.buildCoverage(self.marks, self.glyphMap)
        markClasses = self.buildMarkClasses_(self.marks)
        st.ClassCount = len(markClasses)
        self.setMark1Array_(self.marks, markClasses, st)

        st.Mark2Coverage = otl.buildCoverage(self.baseMarks, self.glyphMap)
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
            st.Coverage = otl.buildCoverage(mapping.keys(), self.glyphMap)
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
        subtable = otl.buildSingleSubst(self.mapping)
        return self.buildLookup_([subtable])

    def getAlternateGlyphs(self):
        return {glyph: set([repl]) for glyph, repl in self.mapping.items()}


class ClassPairPosSubtableBuilder(object):
    def __init__(self, builder, valueFormat1, valueFormat2):
        self.builder_ = builder
        self.classDef1_, self.classDef2_ = None, None
        self.coverage_ = set()
        self.values_ = {}  # (glyphclass1, glyphclass2) --> (value1, value2)
        self.valueFormat1_, self.valueFormat2_ = valueFormat1, valueFormat2
        self.forceSubtableBreak_ = False
        self.subtables_ = []

    def addPair(self, gc1, value1, gc2, value2):
        mergeable = (not self.forceSubtableBreak_ and
                     self.classDef1_ is not None and
                     self.classDef1_.canAdd(gc1) and
                     self.classDef2_ is not None and
                     self.classDef2_.canAdd(gc2))
        if not mergeable:
            self.flush_()
            self.classDef1_ = ClassDefBuilder(useClass0=True)
            self.classDef2_ = ClassDefBuilder(useClass0=False)
            self.coverage_ = set()
            self.values_ = {}
        self.classDef1_.add(gc1)
        self.classDef2_.add(gc2)
        self.coverage_.update(gc1)
        self.values_[(gc1, gc2)] = (value1, value2)

    def addSubtableBreak(self):
        self.forceSubtableBreak_ = True

    def subtables(self):
        self.flush_()
        return self.subtables_

    def flush_(self):
        if self.classDef1_ is None or self.classDef2_ is None:
            return
        st = otTables.PairPos()
        st.Format = 2
        st.Coverage = otl.buildCoverage(self.coverage_, self.builder_.glyphMap)
        st.ValueFormat1 = self.valueFormat1_
        st.ValueFormat2 = self.valueFormat2_
        st.ClassDef1 = self.classDef1_.build()
        st.ClassDef2 = self.classDef2_.build()
        classes1 = self.classDef1_.classes()
        classes2 = self.classDef2_.classes()
        st.Class1Count, st.Class2Count = len(classes1), len(classes2)
        st.Class1Record = []
        for c1 in classes1:
            rec1 = otTables.Class1Record()
            rec1.Class2Record = []
            st.Class1Record.append(rec1)
            for c2 in classes2:
                rec2 = otTables.Class2Record()
                val1, val2 = self.values_.get((c1, c2), (None, None))
                rec2.Value1, rec2.Value2 = val1, val2
                rec1.Class2Record.append(rec2)
        self.subtables_.append(st)


class ClassPairPosBuilder(LookupBuilder):
    SUBTABLE_BREAK_ = "SUBTABLE_BREAK"

    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 2)
        self.pairs = []  # [(location, gc1, value1, gc2, value2)*]

    def add_pair(self, location, glyphclass1, value1, glyphclass2, value2):
        self.pairs.append((location, glyphclass1, value1, glyphclass2, value2))

    def add_subtable_break(self, location):
        self.pairs.append((location,
                           self.SUBTABLE_BREAK_, self.SUBTABLE_BREAK_,
                           self.SUBTABLE_BREAK_, self.SUBTABLE_BREAK_))

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.pairs == other.pairs)

    def build(self):
        builders = {}
        builder = None
        for location, glyphclass1, value1, glyphclass2, value2 in self.pairs:
            if glyphclass1 is self.SUBTABLE_BREAK_:
                if builder is not None:
                    builder.addSubtableBreak()
                continue
            val1, valFormat1 = makeOpenTypeValueRecord(value1)
            val2, valFormat2 = makeOpenTypeValueRecord(value2)
            builder = builders.get((valFormat1, valFormat2))
            if builder is None:
                builder = ClassPairPosSubtableBuilder(
                    self, valFormat1, valFormat2)
                builders[(valFormat1, valFormat2)] = builder
            builder.addPair(glyphclass1, val1, glyphclass2, val2)
        subtables = []
        for key in sorted(builders.keys()):
            subtables.extend(builders[key].subtables())
        return self.buildLookup_(subtables)


class SinglePosBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 1)
        self.locations = {}  # glyph -> (filename, line, column)
        self.mapping = {}  # glyph -> otTables.ValueRecord

    def add_pos(self, location, glyph, valueRecord):
        otValueRecord, _ = makeOpenTypeValueRecord(valueRecord)
        curValue = self.mapping.get(glyph)
        if curValue is not None and curValue != otValueRecord:
            otherLoc = self.locations[glyph]
            raise FeatureLibError(
                'Already defined different position for glyph "%s" at %s:%d:%d'
                % (glyph, otherLoc[0], otherLoc[1], otherLoc[2]),
                location)
        if otValueRecord:
            self.mapping[glyph] = otValueRecord
        self.locations[glyph] = location

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        subtables = otl.buildSinglePos(self.mapping, self.glyphMap)
        return self.buildLookup_(subtables)


class ClassDefBuilder(object):
    """Helper for building ClassDef tables."""
    def __init__(self, useClass0):
        self.classes_ = set()
        self.glyphs_ = {}
        self.useClass0_ = useClass0

    def canAdd(self, glyphs):
        glyphs = frozenset(glyphs)
        if glyphs in self.classes_:
            return True
        for glyph in glyphs:
            if glyph in self.glyphs_:
                return False
        return True

    def add(self, glyphs):
        glyphs = frozenset(glyphs)
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
        # in the output file. We don't get this right with key=len below.
        result = sorted(self.classes_, key=len, reverse=True)
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
        classDef = otTables.ClassDef()
        classDef.classDefs = glyphClasses
        return classDef
