#!/usr/bin/python

# FontDame-to-FontTools for OpenType Layout tables
#
# Source language spec is available at:
# https://rawgit.com/Monotype/OpenType_Table_Source/master/otl_source.html
# https://github.com/Monotype/OpenType_Table_Source/

from __future__ import print_function, division, absolute_import
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otBase import ValueRecord, valueRecordFormatDict
import re

debug = print

def parseGlyph(s):
	if s[:2] == 'U ':
		return ttLib.TTFont._makeGlyphName(int(s[2:], 16))
	elif s[:2] == '# ':
		return "glyph%.5d" % int(s[2:])
	return s

def parseGlyphs(l):
	return [parseGlyph(g) for g in l]

def parseScriptList(lines):
	lines.skipUntil('script table begin')
	self = ot.ScriptList()
	self.ScriptRecord = []
	for line in lines.readUntil('script table end'):
		scriptTag, langSysTag, defaultFeature, features = line
		debug("Adding script", scriptTag, "language-system", langSysTag)

		langSys = ot.LangSys()
		langSys.LookupOrder = None
		# TODO The following two lines should use lazy feature name-to-index mapping
		langSys.ReqFeatureIndex = int(defaultFeature) if defaultFeature else 0xFFFF
		langSys.FeatureIndex = intSplitComma(features)
		langSys.FeatureCount = len(langSys.FeatureIndex)

		script = [s for s in self.ScriptRecord if s.ScriptTag == scriptTag]
		if script:
			script = script[0].Script
		else:
			scriptRec = ot.ScriptRecord()
			scriptRec.ScriptTag = scriptTag
			scriptRec.Script = ot.Script()
			self.ScriptRecord.append(scriptRec)
			script = scriptRec.Script
			script.DefaultLangSys = None
			script.LangSysRecord = []
			script.LangSysCount = 0

		if langSysTag == 'default':
			script.DefaultLangSys = langSys
		else:
			langSysRec = ot.LangSysRecord()
			langSysRec.LangSysTag = langSysTag + ' '*(4 - len(langSysTag))
			langSysRec.LangSys = langSys
			script.LangSysRecord.append(langSysRec)
			script.LangSysCount = len(script.LangSysRecord)

	self.ScriptCount = len(self.ScriptRecord)
	# TODO sort scripts and langSys's?
	return self

def parseFeatureList(lines):
	lines.skipUntil('feature table begin')
	self = ot.FeatureList()
	self.FeatureRecord = []
	for line in lines.readUntil('feature table end'):
		idx, featureTag, lookups = line
		assert int(idx) == len(self.FeatureRecord), "%d %d" % (idx, len(self.FeatureRecord))
		featureRec = ot.FeatureRecord()
		featureRec.FeatureTag = featureTag
		featureRec.Feature = ot.Feature()
		self.FeatureRecord.append(featureRec)
		feature = featureRec.Feature
		feature.FeatureParams = None
		# TODO The following line should use lazy lookup name-to-index mapping
		feature.LookupListIndex = intSplitComma(lookups)
		feature.LookupCount = len(feature.LookupListIndex)

	self.FeatureCount = len(self.FeatureRecord)
	return self

def parseLookupFlags(lines):
	flags = 0
	filterset = None
	for line in lines:
		flag = {
			'righttoleft':		0x0001,
			'ignorebaseglyphs':	0x0002,
			'ignoreligatures':	0x0004,
			'ignoremarks':		0x0008,
			}.get(line[0].lower())
		if flag:
			assert line[1].lower() in ['yes', 'no'], line[1]
			if line[1].lower() == 'yes':
				flags |= flag
			continue
		if line[0].lower() == 'markattachmenttype':
			flags |= int(line[1]) << 8
			continue
		if line[0].lower() == 'markfiltertype':
			flags |= 0x10
			filterset = int(line[1])
		lines.pack(line)
		break
	return flags, filterset

def parseSingleSubst(self, lines, font):
	self.mapping = {}
	for line in lines:
		assert len(line) == 2, line
		line = parseGlyphs(line)
		self.mapping[line[0]] = line[1]

def parseMultiple(self, lines, font):
	self.mapping = {}
	for line in lines:
		line = parseGlyphs(line)
		self.mapping[line[0]] = line[1:]

def parseAlternate(self, lines, font):
	self.alternates = {}
	for line in lines:
		line = parseGlyphs(line)
		self.alternates[line[0]] = line[1:]

def parseLigature(self, lines, font):
	self.ligatures = {}
	for line in lines:
		assert len(line) >= 2, line
		line = parseGlyphs(line)
		# The following single line can replace the rest of this function with fontTools >= 3.1
		#self.ligatures[tuple(line[1:])] = line[0]
		ligGlyph, firstGlyph = line[:2]
		otherComponents = line[2:]
		ligature = ot.Ligature()
		ligature.Component = otherComponents
		ligature.CompCount = len(ligature.Component) + 1
		ligature.LigGlyph = ligGlyph
		self.ligatures.setdefault(firstGlyph, []).append(ligature)

def parseSinglePos(self, lines, font):
	values = {}
	for line in lines:
		assert len(line) == 3, line
		w = line[0].title().replace(' ', '')
		assert w in valueRecordFormatDict
		g = parseGlyph(line[1])
		v = int(line[2])
		if g not in values:
			values[g] = ValueRecord()
		assert not hasattr(values[g], w), (g, w)
		setattr(values[g], w, v)
	self.Coverage = makeCoverage(values.keys(), font)
	values = [values[k] for k in self.Coverage.glyphs]
	self.ValueFormat = reduce(int.__or__, [v.getFormat() for v in values])
	if all(v == values[0] for v in values):
		self.Format = 1
		self.Value = values[0]
	else:
		self.Format = 2
		self.Value = values
		self.ValueCount = len(self.Value)

def parsePair(self, lines, font):
	self.ValueFormat1 = self.ValueFormat2 = 0
	typ = lines.peek()[0].split()[0].lower()
	if typ in ('left', 'right'):
		self.Format = 1
		values = {}
		for line in lines:
			assert len(line) == 4, line
			side = line[0].split()[0].lower()
			assert side in ('left', 'right'), side
			what = line[0][len(side):].title().replace(' ', '')
			mask = valueRecordFormatDict[what][0]
			glyph1, glyph2 = parseGlyphs(line[1:3])
			value = int(line[3])
			if not glyph1 in values: values[glyph1] = {}
			if not glyph2 in values[glyph1]: values[glyph1][glyph2] = (ValueRecord(),ValueRecord())
			rec2 = values[glyph1][glyph2]
			if side == 'left':
				self.ValueFormat1 |= mask
				vr = rec2[0]
			else:
				self.ValueFormat2 |= mask
				vr = rec2[1]
			assert not hasattr(vr, what), (vr, what)
			setattr(vr, what, value)
		self.Coverage = makeCoverage(values.keys(), font)
		self.PairSet = []
		for glyph1 in self.Coverage.glyphs:
			values1 = values[glyph1]
			pairset = ot.PairSet()
			records = pairset.PairValueRecord = []
			for glyph2 in sorted(values1.keys(), key=font.getGlyphID):
				values2 = values1[glyph2]
				pair = ot.PairValueRecord()
				pair.SecondGlyph = glyph2
				pair.Value1,pair.Value2 = values2
				records.append(pair)
			pairset.PairValueCount = len(pairset.PairValueRecord)
			self.PairSet.append(pairset)
		self.PairSetCount = len(self.PairSet)
	elif typ.endswith('class'):
		self.Format = 2
		classDefs = [None, None]
		while lines.peek()[0].endswith("class definition begin"):
			typ = lines.peek()[0][:-len("class definition begin")].lower()
			idx,klass = {
				'first':	(0,ot.ClassDef1),
				'second':	(1,ot.ClassDef2),
			}[typ]
			assert classDefs[idx] is None
			classDefs[idx] = parseClassDef(lines, klass=klass)
		self.ClassDef1, self.ClassDef2 = classDefs
		self.Class1Count, self.Class2Count = (1+max(c.classDefs.values()) for c in classDefs)
		self.Class1Record = [ot.Class1Record() for i in range(self.Class1Count)]
		for rec1 in self.Class1Record:
			rec1.Class2Record = [ot.Class2Record() for j in range(self.Class2Count)]
			for rec2 in rec1.Class2Record:
				rec2.Value1 = ValueRecord()
				rec2.Value2 = ValueRecord()
		for line in lines:
			assert len(line) == 4, line
			side = line[0].split()[0].lower()
			assert side in ('left', 'right'), side
			what = line[0][len(side):].title().replace(' ', '')
			mask = valueRecordFormatDict[what][0]
			class1, class2, value = (int(x) for x in line[1:4])
			rec2 = self.Class1Record[class1].Class2Record[class2]
			if side == 'left':
				self.ValueFormat1 |= mask
				vr = rec2.Value1
			else:
				self.ValueFormat2 |= mask
				vr = rec2.Value2
			assert not hasattr(vr, what), (vr, what)
			setattr(vr, what, value)
		self.Coverage = makeCoverage(self.ClassDef1.classDefs.keys(), font)
	else:
		assert 0

def parseKernset(self, lines, font):
	raise NotImplementedError

def makeAnchor(data, klass=ot.Anchor):
	assert len(data) <= 2
	anchor = klass()
	anchor.Format = 1
	anchor.XCoordinate,anchor.YCoordinate = intSplitComma(data[0])
	if len(data) > 1 and data[1] != '':
		anchor.Format = 2
		anchor.AnchorPoint = int(data[1])
	return anchor

def parseCursive(self, lines, font):
	self.Format = 1
	self.EntryExitRecord = []
	records = {}
	for line in lines:
		assert len(line) in [3,4], line
		idx,klass = {
			'entry':	(0,ot.EntryAnchor),
			'exit':		(1,ot.ExitAnchor),
		}[line[0]]
		glyph = parseGlyph(line[1])
		if glyph not in records:
			records[glyph] = [None,None]
		assert records[glyph][idx] is None, (glyph, idx)
		records[glyph][idx] = makeAnchor(line[2:], klass)
	self.Coverage = makeCoverage(records.keys(), font)
	recs = self.EntryExitRecord = []
	for glyph in self.Coverage.glyphs:
		rec = ot.EntryExitRecord()
		rec.EntryAnchor,rec.ExitAnchor = records[glyph]
		recs.append(rec)
	self.EntryExitCount = len(self.EntryExitRecord)

def makeMarkArrayAndCoverage(data, font, c):
	coverage = makeCoverage(data.keys(), font, c.MarkCoverageClass)
	markArray = c.MarkArrayClass()
	records = []
	for glyph in coverage.glyphs:
		klass, anchor = data[glyph]
		record = c.MarkRecordClass()
		record.Class = klass
		setattr(record, c.MarkAnchor, anchor)
		records.append(record)
	setattr(markArray, c.MarkRecord, records)
	setattr(markArray, c.MarkCount, len(records))
	return markArray, coverage

def makeBaseArrayAndCoverage(data, classCount, font, c):
	coverage = makeCoverage([g for g,k in data.keys()], font, c.BaseCoverageClass)
	baseArray = c.BaseArrayClass()
	records = []
	idx = {}
	for glyph in coverage.glyphs:
		idx[glyph] = len(records)
		record = c.BaseRecordClass()
		anchors = [None] * classCount
		setattr(record, c.BaseAnchor, anchors)
		records.append(record)
	for (glyph,klass),anchor in data.items():
		record = records[idx[glyph]]
		anchors = getattr(record, c.BaseAnchor)
		assert anchors[klass] is None, (glyph, klass)
		anchors[klass] = anchor
	setattr(baseArray, c.BaseRecord, records)
	setattr(baseArray, c.BaseCount, len(records))
	return baseArray, coverage

def parseMarkToSomething(self, lines, font, c):
	self.Format = 1
	markData = {}
	baseData = {}
	Data = {
		'mark':	(markData, c.MarkAnchorClass),
		'base':	(baseData, c.BaseAnchorClass),
	}
	for line in lines:
		typ = line[0]
		assert typ in ('mark', 'base')
		glyph = parseGlyph(line[1])
		data, anchorClass = Data[typ]
		assert glyph not in data
		klass = int(line[2])
		anchor = makeAnchor(line[3:], anchorClass)
		if typ == 'mark':
			data[glyph] = (klass, anchor)
		else:
			data[(glyph, klass)] = anchor

	markArray, markCoverage = makeMarkArrayAndCoverage(markData, font, c)
	setattr(self, c.MarkCoverage, markCoverage)
	setattr(self, c.MarkArray, markArray)
	self.classCount = 0 if not baseData else 1+max(k[1] for k,v in baseData.items())
	baseArray, baseCoverage = makeBaseArrayAndCoverage(baseData, self.classCount, font, c)
	setattr(self, c.BaseCoverage, baseCoverage)
	setattr(self, c.BaseArray, baseArray)


class MarkHelper(object):
	def __init__(self):
		for Which in ('Mark', 'Base'):
			for What in ('Coverage', 'Array', 'Count', 'Record', 'Anchor'):
				key = Which + What
				if Which == 'Mark' and What in ('Count', 'Record', 'Anchor'):
					value = key
				else:
					value = getattr(self, Which) + What
				setattr(self, key, value)
				if What != 'Count':
					klass = getattr(ot, value)
					setattr(self, key+'Class', klass)

class MarkToBaseHelper(MarkHelper):
	Mark = 'Mark'
	Base = 'Base'
class MarkToMarkHelper(MarkHelper):
	Mark = 'Mark1'
	Base = 'Mark2'

def parseMarkToBase(self, lines, font):
	return parseMarkToSomething(self, lines, font, MarkToBaseHelper())
def parseMarkToMark(self, lines, font):
	return parseMarkToSomething(self, lines, font, MarkToMarkHelper())

def parseMarkToLigature(self, lines, font):
	self.Format = 1
	self.MarkArray = []
	self.LigatureArray = []
	raise NotImplementedError

def stripSplitComma(line):
	return [s.strip() for s in line.split(',')] if line else []

def intSplitComma(line):
	return [int(i) for i in line.split(',')] if line else []

# Copied from fontTools.subset
class ContextHelper(object):
	def __init__(self, klassName, Format):
		if klassName.endswith('Subst'):
			Typ = 'Sub'
			Type = 'Subst'
		else:
			Typ = 'Pos'
			Type = 'Pos'
		if klassName.startswith('Chain'):
			Chain = 'Chain'
			InputIdx = 1
			DataLen = 3
		else:
			Chain = ''
			InputIdx = 0
			DataLen = 1
		ChainTyp = Chain+Typ

		self.Typ = Typ
		self.Type = Type
		self.Chain = Chain
		self.ChainTyp = ChainTyp
		self.InputIdx = InputIdx
		self.DataLen = DataLen

		self.LookupRecord = Type+'LookupRecord'

		if Format == 1:
			Coverage = lambda r: r.Coverage
			ChainCoverage = lambda r: r.Coverage
			ContextData = lambda r:(None,)
			ChainContextData = lambda r:(None, None, None)
			SetContextData = None
			SetChainContextData = None
			RuleData = lambda r:(r.Input,)
			ChainRuleData = lambda r:(r.Backtrack, r.Input, r.LookAhead)
			def SetRuleData(r, d):
				(r.Input,) = d
				(r.GlyphCount,) = (len(x)+1 for x in d)
			def ChainSetRuleData(r, d):
				(r.Backtrack, r.Input, r.LookAhead) = d
				(r.BacktrackGlyphCount,r.InputGlyphCount,r.LookAheadGlyphCount,) = (len(d[0]),len(d[1])+1,len(d[2]))
		elif Format == 2:
			Coverage = lambda r: r.Coverage
			ChainCoverage = lambda r: r.Coverage
			ContextData = lambda r:(r.ClassDef,)
			ChainContextData = lambda r:(r.BacktrackClassDef,
						     r.InputClassDef,
						     r.LookAheadClassDef)
			def SetContextData(r, d):
				(r.ClassDef,) = d
			def SetChainContextData(r, d):
				(r.BacktrackClassDef,
				 r.InputClassDef,
				 r.LookAheadClassDef) = d
			RuleData = lambda r:(r.Class,)
			ChainRuleData = lambda r:(r.Backtrack, r.Input, r.LookAhead)
			def SetRuleData(r, d):
				(r.Class,) = d
				(r.GlyphCount,) = (len(x)+1 for x in d)
			def ChainSetRuleData(r, d):
				(r.Backtrack, r.Input, r.LookAhead) = d
				(r.BacktrackGlyphCount,r.InputGlyphCount,r.LookAheadGlyphCount,) = (len(d[0]),len(d[1])+1,len(d[2]))
		elif Format == 3:
			Coverage = lambda r: r.Coverage[0]
			ChainCoverage = lambda r: r.InputCoverage[0]
			ContextData = None
			ChainContextData = None
			SetContextData = None
			SetChainContextData = None
			RuleData = lambda r: r.Coverage
			ChainRuleData = lambda r:(r.BacktrackCoverage +
						  r.InputCoverage +
						  r.LookAheadCoverage)
			def SetRuleData(r, d):
				(r.Coverage,) = d
				(r.GlyphCount,) = (len(x) for x in d)
			def ChainSetRuleData(r, d):
				(r.BacktrackCoverage, r.InputCoverage, r.LookAheadCoverage) = d
				(r.BacktrackGlyphCount,r.InputGlyphCount,r.LookAheadGlyphCount,) = (len(x) for x in d)
		else:
			assert 0, "unknown format: %s" % Format

		if Chain:
			self.Coverage = ChainCoverage
			self.ContextData = ChainContextData
			self.SetContextData = SetChainContextData
			self.RuleData = ChainRuleData
			self.SetRuleData = ChainSetRuleData
		else:
			self.Coverage = Coverage
			self.ContextData = ContextData
			self.SetContextData = SetContextData
			self.RuleData = RuleData
			self.SetRuleData = SetRuleData

		if Format == 1:
			self.Rule = ChainTyp+'Rule'
			self.RuleCount = ChainTyp+'RuleCount'
			self.RuleSet = ChainTyp+'RuleSet'
			self.RuleSetCount = ChainTyp+'RuleSetCount'
			self.Intersect = lambda glyphs, c, r: [r] if r in glyphs else []
		elif Format == 2:
			self.Rule = ChainTyp+'ClassRule'
			self.RuleCount = ChainTyp+'ClassRuleCount'
			self.RuleSet = ChainTyp+'ClassSet'
			self.RuleSetCount = ChainTyp+'ClassSetCount'
			self.Intersect = lambda glyphs, c, r: (c.intersect_class(glyphs, r) if c
							       else (set(glyphs) if r == 0 else set()))

			self.ClassDef = 'InputClassDef' if Chain else 'ClassDef'
			self.ClassDefIndex = 1 if Chain else 0
			self.Input = 'Input' if Chain else 'Class'

def parseLookupRecords(items, klassName):
	klass = getattr(ot, klassName)
	lst = []
	for item in items:
		rec = klass()
		item = intSplitComma(item)
		assert len(item) == 2, item
		assert item[0] > 0, item[0]
		rec.SequenceIndex = item[0] - 1
		# TODO The following line should use lazy lookup name-to-index mapping
		rec.LookupListIndex = item[1]
		lst.append(rec)
	return lst

def makeClassDef(classDefs, klass=ot.Coverage):
	self = klass()
	self.classDefs = dict(classDefs)
	return self

def parseClassDef(lines, klass=ot.ClassDef):
	line = next(lines)
	assert line[0].lower().endswith('class definition begin'), line
	classDefs = {}
	for line in lines.readUntil('class definition end'):
		classDefs[parseGlyph(line[0])] = int(line[1])
	return makeClassDef(classDefs, klass)

def makeCoverage(glyphs, font, klass=ot.Coverage):
	coverage = klass()
	coverage.glyphs = sorted(set(glyphs), key=font.getGlyphID)
	return coverage

def parseCoverage(lines, font, klass=ot.Coverage):
	line = next(lines)
	assert line[0].lower().endswith('coverage definition begin'), line
	glyphs = []
	for line in lines.readUntil('coverage definition end'):
		glyphs.append(parseGlyph(line[0]))
	return makeCoverage(glyphs, font, klass)

def bucketizeRules(self, c, rules, bucketKeys):
	buckets = {}
	for seq,recs in rules:
		buckets.setdefault(seq[c.InputIdx][0], []).append((tuple(s[1 if i==c.InputIdx else 0:] for i,s in enumerate(seq)), recs))

	rulesets = []
	for firstGlyph in bucketKeys:
		if firstGlyph not in buckets:
			rulesets.append(None)
			continue
		thisRules = []
		for seq,recs in buckets[firstGlyph]:
			rule = getattr(ot, c.Rule)()
			c.SetRuleData(rule, seq)
			setattr(rule, c.Type+'Count', len(recs))
			setattr(rule, c.LookupRecord, recs)
			thisRules.append(rule)

		ruleset = getattr(ot, c.RuleSet)()
		setattr(ruleset, c.Rule, thisRules)
		setattr(ruleset, c.RuleCount, len(thisRules))
		rulesets.append(ruleset)

	setattr(self, c.RuleSet, rulesets)
	setattr(self, c.RuleSetCount, len(rulesets))

def parseContext(self, lines, font, Type):
	typ = lines.peek()[0].split()[0].lower()
	if typ == 'glyph':
		self.Format = 1
		debug("Parsing %s format %s" % (Type, self.Format))
		c = ContextHelper(Type, self.Format)
		rules = []
		for line in lines:
			assert line[0].lower() == 'glyph', line[0]
			seq = tuple(parseGlyphs(stripSplitComma(i)) for i in line[1:1+c.DataLen])
			recs = parseLookupRecords(line[1+c.DataLen:], c.LookupRecord)
			rules.append((seq, recs))

		firstGlyphs = set(seq[c.InputIdx][0] for seq,recs in rules)
		self.Coverage = makeCoverage(firstGlyphs, font)
		bucketizeRules(self, c, rules, self.Coverage.glyphs)
	elif typ.endswith('class'):
		self.Format = 2
		debug("Parsing %s format %s" % (Type, self.Format))
		c = ContextHelper(Type, self.Format)
		classDefs = [None] * c.DataLen
		while lines.peek()[0].endswith("class definition begin"):
			typ = lines.peek()[0][:-len("class definition begin")].lower()
			idx,klass = {
			1: {
				'':		(0,ot.ClassDef),
			},
			3: {
				'backtrack':	(0,ot.BacktrackClassDef),
				'':		(1,ot.InputClassDef),
				'lookahead':	(2,ot.LookAheadClassDef),
			},
			}[c.DataLen][typ]
			assert classDefs[idx] is None, idx
			classDefs[idx] = parseClassDef(lines, klass=klass)
		c.SetContextData(self, classDefs)
		rules = []
		for line in lines:
			assert line[0].lower().startswith('class'), line[0]
			seq = tuple(intSplitComma(i) for i in line[1:1+c.DataLen])
			recs = parseLookupRecords(line[1+c.DataLen:], c.LookupRecord)
			rules.append((seq, recs))
		firstClasses = set(seq[c.InputIdx][0] for seq,recs in rules)
		firstGlyphs = set(g for g,c in classDefs[c.InputIdx].classDefs.items() if c in firstClasses)
		self.Coverage = makeCoverage(firstGlyphs, font)
		bucketizeRules(self, c, rules, range(max(firstClasses) + 1))
	elif typ.endswith('coverage'):
		self.Format = 3
		debug("Parsing %s format %s" % (Type, self.Format))
		c = ContextHelper(Type, self.Format)
		coverages = tuple([] for i in range(c.DataLen))
		while lines.peek()[0].endswith("coverage definition begin"):
			typ = lines.peek()[0][:-len("coverage definition begin")].lower()
			idx,klass = {
			1: {
				'':		(0,ot.Coverage),
			},
			3: {
				'backtrack':	(0,ot.BacktrackCoverage),
				'input':	(1,ot.InputCoverage),
				'lookahead':	(2,ot.LookAheadCoverage),
			},
			}[c.DataLen][typ]
			coverages[idx].append(parseCoverage(lines, font, klass=klass))
		c.SetRuleData(self, coverages)
		lines = list(lines)
		assert len(lines) == 1
		line = lines[0]
		assert line[0].lower() == 'coverage', line[0]
		recs = parseLookupRecords(line[1:], c.LookupRecord)
		setattr(self, c.Type+'Count', len(recs))
		setattr(self, c.LookupRecord, recs)
	else:
		assert 0, typ

def parseContextSubst(self, lines, font):
	return parseContext(self, lines, font, "ContextSubst")
def parseContextPos(self, lines, font):
	return parseContext(self, lines, font, "ContextPos")
def parseChainedSubst(self, lines, font):
	return parseContext(self, lines, font, "ChainContextSubst")
def parseChainedPos(self, lines, font):
	return parseContext(self, lines, font, "ChainContextPos")

def parseReverseChainedSubst(self, lines, font):
	self.Format = 1
	coverages = ([], [])
	while lines.peek()[0].endswith("coverage definition begin"):
		typ = lines.peek()[0][:-len("coverage definition begin")].lower()
		idx,klass = {
			'backtrack':	(0,ot.BacktrackCoverage),
			'lookahead':	(1,ot.LookAheadCoverage),
		}[typ]
		coverages[idx].append(parseCoverage(lines, font, klass=klass))
	self.BacktrackCoverage = coverages[0]
	self.BacktrackGlyphCount = len(self.BacktrackCoverage)
	self.LookAheadCoverage = coverages[1]
	self.LookAheadGlyphCount = len(self.LookAheadCoverage)
	mapping = {}
	for line in lines:
		assert len(line) == 2, line
		line = parseGlyphs(line)
		mapping[line[0]] = line[1]
	self.Coverage = makeCoverage(mapping.keys(), font)
	self.Substitute = [mapping[k] for k in self.Coverage.glyphs]
	self.GlyphCount = len(self.Substitute)

def parseLookup(lines, tableTag, font):
	line = lines.skipUntil('lookup')
	if line is None: return None, None
	lookupLines = lines.readUntil('lookup end')
	_, name, typ = line
	debug("Parsing lookup type %s %s" % (typ, name))

	lookup = ot.Lookup()
	lookup.LookupFlag,filterset = parseLookupFlags(lookupLines)
	if filterset is not None:
		lookup.MarkFilteringSet = filterset
	lookup.LookupType, parseLookupSubTable = {
		'GSUB': {
			'single':	(1,	parseSingleSubst),
			'multiple':	(2,	parseMultiple),
			'alternate':	(3,	parseAlternate),
			'ligature':	(4,	parseLigature),
			'context':	(5,	parseContextSubst),
			'chained':	(6,	parseChainedSubst),
			'reversechained':(8,	parseReverseChainedSubst),
		},
		'GPOS': {
			'single':	(1,	parseSinglePos),
			'pair':		(2,	parsePair),
			'kernset':	(2,	parseKernset),
			'cursive':	(3,	parseCursive),
			'mark to base':	(4,	parseMarkToBase),
			'mark to ligature':(5,	parseMarkToLigature),
			'mark to mark':	(6,	parseMarkToMark),
			'context':	(7,	parseContextPos),
			'chained':	(8,	parseChainedPos),
		},
	}[tableTag][typ]

	subtables = []

	while True:
		subLookupLines = lookupLines.readUntil(('% subtable', 'subtable end'))
		if subLookupLines.peek() is None:
			break
		subtable = ot.lookupTypes[tableTag][lookup.LookupType]()
		subtable.LookupType = lookup.LookupType
		try:
			parseLookupSubTable(subtable, subLookupLines, font)
		except NotImplementedError:
			list(subLookupLines) # Exhaust subLookupLines
			continue
		assert subLookupLines.peek() is None
		subtables.append(subtable)

	lookup.SubTable = subtables
	lookup.SubTableCount = len(lookup.SubTable)
	if lookup.SubTableCount is 0:
		return None, name
	return lookup, name

def parseLookupList(lines, tableTag, font):
	debug("Parsing lookup list")
	self = ot.LookupList()
	self.Lookup = []
	while True:
		lookup, name = parseLookup(lines, tableTag, font)
		if name is None: break
		assert int(name) == len(self.Lookup), "%d %d" % (name, len(self.Lookup))
		self.Lookup.append(lookup)
	self.LookupCount = len(self.Lookup)
	return self

def parseGSUB(lines, font):
	debug("Parsing GSUB")
	self = ot.GSUB()
	self.Version = 1.0
	self.ScriptList = parseScriptList(lines)
	self.FeatureList = parseFeatureList(lines)
	self.LookupList = parseLookupList(lines, 'GSUB', font)
	return self

def parseGPOS(lines, font):
	debug("Parsing GPOS")
	self = ot.GPOS()
	self.Version = 1.0
	# TODO parse EM?
	self.ScriptList = parseScriptList(lines)
	self.FeatureList = parseFeatureList(lines)
	self.LookupList = parseLookupList(lines, 'GPOS', font)
	return self

def parseGDEF(lines, font):
	debug("Parsing GDEF TODO")
	return None


class ReadUntilMixin(object):

	def _readUntil(self, what):
		if type(what) is not tuple:
			what = (what,)
		for line in self:
			if line[0].lower() in what:
				raise StopIteration
			yield line
	def readUntil(self, what):
		return BufferedIter(self._readUntil(what))

class BufferedIter(ReadUntilMixin):

	def __init__(self, it):
		self.iter = it
		self.buffer = []

	def __iter__(self):
		return self

	def next(self):
		if self.buffer:
			return self.buffer.pop(0)
		else:
			return self.iter.next()

	def peek(self, n=0):
		"""Return an item n entries ahead in the iteration."""
		while n >= len(self.buffer):
			try:
				self.buffer.append(self.iter.next())
			except StopIteration:
				return None
		return self.buffer[n]

	def pack(self, item):
		"""Push back item into the iterator."""
		self.buffer.insert(0, item)

class Tokenizer(ReadUntilMixin):

	def __init__(self, f):
		# TODO BytesIO / StringIO as needed?  also, figure out whether we work on bytes or unicode

		lines = iter(f)
		lines = ([s.strip() for s in line.split('\t')] for line in lines)
		try:
			self.filename = f.name
		except:
			self.filename = None
		self._lines = lines
		self._lineno = 0

	def __iter__(self):
		return self

	def _next(self):
		self._lineno += 1
		return next(self._lines)

	def next(self):
		while True:
			line = self._next()
			# Skip comments and empty lines
			if line[0] and (line[0][0] != '%' or line[0] == '% subtable'):
				return line

	def skipUntil(self, what):
		for line in self:
			if line[0].lower() == what:
				return line

def parseTable(lines, font):
	debug("Parsing table")
	line = next(lines)
	assert line[0][:9] == 'FontDame ', line
	assert line[0][13:] == ' table', line
	tableTag = line[0][9:13]
	container = ttLib.getTableClass(tableTag)()
	table = {'GSUB': parseGSUB,
		 'GPOS': parseGPOS,
		 'GDEF': parseGDEF,
		}[tableTag](lines, font)
	container.table = table
	return container

def build(f, font):
	lines = Tokenizer(f)
	return parseTable(lines, font)


class MockFont(object):

	def __init__(self):
		self._glyphOrder = ['.notdef']
		self._reverseGlyphOrder = {'.notdef': 0}
		self.lazy = False

	def getGlyphID(self, glyph, requireReal=None):
		gid = self._reverseGlyphOrder.get(glyph, None)
		if gid is None:
			gid = len(self._glyphOrder)
			self._glyphOrder.append(glyph)
			self._reverseGlyphOrder[glyph] = gid
		return gid

	def getGlyphName(self, gid):
		return self._glyphOrder[gid]

	def getGlyphOrder(self):
		return self._glyphOrder

def main(args):
	font = MockFont()
	for f in args:
		debug("Processing", f)
		table = build(open(f, 'rt'), font)
		blob = table.compile(font)
		decompiled = table.__class__()
		decompiled.decompile(blob, font)

		continue
		from fontTools.misc import xmlWriter
		tag = table.tableTag
		writer = xmlWriter.XMLWriter(sys.stdout)
		writer.begintag(tag)
		writer.newline()
		#table.toXML(writer, font)
		decompiled.toXML(writer, font)
		writer.endtag(tag)
		writer.newline()

if __name__ == '__main__':
	import sys
	main (sys.argv[1:])
