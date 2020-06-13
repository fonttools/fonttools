from collections import defaultdict, OrderedDict
from fontTools.ttLib.tables import otBase, otTables
from fontTools.otlLib.error import OTLLibError
from fontTools.otlLib import builder as otl
import logging


log = logging.getLogger(__name__)

class LookupBuilder(object):
    SUBTABLE_BREAK_ = "SUBTABLE_BREAK"

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

    def build_subst_subtables(self, mapping, klass):
        substitutions = [{}]
        for key in mapping:
            if key[0] == self.SUBTABLE_BREAK_:
                substitutions.append({})
            else:
                substitutions[-1][key] = mapping[key]
        subtables = [klass(s) for s in substitutions]
        return subtables

    def add_subtable_break(self, location):
        log.warning(OTLLibError(
            'unsupported "subtable" statement for lookup type',
            location
        ))


class AlternateSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 3)
        self.alternates = OrderedDict()

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.alternates == other.alternates)

    def build(self):
        subtables = self.build_subst_subtables(self.alternates,
                otl.buildAlternateSubstSubtable)
        return self.buildLookup_(subtables)

    def getAlternateGlyphs(self):
        return self.alternates

    def add_subtable_break(self, location):
        self.alternates[(self.SUBTABLE_BREAK_, location)] = self.SUBTABLE_BREAK_


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
            if prefix == self.SUBTABLE_BREAK_:
                continue
            st = otTables.ChainContextPos()
            subtables.append(st)
            st.Format = 3
            self.setBacktrackCoverage_(prefix, st)
            self.setLookAheadCoverage_(suffix, st)
            self.setInputCoverage_(glyphs, st)

            st.PosCount = 0
            st.PosLookupRecord = []
            for sequenceIndex, lookupList in enumerate(lookups):
                if lookupList is not None:
                    if not isinstance(lookupList, list):
                        # Can happen with synthesised lookups
                        lookupList = [ lookupList ]
                    for l in lookupList:
                        st.PosCount += 1
                        if l.lookup_index is None:
                            raise OTLLibError('Missing index of the specified '
                                'lookup, might be a substitution lookup',
                                self.location)
                        rec = otTables.PosLookupRecord()
                        rec.SequenceIndex = sequenceIndex
                        rec.LookupListIndex = l.lookup_index
                        st.PosLookupRecord.append(rec)
        return self.buildLookup_(subtables)

    def find_chainable_single_pos(self, lookups, glyphs, value):
        """Helper for add_single_pos_chained_()"""
        res = None
        for lookup in lookups[::-1]:
            if lookup == self.SUBTABLE_BREAK_:
                return res
            if isinstance(lookup, SinglePosBuilder) and \
                    all(lookup.can_add(glyph, value) for glyph in glyphs):
                res = lookup
        return res

    def add_subtable_break(self, location):
        self.rules.append((self.SUBTABLE_BREAK_, self.SUBTABLE_BREAK_,
                           self.SUBTABLE_BREAK_, [self.SUBTABLE_BREAK_]))


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
            if prefix == self.SUBTABLE_BREAK_:
                continue
            st = otTables.ChainContextSubst()
            subtables.append(st)
            st.Format = 3
            self.setBacktrackCoverage_(prefix, st)
            self.setLookAheadCoverage_(suffix, st)
            self.setInputCoverage_(input, st)

            st.SubstCount = 0
            st.SubstLookupRecord = []
            for sequenceIndex, lookupList in enumerate(lookups):
                if lookupList is not None:
                    if not isinstance(lookupList, list):
                        # Can happen with synthesised lookups
                        lookupList = [ lookupList ]
                    for l in lookupList:
                        st.SubstCount += 1
                        if l.lookup_index is None:
                            raise OTLLibError('Missing index of the specified '
                                'lookup, might be a positioning lookup',
                                self.location)
                        rec = otTables.SubstLookupRecord()
                        rec.SequenceIndex = sequenceIndex
                        rec.LookupListIndex = l.lookup_index
                        st.SubstLookupRecord.append(rec)
        return self.buildLookup_(subtables)

    def getAlternateGlyphs(self):
        result = {}
        for (_, _, _, lookuplist) in self.substitutions:
            if lookuplist == self.SUBTABLE_BREAK_:
                continue
            for lookups in lookuplist:
                if not isinstance(lookups, list):
                    lookups = [lookups]
                for lookup in lookups:
                    if lookup is not None:
                        alts = lookup.getAlternateGlyphs()
                        for glyph, replacements in alts.items():
                            result.setdefault(glyph, set()).update(replacements)
        return result

    def find_chainable_single_subst(self, glyphs):
        """Helper for add_single_subst_chained_()"""
        res = None
        for _, _, _, substitutions in self.substitutions[::-1]:
            if substitutions == self.SUBTABLE_BREAK_:
                return res
            for sub in substitutions:
                if (isinstance(sub, SingleSubstBuilder) and
                        not any(g in glyphs for g in sub.mapping.keys())):
                    res = sub
        return res

    def add_subtable_break(self, location):
        self.substitutions.append((self.SUBTABLE_BREAK_, self.SUBTABLE_BREAK_,
                                   self.SUBTABLE_BREAK_, self.SUBTABLE_BREAK_))


class LigatureSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 4)
        self.ligatures = OrderedDict()  # {('f','f','i'): 'f_f_i'}

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.ligatures == other.ligatures)

    def build(self):
        subtables = self.build_subst_subtables(self.ligatures,
                otl.buildLigatureSubstSubtable)
        return self.buildLookup_(subtables)

    def add_subtable_break(self, location):
        self.ligatures[(self.SUBTABLE_BREAK_, location)] = self.SUBTABLE_BREAK_


class MultipleSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 2)
        self.mapping = OrderedDict()

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        subtables = self.build_subst_subtables(self.mapping,
                otl.buildMultipleSubstSubtable)
        return self.buildLookup_(subtables)

    def add_subtable_break(self, location):
        self.mapping[(self.SUBTABLE_BREAK_, location)] = self.SUBTABLE_BREAK_


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

    def add_subtable_break(self, location):
        # Nothing to do here, each substitution is in its own subtable.
        pass


class SingleSubstBuilder(LookupBuilder):
    def __init__(self, font, location):
        LookupBuilder.__init__(self, font, location, 'GSUB', 1)
        self.mapping = OrderedDict()

    def equals(self, other):
        return (LookupBuilder.equals(self, other) and
                self.mapping == other.mapping)

    def build(self):
        subtables = self.build_subst_subtables(self.mapping,
                otl.buildSingleSubstSubtable)
        return self.buildLookup_(subtables)

    def getAlternateGlyphs(self):
        return {glyph: set([repl]) for glyph, repl in self.mapping.items()}

    def add_subtable_break(self, location):
        self.mapping[(self.SUBTABLE_BREAK_, location)] = self.SUBTABLE_BREAK_


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
            self.glyphPairs[key] = (value1, value2)
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
            valFormat1, valFormat2 = 0, 0
            if value1: valFormat1 = value1.getFormat()
            if value2: valFormat2 = value2.getFormat()
            builder = builders.get((valFormat1, valFormat2))
            if builder is None:
                builder = ClassPairPosSubtableBuilder(
                    self, valFormat1, valFormat2)
                builders[(valFormat1, valFormat2)] = builder
            builder.addPair(glyphclass1, value1, glyphclass2, value2)
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

    def add_pos(self, location, glyph, otValueRecord):
        if not self.can_add(glyph, otValueRecord):
            otherLoc = self.locations[glyph]
            raise OTLLibError(
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

