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
        self.lookupflag_ = 0
        self.language_systems = set()

    def build(self):
        self.gpos = self.font['GPOS'] = self.makeTable('GPOS')
        self.gsub = self.font['GSUB'] = self.makeTable('GSUB')
        parsetree = Parser(self.featurefile_path).parse()
        parsetree.build(self)

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
        table.LookupList.LookupCount = 0
        table.LookupList.Lookup = []
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

    def set_language(self, location, language, include_default):
        if include_default:
            langsys = set(self.get_default_language_systems_())
        else:
            langsys = set()
        langsys.add((self.script_, language))
        self.language_systems = frozenset(langsys)

    def set_script(self, location, script):
        self.script_ = script
        self.lookupflag_ = 0
        self.set_language(location, 'dflt', include_default=True)
