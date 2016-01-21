from __future__ import print_function, absolute_import
from fontTools.misc.py23 import *
from collections import OrderedDict
from functools import partial

def getStatusAllTrue(item, requiredState=None):
    """
        Print everything no filtering.
        A very basic implementation as default fallback.

        No need to run SelectExports prior printing.
        See SelectExports if filtering is of interest.
    """
    return (True, True)

def makeName(*names, **kwargs):
    """
        Return a string with all positional arguments joined by a "_" underscore.

        NOTE: for named glyph classes maximum length is 30 in fea. So inputs
              should not be too long.

        Keyword arguments:
            prefix: string; prepended to the result; default: ''
            suffix: string; appended to the result; default: ''
            unique: bool; When True return a different string for each call,
                    even with the same input arguments, requires "uniquenessDict";
                    default: False
            uniquenessDict: dict; used to store the uniqueness information
                            of calls where "unique=true";
                            default: None

        NOTE: you can use functools.partial to create a customized makeName
        function that call this function with preset keyword:

            from functools import partial
            myMakeName = functools.partial(uniquenessDict={})

        And then pass the new function to functions that require a uniquenessDict:

            formatLookupGPOS(lookup, makeName=myMakeName)

        A uniquenessDict is currently required to make unique anchor-class names.
    """
    # python 2 compatible "only keyword" arguments
    prefix = kwargs.get('prefix', '')
    suffix = kwargs.get('suffix', '')
    unique = kwargs.get('unique', False)
    uniquenessDict = kwargs.get('uniquenessDict', None)

    if unique and uniquenessDict is None:
        raise TypeError('When "unique" is True "uniquenessDict" must be provided')
    init = names[0]
    base = ''
    if len(names) > 1:
        base = '_{0}'.format('_'.join(str(name) for name in names[1:]))

    placeholder = '' if not unique else '{uid}'
    name = '{prefix}{init}{uid}{base}{suffix}'.format(
        prefix=prefix,
        suffix=suffix,
        init=init,
        base=base,
        uid=placeholder
    )
    if unique:
        uid = uniquenessDict.get(name, None)
        uid = 0 if uid is None else uid + 1
        uniquenessDict[name] = uid
        name = name.format(uid=uid)
    return name

# GPOS and GSUB

def formatLookupflag(lookup, makeName=makeName):
    value = lookup.LookupFlag
    # format A: "lookupflag RightToLeft MarkAttachmentType @M;"
    # https://www.microsoft.com/typography/otspec/chapter2.htm
    flags = {
        "RightToLeft": 1, "IgnoreBaseGlyphs": 2,
        "IgnoreLigatures": 4, "IgnoreMarks": 8
    }
    # flags.UseMarkFilteringSet = 16 # == 0x10

    # format B: "lookupflag 6;"
    # There's apparently format B wich is just the raw number. We could
    # just output the lookupflag as it.
    # However, if there is information about the markAttachClass-id or
    # MarkFilteringSet-id this approach fails, because these ids depend
    # on the actual GDEF contents (which is unkown for a fea file).

    lookupflags = []
    for flag, bit in flags.items():
        if value & bit:
            lookupflags.append(flag)

    # 0x10 UseMarkFilteringSet
    if value & 0x10:
        markGlyphSetName = makeName('MarkGlyphSet', lookup.MarkFilteringSet)
        lookupflags.append('UseMarkFilteringSet @{0}'.format(markGlyphSetName))

    # A markAttachmentClass ID is set to the second Byte: (markAttachClass << 8)
    markAttachClassID = value >> 8
    if markAttachClassID:
        markAttachClassName = makeName('MarkAttachClass', markAttachClassID)
        lookupflags.append('MarkAttachmentType @{0}'.format(markAttachClassName))

    return 'lookupflag {0};'.format(' '.join(lookupflags))

def formatAnchor(anchorClassPrefix, classId, anchor):
    anchorType = type(anchor).__name__
    anchorFormat = ({
        'Anchor': '<anchor {1} {2}> {0}'
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

def formatLookupMarkToBase(lookup, makeName=makeName):
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
    anchorClassPrefix = makeName('Anchor', unique=True)
    lines = [ formatLookupflag(lookup, makeName=makeName) ] \
            + formatMarkArray(subtable.MarkArray, subtable.MarkCoverage, anchorClassPrefix) \
            + formatBaseArray(subtable.BaseArray, subtable.BaseCoverage, anchorClassPrefix)

    return (True, lines)

def formatLookupMarkToLigature(lookup, makeName=makeName):
    # See comment in def formatLookupMarkToBase
    assert lookup.SubTableCount == 1, 'More than one subtables per lookup '\
                                                    + 'is not supported.'

    subtable = lookup.SubTable[0] # fontTools.ttLib.tables.otTables.MarkLigPos

    assert subtable.Format == 1, 'Unknown subtable format {0} for lookup-type {1} {2}.' \
                                 .format( subtable.Format
                                        , subtable.LookupType
                                        , lookupTypesGPOS[subtable.LookupType][2])
    anchorClassPrefix = makeName('Anchor', unique=True)
    lines = [ formatLookupflag(lookup, makeName=makeName) ] \
            + formatMarkArray(subtable.MarkArray, subtable.MarkCoverage, anchorClassPrefix) \
            + formatLigatureArray(subtable.LigatureArray, subtable.LigatureCoverage, anchorClassPrefix)

    return (True, lines)

def formatLookupMarkToMark(lookup, makeName=makeName):
    # See comment in def formatLookupMarkToBase
    assert lookup.SubTableCount == 1, 'More than one subtables per lookup '\
                                                    + 'is not supported.'

    subtable = lookup.SubTable[0] # fontTools.ttLib.tables.otTables.MarkMarkPos

    assert subtable.Format == 1, 'Unknown subtable format {0} for lookup-type {1} {2}.' \
                                 .format( subtable.Format
                                        , subtable.LookupType
                                        , lookupTypesGPOS[subtable.LookupType][2])
    anchorClassPrefix = makeName('Anchor', unique=True)
    lines = [ formatLookupflag(lookup, makeName=makeName) ] \
            + formatMarkArray(subtable.Mark1Array, subtable.Mark1Coverage, anchorClassPrefix) \
            + formatMark2Array(subtable.Mark2Array, subtable.Mark2Coverage, anchorClassPrefix)
    return (True, lines)

def formatLookupNotImplementedGPOS(lookup, makeName=makeName):
    return formatLookupNotImplemented(lookup, lookupTypesGPOS, 'GPOS', makeName=makeName)

def formatLookupNotImplementedGSUB(lookup, makeName=makeName):
    return formatLookupNotImplemented(lookup, lookupTypesGSUB, 'GSUB', makeName=makeName)

def formatLookupNotImplemented(lookup, lookupTypes, tableTag, makeName=makeName):
    return (False, ['# Not implemented: {2} lookup-type {0} {1}.'
                .format(lookup.LookupType, lookupTypes[lookup.LookupType][2], tableTag)])

lookupTypesGPOS = {
    # enum from https://www.microsoft.com/typography/otspec/gpos.htm
    1: (formatLookupNotImplementedGPOS, 'singlePos', 'Single adjustment' ,'Adjust position of a single glyph'),
    2: (formatLookupNotImplementedGPOS, 'pairPos', 'Pair adjustment' ,'Adjust position of a pair of glyphs'),
    3: (formatLookupNotImplementedGPOS, 'cursiveAttach', 'Cursive attachment' ,'Attach cursive glyphs'),
    4: (formatLookupMarkToBase, 'markToBase', 'MarkToBase attachment' ,'Attach a combining mark to a base glyph'),
    5: (formatLookupMarkToLigature, 'markToLigature', 'MarkToLigature attachment' ,'Attach a combining mark to a ligature'),
    6: (formatLookupMarkToMark, 'markToMark', 'MarkToMark attachment' ,'Attach a combining mark to another mark'),
    7: (formatLookupNotImplementedGPOS, 'contextPos', 'Context positioning' ,'Position one or more glyphs in context'),
    8: (formatLookupNotImplementedGPOS, 'chainedCtxPos','Chained Context positioning' ,'Position one or more glyphs in chained context'),
    9: (formatLookupNotImplementedGPOS, 'extensionPos', 'Extension positioning' ,'Extension mechanism for other positionings'),
}

lookupTypesGSUB = {
    # enum from https://www.microsoft.com/typography/otspec/gsub.htm
    1: (formatLookupNotImplementedGSUB, 'singleSub', 'Single', 'Replace one glyph with one glyph'),
    2: (formatLookupNotImplementedGSUB, 'multipleSub', 'Multiple', 'Replace one glyph with more than one glyph'),
    3: (formatLookupNotImplementedGSUB, 'alternateSub', 'Alternate', 'Replace one glyph with one of many glyphs'),
    4: (formatLookupNotImplementedGSUB, 'ligatureSub', 'Ligature', 'Replace multiple glyphs with one glyph'),
    5: (formatLookupNotImplementedGSUB, 'contextSub', 'Context', 'Replace one or more glyphs in context'),
    6: (formatLookupNotImplementedGSUB, 'chainingCtxSub', 'Chaining Context', 'Replace one or more glyphs in chained context'),
    7: (formatLookupNotImplementedGSUB, 'extensionSub', 'Extension Substitution', 'Extension mechanism for other substitutions (i.e. this excludes the Extension type substitution itself)'),
    8: (formatLookupNotImplementedGSUB, 'revChainingCtxSub', 'Reverse chaining context single', 'Applied in reverse order, replace single glyph in chaining context'),
}

lookupTypes = {
    'GPOS': lookupTypesGPOS,
    'GSUB': lookupTypesGSUB
}



def formatLookup(lookup, lookupIdx, lookupTypes, makeName=makeName):
    # lookup is fontTools.ttLib.tables.otTables.Lookup
    if lookup.LookupType not in lookupTypes:
        raise ValueError('Lookup type "{0}" is not defined'.format(lookup.LookupType))
    func, nameBase = lookupTypes[lookup.LookupType][:2]
    name = makeName(nameBase, lookupIdx)
    success, body = func(lookup, makeName=makeName)
    # TODO: success can temporary be False until all lookup
    # types have been implemented. Then remove it
    # see also printFeatures
    if success:
        lines = ['lookup {0} {{'.format(name)] \
              + ['  {0}'.format(line) for line in body] \
              + ['}} {0};'.format(name)]
    else:
        lines = body
        name = '# lookup {0}; Type {1} not implemented!'.format(name, lookup.LookupType)
    return name, lines

def formatLookupGPOS(lookup, lookupIdx, makeName=makeName):
    return formatLookup(lookup, lookupIdx, lookupTypesGPOS, makeName=makeName)

def formatLookupGSUB(lookup, lookupIdx, makeName=makeName):
    return formatLookup(lookup, lookupIdx, lookupTypesGSUB, makeName=makeName)

def printFeatures(features, lookupNames, indentation='  ', print=print):
    for featureTag, scripts in features.items():
        print('feature {0} {{'.format(featureTag))
        for scriptTag, languages in scripts.items():
            print('{1}script {0};'.format(scriptTag, 1 * indentation))
            for langTag, lookups in languages.items():
                print('{1}language {0};'.format(langTag.strip(), 2 * indentation))
                for lookupIdx in lookups:
                    lookupName = lookupNames[lookupIdx]
                    if lookupName[0] == '#':
                        # FIXME: we skip some not yet implemented lookups
                        # and print comments instead.
                        # Remove this when all lookups have been implemented
                        # see also formatLookup
                        print('{1}{0}'.format(lookupNames[lookupIdx], 3 * indentation))
                    else:
                        print('{1}lookup {0};'.format(lookupName, 3 * indentation))
        print('}} {0};'.format(featureTag))
        print()

def _prepareFeatureLangSys(langTag, langSys, table, features, scriptTag, scriptRequired, getStatus):
    # This is a part of prepareFeatures
    printLang, langRequired = getStatus((langTag, langSys), scriptRequired)
    if not printLang: return
    for featureIdx in langSys.FeatureIndex:
        featureRecord = table.table.FeatureList.FeatureRecord[featureIdx]
        printFeature, featureRequired = getStatus(featureRecord, langRequired)
        if not printFeature: continue

        featureTag = featureRecord.FeatureTag
        scripts = features.get(featureTag, None)
        if scripts is None:
            scripts = features[featureTag] = OrderedDict()

        languages = scripts.get(scriptTag, None)
        if languages is None:
            languages = scripts[scriptTag] = OrderedDict()

        lookups = languages.get(langTag, None)
        if lookups is None:
            lookups = languages[langTag] = []

        for lookupIdx in featureRecord.Feature.LookupListIndex:
            lookup = table.table.LookupList.Lookup[lookupIdx]
            printLookup, _ = getStatus(lookup, featureRequired)
            if printLookup:
                lookups.append(lookupIdx)

def prepareFeatures(tableRequired, table, getStatus=getStatusAllTrue):
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

def printLookups(table, makeName=makeName, getStatus=getStatusAllTrue, print=print):
    lookupNames = {}
    types = lookupTypes[table.tableTag]
    for lookupIdx, lookup in enumerate(table.table.LookupList.Lookup):
        printLookup, _ = getStatus(lookup)
        if not printLookup:
            continue
        name, lines = formatLookup(lookup, lookupIdx, types, makeName=makeName)
        lookupNames[lookupIdx] = name
        print('\n'.join(lines))
        print()
    return lookupNames

def printCommonGTable(table, makeName=makeName, getStatus=getStatusAllTrue, print=print):
    printTable, tableRequired = getStatus(table, False)
    if not printTable:
        return

    print('\n#### Table {0} ####\n'.format(table.tableTag))

    print('# {0} Lookups:\n'.format(table.tableTag))
    lookupNames = printLookups(table, makeName=makeName, getStatus=getStatus, print=print)

    print('# {0} Features:\n'.format(table.tableTag))
    features = prepareFeatures(tableRequired, table, getStatus=getStatus)
    printFeatures(features, lookupNames, print=print)

# GDEF

def formatClassDefs(classDefs, classNames, returnFoundClasses=False):
    lines = []
    if returnFoundClasses:
        foundClasses = []
    classes = OrderedDict()
    for name, i in classDefs.items():
        if i not in classNames:
            continue
        className = classNames[i]
        if className not in classes:
            classes[className] = []
            if returnFoundClasses:
                foundClasses.append(i)
        classes[className].append(name)
    for className in classes:
        lines.append('@{0} = [ {1} ];'.format(className, ' '.join(classes[className])))
    return (lines, foundClasses) if returnFoundClasses else lines

def formatClassFromCoverage(coverage, name):
    return '@{0} = [ {1} ]'.format(name, ' '.join(coverage))

def formatAttachList(AttachList):
    lines = []
    for idx, glyph in enumerate(AttachList.Coverage.glyphs):
        attachmentPoints = AttachList.AttachPoint[idx]
        for point in attachmentPoints.PointIndex:
            lines.append('  Attach {0} {1};', glyph, point)
    return lines

def formatLigCaretList(ligCaretList):
    lines = []
    for idx, glyph in enumerate(ligCaretList.Coverage.glyphs):
        ligGlyph = ligCaretList.LigGlyph[idx]
        formats = list({cv.Format for cv in ligGlyph.CaretValue})
        assert len(formats) == 1, 'Can\'t use different CaretValue formats in one LigatureCaret entry'
        caretsFormat = formats[0]
        if caretsFormat == 1:
            # Format == 1: Design units only
            # LigatureCaretByPos <glyph|glyphclass> <caret position value>+;
            values = [str(cv.Coordinate) for cv in ligGlyph.CaretValue]
            formatString = '  LigatureCaretByPos {0} {1};'
        elif caretsFormat == 2:
            # Format == 2: Contour point
            values = [str(cv.CaretValuePoint) for cv in ligGlyph.CaretValue]
            formatString = '  LigatureCaretByIndex {0} {1};'
        elif caretsFormat == 3:
            # Format == 3: Design units plus Device table
            # LigatureCaretbyDev [* Currently not implemented. ]
            # see http://www.adobe.com/devnet/opentype/afdko/topic_feature_file_syntax.html#9.b
            # It would probbaly look like this:
            #   LigatureCaretbyDev 23 <device 11 -1, 12 -1> 42 <device 11 -80, 12 -11>
            # Or so:
            #   LigatureCaretbyDev 23 42 <device 11 -1, 12 -1> <device 11 -80, 12 -11>
            # There is also a Null device: <device NULL>
            # A generic DeviceTable formatting function is indicated, because
            # device tables are a reused type in fea:
            # http://www.adobe.com/devnet/opentype/afdko/topic_feature_file_syntax.html#2.e.iii
            # But also there: "[ Currently not implemented. ]"
            # ligGlyph.CaretValue[0].Coordinate, ligGlyph.CaretValue[0].DeviceTable
            values = ['[* Currently not implemented. ]']
            formatString = '# LigatureCaretbyDev {0} {1};'
        lines.append(formatString.format(glyph, None or ' '.join(values)))
    return lines

def printGDEF(table, makeName=makeName, getStatus=getStatusAllTrue, print=print):
    printTable, tableRequired = getStatus(table, False)
    if not printTable:
        return

    print('\n#### Table {0} ####\n'.format(table.tableTag))

    if table.table.MarkAttachClassDef is not None:
        markAttachClassDef = table.table.MarkAttachClassDef
        classDefs = markAttachClassDef.classDefs
        markAttachClassIDs = set(classDefs.values())
        classNames = {}
        for markAttachClassID in markAttachClassIDs:
            if markAttachClassID == 0: continue
            # ad-hoc type to make it selectable
            markAttachClassTuple = (markAttachClassDef, markAttachClassID)
            printClass, _ = getStatus(markAttachClassTuple)
            if printClass:
                classNames[markAttachClassID] = makeName('MarkAttachClass', markAttachClassID)
        if len(classNames):
            lines = formatClassDefs(classDefs, classNames)
            print('# GDEF Mark Attachment Classes:\n')
            print('\n'.join(lines))
            print()

    if hasattr(table.table, 'MarkGlyphSetsDef') \
                    and table.table.MarkGlyphSetsDef is not None:
        lines = []
        for idx, coverage in enumerate(table.table.MarkGlyphSetsDef.Coverage):
            printClass, _ = getStatus(coverage)
            if printClass:
                name = makeName('MarkGlyphSet', idx)
                lines.append(formatClassFromCoverage(coverage.glyphs, name))
        if len(lines):
            print('# GDEF Mark Filtering Sets:\n')
            print('\n'.join(lines))
            print()

    gdefLines = []

    if table.table.GlyphClassDef is not None:
        printClass, _ = getStatus(table.table.GlyphClassDef)
        if printClass:
            classNames = {
                1: 'GDEF_Base', # Base glyph (single character, spacing glyph)
                2: 'GDEF_Ligature', # Ligature glyph (multiple character, spacing glyph)
                3: 'GDEF_Mark', # Mark glyph (non-spacing combining glyph)
                4: 'GDEF_Component' # Component glyph (part of single character, spacing glyph)
            }
            lines, foundClasses = formatClassDefs(table.table.GlyphClassDef.classDefs, classNames, returnFoundClasses=True)
            if len(lines):
                glyphClassDef = ['@{0}'.format(classNames[i])
                                if i in foundClasses else '' for i in range(1,5)]
                gdefLines.append('  GlyphClassDef {0};'.format(', '.join(glyphClassDef)))

                print('# GDEF Glyph Class Definitions:\n')
                print('\n\n'.join(lines))
                print()

    if table.table.AttachList is not None:
        printAttachList, _ = getStatus(table.table.AttachList)
        if printAttachList:
            gdefLines += formatAttachList(table.table.AttachList)

    if table.table.LigCaretList is not None:
        printLigCaretList, _ = getStatus(table.table.LigCaretList)
        if printLigCaretList:
            gdefLines += formatLigCaretList(table.table.LigCaretList)

    if len(gdefLines):
        print('table {0} {{'.format(table.tableTag))
        print('\n'.join(gdefLines))
        print('}} {0};\n'.format(table.tableTag))


def printLanguageSystem(tables, getStatus=getStatusAllTrue, print=print):
    printLangSys , _ = getStatus('languagesystem')
    if not printLangSys:
        return
    scripts = OrderedDict()
    for table in tables:
        for scriptRecord in table.table.ScriptList.ScriptRecord:
            scriptTag = scriptRecord.ScriptTag
            languages = scripts.get(scriptTag, [])
            script = scriptRecord.Script

            # prepare some tuples: ("languageTag", LangSysRecordInstance)
            items = [];
            if script.DefaultLangSys is not None:
                items.append(('dflt', script.DefaultLangSys))
            items += [(l.LangSysTag, l.LangSys) for l in script.LangSysRecord]

            for langTuple in items:
                langTag = langTuple[0]
                if langTag in languages:
                    continue
                if not getStatus(langTuple)[0]:
                    continue
                languages.append(langTag)

            if languages and not scriptTag in scripts:
                scripts[scriptTag] = languages

    for script, languages in scripts.items():
        for language in languages:
            print('languagesystem {0} {1};'.format(script, language.strip()))


def printFont(font, makeName=makeName, getStatus=getStatusAllTrue, print=print):
    gpos_gsub = [font[tableTag] for tableTag in ('GPOS', 'GSUB') \
                                                    if tableTag in font]

    printLanguageSystem(gpos_gsub, getStatus=getStatus, print=print)

    if 'GDEF' in font:
        gdef = font['GDEF']
        printGDEF(gdef, makeName=makeName, getStatus=getStatus, print=print)

    for table in gpos_gsub:
        table = font[table.tableTag]
        printCommonGTable(table, makeName=makeName, getStatus=getStatus, print=print)

def main(font):
    printFont(font, makeName=partial(makeName, uniquenessDict={}))

if __name__ == '__main__':
    import sys
    from fontTools.ttLib import TTFont
    if not len(sys.argv) > 1:
        raise Exception('font-file argument missing')
    fontPath = sys.argv[1]
    font = TTFont(fontPath)
    main(font)
