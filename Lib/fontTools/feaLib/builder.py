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
        self.language_systems_ = []

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
        if script == "DFLT" and language == "dflt" and self.language_systems_:
            # OpenType Feature File Specification, section 4.b.i
            raise FeatureLibError(
                'If "languagesystem DFLT dflt" is present, it must be '
                'the first of the languagesystem statements', location)
        self.language_systems_.append((script, language))
