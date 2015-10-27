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


def parseSingleSubst(self, lines):
	self.mapping = {}
	for line in lines:
		assert len(line) == 2, line
		self.mapping[line[0]] = line[1]

def parseMultiple(self, lines):
	debug(line)
	raise NotImplementedError

def parseAlternate(self, lines):
	debug(line)
	raise NotImplementedError

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
		if firstGlyph not in self.ligatures:
			self.ligatures[firstGlyph] = []
		self.ligatures[firstGlyph].append(ligature)

def parseSinglePos(self, lines):
	debug(line)
	raise NotImplementedError

def parsePair(self, lines):
	debug(line)
	raise NotImplementedError

def parseCursive(self, lines):
	debug(line)
	raise NotImplementedError

def parseMarkToSomething(self, lines):
	debug(line)
	raise NotImplementedError

def parseMarkToLigature(self, lines):
	debug(line)
	raise NotImplementedError

def parseContext(self, lines):
	raise NotImplementedError
	typ = line[0]
	print(line)
	if typ == 'glyph':
		return
	raise NotImplementedError

def parseChained(self, lines):
	debug(line)
	raise NotImplementedError

def parseLookupList(lines, tableTag):
	self = ot.LookupList()
	self.Lookup = []
	while True:
		line = lines.skipUntil('lookup')
		if line is None: break
		_, idx, typ = line
		assert int(idx) == len(self.Lookup), "%d %d" % (idx, len(self.Lookup))

		lookup = ot.Lookup()
		self.Lookup.append(lookup)
		lookup.LookupFlags = 0
		lookup.LookupType, parseLookup = {
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

		lookupLines = lines.readUntil('lookup end')
		for line in lookupLines:
			flag = {
				'RightToLeft':		0x0001,
				'IgnoreBaseGlyphs':	0x0002,
				'IgnoreLigatures':	0x0004,
				'IgnoreMarks':		0x0008,
				}.get(line[0])
			if flag:
				assert line[1] in ['yes', 'no'], line[1]
				if line[1] == 'yes':
					lookup.LookupFlags |= flag
				continue
			if line[0] == 'MarkAttachmentType':
				lookup.LookupFlags |= int(line[1]) << 8
				continue
			break
		parseLookup(subtable, lookupLines)

		lookup.SubTable = [subtable]
		lookup.SubTableCount = len(lookup.SubTable)

	self.LookupCount = len(self.Lookup)
	return self

def parseGSUB(lines):
	debug("Parsing GSUB")
	self = ot.GSUB()
	self.ScriptList = parseScriptList(lines)
	self.FeatureList = parseFeatureList(lines)
	self.LookupList = parseLookupList(lines, 'GSUB')
	return self

def parseGPOS(lines):
	debug("Parsing GPOS")
	self = ot.GPOS()
	# TODO parse EM?
	self.ScriptList = parseScriptList(lines)
	self.FeatureList = parseFeatureList(lines)
	self.LookupList = parseLookupList(lines, 'GPOS')
	return self

def parseGDEF(lines):
	debug("Parsing GDEF TODO")
	return None

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

	def readUntil(self, what):
		for line in self:
			if line[0] == what:
				raise StopIteration
			yield line


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

if __name__ == '__main__':
	import sys
	for f in sys.argv[1:]:
		debug("Processing", f)
		compile(open(f, 'rt'))

