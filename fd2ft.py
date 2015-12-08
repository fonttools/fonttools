#!/usr/bin/python

# FontDame-to-FontTools for OpenType Layout tables
#
# Source language spec is available at:
# https://rawgit.com/Monotype/OpenType_Table_Source/master/otl_source.html
# https://github.com/Monotype/OpenType_Table_Source/

from __future__ import print_function, division, absolute_import
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot
import re

debug = print

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
	for line in lines:
		flag = {
			'RightToLeft':		0x0001,
			'IgnoreBaseGlyphs':	0x0002,
			'IgnoreLigatures':	0x0004,
			'IgnoreMarks':		0x0008,
			}.get(line[0])
		if flag:
			assert line[1] in ['yes', 'no'], line[1]
			if line[1] == 'yes':
				flags |= flag
			continue
		if line[0] == 'MarkAttachmentType':
			flags |= int(line[1]) << 8
			continue
		lines.pack(line)
		break
	return flags

def parseClassDef(lines, klass=ot.ClassDef):
	line = next(lines)
	assert line[0].endswith('class definition begin'), line
	self = klass()
	classDefs = self.classDefs = {}
	for line in lines.readUntil('class definition end'):
		classDefs[line[0]] = int(line[1])
	return self

def parseSingleSubst(self, lines, font):
	self.mapping = {}
	for line in lines:
		assert len(line) == 2, line
		self.mapping[line[0]] = line[1]

def parseMultiple(self, lines, font):
	self.mapping = {}
	for line in lines:
		self.mapping[line[0]] = line[1:]

def parseAlternate(self, lines, font):
	self.alternates = {}
	for line in lines:
		self.alternates[line[0]] = line[1:]

def parseLigature(self, lines, font):
	self.ligatures = {}
	for line in lines:
		assert len(line) >= 2, line
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
	raise NotImplementedError

def parsePair(self, lines, font):
	raise NotImplementedError

def parseCursive(self, lines, font):
	raise NotImplementedError

def parseMarkToSomething(self, lines, font):
	raise NotImplementedError

def parseMarkToLigature(self, lines, font):
	raise NotImplementedError

def stripSplitComma(line):
	return [s.strip() for s in line.split(',')]

def intSplitComma(line):
	return [int(i) for i in line.split(',')]

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
		else:
			Chain = ''
		ChainTyp = Chain+Typ

		self.Typ = Typ
		self.Type = Type
		self.Chain = Chain
		self.ChainTyp = ChainTyp

		self.LookupRecord = Type+'LookupRecord'

		if Format == 1:
			Coverage = lambda r: r.Coverage
			ChainCoverage = lambda r: r.Coverage
			ContextData = lambda r:(None,)
			ChainContextData = lambda r:(None, None, None)
			RuleData = lambda r:(r.Input,)
			ChainRuleData = lambda r:(r.Backtrack, r.Input, r.LookAhead)
			SetRuleData = None
			ChainSetRuleData = None
		elif Format == 2:
			Coverage = lambda r: r.Coverage
			ChainCoverage = lambda r: r.Coverage
			ContextData = lambda r:(r.ClassDef,)
			ChainContextData = lambda r:(r.BacktrackClassDef,
						     r.InputClassDef,
						     r.LookAheadClassDef)
			RuleData = lambda r:(r.Class,)
			ChainRuleData = lambda r:(r.Backtrack, r.Input, r.LookAhead)
			def SetRuleData(r, d):(r.Class,) = d
			def ChainSetRuleData(r, d):(r.Backtrack, r.Input, r.LookAhead) = d
		elif Format == 3:
			Coverage = lambda r: r.Coverage[0]
			ChainCoverage = lambda r: r.InputCoverage[0]
			ContextData = None
			ChainContextData = None
			RuleData = lambda r: r.Coverage
			ChainRuleData = lambda r:(r.BacktrackCoverage +
						  r.InputCoverage +
						  r.LookAheadCoverage)
			SetRuleData = None
			ChainSetRuleData = None
		else:
			assert 0, "unknown format: %s" % Format

		if Chain:
			self.Coverage = ChainCoverage
			self.ContextData = ChainContextData
			self.RuleData = ChainRuleData
			self.SetRuleData = ChainSetRuleData
		else:
			self.Coverage = Coverage
			self.ContextData = ContextData
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

def makeCoverage(glyphs, fonts):
	coverage = ot.Coverage()
	coverage.glyphs = sorted(set(glyphs), key=font.getGlyphID)
	return coverage

def bucketizeRules(self, c, rules, bucketKeys):
	buckets = {}
	for seq,recs in rules:
		buckets.setdefault(seq[0], []).append((seq[1:], recs))

	rulesets = []
	for firstGlyph in bucketKeys:
		if firstGlyph not in buckets:
			rulesets.append(None)
			continue
		thisRules = []
		for seq,recs in buckets[firstGlyph]:
			rule = getattr(ot, c.Rule)()
			rule.GlyphCount = 1 + len(seq)
			rule.Input = seq
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
	typ = lines.peek()[0]
	if typ == 'glyph':
		self.Format = 1
		c = ContextHelper('Context'+Type, self.Format)
		rules = []
		for line in lines:
			recs = parseLookupRecords(line[2:], c.LookupRecord)
			seq = stripSplitComma(line[1])
			rules.append((seq, recs))

		self.Coverage = makeCoverage((seq[0] for seq,recs in rules), font)

		bucketizeRules(self, c, rules, self.Coverage.glyphs)
		return

	elif typ == 'class definition begin':
		self.Format = 2
		c = ContextHelper('Context'+Type, self.Format)
		self.ClassDef = parseClassDef(lines)
		rules = []
		for line in lines:
			recs = parseLookupRecords(line[2:], c.LookupRecord)
			seq = intSplitComma(line[1])
			rules.append((seq, recs))

		self.Coverage = makeCoverage(self.ClassDef.classDefs.keys(), font)

		maxClass = max(seq[0] for seq,recs in rules)

		bucketizeRules(self, c, rules, range(maxClass + 1))

		return
	print(typ)
	raise NotImplementedError

def parseContextSubst(self, lines, font):
	return parseContext(self, lines, font, "Subst")
def parseContextPos(self, lines, font):
	return parseContext(self, lines, font, "Pos")

def parseChained(self, lines, font, Type):
	typ = lines.peek()[0]
	if typ == 'glyph':
		self.Format = 1
		for line in lines:
			print (line)
		return
	elif typ == 'backtrackclass definition begin':
		self.Format = 2
		return
	print(typ)
	raise NotImplementedError

def parseChainedSubst(self, lines, font):
	return parseChained(self, lines, font, "Subst")
def parseChainedPos(self, lines):
	return parseChained(self, lines, font, "Pos")

def parseLookupList(lines, tableTag, font):
	self = ot.LookupList()
	self.Lookup = []
	while True:
		line = lines.skipUntil('lookup')
		if line is None: break
		lookupLines = lines.readUntil('lookup end')
		_, idx, typ = line
		assert int(idx) == len(self.Lookup), "%d %d" % (idx, len(self.Lookup))

		lookup = ot.Lookup()
		self.Lookup.append(lookup)
		lookup.LookupFlag = parseLookupFlags(lookupLines)
		lookup.LookupType, parseLookupSubTable = {
			'GSUB': {
				'single':	(1,	parseSingleSubst),
				'multiple':	(2,	parseMultiple),
				'alternate':	(3,	parseAlternate),
				'ligature':	(4,	parseLigature),
				'context':	(5,	parseContextSubst),
				'chained':	(6,	parseChainedSubst),
			},
			'GPOS': {
				'single':	(1,	parseSinglePos),
				'pair':		(2,	parsePair),
				'kernset':	(2,	parsePair),
				'cursive':	(3,	parseCursive),
				'mark to base':	(4,	parseMarkToSomething),
				'mark to ligature':(5,	parseMarkToLigature),
				'mark to mark':	(6,	parseMarkToSomething),
				'context':	(7,	parseContextPos),
				'chained':	(8,	parseChainedPos),
			},
		}[tableTag][typ]
		subtable = ot.lookupTypes[tableTag][lookup.LookupType]()
		subtable.LookupType = lookup.LookupType

		parseLookupSubTable(subtable, lookupLines, font)

		lookup.SubTable = [subtable]
		lookup.SubTableCount = len(lookup.SubTable)

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
		for line in self:
			if line[0] == what:
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
			if line[0] not in ['', '%']:
				return line

	def skipUntil(self, what):
		for line in self:
			if line[0] == what:
				return line

def build(f, font):
	lines = Tokenizer(f)
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

if __name__ == '__main__':
	import sys
	font = MockFont()
	for f in sys.argv[1:]:
		debug("Processing", f)
		table = build(open(f, 'rt'), font)
		blob = table.compile(font)
		decompiled = table.__class__()
		decompiled.decompile(blob, font)

		#continue
		from fontTools.misc import xmlWriter
		tag = table.tableTag
		writer = xmlWriter.XMLWriter(sys.stdout)
		writer.begintag(tag)
		writer.newline()
		#table.toXML(writer, font)
		decompiled.toXML(writer, font)
		writer.endtag(tag)
		writer.newline()

