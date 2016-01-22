#! /usr/bin/env python

"""
    A command line interface for the ft2fea library.
"""

from __future__ import print_function, absolute_import
from fontTools.misc.py23 import *
from functools import wraps, partial
import argparse

warn = partial(print, 'Warning:', file=sys.stderr)

# these operations should set the items state to
# yes, no (or Maybe, which is not registered)
# we will in another pass render the actual lookup tables if they are "yes"
# or if they are "Maybe" and getQueryStatus(['GPOS', 'lookup', lookup.typeName])
# returns true
# So, now, with this done the rest should be easy!
# above pseudo rendering code can ask at each stage if it should render the
# item, by asking the registry!

class ExportAggregator(object):
    def __init__(self, font, getQueryStatus):
        self.getQueryStatus = getQueryStatus
        self.font = font
        self.registry = {}
        self._transactions = []

    def getStatus(self, item, requiredState=None):
        # If there are any, the "True" values trump the "False" values
        # Thus, when requiredState is None and we check for both key types
        # i.e. (item, True) and (item, False) it's more likeley that the
        # item is going to be printed. If a diverse answer it needed for
        # the different requiredStates then this function should be called
        # with an explicit requiredState

        noEntry = (None, None)
        if requiredState is not None:
            return self.registry.get((item, requiredState), noEntry)

        result = list(noEntry)
        for req in (True, False):
            key = (item, req)
            printIt, required = self.registry.get(key, noEntry)
            result[0] = result[0] or printIt
            result[1] = result[1] or required
            if result[0] and result[1]:
                # the result won't change anymore
                break
        return tuple(result)

    # this is used as a decorator
    def register(func):
        @wraps(func)
        def wrapper(self, item, required, *args, **kwargs):
            # requiredKeyOverride: is used to run a validator with a different
            # required flag than the cache key will use. That way "validateLookup"
            # can declare lookupflag dependencies in GDEF. GDEF validation
            # needs to run after all potentially dependent validations though
            key = (item, kwargs.get('requiredKeyOverride', required))
            if 'requiredKeyOverride' in kwargs:
                del kwargs['requiredKeyOverride']
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
        self._transactions.append(self.registry)
        self.registry = {}

    def _commitTransaction(self):
        registry = self._transactions.pop()
        registry.update(self.registry)
        self.registry = registry

    def _rollbackTransaction(self):
        self.registry = self._transactions.pop()

    def _validateSimpleEntry(self, selector, parentRequired):
        requestStatus = self.getQueryStatus(*selector)
        required = requestStatus or parentRequired
        result = requestStatus is not False and (requestStatus or required) is True
        return (result, required)

    # GDEF

    @register
    def validateMarkGlyphClassDef(self, glyphClassDef, parentRequired, table):
        selector = (table.tableTag, 'glyphClassDef')
        return self._validateSimpleEntry(selector, parentRequired)

    @register
    def validateAttachList(self, attachList, parentRequired, table):
        selector = (table.tableTag, 'attachList')
        return self._validateSimpleEntry(selector, parentRequired)

    @register
    def validateLigCaretList(self, ligCaretList, parentRequired, table):
        selector = (table.tableTag, 'ligCaretList')
        return self._validateSimpleEntry(selector, parentRequired)

    @register
    def validateMarkAttachmentClass(self, markAttachClassTuple, parentRequired, table):
        selector = (table.tableTag, 'markAttachClasses')
        return self._validateSimpleEntry(selector, parentRequired)

    @register
    def validateMarkAttachmentClassDef(self, markAttachmentClassDef, parentRequired, table):
        # This can't be (de-)selected directly so here's no selector check.
        # But, it's children can be selected using "GDEF markAttachClasses"
        # Which has the same effect. This way we can have the dependants
        # select just the required classes. See validateLookup
        required = parentRequired
        childCount = 0
        markAttachClassIDs = set(markAttachmentClassDef.classDefs.values())
        for markAttachClassID in markAttachClassIDs:
            # "All glyphs not assigned to a class fall into Class 0."
            # Thus there's no meaning in outputting this if it is ever present
            # It can't be referenced by a LookupFlag.
            if markAttachClassID == 0: continue
            # ad-hoc type to make it selectable
            markAttachClassTuple = (markAttachmentClassDef, markAttachClassID)
            success, _ = self.validateMarkAttachmentClass(markAttachClassTuple, required, table)
            if success:
                childCount += 1
        return (childCount > 0, required)

    @register
    def validateMarkGlyphSet(self, markGlyphSet_Coverage, parentRequired, table):
        selector = (table.tableTag, 'markGlyphSets')
        return self._validateSimpleEntry(selector, parentRequired)

    @register
    def validateMarkGlyphSetsDef(self, markGlyphSetsDef, parentRequired, table):
        # This can't be (de-)selected directly so here's no selector check.
        # But, it's children can be selected using "GDEF markGlyphSets"
        # which has the same effect. This way we can have the dependants
        # select just the required markSets. See validateLookup
        required = parentRequired
        childCount = 0
        for coverage in markGlyphSetsDef.Coverage:
            success, _ = self.validateMarkGlyphSet(coverage, required, table)
            if success:
                childCount += 1
        return (childCount > 0, required)

    @register
    def validateGDEF(self, table, parentRequired):
        requestStatus = self.getQueryStatus(table.tableTag)
        required = requestStatus or parentRequired
        if requestStatus is False:
            return (False, required)

        # check all dependencies
        childCount = 0
        children = [
            (self.validateMarkGlyphClassDef, table.table.GlyphClassDef),
            (self.validateAttachList, table.table.AttachList),
            (self.validateLigCaretList, table.table.LigCaretList),
            (self.validateMarkAttachmentClassDef, table.table.MarkAttachClassDef)
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
        class Invalidation(Exception): pass
        # it has not really a tag, so we make one up
        # gpos3 is GPOS LookupType 3
        # gsub2 is GSUB LookupType 2 etc
        tag = '{0}{1}'.format(table.tableTag.lower(), lookup.LookupType)
        requestStatus = self.getQueryStatus(table.tableTag, 'lookup', tag)
        required = requestStatus or parentRequired
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
            if lookup.LookupFlag & 0x10:
                # don't validate if the table is blocked
                if self.getQueryStatus('GDEF') is False:
                    raise Invalidation
                gdef = self.font['GDEF']
                coverage = gdef.table.MarkGlyphSetsDef.Coverage[lookup.MarkFilteringSet]
                success, _ = self.validateMarkGlyphSet(coverage, True, gdef, requiredKeyOverride=False)
                if not success:
                    raise Invalidation

            # MarkAttachmentType
            markAttachClassID = lookup.LookupFlag >> 8
            if markAttachClassID:
                # don't validate if the table is blocked
                if self.getQueryStatus('GDEF') is False:
                    raise Invalidation
                gdef = self.font['GDEF']
                # An ad-hoc pseudo item, to enable outputting just the used
                # mark attachment classes
                markAttachClassTuple = (gdef.table.MarkAttachClassDef, markAttachClassID)
                success, _ = self.validateMarkAttachmentClass(markAttachClassTuple, True, gdef, requiredKeyOverride=False)
                if not success:
                    raise Invalidation

            # TODO
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
        except Invalidation:
            invalid = True
        except Exception as e:
            invalid = True
            raise e
        finally:
            if invalid:
                self._rollbackTransaction()
                result = (False, True)
            else:
                self._commitTransaction()
                result = (True, True)
        return result

    @register
    def validateFeatureRecord(self, featureRecord, parentRequired, table):
        requestStatus = self.getQueryStatus(table.tableTag, 'feature', featureRecord.FeatureTag)
        required = requestStatus or parentRequired
        if requestStatus is False:
            return (False, required)

        # check all dependencies
        childCount = 0
        for lookupIdx in featureRecord.Feature.LookupListIndex:
            # get the lookup from the lookupList
            lookup = table.table.LookupList.Lookup[lookupIdx]
            success, _ = self.validateLookup(lookup, required, table)
            if success:
                childCount += 1
        return (childCount > 0, required)

    @register
    def validateLanguage(self, langTuple, parentRequired, table):
        langTag, langSys = langTuple
        requestStatus = self.getQueryStatus(table.tableTag, 'language', langTag)
        required = requestStatus or parentRequired
        if requestStatus is False:
            return (False, required)

        # check all dependencies
        childCount = 0
        for featureIdx in langSys.FeatureIndex:
            featureRecord = table.table.FeatureList.FeatureRecord[featureIdx]
            success, _ = self.validateFeatureRecord(featureRecord, required, table)
            if success:
                childCount += 1
        return (childCount > 0, required)

    @register
    def validateScriptRecord(self, scriptRecord, parentRequired, table):
        requestStatus = self.getQueryStatus(table.tableTag, 'script', scriptRecord.ScriptTag)
        required = requestStatus or parentRequired
        if requestStatus is False:
            return (False, required)
        # check all dependencies
        childCount = 0
        if scriptRecord.Script.DefaultLangSys is not None:
            lang = ('dflt', scriptRecord.Script.DefaultLangSys)
            success, _ = self.validateLanguage(lang, required, table)
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
            success, _ = self.validateLanguage(lang, required, table)
            if success:
                childCount += 1
        return (childCount > 0, required)

    @register
    def validateCommonGTable(self, table, parentRequired):
        assert table.tableTag in {'GPOS', 'GSUB'}, 'Wrong table type: {0}'.format(table.tableTag)
        requestStatus = self.getQueryStatus(table.tableTag)
        required = requestStatus or parentRequired
        if requestStatus is False:
            return (False, required)
        # check all dependencies
        childCount = 0
        for scriptRecord in table.table.ScriptList.ScriptRecord:
            sucess, _ = self.validateScriptRecord(scriptRecord, required, table)
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
            success, _ = self.validateLookup(lookup, False, table)
            if success:
                childCount += 1
        return (childCount > 0, required)

    @register
    def validateLanguagesystem(self, itemString, parentRequired):
        # NOTE: item is really just a string, as there is not an
        # item for the languagesystem definition in fea files, since a
        # string can be reproduced, identitywise, this works just fine.
        selector = (itemString, ) # one string in a tuple
        return self._validateSimpleEntry(selector, parentRequired)

    def validate(self, required=False):
        self.validateLanguagesystem('languagesystem', required)

        for tableTag in ('GPOS', 'GSUB'):
            if tableTag in self.font:
                self.validateCommonGTable(self.font[tableTag], required)
        if 'GDEF' in self.font:
            self.validateGDEF(self.font['GDEF'], required)



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
    # other
    #     languagesystem
    #
    # We should also have a way to select all of GPOS or all of GDEF
    # I'd really like to say --request "GPOS *" OR --blacklist "GSUB *"
    # but in a way adding this GPOS/GSUB tags makes it a bit harder for the
    # filtering selector language.
    #
    # HIERARCHIES:
    #   languagesystem
    #   GDEF
    #       glyphClassDef
    #       attachList
    #       ligCaretList
    #       markAttachClasses
    #       markGlyphSets
    #   GSUB and GPOS
    #       script
    #           DFLT latn arab ...
    #       language
    #           DEU dflt ARA URD ...
    #       feature
    #           mkm mark calt dlig liga init medi ...
    #       lookup
    #           gpos1 singlePos gsub2 ... // gpos1 singlePos are the same?
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

class ExportQuery(object):
    def __init__(self, request=None, whitelist=None, blacklist=None, silence=None, **kwargs):
        self._request = Selector(request) \
                            if request is not None else Selector('**')
        self._whitelist = Selector(whitelist) \
                            if whitelist is not None else None
        self._blacklist = Selector(blacklist) \
                            if blacklist is not None else None
        self._silence = Selector(silence) \
                            if silence is not None else None

    def getQueryStatus(self, *item):
        """ Return the query state of the item; True, False or None:
                True: Item is requested
                False: Item is blocked
                None: Item may be exported, if a dependent item requires it
        """

        if (self._whitelist is not None and item not in self._whitelist) \
                or (self._blacklist is not None and item in self._blacklist):
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


parser = argparse.ArgumentParser(description='Generate an OpenType Feature file (fea) from an otf/ttf font.')

# Metavar for the source-font-file" argument, for the future this could alse be many sources
#parser.add_argument('integers', metavar='N', type=int, nargs='+',
#                   help='an integer for the accumulator')

parser.add_argument('-r, --request', dest='request', metavar="REQUIRED", nargs='?'\
                 , help='The fea contents to export.')

parser.add_argument('-w, --whitelist', dest='whitelist', metavar="WHITELIST", nargs='?'\
                 , help='Whitelist of fea contents.')

parser.add_argument('-b, --blacklist', dest='blacklist', metavar="BLACKLIST", nargs='?'\
                 , help='Blacklist of fea contents.')



parser.add_argument('font', help='A ttf or otf OpenType font file.'\
                   , metavar="FONT-PATH")

def main():
    import sys
    from fontTools.ttLib import TTFont
    from ft2fea import makeName, printFont
    args = parser.parse_args()
    font = TTFont(args.font)
    query = ExportQuery(**vars(args))
    aggregator = ExportAggregator(font, query.getQueryStatus)
    aggregator.validate()

    printFont(font,
              makeName=partial(makeName, uniquenessDict={}),
              getStatus=aggregator.getStatus)

if __name__ == '__main__':
    main()
