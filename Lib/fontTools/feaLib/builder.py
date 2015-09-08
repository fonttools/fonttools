from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.error import FeatureLibError
from fontTools.feaLib.parser import Parser
from fontTools.ttLib.tables import otTables
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
        self.features_ = {}  # ('latn', 'DEU', 'smcp') --> [LookupBuilder*]

    def build(self):
        parsetree = Parser(self.featurefile_path).parse()
        parsetree.build(self)
        self.gpos = self.font['GPOS'] = self.makeTable('GPOS')
        self.gsub = self.font['GSUB'] = self.makeTable('GSUB')

    def get_lookup_(self, location, builder_class):
        if (self.cur_lookup_ and
                type(self.cur_lookup_) == builder_class and
                self.cur_lookup_.lookup_flag == self.lookup_flag_):
            return self.cur_lookup_
        if self.cur_lookup_name_ and self.cur_lookup_:
            raise FeatureLibError(
                "Within a named lookup block, all rules must be of "
                "the same lookup type and flag", location)
        self.cur_lookup_ = builder_class(location, self.lookup_flag_)
        self.lookups_.append(self.cur_lookup_)
        if self.cur_lookup_name_:
            # We are starting a lookup rule inside a named lookup block.
            self.named_lookups_[self.cur_lookup_name_] = self.cur_lookup_
        else:
            # We are starting a lookup rule inside a feature.
            for script, lang in self.language_systems:
                key = (script, lang, self.cur_feature_name_)
                self.features_.setdefault(key, []).append(self.cur_lookup_)
        return self.cur_lookup_

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
        scripts = {}  # 'cyrl' --> {'DEU': [23, 24]} for feature #23,24
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
                langrec.LangSys.ReqFeatureIndex = 0xFFFF
                langrec.LangSys.FeatureCount = len(feature_indices)
                langrec.LangSys.FeatureIndex = feature_indices
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

    def set_language(self, location, language, include_default):
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
        self.set_language(location, 'dflt', include_default=True)

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
        # TODO(sascha): Implement this, possibly via a new class
        # otTables.MultipleSubst modeled after otTables.SingleSubst.
        warnings.warn('Multiple substitution (GPOS LookupType 2) '
                      'is not yet implemented')

    def add_single_substitution(self, location, mapping):
        lookup = self.get_lookup_(location, SingleSubstBuilder)
        for (from_glyph, to_glyph) in mapping.items():
            if from_glyph in lookup.mapping:
                raise FeatureLibError(
                    'Already defined rule for replacing glyph "%s" by "%s"' %
                    (from_glyph, lookup.mapping[from_glyph]),
                    location)
            lookup.mapping[from_glyph] = to_glyph


class LookupBuilder(object):
    def __init__(self, location, table, lookup_type, lookup_flag):
        self.location = location
        self.table, self.lookup_type = table, lookup_type
        self.lookup_flag = lookup_flag
        self.lookup_index = None  # assigned when making final tables
        assert table in ('GPOS', 'GSUB')

    def equals(self, other):
        return (isinstance(other, self.__class__) and
                self.table == other.table and
                self.lookup_flag == other.lookup_flag)


class AlternateSubstBuilder(LookupBuilder):
    def __init__(self, location, lookup_flag):
        LookupBuilder.__init__(self, location, 'GSUB', 3, lookup_flag)
        self.alternates = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.alternates == other.alternates)

    def build(self):
        lookup = otTables.AlternateSubst()
        lookup.Format = 1
        lookup.alternates = self.alternates
        return lookup


class LigatureSubstBuilder(LookupBuilder):
    def __init__(self, location, lookup_flag):
        LookupBuilder.__init__(self, location, 'GSUB', 4, lookup_flag)
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
        lookup = otTables.LigatureSubst()
        lookup.Format = 1
        lookup.ligatures = {}
        for components in sorted(self.ligatures.keys(), key=self.make_key):
            lig = otTables.Ligature()
            lig.Component = components
            lig.LigGlyph = self.ligatures[components]
            lookup.ligatures.setdefault(components[0], []).append(lig)
        return lookup


class SingleSubstBuilder(LookupBuilder):
    def __init__(self, location, lookup_flag):
        LookupBuilder.__init__(self, location, 'GSUB', 1, lookup_flag)
        self.mapping = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        lookup = otTables.SingleSubst()
        lookup.mapping = self.mapping
        return lookup
