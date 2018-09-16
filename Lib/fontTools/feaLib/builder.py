from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import binary2num, safeEval
from fontTools.feaLib.error import FeatureLibError
from fontTools.feaLib.parser import Parser
from fontTools.feaLib.ast import FeatureFile
from fontTools.otlLib import builder as otl
from fontTools.ttLib import newTable, getTableModule
from fontTools.ttLib.tables import otBase, otTables
from collections import defaultdict
import itertools
import logging


log = logging.getLogger(__name__)


def addOpenTypeFeatures(font, featurefile, tables=None):
    builder = Builder(font, featurefile)
    builder.build(tables=tables)


def addOpenTypeFeaturesFromString(font, features, filename=None, tables=None):
    featurefile = UnicodeIO(tounicode(features))
    if filename:
        # the directory containing 'filename' is used as the root of relative
        # include paths; if None is provided, the current directory is assumed
        featurefile.name = filename
    addOpenTypeFeatures(font, featurefile, tables=tables)


class Builder(object):

    supportedTables = frozenset(Tag(tag) for tag in [
        "BASE",
        "GDEF",
        "GPOS",
        "GSUB",
        "OS/2",
        "head",
        "hhea",
        "name",
        "vhea",
    ])

    def __init__(self, font, featurefile):
        self.font = font
        # 'featurefile' can be either a path or file object (in which case we
        # parse it into an AST), or a pre-parsed AST instance
        if isinstance(featurefile, FeatureFile):
            self.parseTree, self.file = featurefile, None
        else:
            self.parseTree, self.file = None, featurefile
        self.glyphMap = font.getReverseGlyphMap()
        self.default_language_systems_ = set()
        self.script_ = None
        self.lookupflag_ = 0
        self.lookupflag_markFilterSet_ = None
        self.language_systems = set()
        self.seen_non_DFLT_script_ = False
        self.named_lookups_ = {}
        self.cur_lookup_ = None
        self.cur_lookup_name_ = None
        self.cur_feature_name_ = None
        self.lookups_ = []
        self.features_ = {}  # ('latn', 'DEU ', 'smcp') --> [LookupBuilder*]
        self.required_features_ = {}  # ('latn', 'DEU ') --> 'scmp'
        # for feature 'aalt'
        self.aalt_features_ = []  # [(location, featureName)*], for 'aalt'
        self.aalt_location_ = None
        self.aalt_alternates_ = {}
        # for 'featureNames'
        self.featureNames_ = set()
        self.featureNames_ids_ = {}
        # for 'cvParameters'
        self.cv_parameters_ = set()
        self.cv_parameters_ids_ = {}
        self.cv_num_named_params_ = {}
        self.cv_characters_ = defaultdict(list)
        # for feature 'size'
        self.size_parameters_ = None
        # for table 'head'
        self.fontRevision_ = None  # 2.71
        # for table 'name'
        self.names_ = []
        # for table 'BASE'
        self.base_horiz_axis_ = None
        self.base_vert_axis_ = None
        # for table 'GDEF'
        self.attachPoints_ = {}  # "a" --> {3, 7}
        self.ligCaretCoords_ = {}  # "f_f_i" --> {300, 600}
        self.ligCaretPoints_ = {}  # "f_f_i" --> {3, 7}
        self.glyphClassDefs_ = {}  # "fi" --> (2, (file, line, column))
        self.markAttach_ = {}  # "acute" --> (4, (file, line, column))
        self.markAttachClassID_ = {}  # frozenset({"acute", "grave"}) --> 4
        self.markFilterSets_ = {}  # frozenset({"acute", "grave"}) --> 4
        # for table 'OS/2'
        self.os2_ = {}
        # for table 'hhea'
        self.hhea_ = {}
        # for table 'vhea'
        self.vhea_ = {}

    def build(self, tables=None):
        if self.parseTree is None:
            self.parseTree = Parser(self.file, self.glyphMap).parse()
        self.parseTree.build(self)
        # by default, build all the supported tables
        if tables is None:
            tables = self.supportedTables
        else:
            tables = frozenset(tables)
            unsupported = tables - self.supportedTables
            assert not unsupported, unsupported
        if "GSUB" in tables:
            self.build_feature_aalt_()
        if "head" in tables:
            self.build_head()
        if "hhea" in tables:
            self.build_hhea()
        if "vhea" in tables:
            self.build_vhea()
        if "name" in tables:
            self.build_name()
        if "OS/2" in tables:
            self.build_OS_2()
        for tag in ('GPOS', 'GSUB'):
            if tag not in tables:
                continue
            table = self.makeTable(tag)
            if (table.ScriptList.ScriptCount > 0 or
                    table.FeatureList.FeatureCount > 0 or
                    table.LookupList.LookupCount > 0):
                fontTable = self.font[tag] = newTable(tag)
                fontTable.table = table
            elif tag in self.font:
                del self.font[tag]
        if "GDEF" in tables:
            gdef = self.buildGDEF()
            if gdef:
                self.font["GDEF"] = gdef
            elif "GDEF" in self.font:
                del self.font["GDEF"]
        if "BASE" in tables:
            base = self.buildBASE()
            if base:
                self.font["BASE"] = base
            elif "BASE" in self.font:
                del self.font["BASE"]

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
        if not self.aalt_features_ and not self.aalt_alternates_:
            return
        alternates = {g: set(a) for g, a in self.aalt_alternates_.items()}
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
        # TODO: Figure out the glyph alternate ordering used by makeotf.
        # https://github.com/fonttools/fonttools/issues/836
        multi = {glyph: sorted(repl, key=self.font.getGlyphID)
                 for glyph, repl in alternates.items()
                 if len(repl) > 1}
        if not single and not multi:
            return
        self.features_ = {(script, lang, feature): lookups
                          for (script, lang, feature), lookups
                          in self.features_.items()
                          if feature != "aalt"}
        old_lookups = self.lookups_
        self.lookups_ = []
        self.start_feature(self.aalt_location_, "aalt")
        if single:
            single_lookup = self.get_lookup_(location, SingleSubstBuilder)
            single_lookup.mapping = single
        if multi:
            multi_lookup = self.get_lookup_(location, AlternateSubstBuilder)
            multi_lookup.alternates = multi
        self.end_feature()
        self.lookups_.extend(old_lookups)

    def build_head(self):
        if not self.fontRevision_:
            return
        table = self.font.get("head")
        if not table:  # this only happens for unit tests
            table = self.font["head"] = newTable("head")
            table.decompile(b"\0" * 54, self.font)
            table.tableVersion = 1.0
            table.created = table.modified = 3406620153  # 2011-12-13 11:22:33
        table.fontRevision = self.fontRevision_

    def build_hhea(self):
        if not self.hhea_:
            return
        table = self.font.get("hhea")
        if not table:  # this only happens for unit tests
            table = self.font["hhea"] = newTable("hhea")
            table.decompile(b"\0" * 36, self.font)
            table.tableVersion = 0x00010000
        if "caretoffset" in self.hhea_:
            table.caretOffset = self.hhea_["caretoffset"]
        if "ascender" in self.hhea_:
            table.ascent = self.hhea_["ascender"]
        if "descender" in self.hhea_:
            table.descent = self.hhea_["descender"]
        if "linegap" in self.hhea_:
            table.lineGap = self.hhea_["linegap"]

    def build_vhea(self):
        if not self.vhea_:
            return
        table = self.font.get("vhea")
        if not table:  # this only happens for unit tests
            table = self.font["vhea"] = newTable("vhea")
            table.decompile(b"\0" * 36, self.font)
            table.tableVersion = 0x00011000
        if "verttypoascender" in self.vhea_:
            table.ascent = self.vhea_["verttypoascender"]
        if "verttypodescender" in self.vhea_:
            table.descent = self.vhea_["verttypodescender"]
        if "verttypolinegap" in self.vhea_:
            table.lineGap = self.vhea_["verttypolinegap"]

    def get_user_name_id(self, table):
        # Try to find first unused font-specific name id
        nameIDs = [name.nameID for name in table.names]
        for user_name_id in range(256, 32767):
            if user_name_id not in nameIDs:
                return user_name_id

    def buildFeatureParams(self, tag):
        params = None
        if tag == "size":
            params = otTables.FeatureParamsSize()
            params.DesignSize, params.SubfamilyID, params.RangeStart, \
                    params.RangeEnd = self.size_parameters_
            if tag in self.featureNames_ids_:
                params.SubfamilyNameID = self.featureNames_ids_[tag]
            else:
                params.SubfamilyNameID = 0
        elif tag in self.featureNames_:
            if not self.featureNames_ids_:
                # name table wasn't selected among the tables to build; skip
                pass
            else:
                assert tag in self.featureNames_ids_
                params = otTables.FeatureParamsStylisticSet()
                params.Version = 0
                params.UINameID = self.featureNames_ids_[tag]
        elif tag in self.cv_parameters_:
            params = otTables.FeatureParamsCharacterVariants()
            params.Format = 0
            params.FeatUILabelNameID = self.cv_parameters_ids_.get(
                (tag, 'FeatUILabelNameID'), 0)
            params.FeatUITooltipTextNameID = self.cv_parameters_ids_.get(
                (tag, 'FeatUITooltipTextNameID'), 0)
            params.SampleTextNameID = self.cv_parameters_ids_.get(
                (tag, 'SampleTextNameID'), 0)
            params.NumNamedParameters = self.cv_num_named_params_.get(tag, 0)
            params.FirstParamUILabelNameID = self.cv_parameters_ids_.get(
                (tag, 'ParamUILabelNameID_0'), 0)
            params.CharCount = len(self.cv_characters_[tag])
            params.Character = self.cv_characters_[tag]
        return params

    def build_name(self):
        if not self.names_:
            return
        table = self.font.get("name")
        if not table:  # this only happens for unit tests
            table = self.font["name"] = newTable("name")
            table.names = []
        for name in self.names_:
            nameID, platformID, platEncID, langID, string = name
            # For featureNames block, nameID is 'feature tag'
            # For cvParameters blocks, nameID is ('feature tag', 'block name')
            if not isinstance(nameID, int):
                tag = nameID
                if tag in self.featureNames_:
                    if tag not in self.featureNames_ids_:
                        self.featureNames_ids_[tag] = self.get_user_name_id(table)
                        assert self.featureNames_ids_[tag] is not None
                    nameID = self.featureNames_ids_[tag]
                elif tag[0] in self.cv_parameters_:
                    if tag not in self.cv_parameters_ids_:
                        self.cv_parameters_ids_[tag] = self.get_user_name_id(table)
                        assert self.cv_parameters_ids_[tag] is not None
                    nameID = self.cv_parameters_ids_[tag]
            table.setName(string, nameID, platformID, platEncID, langID)

    def build_OS_2(self):
        if not self.os2_:
            return
        table = self.font.get("OS/2")
        if not table:  # this only happens for unit tests
            table = self.font["OS/2"] = newTable("OS/2")
            data = b"\0" * sstruct.calcsize(getTableModule("OS/2").OS2_format_0)
            table.decompile(data, self.font)
        version = 0
        if "fstype" in self.os2_:
            table.fsType = self.os2_["fstype"]
        if "panose" in self.os2_:
            panose = getTableModule("OS/2").Panose()
            panose.bFamilyType, panose.bSerifStyle, panose.bWeight,\
                panose.bProportion, panose.bContrast, panose.bStrokeVariation,\
                panose.bArmStyle, panose.bLetterForm, panose.bMidline, \
                panose.bXHeight = self.os2_["panose"]
            table.panose = panose
        if "typoascender" in self.os2_:
            table.sTypoAscender = self.os2_["typoascender"]
        if "typodescender" in self.os2_:
            table.sTypoDescender = self.os2_["typodescender"]
        if "typolinegap" in self.os2_:
            table.sTypoLineGap = self.os2_["typolinegap"]
        if "winascent" in self.os2_:
            table.usWinAscent = self.os2_["winascent"]
        if "windescent" in self.os2_:
            table.usWinDescent = self.os2_["windescent"]
        if "vendor" in self.os2_:
            table.achVendID = safeEval("'''" + self.os2_["vendor"] + "'''")
        if "weightclass" in self.os2_:
            table.usWeightClass = self.os2_["weightclass"]
        if "widthclass" in self.os2_:
            table.usWidthClass = self.os2_["widthclass"]
        if "unicoderange" in self.os2_:
            table.setUnicodeRanges(self.os2_["unicoderange"])
        if "codepagerange" in self.os2_:
            pages = self.build_codepages_(self.os2_["codepagerange"])
            table.ulCodePageRange1, table.ulCodePageRange2 = pages
            version = 1
        if "xheight" in self.os2_:
            table.sxHeight = self.os2_["xheight"]
            version = 2
        if "capheight" in self.os2_:
            table.sCapHeight = self.os2_["capheight"]
            version = 2
        if "loweropsize" in self.os2_:
            table.usLowerOpticalPointSize = self.os2_["loweropsize"]
            version = 5
        if "upperopsize" in self.os2_:
            table.usUpperOpticalPointSize = self.os2_["upperopsize"]
            version = 5
        def checkattr(table, attrs):
            for attr in attrs:
                if not hasattr(table, attr):
                    setattr(table, attr, 0)
        table.version = max(version, table.version)
        # this only happens for unit tests
        if version >= 1:
            checkattr(table, ("ulCodePageRange1", "ulCodePageRange2"))
        if version >= 2:
            checkattr(table, ("sxHeight", "sCapHeight", "usDefaultChar",
                              "usBreakChar", "usMaxContext"))
        if version >= 5:
            checkattr(table, ("usLowerOpticalPointSize",
                              "usUpperOpticalPointSize"))

    def build_codepages_(self, pages):
        pages2bits = {
            1252: 0,  1250: 1, 1251: 2, 1253: 3, 1254: 4, 1255: 5, 1256: 6,
            1257: 7,  1258: 8, 874: 16, 932: 17, 936: 18, 949: 19, 950: 20,
            1361: 21, 869: 48, 866: 49, 865: 50, 864: 51, 863: 52, 862: 53,
            861:  54, 860: 55, 857: 56, 855: 57, 852: 58, 775: 59, 737: 60,
            708:  61, 850: 62, 437: 63,
        }
        bits = [pages2bits[p] for p in pages if p in pages2bits]
        pages = []
        for i in range(2):
            pages.append("")
            for j in range(i * 32, (i + 1) * 32):
                if j in bits:
                    pages[i] += "1"
                else:
                    pages[i] += "0"
        return [binary2num(p[::-1]) for p in pages]

    def buildBASE(self):
        if not self.base_horiz_axis_ and not self.base_vert_axis_:
            return None
        base = otTables.BASE()
        base.Version = 0x00010000
        base.HorizAxis = self.buildBASEAxis(self.base_horiz_axis_)
        base.VertAxis = self.buildBASEAxis(self.base_vert_axis_)

        result = newTable("BASE")
        result.table = base
        return result

    def buildBASEAxis(self, axis):
        if not axis:
            return
        bases, scripts = axis
        axis = otTables.Axis()
        axis.BaseTagList = otTables.BaseTagList()
        axis.BaseTagList.BaselineTag = bases
        axis.BaseTagList.BaseTagCount = len(bases)
        axis.BaseScriptList = otTables.BaseScriptList()
        axis.BaseScriptList.BaseScriptRecord = []
        axis.BaseScriptList.BaseScriptCount = len(scripts)
        for script in sorted(scripts):
            record = otTables.BaseScriptRecord()
            record.BaseScriptTag = script[0]
            record.BaseScript = otTables.BaseScript()
            record.BaseScript.BaseLangSysCount = 0
            record.BaseScript.BaseValues = otTables.BaseValues()
            record.BaseScript.BaseValues.DefaultIndex = bases.index(script[1])
            record.BaseScript.BaseValues.BaseCoord = []
            record.BaseScript.BaseValues.BaseCoordCount = len(script[2])
            for c in script[2]:
                coord = otTables.BaseCoord()
                coord.Format = 1
                coord.Coordinate = c
                record.BaseScript.BaseValues.BaseCoord.append(coord)
            axis.BaseScriptList.BaseScriptRecord.append(record)
        return axis

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
        gdef.Version = 0x00010002 if gdef.MarkGlyphSetsDef else 0x00010000
        if any((gdef.GlyphClassDef, gdef.AttachList, gdef.LigCaretList,
                gdef.MarkAttachClassDef, gdef.MarkGlyphSetsDef)):
            result = newTable("GDEF")
            result.table = gdef
            return result
        else:
            return None

    def buildGDEFGlyphClassDef_(self):
        if self.glyphClassDefs_:
            classes = {g: c for (g, (c, _)) in self.glyphClassDefs_.items()}
        else:
            classes = {}
            for lookup in self.lookups_:
                classes.update(lookup.inferGlyphClasses())
            for markClass in self.parseTree.markClasses.values():
                for markClassDef in markClass.definitions:
                    for glyph in markClassDef.glyphSet():
                        classes[glyph] = 3
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
        sets = []
        for glyphs, id_ in sorted(self.markFilterSets_.items(),
                                 key=lambda item: item[1]):
            sets.append(glyphs)
        return otl.buildMarkGlyphSetsDef(sets, self.glyphMap)

    def buildLookups_(self, tag):
        assert tag in ('GPOS', 'GSUB'), tag
        for lookup in self.lookups_:
            lookup.lookup_index = None
        lookups = []
        for lookup in self.lookups_:
            if lookup.table != tag:
                continue
            lookup.lookup_index = len(lookups)
            lookups.append(lookup)
        return [l.build() for l in lookups]

    def makeTable(self, tag):
        table = getattr(otTables, tag, None)()
        table.Version = 0x00010000
        table.ScriptList = otTables.ScriptList()
        table.ScriptList.ScriptRecord = []
        table.FeatureList = otTables.FeatureList()
        table.FeatureList.FeatureRecord = []
        table.LookupList = otTables.LookupList()
        table.LookupList.Lookup = self.buildLookups_(tag)

        # Build a table for mapping (tag, lookup_indices) to feature_index.
        # For example, ('liga', (2,3,7)) --> 23.
        feature_indices = {}
        required_feature_indices = {}  # ('latn', 'DEU') --> 23
        scripts = {}  # 'latn' --> {'DEU': [23, 24]} for feature #23,24
        # Sort the feature table by feature tag:
        # https://github.com/behdad/fonttools/issues/568
        sortFeatureTag = lambda f: (f[0][2], f[0][1], f[0][0], f[1])
        for key, lookups in sorted(self.features_.items(), key=sortFeatureTag):
            script, lang, feature_tag = key
            # l.lookup_index will be None when a lookup is not needed
            # for the table under construction. For example, substitution
            # rules will have no lookup_index while building GPOS tables.
            lookup_indices = tuple([l.lookup_index for l in lookups
                                    if l.lookup_index is not None])

            size_feature = (tag == "GPOS" and feature_tag == "size")
            if len(lookup_indices) == 0 and not size_feature:
                continue

            feature_key = (feature_tag, lookup_indices)
            feature_index = feature_indices.get(feature_key)
            if feature_index is None:
                feature_index = len(table.FeatureList.FeatureRecord)
                frec = otTables.FeatureRecord()
                frec.FeatureTag = feature_tag
                frec.Feature = otTables.Feature()
                frec.Feature.FeatureParams = self.buildFeatureParams(
                                                feature_tag)
                frec.Feature.LookupListIndex = list(lookup_indices)
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
        if script == "DFLT":
            if self.seen_non_DFLT_script_:
                raise FeatureLibError(
                    'languagesystems using the "DFLT" script tag must '
                    "precede all other languagesystems",
                    location
                )
        else:
            self.seen_non_DFLT_script_ = True
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
        self.script_ = 'DFLT'
        self.cur_lookup_ = None
        self.cur_feature_name_ = name
        self.lookupflag_ = 0
        self.lookupflag_markFilterSet_ = None
        if name == "aalt":
            self.aalt_location_ = location

    def end_feature(self):
        assert self.cur_feature_name_ is not None
        self.cur_feature_name_ = None
        self.language_systems = None
        self.cur_lookup_ = None
        self.lookupflag_ = 0
        self.lookupflag_markFilterSet_ = None

    def start_lookup_block(self, location, name):
        if name in self.named_lookups_:
            raise FeatureLibError(
                'Lookup "%s" has already been defined' % name, location)
        if self.cur_feature_name_ == "aalt":
            raise FeatureLibError(
                "Lookup blocks cannot be placed inside 'aalt' features; "
                "move it out, and then refer to it with a lookup statement",
                location)
        self.cur_lookup_name_ = name
        self.named_lookups_[name] = None
        self.cur_lookup_ = None
        self.lookupflag_ = 0
        self.lookupflag_markFilterSet_ = None

    def end_lookup_block(self):
        assert self.cur_lookup_name_ is not None
        self.cur_lookup_name_ = None
        self.cur_lookup_ = None
        self.lookupflag_ = 0
        self.lookupflag_markFilterSet_ = None

    def add_lookup_call(self, lookup_name):
        assert lookup_name in self.named_lookups_, lookup_name
        self.cur_lookup_ = None
        lookup = self.named_lookups_[lookup_name]
        self.add_lookup_to_feature_(lookup, self.cur_feature_name_)

    def set_font_revision(self, location, revision):
        self.fontRevision_ = revision

    def set_language(self, location, language, include_default, required):
        assert(len(language) == 4)
        if self.cur_feature_name_ in ('aalt', 'size'):
            raise FeatureLibError(
                "Language statements are not allowed "
                "within \"feature %s\"" % self.cur_feature_name_, location)
        self.cur_lookup_ = None

        key = (self.script_, language, self.cur_feature_name_)
        lookups = self.features_.get((key[0], 'dflt', key[2]))
        if (language == 'dflt' or include_default) and lookups:
            self.features_[key] = lookups[:]
        else:
            self.features_[key] = []
        self.language_systems = frozenset([(self.script_, language)])

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
        glyphs = frozenset(glyphs)
        id_ = self.markAttachClassID_.get(glyphs)
        if id_ is not None:
            return id_
        id_ = len(self.markAttachClassID_) + 1
        self.markAttachClassID_[glyphs] = id_
        for glyph in glyphs:
            if glyph in self.markAttach_:
                _, loc = self.markAttach_[glyph]
                raise FeatureLibError(
                    "Glyph %s already has been assigned "
                    "a MarkAttachmentType at %s:%d:%d" % (
                        glyph, loc[0], loc[1], loc[2]),
                    location)
            self.markAttach_[glyph] = (id_, location)
        return id_

    def getMarkFilterSet_(self, location, glyphs):
        glyphs = frozenset(glyphs)
        id_ = self.markFilterSets_.get(glyphs)
        if id_ is not None:
            return id_
        id_ = len(self.markFilterSets_)
        self.markFilterSets_[glyphs] = id_
        return id_

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
        if self.cur_feature_name_ == "aalt":
            alts = self.aalt_alternates_.setdefault(glyph, set())
            alts.update(replacement)
            return
        if prefix or suffix:
            chain = self.get_lookup_(location, ChainContextSubstBuilder)
            lookup = self.get_chained_lookup_(location, AlternateSubstBuilder)
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

    def add_featureName(self, tag):
        self.featureNames_.add(tag)

    def add_cv_parameter(self, tag):
        self.cv_parameters_.add(tag)

    def add_to_cv_num_named_params(self, tag):
        """Adds new items to self.cv_num_named_params_
        or increments the count of existing items."""
        if tag in self.cv_num_named_params_:
            self.cv_num_named_params_[tag] += 1
        else:
            self.cv_num_named_params_[tag] = 1

    def add_cv_character(self, character, tag):
        self.cv_characters_[tag].append(character)

    def set_base_axis(self, bases, scripts, vertical):
        if vertical:
            self.base_vert_axis_ = (bases, scripts)
        else:
            self.base_horiz_axis_ = (bases, scripts)

    def set_size_parameters(self, location, DesignSize, SubfamilyID,
                            RangeStart, RangeEnd):
        if self.cur_feature_name_ != 'size':
            raise FeatureLibError(
                "Parameters statements are not allowed "
                "within \"feature %s\"" % self.cur_feature_name_, location)
        self.size_parameters_ = [DesignSize, SubfamilyID, RangeStart, RangeEnd]
        for script, lang in self.language_systems:
            key = (script, lang, self.cur_feature_name_)
            self.features_.setdefault(key, [])

    def add_ligature_subst(self, location,
                           prefix, glyphs, suffix, replacement, forceChain):
        if prefix or suffix or forceChain:
            chain = self.get_lookup_(location, ChainContextSubstBuilder)
            lookup = self.get_chained_lookup_(location, LigatureSubstBuilder)
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
            chain = self.get_lookup_(location, ChainContextSubstBuilder)
            sub = self.get_chained_lookup_(location, MultipleSubstBuilder)
            sub.mapping[glyph] = replacements
            chain.substitutions.append((prefix, [{glyph}], suffix, [sub]))
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

    def add_single_subst(self, location, prefix, suffix, mapping, forceChain):
        if self.cur_feature_name_ == "aalt":
            for (from_glyph, to_glyph) in mapping.items():
                alts = self.aalt_alternates_.setdefault(from_glyph, set())
                alts.add(to_glyph)
            return
        if prefix or suffix or forceChain:
            self.add_single_subst_chained_(location, prefix, suffix, mapping)
            return
        lookup = self.get_lookup_(location, SingleSubstBuilder)
        for (from_glyph, to_glyph) in mapping.items():
            if from_glyph in lookup.mapping:
                raise FeatureLibError(
                    'Already defined rule for replacing glyph "%s" by "%s"' %
                    (from_glyph, lookup.mapping[from_glyph]),
                    location)
            lookup.mapping[from_glyph] = to_glyph

    def find_chainable_SingleSubst_(self, chain, glyphs):
        """Helper for add_single_subst_chained_()"""
        for _, _, _, substitutions in chain.substitutions:
            for sub in substitutions:
                if (isinstance(sub, SingleSubstBuilder) and
                        not any(g in glyphs for g in sub.mapping.keys())):
                    return sub
        return None

    def add_single_subst_chained_(self, location, prefix, suffix, mapping):
        # https://github.com/behdad/fonttools/issues/512
        chain = self.get_lookup_(location, ChainContextSubstBuilder)
        sub = self.find_chainable_SingleSubst_(chain, set(mapping.keys()))
        if sub is None:
            sub = self.get_chained_lookup_(location, SingleSubstBuilder)
        sub.mapping.update(mapping)
        chain.substitutions.append((prefix, [mapping.keys()], suffix, [sub]))

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
                    else:
                        existingMarkClass = lookupBuilder.marks[mark][0]
                        if markClass.name != existingMarkClass:
                            raise FeatureLibError(
                                "Glyph %s cannot be in both @%s and @%s" % (
                                    mark, existingMarkClass, markClass.name),
                                location)

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
        lookup = self.get_lookup_(location, PairPosBuilder)
        lookup.addClassPair(location, glyphclass1, value1, glyphclass2, value2)

    def add_subtable_break(self, location):
        if type(self.cur_lookup_) is not PairPosBuilder:
            raise FeatureLibError(
                'explicit "subtable" statement is intended for use with only '
                "Pair Adjustment Positioning Format 2 (i.e. pair class kerning)",
                location
            )
        lookup = self.get_lookup_(location, PairPosBuilder)
        lookup.add_subtable_break(location)

    def add_specific_pair_pos(self, location, glyph1, value1, glyph2, value2):
        lookup = self.get_lookup_(location, PairPosBuilder)
        lookup.addGlyphPair(location, glyph1, value1, glyph2, value2)

    def add_single_pos(self, location, prefix, suffix, pos, forceChain):
        if prefix or suffix or forceChain:
            self.add_single_pos_chained_(location, prefix, suffix, pos)
        else:
            lookup = self.get_lookup_(location, SinglePosBuilder)
            for glyphs, value in pos:
                for glyph in glyphs:
                    lookup.add_pos(location, glyph, value)

    def find_chainable_SinglePos_(self, lookups, glyphs, value):
        """Helper for add_single_pos_chained_()"""
        for look in lookups:
            if all(look.can_add(glyph, value) for glyph in glyphs):
                return look
        return None

    def add_single_pos_chained_(self, location, prefix, suffix, pos):
        # https://github.com/fonttools/fonttools/issues/514
        chain = self.get_lookup_(location, ChainContextPosBuilder)
        targets = []
        for _, _, _, lookups in chain.rules:
            for lookup in lookups:
                if isinstance(lookup, SinglePosBuilder):
                    targets.append(lookup)
        subs = []
        for glyphs, value in pos:
            if value is None:
                subs.append(None)
                continue
            otValue, _ = makeOpenTypeValueRecord(value, pairPosContext=False)
            sub = self.find_chainable_SinglePos_(targets, glyphs, otValue)
            if sub is None:
                sub = self.get_chained_lookup_(location, SinglePosBuilder)
                targets.append(sub)
            for glyph in glyphs:
                sub.add_pos(location, glyph, value)
            subs.append(sub)
        assert len(pos) == len(subs), (pos, subs)
        chain.rules.append(
            (prefix, [g for g, v in pos], suffix, subs))

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

    def add_name_record(self, location, nameID, platformID, platEncID,
                        langID, string):
        self.names_.append([nameID, platformID, platEncID, langID, string])

    def add_os2_field(self, key, value):
        self.os2_[key] = value

    def add_hhea_field(self, key, value):
        self.hhea_[key] = value

    def add_vhea_field(self, key, value):
        self.vhea_[key] = value


def makeOpenTypeAnchor(anchor):
    """ast.Anchor --> otTables.Anchor"""
    if anchor is None:
        return None
    deviceX, deviceY = None, None
    if anchor.xDeviceTable is not None:
        deviceX = otl.buildDevice(dict(anchor.xDeviceTable))
    if anchor.yDeviceTable is not None:
        deviceY = otl.buildDevice(dict(anchor.yDeviceTable))
    return otl.buildAnchor(anchor.x, anchor.y, anchor.contourpoint,
                           deviceX, deviceY)


_VALUEREC_ATTRS = {
    name[0].lower() + name[1:]: (name, isDevice)
    for _, name, isDevice, _ in otBase.valueRecordFormat
    if not name.startswith("Reserved")
}


def makeOpenTypeValueRecord(v, pairPosContext):
    """ast.ValueRecord --> (otBase.ValueRecord, int ValueFormat)"""
    if v is None:
        return None, 0

    vr = {}
    for astName, (otName, isDevice) in _VALUEREC_ATTRS.items():
        val = getattr(v, astName, None)
        if val:
            vr[otName] = otl.buildDevice(dict(val)) if isDevice else val
    if pairPosContext and not vr:
        vr = {"YAdvance": 0} if v.vertical else {"XAdvance": 0}
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
        return otl.buildLookup(subtables, self.lookupflag, self.markFilterSet)

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


class AlternateSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 3)
        self.alternates = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.alternates == other.alternates)

    def build(self):
        subtable = otl.buildAlternateSubstSubtable(self.alternates)
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
        subtable = otl.buildLigatureSubstSubtable(self.ligatures)
        return self.buildLookup_([subtable])


class MultipleSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 2)
        self.mapping = {}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        subtable = otl.buildMultipleSubstSubtable(self.mapping)
        return self.buildLookup_([subtable])


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
        st = otl.buildCursivePosSubtable(self.attachments, self.glyphMap)
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
        markClasses = self.buildMarkClasses_(self.marks)
        marks = {mark: (markClasses[mc], anchor)
                 for mark, (mc, anchor) in self.marks.items()}
        bases = {}
        for glyph, anchors in self.bases.items():
            bases[glyph] = {markClasses[mc]: anchor
                            for (mc, anchor) in anchors.items()}
        subtables = otl.buildMarkBasePos(marks, bases, self.glyphMap)
        return self.buildLookup_(subtables)


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
        markClasses = self.buildMarkClasses_(self.marks)
        marks = {mark: (markClasses[mc], anchor)
                 for mark, (mc, anchor) in self.marks.items()}
        ligs = {}
        for lig, components in self.ligatures.items():
            ligs[lig] = []
            for c in components:
                ligs[lig].append({markClasses[mc]: a for mc, a in c.items()})
        subtables = otl.buildMarkLigPos(marks, ligs, self.glyphMap)
        return self.buildLookup_(subtables)


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
        markClasses = self.buildMarkClasses_(self.marks)
        markClassList = sorted(markClasses.keys(), key=markClasses.get)
        marks = {mark: (markClasses[mc], anchor)
                 for mark, (mc, anchor) in self.marks.items()}

        st = otTables.MarkMarkPos()
        st.Format = 1
        st.ClassCount = len(markClasses)
        st.Mark1Coverage = otl.buildCoverage(marks, self.glyphMap)
        st.Mark2Coverage = otl.buildCoverage(self.baseMarks, self.glyphMap)
        st.Mark1Array = otl.buildMarkArray(marks, self.glyphMap)
        st.Mark2Array = otTables.Mark2Array()
        st.Mark2Array.Mark2Count = len(st.Mark2Coverage.glyphs)
        st.Mark2Array.Mark2Record = []
        for base in st.Mark2Coverage.glyphs:
            anchors = [self.baseMarks[base].get(mc) for mc in markClassList]
            st.Mark2Array.Mark2Record.append(otl.buildMark2Record(anchors))
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
        subtable = otl.buildSingleSubstSubtable(self.mapping)
        return self.buildLookup_([subtable])

    def getAlternateGlyphs(self):
        return {glyph: set([repl]) for glyph, repl in self.mapping.items()}


class ClassPairPosSubtableBuilder(object):
    def __init__(self, builder, valueFormat1, valueFormat2):
        self.builder_ = builder
        self.classDef1_, self.classDef2_ = None, None
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
            self.classDef1_ = otl.ClassDefBuilder(useClass0=True)
            self.classDef2_ = otl.ClassDefBuilder(useClass0=False)
            self.values_ = {}
        self.classDef1_.add(gc1)
        self.classDef2_.add(gc2)
        self.values_[(gc1, gc2)] = (value1, value2)

    def addSubtableBreak(self):
        self.forceSubtableBreak_ = True

    def subtables(self):
        self.flush_()
        return self.subtables_

    def flush_(self):
        if self.classDef1_ is None or self.classDef2_ is None:
            return
        st = otl.buildPairPosClassesSubtable(self.values_,
                                             self.builder_.glyphMap)
        if st.Coverage is None:
            return
        self.subtables_.append(st)
        self.forceSubtableBreak_ = False


class PairPosBuilder(LookupBuilder):
    SUBTABLE_BREAK_ = "SUBTABLE_BREAK"

    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 2)
        self.pairs = []  # [(gc1, value1, gc2, value2)*]
        self.glyphPairs = {}  # (glyph1, glyph2) --> (value1, value2)
        self.locations = {}  # (gc1, gc2) --> (filepath, line, column)

    def addClassPair(self, location, glyphclass1, value1, glyphclass2, value2):
        self.pairs.append((glyphclass1, value1, glyphclass2, value2))

    def addGlyphPair(self, location, glyph1, value1, glyph2, value2):
        key = (glyph1, glyph2)
        oldValue = self.glyphPairs.get(key, None)
        if oldValue is not None:
            # the Feature File spec explicitly allows specific pairs generated
            # by an 'enum' rule to be overridden by preceding single pairs
            otherLoc = self.locations[key]
            log.debug(
                'Already defined position for pair %s %s at %s:%d:%d; '
                'choosing the first value',
                glyph1, glyph2, otherLoc[0], otherLoc[1], otherLoc[2])
        else:
            val1, _ = makeOpenTypeValueRecord(value1, pairPosContext=True)
            val2, _ = makeOpenTypeValueRecord(value2, pairPosContext=True)
            self.glyphPairs[key] = (val1, val2)
            self.locations[key] = location

    def add_subtable_break(self, location):
        self.pairs.append((self.SUBTABLE_BREAK_, self.SUBTABLE_BREAK_,
                           self.SUBTABLE_BREAK_, self.SUBTABLE_BREAK_))

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.glyphPairs == other.glyphPairs and
                self.pairs == other.pairs)

    def build(self):
        builders = {}
        builder = None
        for glyphclass1, value1, glyphclass2, value2 in self.pairs:
            if glyphclass1 is self.SUBTABLE_BREAK_:
                if builder is not None:
                    builder.addSubtableBreak()
                continue
            val1, valFormat1 = makeOpenTypeValueRecord(
                value1, pairPosContext=True)
            val2, valFormat2 = makeOpenTypeValueRecord(
                value2, pairPosContext=True)
            builder = builders.get((valFormat1, valFormat2))
            if builder is None:
                builder = ClassPairPosSubtableBuilder(
                    self, valFormat1, valFormat2)
                builders[(valFormat1, valFormat2)] = builder
            builder.addPair(glyphclass1, val1, glyphclass2, val2)
        subtables = []
        if self.glyphPairs:
            subtables.extend(
                otl.buildPairPosGlyphs(self.glyphPairs, self.glyphMap))
        for key in sorted(builders.keys()):
            subtables.extend(builders[key].subtables())
        return self.buildLookup_(subtables)


class SinglePosBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GPOS', 1)
        self.locations = {}  # glyph -> (filename, line, column)
        self.mapping = {}  # glyph -> otTables.ValueRecord

    def add_pos(self, location, glyph, valueRecord):
        otValueRecord, _ = makeOpenTypeValueRecord(
            valueRecord, pairPosContext=False)
        if not self.can_add(glyph, otValueRecord):
            otherLoc = self.locations[glyph]
            raise FeatureLibError(
                'Already defined different position for glyph "%s" at %s:%d:%d'
                % (glyph, otherLoc[0], otherLoc[1], otherLoc[2]),
                location)
        if otValueRecord:
            self.mapping[glyph] = otValueRecord
        self.locations[glyph] = location

    def can_add(self, glyph, value):
        assert isinstance(value, otl.ValueRecord)
        curValue = self.mapping.get(glyph)
        return curValue is None or curValue == value

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        subtables = otl.buildSinglePos(self.mapping, self.glyphMap)
        return self.buildLookup_(subtables)
