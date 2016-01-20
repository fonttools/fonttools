#! /usr/bin/env python
# coding: utf-8

from __future__ import print_function
import sys
from collections import OrderedDict
from functools import wraps
import fontTools.ttLib as ttLib


# GPOS and GSUB

def lookupflag(state, value):
    # format B: "lookupflag 6;"
    # There's apparently format B wich is just the raw number. We could
    # just output the lookupflag as it.
    # However, if there is information about the markAttachClassID or
    # UseMarkFilteringSet this approach is bound to fail, because markAttachClassID
    # depends on the font compiler.

    # format A: "lookupflag RightToLeft MarkAttachmentType @M;"
    # here is the official LookupFlag bit enumeration:
    # https://www.microsoft.com/typography/otspec/chapter2.htm
    flags = {
        "RightToLeft": 1, "IgnoreBaseGlyphs": 2,
        "IgnoreLigatures": 4, "IgnoreMarks": 8
    }
    # flags.UseMarkFilteringSet = 16 # == 0x10 means: this has a MarkFilterSet
    # I don't have a MarkFilterSet in the lookups right now.
    # FIXME: I have used this in a GSUB lookup
    # So no good example for it to implement, thus:
    assert not (value & 0x10), 'MarkFilterSet is not yet implemented'

    lookupflags = []
    for flag, bit in flags.items():
        if value & bit:
            lookupflags.append(flag)

    # A markAttachmentClass ID is set to the second Byte: (markAttachClass << 8)
    # The markAttachClass ID is never 0: "All glyphs not assigned to a class
    # fall into Class 0"
    # see https://www.microsoft.com/typography/otspec/chapter2.htm
    markAttachClassID = value >> 8
    if markAttachClassID:
        # at this point we need GDEF, reading from MarkAttachClassDef
        markAttachClassName = state.registerMarkAttachClassGetName(markAttachClassID)
        lookupflags.append('MarkAttachmentType @{0}'.format(markAttachClassName))

    return 'lookupflag {0};'.format(' '.join(lookupflags))

def lookupNotImplementedGPOS(state, lookup):
    return lookupNotImplemented(state, lookup, lookupTypesGPOS, 'GPOS');

def lookupNotImplementedGSUB(state, lookup):
    return lookupNotImplemented(state, lookup, lookupTypesGSUB, 'GSUB')

def lookupNotImplemented(state, lookup, lookupTypes, tableTag):
    return (False, '# Not implemented: {3} lookup-type {0} {1}.'
                .format(lookup.LookupType, lookupTypes[lookup.LookupType][2], tableTag))


def formatAnchor(anchorClassPrefix, classId, anchor):
    anchorType = type(anchor).__name__
    anchorFormat = ({
        'MarkAnchor': '<anchor {1} {2}> {0}'
      , 'BaseAnchor': '<anchor {1} {2}> mark {0}'
      , 'LigatureAnchor': '<anchor {1} {2}> mark {0}'
      , 'Mark2Anchor': '<anchor {1} {2}> mark {0}'
    })[anchorType]

    assert anchor.Format == 1, '{0} Format {1} is not supported yet' \
                        .format(anchorType, anchor.Format)
    anchorClass = '@{0}_{1}'.format(anchorClassPrefix, classId)
    return anchorFormat.format(anchorClass, anchor.XCoordinate, anchor.YCoordinate)


def formatMarkArray(markArray, markCoverage, anchorClassPrefix):
    # markClass [uni064D ] <anchor 0 -163> @Anchor0;
    lines = []
    id2Name = markCoverage.glyphs
    definitions = OrderedDict()
    for i, markRecord in enumerate(markArray.MarkRecord):
        value = formatAnchor(anchorClassPrefix, markRecord.Class, markRecord.MarkAnchor)
        if value not in definitions:
            definitions[value] = []
        definitions[value].append(id2Name[i])
    for value, glyphs in definitions.items():
        lines.append('markClass [ {1} ] {0};'.format(value, ' '.join(glyphs)))
    return lines

def formatBaseArray(baseArray, baseCoverage, anchorClassPrefix):
    # pos base [uni0639 uni063A uni06A0 uni06FC uni075D uni075E uni075F ]
    #     <anchor 293 -48> mark @Anchor2
    #     <anchor 243 406> mark @Anchor1
    #     <anchor 290 -369> mark @Anchor0;
    lines = []
    id2Name = baseCoverage.glyphs
    definitions = OrderedDict()
    for i, baseRecord in enumerate(baseArray.BaseRecord):
        value = tuple([formatAnchor(anchorClassPrefix, classId, anchor)
                for classId, anchor in enumerate(baseRecord.BaseAnchor)])
        if value not in definitions:
            definitions[value] = []
        definitions[value].append(id2Name[i])
    for value, glyphs in definitions.items():
        lines.append('pos base [ {1} ]\n    {0};'
                            .format('\n    '.join(value), ' '.join(glyphs)))
    return lines

def formatLigatureArray(ligatureArray, ligatureCoverage, anchorClassPrefix):
    # pos ligature uni06B80627.isol
    #     <anchor 335 -46> mark @Anchor4
    #     <anchor 294 557> mark @Anchor3
    #     ligComponent
    #     <anchor 129 -42> mark @Anchor4
    #     <anchor 49 523> mark @Anchor3;
    lines = []
    id2Name = ligatureCoverage.glyphs
    definitions = OrderedDict()
    for i, ligatureAttach in enumerate(ligatureArray.LigatureAttach):
        value = []
        for componentRecord in ligatureAttach.ComponentRecord:
            if len(value):
                value.append('ligComponent') # separator
            value += [formatAnchor(anchorClassPrefix, classId, anchor) for classId, anchor
                                in enumerate(componentRecord.LigatureAnchor)]
        value = tuple(value)
        if value not in definitions:
            definitions[value] = []
        definitions[value].append(id2Name[i])
    for value, glyphs in definitions.items():
        lines.append('pos ligature [ {1} ]\n    {0};'
                            .format('\n    '.join(value), ' '.join(glyphs)))
    return lines

def formatMark2Array(mark2Array, mark2Coverage, anchorClassPrefix):
    # pos mark [uni0610 ]
    #     <anchor 1 876> mark @Anchor0;
    lines = []
    id2Name = mark2Coverage.glyphs
    definitions = OrderedDict()
    for i, mark2Record in enumerate(mark2Array.Mark2Record):
        value = tuple([formatAnchor(anchorClassPrefix, classId, anchor)
                for classId, anchor in enumerate(mark2Record.Mark2Anchor)])
        if value not in definitions:
            definitions[value] = []
        definitions[value].append(id2Name[i])
    for value, glyphs in definitions.items():
        lines.append('pos mark [ {1} ]\n    {0};'.format('\n    '.join(value), ' '.join(glyphs)))
    return lines

def lookupMarkToBase(state, lookup):
    # I did not research if this happens ever in this context though
    # but since "All subtables in a lookup must be of the same LookupType
    # This would be easy to implement. The question is: do we need to separate
    # these explicitly using the "subtable;" statement? I think not, about "subtable;":
    # "This is intended for use with only Pair Adjustment Positioning Format 2
    # (i.e. pair class kerning)"
    # see: http://www.adobe.com/devnet/opentype/afdko/topic_feature_file_syntax.html#4.g
    assert lookup.SubTableCount == 1, 'More than one subtables per lookup '\
                                                    + 'is not supported.'

    subtable = lookup.SubTable[0] # fontTools.ttLib.tables.otTables.MarkBasePos

    assert subtable.Format == 1, 'Unknown subtable format {0} for lookup-type {1} {2}.' \
                                 .format( subtable.Format
                                        , subtable.LookupType
                                        , lookupTypesGPOS[subtable.LookupType][2])
    anchorClassPrefix = state.getUID('Anchor_')
    lines = [ lookupflag(state, lookup.LookupFlag) ] \
            + formatMarkArray(subtable.MarkArray, subtable.MarkCoverage, anchorClassPrefix) \
            + formatBaseArray(subtable.BaseArray, subtable.BaseCoverage, anchorClassPrefix)

    return (True, '  {0}'.format('\n  '.join(lines)))

def lookupMarkToLigature(state, lookup):
    # See comment in def lookupMarkToBase
    assert lookup.SubTableCount == 1, 'More than one subtables per lookup '\
                                                    + 'is not supported.'

    subtable = lookup.SubTable[0] # fontTools.ttLib.tables.otTables.MarkLigPos

    assert subtable.Format == 1, 'Unknown subtable format {0} for lookup-type {1} {2}.' \
                                 .format( subtable.Format
                                        , subtable.LookupType
                                        , lookupTypesGPOS[subtable.LookupType][2])
    anchorClassPrefix = state.getUID('Anchor_')
    lines = [ lookupflag(state, lookup.LookupFlag) ] \
            + formatMarkArray(subtable.MarkArray, subtable.MarkCoverage, anchorClassPrefix) \
            + formatLigatureArray(subtable.LigatureArray, subtable.LigatureCoverage, anchorClassPrefix)

    return (True, '  {0}'.format('\n  '.join(lines)))

def lookupMarkToMark(state, lookup):
    # See comment in def lookupMarkToBase
    assert lookup.SubTableCount == 1, 'More than one subtables per lookup '\
                                                    + 'is not supported.'

    subtable = lookup.SubTable[0] # fontTools.ttLib.tables.otTables.MarkMarkPos

    assert subtable.Format == 1, 'Unknown subtable format {0} for lookup-type {1} {2}.' \
                                 .format( subtable.Format
                                        , subtable.LookupType
                                        , lookupTypesGPOS[subtable.LookupType][2])
    anchorClassPrefix = state.getUID('Anchor_')
    lines = [ lookupflag(state, lookup.LookupFlag) ] \
            + formatMarkArray(subtable.Mark1Array, subtable.Mark1Coverage, anchorClassPrefix) \
            + formatMark2Array(subtable.Mark2Array, subtable.Mark2Coverage, anchorClassPrefix)

    return (True, '  {0}'.format('\n  '.join(lines)))

lookupTypesGPOS = {
    # enum from https://www.microsoft.com/typography/otspec/gpos.htm
    1: (lookupNotImplementedGPOS, 'singlePos', 'Single adjustment' ,'Adjust position of a single glyph'),
    2: (lookupNotImplementedGPOS, 'pairPos', 'Pair adjustment' ,'Adjust position of a pair of glyphs'),
    3: (lookupNotImplementedGPOS, 'cursiveAttachment', 'Cursive attachment' ,'Attach cursive glyphs'),
    4: (lookupMarkToBase, 'markToBase', 'MarkToBase attachment' ,'Attach a combining mark to a base glyph'),
    5: (lookupMarkToLigature, 'markToLigature', 'MarkToLigature attachment' ,'Attach a combining mark to a ligature'),
    6: (lookupMarkToMark, 'markToMark', 'MarkToMark attachment' ,'Attach a combining mark to another mark'),
    7: (lookupNotImplementedGPOS, 'contextPos', 'Context positioning' ,'Position one or more glyphs in context'),
    8: (lookupNotImplementedGPOS, 'chainedContextPos','Chained Context positioning' ,'Position one or more glyphs in chained context'),
    9: (lookupNotImplementedGPOS, 'extensionPos', 'Extension positioning' ,'Extension mechanism for other positionings'),
}

lookupTypesGSUB = {
    # enum from https://www.microsoft.com/typography/otspec/gsub.htm
    1: (lookupNotImplementedGSUB, 'singleSub', 'Single', 'Replace one glyph with one glyph'),
    2: (lookupNotImplementedGSUB, 'multipleSub', 'Multiple', 'Replace one glyph with more than one glyph'),
    3: (lookupNotImplementedGSUB, 'alternateSub', 'Alternate', 'Replace one glyph with one of many glyphs'),
    4: (lookupNotImplementedGSUB, 'ligatureSub', 'Ligature', 'Replace multiple glyphs with one glyph'),
    5: (lookupNotImplementedGSUB, 'contextSub', 'Context', 'Replace one or more glyphs in context'),
    6: (lookupNotImplementedGSUB, 'chainingContextSub', 'Chaining Context', 'Replace one or more glyphs in chained context'),
    7: (lookupNotImplementedGSUB, 'extensionSub', 'Extension Substitution', 'Extension mechanism for other substitutions (i.e. this excludes the Extension type substitution itself)'),
    8: (lookupNotImplementedGSUB, 'reverseChainingContextSingleSub', 'Reverse chaining context single', 'Applied in reverse order, replace single glyph in chaining context'),
}



def lookup(state, lookup, lookupTypes):
    # lookup is fontTools.ttLib.tables.otTables.Lookup
    if lookup.LookupType not in lookupTypes:
        raise ValueError('Lookup type "{0}" is not defined'.format(lookup.LookupType))
    func = lookupTypes[lookup.LookupType][0]
    return func(state, lookup)

def lookupGPOS(state, lookup):
    return lookups(state, lookup, lookupTypesGPOS)

def lookupGSUB(state, lookup):
    return lookups(state, lookup, lookupTypesGSUB)


# it looks like we don't need to use languagsystem at all, all
# script/language tags in features should work without registering the features
# first. On the other hand, it would do no harm, since all rules in a feature
# that follow the script + language definitions end up in defined places anyways
# If for our case (with very verbose script + language usage) it is not needed
# to define the used languagsystem first, that's one dependency less. And
# the languagesystems can be filtered withoud further consequences. Otherwise
# filtering a languagesystem would be the same as filtering a language, hence
# it can be just one of both that is available to apply filters.
# Lastly, if we don't want the languagesystems to appear but don't filter it
# either, because of the consequences it has, the answer would be to silence
# them!
# TODO: find out if in order to use a script/language definition in a feature
# the languagesystem has to be defined (by not defining the languagesystem
# and trying it out):
# AFDKO makeotf issues a warning but does not fail (as it seems):
# makeotfexe [WARNING] <Mirza-Regular> [internal] Feature block seen before any
# language system statement.  You should place languagesystem statements before any
# feature definition [../Sources/features.fea 25]
#
# well, but we "should" do it. I conclude that we'll do it but there's no
# hard dependency on it. In the here generated case, all features are fully
# specified with the script/lang definitions, no room for uncertainty.
# ALSO, in my file [../Sources/features.fea 25] on Line 25 is a lookup
# definition, not a feature definition, makeotf is a bit inaccurate here,
# which may give us a hint about the importance of the advice (WARNING! lol)

def languageSystems(state, gpos):

    FIXME TODO

    for scriptRecord in gpos.table.ScriptList.ScriptRecord:
        # https://www.microsoft.com/typography/otspec/chapter2.htm
        scriptRecord.ScriptTag # DFLT | arab

        # If a Script table with the script tag 'DFLT' (default) is present
        # in the ScriptList table, it must have a non-NULL DefaultLangSys
        # and LangSysCount must be equal to 0. The 'DFLT' Script table should
        # be used if there is not an explicit entry for the script being formatted.

        # DefaultLangSys is an equivalent of LangSys
        scriptRecord.Script.DefaultLangSys # may be NULL

        # scriptRecord.Script.LangSysRecord is an array of
        # LangSysRecords-listed alphabetically by LangSysTag
        for langSysRecord in scriptRecord.Script.LangSysRecord:
            langSysRecord.LangSysTag # URD DEU ARA
            langSysRecord.LangSys.FeatureIndex # [2,5]

# GDEF

def classeDefs(classDefs, classNames):
    lines = []
    classes = OrderedDict
    for name, i in classDefs.items():
        if i not in classNames:
            continue;
        className = classNames[i]
        if className not in classes:
            classes[className] = []
        classes[className].append(name)
    for className in classes:
        lines.append('@{0} = [ {1} ];'.format(className, ' '.join(classes[className])))
    return lines

def classFromCoverage(coverage, name):
    return '@{0} = [ {1} ]'.format(name, ' '.join(coverage))

def attachList(AttachList):
        for idx, glyph in enumerate(AttachList.Coverage.glyphs):
            attachmentPoints = AttachList.AttachPoint[idx]
            for point in attachmentPoints.PointIndex:
                lines.append('  Attach {0} {1};', glyph, point)
    return lines;

def printGDEF(table, getStatus, getUniqueName, print=print)
    printTable, tableRequired = getStatus(table, False)
    if not printTable:
        return

    print('\n#### Table {0} ####\n'.format(table.tableTag))

    markAttachClassDefs = table.table.MarkAttachClassDef.classDefs
    markAttachClassIDs = set(markAttachClassDefs.values())
    classNames = {}
    for markAttachClassID in markAttachClassIDs:
        if markAttachClassID == 0: continue
        # ad-hoc type to make it selectable
        markAttachClassTuple = (markAttachmentClassDef, markAttachClassID)
        for required in (True, False)
            printClass, _ = getStatus(markAttachClassTuple, required):
            if printClass:
                classNames[markAttachClassID] = getUniqueName(markAttachClassID, 'MarkAttachClass')
                break;
    if len(classNames):
        lines = classeDefs(markAttachClassDefs, classNames):
        print('# GDEF Mark Attachment Classes:\n')
        print('\n'.join(lines))

    if hasattr(table.table, 'MarkGlyphSetsDef'):
        lines = []
        for idx, coverage in enumerate(table.table.MarkGlyphSetsDef.Coverage):
            for required in (True, False):
                printClass, _ = getStatus(coverage, required)
                if printClass:
                    name = getUniqueName(idx, 'UseMarkFilteringSet')
                    lines.append(classFromCoverage(coverage, name))
                    break
        if len(lines):
            lines = classeDefs(markAttachClassDefs, classNames):
            print('# GDEF Mark Filtering Sets:\n')
            print('\n'.join(lines))

    gdefLines = []
    if table.table.AttachList is not None:
        for required in (True, False):
            printAttachList, _ = getStatus(table.table.AttachList, required)
            if printAttachList:
                lines = attachList(table.table.AttachList)
                break
        gdefLines.append('')
        gdefLines += lines


    MISSING:
    self.validateLigCaretList
    table.table.LigCaretList
    see http://www.adobe.com/devnet/opentype/afdko/topic_feature_file_syntax.html#9.b


    if len(gdefLines):
        print('table {0} {'.format(table.tableTag))
        print('\n'.join(gdefLines))
        print('} {0};\n'.format(table.tableTag))

def printLookups(state, table, getStatus, getUniqueName, print=print)
    lookupNames = {}
    lookupTypes = {'GPOS': lookupTypesGPOS, 'GSUB': lookupTypesGSUB}[table.tableTag]
    for lookupIdx, lookup in enumerate(table.table.LookupList.Lookup)
        for required in (False, True):
            printLookup, _ = getStatus(lookup, required)
            if not printLookup: continue
                # FIXME: success can temporary be False until all lookup
                # types have been implemented. Then remove it
                # see also printFeatures
                success, body = lookup(state, lookup, lookupTypes)
                nameBase = lookupTypes[lookup.LookupType][1]
                uniqueName = getUniqueName(nameBase, lookupIdx)
                if !success:
                    uniqueName = '# lookup type not implemented for {0}'.format(uniqueName);
                    print(body)
                else
                    print('lookup {0} {{\n{1}\n}} {0};'.format(uniqueName, body))
                lookupNames[lookupIdx] = uniqueName
                print();
            break # printing it once is enough
        return lookupNames

def printFeatures(features, lookupNames, indentation='  ', print=print):
    for featureTag, scripts in features.items():
        print('feature {0} {'.format(featureTag));
        for scriptTag, languages in scripts.items():
            print('{1}script {0};'.format(scriptTag, 1 * indentation))
            for langTag, lookups in languages.items():
                print('{1}language {0};'.format(langTag, 2 * indentation))
                for lookupIdx in lookups:
                    lookupName = lookupNames[lookupIdx]
                    if lookupName[0] === '#':
                        # FIXME: we skip some not yet implemented lookups
                        # and print comments instead.
                        # Remove this when all lookups have been implemented
                        # see also printLookups
                        print('{1}{0}'.format(lookupNames[lookupIdx], 3 * indentation))
                    else
                        print('{1}lookup{0};'.format(lookupName, 3 * indentation))
        print '} {0};'.format(feature);

def _prepareFeatureLangSys(langTag, langSys, table, features, scriptTag, scriptRequired, getStatus):
    printLang, langRequired = getStatus((langTag, langSys), scriptRequired)
    if not printLang: return
    for featureIdx in langSys.FeatureIndex:
        featureRecord = table.table.FeatureList.featureRecord[featureIdx]
        printFeature, featureRequired = getStatus(featureRecord, langRequired)
        if not printFeature: continue

        featureTag = featureRecord.FeatureTag
        scripts = features.get(featureTag, None)
        if scripts is None:
            scripts = features[featureTag] = OrderedDict()

        languages = scripts.get(scriptTag, None)
        if languages is None:
            languages = scripts[scriptTag] = OrderedDict()

        lookups = script.get(langTag, None)
        if lookups is None:
            lookups = script[langTag] = []

        for lookupIdx in featureRecord.Feature.LookupListIndex:
            lookup = table.table.LookupList.Lookup[lookupIdx]
            printLookup, _ = getStatus(lookup, featureRequired)
            if printLookup:
                lookups.append(lookupIdx)

def prepareFeatures(tableRequired, table, lookupNames, getStatus):
    features = OrderedDict()
    for scriptRecord in table.table.ScriptList.ScriptRecord:
        printScript, scriptRequired = getStatus(scriptRecord, tableRequired)
        if not printScript:
            continue
        scriptTag = scriptRecord.ScriptTag
        _repFeaLangSysArgs = (table, features, scriptTag, scriptRequired, getStatus)
        if scriptRecord.Script.DefaultLangSys is not None:
            _prepareFeatureLangSys('dflt', scriptRecord.Script.DefaultLangSys, *_repFeaLangSysArgs)
        for langSysRecord in scriptRecord.Script.LangSysRecord:
            _prepareFeatureLangSys(langSysRecord.LangSysTag, langSysRecord.LangSys, *_repFeaLangSysArgs)
    return features

def printCommonGTable(table, getStatus, getUniqueName, print=print):
    printTable, tableRequired = getStatus(table, False)
    if not printTable:
            return

    print('\n#### Table {0} ####\n'.format(table.tableTag))

    print('# {0} Lookups\n\n'.format(table.tableTag))
    lookupNames = printLookups(state, table, getStatus, getUniqueName, print=print)

    print('# {0} Features:'.format(table.tableTag))
    features = prepareFeatures(tableRequired, table, getStatus)
    printFeatures(features, lookupNames, print=print)

def printingCode(state, font, getStatus, getUniqueName, print=print):
    tables = OrderedDict()

    if 'GDEF' in font:
        gdef = font['GDEF']
        printGDEF(gdef, getStatus, getUniqueName, print=print)

    for tableTag in ('GPOS', 'GSUB'):
        if tableTag not in font:
            continue
        table = font[tableTag]
        printCommonGTable(table, getStatus, getUniqueName, print=print)



# these operations should set the items state to
# yes, no (or Maybe, which is not registered)
# we will in another pass render the actual lookup tables if they are "yes"
# or if they are "Maybe" and getRequestStatus(['GPOS', 'lookup', lookup.typeName])
# returns true
# So, now, with this done the rest should be easy!
# above pseudo rendering code can ask at each stage if it should render the
# item, by asking the registry!

class SelectExports(object):
    def __init__(self, font, getRequestStatus):
        self.getRequestStatus = getRequestStatus
        self.font = font
        self.registry = {}
        self._transactions = []

    @staticmethod
    def register(func):
        @wraps(func)
        def wrapper(self, item, required, *args, **kwargs):
            key = (item, required)
            registered = self.registry.get(key, None)
            if registered is not None:
                return registered
            # maybe it has been registered prior to this transaction
            for registry in reversed(self._transactions):
                registered = registry.get(key, None)
                if registered is not None:
                    return registered
            result = self.registry[key] = func(self, item, required, *args, **kwargs)
            return result
        return wrapper

    def _startTransaction(self):
        self._transactions.append(self.registrations)
        self.registrations = {}

    def _commitTransaction(self):
        registrations = self._transactions.pop()
        self.registrations.update(registrations)
        self.registrations = registrations;

    def _rollbackTransaction(self):
        self.registrations = self._transactions.pop()

    def _validateSimpleEntry(self, selector, parentRequired):
        requestStatus = self.getRequestStatus(*selector)
        required = parentRequired or requestStatus
        result = requestStatus is not False and (requestStatus or required) is True
        return (result, required)

    # GDEF

    @register
    def validateMarkGlyphClassDef(self, glyphClassDef, parentRequired):
        selector = (table.tableTag, 'glyphClassDef')
        return _validateSimpleEntry(selector, parentRequired)

    @register
    def validateAttachList(self, attachList, parentRequired, table):
        selector = (table.tableTag, 'attachList')
        return _validateSimpleEntry(selector, parentRequired)

    @register
    def validateLigCaretList(self, ligCaretList, parentRequired, table):
        selector = (table.tableTag, 'ligCaretList')
        return _validateSimpleEntry(selector, parentRequired)

    @register
    def validateMarkAttachmentClass(self, markAttachClassTuple, parentRequired, table):
        selector = (table.tableTag, 'markAttachClasses')
        return _validateSimpleEntry(selector, parentRequired)

    @register
    def validateMarkAttachmentClassDef(self, markAttachmentClassDef, parentRequired, table):
        # This can't be (de-)selected directly so here's no selector check.
        # But, it's children can be selected using "GDEF markAttachClasses"
        # Which has the same effect. This way we can have the dependants
        # select just the required classes. See validateLookup
        childCount = 0
        markAttachClassIDs = set(gdef.table.MarkAttachClassDef.classDefs.values())
        for markAttachClassID in markAttachClassIDs:
            # "All glyphs not assigned to a class fall into Class 0."
            # Thus there's no meaning in outputting this if it is ever present
            # It can't be referenced by a LookupFlag.
            if markAttachClassID == 0: continue
            # ad-hoc type to make it selectable
            markAttachClassTuple = (markAttachmentClassDef, markAttachClassID)
            success, _ = self.validateMarkAttachmentClass(markAttachClassTuple, required, gdef):
            if success:
                childCount += 1
        return (childCount > 0, required)

    @register
    def validateMarkGlyphSet(self, markGlyphSet_Coverage, parentRequired, table):
        selector = (table.tableTag, 'markGlyphSets')
        return _validateSimpleEntry(selector, parentRequired)

    @register
    def validateMarkGlyphSetsDef(self, markGlyphSetsDef, parentRequired, table):
        # This can't be (de-)selected directly so here's no selector check.
        # But, it's children can be selected using "GDEF markGlyphSets"
        # which has the same effect. This way we can have the dependants
        # select just the required markSets. See validateLookup
        childCount = 0
        for coverage in markGlyphSetsDef.Coverage:
            success, _ = validateMarkGlyphSet(coverage, parentRequired, table)
            if success:
                childCount += 1
        return (childCount > 0, required)

    @register
    def validateGDEF(self, table, parentRequired):
        requestStatus = self.getRequestStatus(table.tableTag)
        required = parentRequired or requestStatus
        if requestStatus is False:
            return (False, required)

        # check all dependencies
        childCount = 0
        children = [
            self.validateMarkGlyphClassDef, table.table.GlyphClassDef
            self.validateAttachList, table.table.AttachList
            self.validateLigCaretList, table.table.LigCaretList
            self.validateMarkAttachmentClassDef, table.table.MarkAttachClassDef
        ]
        if hasattr(table.table, 'MarkGlyphSetsDef'):
            children.append((self.validateMarkGlyphSetsDef, table.table.MarkGlyphSetsDef))

        for validate, item in children:
            if item is None:
                continue
            success, _ = validate(item, required, table)
            if success:
                childCount += 1

        return (childCount > 0, required)

    # GPOS and GSUB
    @register
    def validateLookup(self, lookup, parentRequired, table):
        # it has not really a tag, so we make one up
        # gpos3 is GPOS LookupType 3
        # gsub2 is GSUB LookupType 2 etc
        class Invalidate: pass
        tag = '{0}{1}'.format(table.tableTag.lower(), lookup.LookypType);
        requestStatus = self.getRequestStatus(table.tableTag, 'lookup', tag)
        required = parentRequired or requestStatus
        if requestStatus is False or not required:
            return (False, required)
        # required is true, check dependencies:
        self._startTransaction()
        invalid = False
        # using try/catch so that the transaction can be finalized properly
        # via either commit or rollback
        try:
            # check the lookupFlag

            # 0x10 UseMarkFilteringSet
            if lookup.lookupFlag & 0x10:
                gdef = self.font['GDEF']
                coverage = gdef.table.MarkGlyphSetsDef.Coverage[lookup.MarkFilteringSet]
                success, _ = self.validateMarkGlyphSet(self, coverage, True, gdef)
                if !success:
                    raise Invalidation

            # MarkAttachmentType
            markAttachClassID = lookup.lookupFlag >> 8
            if markAttachClassID:
                gdef = self.font['GDEF']
                # a adhoc pseudo item, to enable outputting just the used
                # mark attachment classes
                markAttachClassTuple = (gdef.table.MarkAttachClassDef, markAttachClassID)
                success, _ = self.validateMarkAttachmentClass(markAttachClassTuple, required, gdef):
                if !success:
                    raise Invalidation

            # TODO/FIXME
            # Possible dependencies to other lookups:
            #     GSUB type 5 Context (format 5.1 5.2 5.3)
            #     GSUB type 6 Chaining Context (format 6.1 6.2 6.3)
            #     GPOS type 7 Context positioning (format 7.1 7.2 7.3)
            #     GPOS type 8 Chained Context positioning (format 7.1 7.2 7.3)
            #
            # GSUB contextuals: each of these have somewhere: an array of
            # SubstLookupRecord which has a LookupListIndex into the GSUB LookupList
            #
            # GPOS contextuals: each of these have somewhere: an array of
            # PosLookupRecord which has a LookupListIndex into the GPOS LookupList
            #
            # lookupList = table.table.LookupList.Lookup
        except Invalidation as e:
            invalid = True
        except Exception as e:
            invalid = True
            raise e
        finally
            if invalid:
                self._rollbackTransaction()
                return (False, True)
            self._commitTransaction()
            return (True, True)

    @register
    def validateFeatureRecord(self, featureRecord, parentRequired, table):
        requestStatus = self.getRequestStatus(table.tableTag, 'feature', featureRecord.FeatureTag)
        required = parentRequired or requestStatus
        if requestStatus is False:
            return (False, required)

        # check all dependencies
        childCount = 0
        for lookupIdx in featureRecord.Feature.LookupListIndex:
            # get the lookup from the lookupList
            lookup = table.table.LookupList.Lookup[lookupIdx]
            success, _ = validateLookup(lookup, required, table)
            if success:
                childCount += 1
        return (childCount > 0, required)

    @register
    def validateLanguage(self, langTuple, parentRequired, table):
        langTag, langSys = langTuple
        requestStatus = self.getRequestStatus(table.tableTag, 'language', langTag)
        required = parentRequired or requestStatus
        if requestStatus is False:
            return (False, required)

        # check all dependencies
        childCount = 0
        for featureIdx in langSys.FeatureIndex:
            featureRecord = table.table.FeatureList.featureRecord[featureIdx]
            success, _ = validateFeatureRecord(featureRecord, required, table)
            if success:
                childCount += 1
        return (childCount > 0, required)

    @register
    def validateScriptRecord(self, scriptRecord, parentRequired, table):
        requestStatus = self.getRequestStatus(table.tableTag, 'script', scriptRecord.ScriptTag)
        required = parentRequired or requestStatus
        if requestStatus is False:
            return (False, required)

        # check all dependencies
        childCount = 0
        if scriptRecord.Script.DefaultLangSys is not None:
            lang = ('dflt', sr0.Script.DefaultLangSys)
            success, _ = validateLanguage(lang, required, table)
            if success:
                childCount += 1

        for langSysRecord in scriptRecord.Script.LangSysRecord:
            # Use tuples, as they register fine within the registry dict
            # and they can be recreated later without loosing identity.
            # This way I don't need to branch validateLanguage for DefaultLangSys
            # (see above) which has no DefaultLangSysRecord or a simmilar
            # that features LangSysTag and LangSys (DefaultLangSys is
            # equivalent to LangSys) The rendering code will have to
            # recreate these tuples as well, to read the registry status.
            lang = (langSysRecord.LangSysTag, langSysRecord.LangSys)
            success, _ = validateLanguage(lang, required, table)
            if success:
                childCount += 1
        return (childCount > 0, required)

    @register
    def validateCommonGTable(self, table, parentRequired):
        assert table.tableTag in {'GPOS', 'GSUB'}, 'Wrong table type: {0}'.format(table.tableTag)
        requestStatus = self.getRequestStatus(table.tableTag)
        required = parentRequired or requestStatus
        if requestStatus is False:
            return (False, required);
        # check all dependencies
        childCount = 0
        for scriptRecord in table.table.ScriptList.ScriptRecord:
            sucess, _ = validateScriptRecord(scriptRecord, required, table)
            if sucess:
                childCount += 1
        # No need to do features etc, as they are fully dependent on the script
        # records. Yet there's just no way to output them when there's no script
        # where they are contained in. This may change if we decide to print
        # features without script/language which is mandatory at the moment.

        # Lookups can be outputted without script/lang/feature and that can be
        # requested so. We iterate over these now so that we don't invalidate
        # this table if there's otherwise no child.
        for lookup in table.table.LookupList.Lookup:
            success, _ = validateLookup(lookup, False, table)
            if success:
                childCount += 1
        return (childCount > 0, required)

class ExportState(object):
    # Some names must be unique and also other information needs to be carried
    # through the export process.
    def __init__(self):
        self._font = font
        self.usedMarkAttachClasses = {}
        self._uidCounters = {}

    def registerMarkAttachClassGetName(self, id):
        name = self.usedMarkAttachClasses.get(id, None)
        if name is None:
            name = self.usedMarkAttachClasses[id] = 'MarkAttachClass_{0}'.format(id)
        return name

    def getUID(self, prefix):
        if prefix not in self._uidCounters:
            self._uidCounters[prefix] = 0
        uid = self._uidCounters[prefix]
        self._uidCounters[prefix] += 1
        return '{0}{1}'format(prefix, uid);

def mainGPOS(font):
    gpos = font['GPOS']
    gdef = font['GDEF']
    state = ExportState()

    lookups = lookupsGPOS(state, gpos)
    classes = []
    if len(state.usedMarkAttachClasses):
        classes = classesGDEF( gdef.table.MarkAttachClassDef.classDefs
                             , state.usedMarkAttachClasses)
        print( '# GDEF Mark Attachment Classes:\n')
        print('\n\n'.join(classes))
        print('\n')
    print ( '# GPOS lookups:\n')
    print('\n\n'.join(lookups) )

    scriptsGPOS(state, gpos)

    # top level items:
    #   - ScriptList
    #   - FeatureList
    #   - LookupList
    #
    # The Scriptlist lists all features per script and language, so we want
    # to consult it when writing our features.
    #
    # the FeatureList has FeatureRecords which map FeatureTags (mkmk, mark)
    # to LookupListIndexes

    # The reason to have this request/filtering/lazy-eval thing in place
    # before starting a PR is that the tool can be useful for my purpose
    # while adding other lookups to the export.
    # Without having this the tool will export too much for my specific purpose.

    # TODO 0: Make this a proposal for the PR. Before that, make your mind
    # up about implementation details.
    # TODO A: I want to be able to control which items are exported
    # by making a specific request and by filtering via whitelist/blacklist.
    # --request "features: mark"
    #       -> will export the mark feature and all associated lookups
    # --request "features: mark; lookups markToBase"
    #       -> will export the mark feature and it's markToBase lookups,
    #          but not markToLigature
    # --request "features: mark" --blacklist "lookups: markToLigature"
    #       -> similar like the above
    # "language" and "script" would be further candidates for filtering.
    # A wildcart "*" can be used like so --request * or --whitelist "features:* --"
    #
    # Neither on a request or white-/blacklist filtered means the item
    # may be exported if it is used somewhere.
    # On a request means the item will be exported even if it is unused.
    # If it can't be exported that is because a "hard/blacklisted" dependency
    # is blocking it or because it is "empty" i.e. all lookups of a feature
    # have been filtered, so the feature is empty and won't be exported.
    #
    # * If there are no lookups in a feature, it shouldn't be exported then.
    # * we need a way to export just the lookups, without features
    # * All glyphs-classes needed will be created when used (we could make
    #   them requestable/filterable)
    # * We need two things: A) export just the used stuff and skip the not
    #   reachable (like skip unused lookups/classes)
    #   B) export everything, regardless
    #
    # The default should be --request "*" (the wildcard may rather be something
    # that is not expanded by the shell)
    # Then there would be an option to export just stuff that is actually being
    # used (like in a lazy evaluation -> that could be the programming model!)
    #
    # TODO B: Export from multiple fonts into one file. By using ExportState
    # name clashes should be handled. This is useful to merge the features of
    # two fonts that should go together. Like adding a latin font to an arabic font.
    # I wouldn't check for overlapping character names (e.g. in GDEF) the
    # font's should be subsetted before doing this.
    # Maybe we can generate warnings when problematic situations occur.

    # for A:
    # I can imagine doing 2 passes:
    # first pass: evaluate which items are going to be exported
    # seccond pass: export every item in font order (as they appear in the data)
    #
    # That has the advantage of not needing to "backtrack" if an item becomes
    # relevant after it has been defined (which shoukd be the normal case)
    # Another way would be to send the items into a structure where they can
    # be sorted before they are printed, i.e.: lookups = [(index, item)]
    # can be sorted by index.
    #
    # an item can have 3 export states: yes(true), no(false), maybe(null)
    # The lazy mode puts all items on "maybe"
    # a "request" set's items on "yes"
    # whitelist and blacklist can set items on "no". if there is a whitelist,
    # the item must be in it. If there is a blacklist, the item must not be
    # in it. The default whitelist is "*" (or ALL?) the defaukt blacklist
    # is empty.
    #
    # Dependencies and how an empty item won't be exported even if requested.
    # A lookup can't be empty. if it has dependencies and they are blocking,
    # the lookup wont be exported.
    #
    # A feature has a list of lookups, if this list is empty it wont be exported
    # the structure with languages and features is however a bit twisted!
    # in fea the languages are "inside" of the lookups, while in ttx the
    # features are inside the languages
    #
    # Also, I may choose to not export the language tags that come at the
    # beginning of the fea file, as I may have these positioned in other
    # files in my workflow.
    # So, maybe another, last system is to "silence" stuff that would
    # otherwise be exported.
    #
    #
    # all --request --whitelist --blacklist --silence options should talk
    # the same selector language.
    #
    # These apply to GPOS and GSUB:
    # I'd say that without
    #     {GSUB|GPOS} script: DFLT latn arab;
    #     {GSUB|GPOS} language: DEU dflt ARA URD;
    #     {GSUB|GPOS} feature: mkm mark calt dlig liga init medi;
    #     {GSUB|GPOS} lookup: gpos1 singlePos gsub2 // gpos1 singlePos are the same?
    # obviously: GDEF
    #     GDEF: glyphClassDef attachList ligCaretList markAttachClasses markGlyphSets
    #
    # We should also have a way to select all of GPOS or all of GDEF
    # I'd really like to say --request "GPOS *" OR --blacklist "GSUB *"
    # but in a way adding this GPOS/GSUB tags makes it a bit harder for the
    # filtering selector language.
    #
    # HIERARCHIES:
    #   GSUB and GPOS
    #       script
    #           DFLT latn arab ...
    #       language
    #           DEU dflt ARA URD ...
    #       feature
    #           mkm mark calt dlig liga init medi ...
    #       lookup
    #           gpos1 singlePos gsub2 ... // gpos1 singlePos are the same?
    #   GDEF
    #       glyphClassDef
    #       attachList
    #       ligCaretList
    #       markAttachClasses
    #       markGlyphSets
    #
    #  each entity could have a fully qualified name like:
    #       GSUB feature calt || GPOS lookup gpos1
    #  but that would be hard to type. Instead I want to have some shortcuts
    #
    #   i.e.:  GSUB feature *; GSUB **; GSUB|GPOS language|feature|lookup dlig|liga|gsub2
    #   * is matches all on the current level
    #   ** matches all on the current and all subsequent levels (having any
    #      name after this selector has no effect, as it is matched anyways)
    #
    # So, one thing when we lazily evaluate what to print and what not is
    # that an item needs to request its dependencies, which we learn when
    # evaluating the item.
    # the other thing is that we need to identify an item as one of the
    # things that we can filter for. I.e. the selector of an item should
    # be quite clear.
    #

    # a rule is a list of sets

class Selector(object):
    def __init__(self, string):
        self._rules = self.parse(string)

    def parse(self, string):
        rules = [[{ z for z in y.split('|') if len(z)} # set comprehension, no empty entries
                        for y in x.strip().split()] # split without argument splits on whitespace
                            for x in string.split(';')] # rules are separated by semicolons
        result = []
        for rule in rules:
            if not len(rule):
                continue
            for i,entry in enumerate(rule):
                if not len(entry):
                    # the rule won't select anything
                    rule = None
                    break
                # remove everything after "**"
                if '**' in entry:
                    # so we can later sort the rules by length ???? (if it makes sense)
                    del rule[i + 1:]
            if rule is not None:
                result.append(rule)
        # shortest rule first, may speed up selecting a bit
        result.sort(cmp=lambda x,y:len(x)-len(y))
        return result;

    def _ruleSelects(self, rule, item):
        if len(rule) == 0 \
                or len(rule) > len(item) \
                or len(rule) < len(item) and "**" not in rule[-1]:
            return False

        for entry, name in zip(rule, item):
            if '**' in entry:
                # validates all the rest of item, no matter what the content
                break
            elif '*' in entry:
                continue
            elif name not in entry:
                return False
        return True

    def __contains__(self, item):
        for rule in self._rules:
            if self._ruleSelects(rule, item):
                return True
        return False

class RequestStates(object):
    def __init__(self, request=None, whitelist=None, blacklist=None, silence=None):
        self._request = Selector(request]) \
                            if request is not None else Selector('**')
        self._whitelist = Selector(whitelist) \
                            if whitelist is not None else None
        self._blacklist = Selector(blacklist) \
                            if blacklist is not None else None
        self._silence = Selector(silence) \
                            if silence is not None else None

    def getRequestState(self *item):
        # snippet can item be exported
        if (self._whitelist is not None and item not in self._whitelist)
            or (self._blacklist is not None and item in self._blacklist)
            return False
        if item in self._request:
            return True
        return None # Maybe


    # As far as dependencies go: when we check anything, we should put it
    # save it's yes/no state (don't forget to delete that thing after the run)
    # can perfectly use a dict, btw.
    # So, when it comes to rendering, everything that has a YES state should
    # be rendered. Rendering will be as static as below. Just, render anything
    # in font order, if it has a yes.
    # so the main thing will be to visit all nodes first, or at least all
    # that have dependencies (but I wouldn't make that the rule)
    # Walk through all nodes first, if a node has dependencies there are
    # two possibilities:
    #           1.) the block is invalid if any of it's dependencies are invalid
    #                   like a lookup if it's markAttachment filter is invalid
    #           2.) the block is invalid if all of it's dependencies are invalid
    #                   a list like block, that could work with a subset of children
    #                   like an empty feature block is invalid
    #                   or like the GPOS table is invalid if all of its children are
    #
    # In the end, don't print maybe, print only items marked explicitly with yes

    # next up export languagesets and features
    # Probably a script/language is dependent on whether a appropriate language set
    # is exported! (TODO: check docs/makeotf if declaring script/language
    # is illegal without a fitting languageset. Also, special attention for the defaults!)
    # that may become a bit dirty.

if __name__ == '__main__':
    args = sys.argv[1:]
    exportType = args[0]
    fontPath = args[1]

    mains = {
        "GPOS": mainGPOS
    }

    font = ttLib.TTFont(fontPath)
    mains[exportType](font, *args[2:])


