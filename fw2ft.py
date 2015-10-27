#!/usr/bin/python

# FontWorker-to-FontTools for OpenType Layout tables

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
		langSys.FeatureIndex = [int(f) for f in features.split(',')]
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
		feature.LookupListIndex = [int(l) for l in lookups.split(',')]
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

def parseSingleSubst(self, lines):
	self.mapping = {}
	for line in lines:
		assert len(line) == 2, line
		self.mapping[line[0]] = line[1]

def parseMultiple(self, lines):
	self.mapping = {}
	for line in lines:
		self.mapping[line[0]] = line[1:]

def parseAlternate(self, lines):
	self.alternates = {}
	for line in lines:
		self.alternates[line[0]] = line[1:]

def parseLigature(self, lines):
	self.ligatures = {}
	for line in lines:
		assert len(line) >= 2, line
		ligGlyph, firstGlyph = line[:2]
		otherComponents = line[2:]
		ligature = ot.Ligature()
		ligature.Component = otherComponents
		ligature.CompCount = len(ligature.Component) + 1
		ligature.LigGlyph = ligGlyph
		self.ligatures.setdefault(firstGlyph, []).append(ligature)

def parseSinglePos(self, lines):
	raise NotImplementedError

def parsePair(self, lines):
	raise NotImplementedError

def parseCursive(self, lines):
	raise NotImplementedError

def parseMarkToSomething(self, lines):
	raise NotImplementedError

def parseMarkToLigature(self, lines):
	raise NotImplementedError

def parseContext(self, lines):
	typ = lines.peek()[0]
	if typ == 'glyph':
		self.Format = 1
		return
	elif typ == 'class definition begin':
		self.Format = 2
		return
	print(typ)
	raise NotImplementedError

def parseChained(self, lines):
	typ = lines.peek()[0]
	if typ == 'glyph':
		self.Format = 1
		return
	elif typ == 'backtrackclass definition begin':
		self.Format = 2
		return
	print(typ)
	raise NotImplementedError

def parseLookupList(lines, tableTag):
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
				'context':	(5,	parseContext),
				'chained':	(6,	parseChained),
			},
			'GPOS': {
				'single':	(1,	parseSinglePos),
				'pair':		(2,	parsePair),
				'kernset':	(2,	parsePair),
				'cursive':	(3,	parseCursive),
				'mark to base':	(4,	parseMarkToSomething),
				'mark to ligature':(5,	parseMarkToLigature),
				'mark to mark':	(6,	parseMarkToSomething),
				'context':	(7,	parseContext),
				'chained':	(8,	parseChained),
			},
		}[tableTag][typ]
		subtable = ot.lookupTypes[tableTag][lookup.LookupType]()
		subtable.LookupType = lookup.LookupType

		parseLookupSubTable(subtable, lookupLines)

		lookup.SubTable = [subtable]
		lookup.SubTableCount = len(lookup.SubTable)

	self.LookupCount = len(self.Lookup)
	return self

def parseGSUB(lines):
	debug("Parsing GSUB")
	self = ot.GSUB()
	self.Version = 1.0
	self.ScriptList = parseScriptList(lines)
	self.FeatureList = parseFeatureList(lines)
	self.LookupList = parseLookupList(lines, 'GSUB')
	return self

def parseGPOS(lines):
	debug("Parsing GPOS")
	self = ot.GPOS()
	self.Version = 1.0
	# TODO parse EM?
	self.ScriptList = parseScriptList(lines)
	self.FeatureList = parseFeatureList(lines)
	self.LookupList = parseLookupList(lines, 'GPOS')
	return self

def parseGDEF(lines):
	debug("Parsing GDEF TODO")
	return None

class BufferedIter(object):

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

class Tokenizer(object):

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

	def _readUntil(self, what):
		for line in self:
			if line[0] == what:
				raise StopIteration
			yield line
	def readUntil(self, what):
		return BufferedIter(self._readUntil(what))

def compile(f):
	lines = Tokenizer(f)
	line = next(lines)
	assert line[0][:9] == 'FontDame ', line
	assert line[0][13:] == ' table', line
	tableTag = line[0][9:13]
	container = ttLib.getTableClass(tableTag)()
	table = {'GSUB': parseGSUB,
		 'GPOS': parseGPOS,
		 'GDEF': parseGDEF,
		}[tableTag](lines)
	container.table = table
	return container


class MockFont(object):

	def __init__(self):
		self._glyphOrder = ['.notdef']
		self._reverseGlyphOrder = {'.notdef': 0}

	def getGlyphID(self, glyph):
		gid = self._reverseGlyphOrder.get(glyph, None)
		if gid is None:
			gid = len(self._glyphOrder)
			self._glyphOrder.append(glyph)
			self._reverseGlyphOrder[glyph] = gid
		return gid

	def getGlyphName(self, gid):
		return self._glyphOrder[gid]

if __name__ == '__main__':
	import sys
	font = MockFont()
	for f in sys.argv[1:]:
		debug("Processing", f)
		table = compile(open(f, 'rt'))
		blob = table.compile(font)

