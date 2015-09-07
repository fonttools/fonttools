from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.feaLib.error import FeatureLibError
from fontTools.feaLib.parser import Parser
from fontTools.ttLib.tables import otTables


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
        self.cur_lookup_ = None
        self.lookups_ = []

    def build(self):
        parsetree = Parser(self.featurefile_path).parse()
        parsetree.build(self)
        self.gpos = self.font['GPOS'] = self.makeTable('GPOS')
        self.gsub = self.font['GSUB'] = self.makeTable('GSUB')

    def get_lookup_(self, location, builder_class):
        if self.cur_lookup_ and type(self.cur_lookup_) == builder_class:
            return self.cur_lookup_
        self.cur_lookup_ = builder_class(location, self.lookup_flag_)
        self.lookups_.append(self.cur_lookup_)
        return self.cur_lookup_

    def makeTable(self, tag):
        table = getattr(otTables, tag, None)()
        table.Version = 1.0
        table.ScriptList = otTables.ScriptList()
        table.ScriptList.ScriptCount = 0
        table.ScriptList.ScriptRecord = []
        table.FeatureList = otTables.FeatureList()
        table.FeatureList.FeatureCount = 0
        table.FeatureList.FeatureRecord = []

        table.LookupList = otTables.LookupList()
        table.LookupList.Lookup = []
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
        table.LookupList.LookupCount = len(table.LookupList.Lookup)
        return table

    def add_language_system(self, location, script, language):
        # OpenType Feature File Specification, section 4.b.i
        if (script == "DFLT" and language == "dflt" and
                self.default_language_systems_):
            raise FeatureLibError(
                'If "languagesystem DFLT dflt" is present, it must be '
                'the first of the languagesystem statements', location)
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

    def end_feature(self):
        self.language_systems = None
        self.cur_lookup_ = None

    def set_language(self, location, language, include_default):
        self.cur_lookup_ = None
        if include_default:
            langsys = set(self.get_default_language_systems_())
        else:
            langsys = set()
        langsys.add((self.script_, language))
        self.language_systems = frozenset(langsys)

    def set_script(self, location, script):
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


class LookupBuilder(object):
    def __init__(self, location, table, lookup_type, lookup_flag):
        self.location = location
        self.table, self.lookup_type = table, lookup_type
        self.lookup_flag = lookup_flag
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
