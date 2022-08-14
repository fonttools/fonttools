
from fontTools import ttLib
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.ttLib.tables import otTables
from fontTools.merge.base import add_method, mergeObjects
from fontTools.merge.util import *
import fontTools.merge.classify_context

def _convertList(lst, fromType, toType):
	new_list = []
	for item in lst:
		if item is not None:
			assert type(item) == fromType, (type(item), fromType)
			new_item = toType()
			new_item.__dict__ = item.__dict__
			item = new_item
		new_list.append(item)
	return new_list

@add_method(otTables.SingleSubst,
		otTables.MultipleSubst,
		otTables.AlternateSubst,
		otTables.LigatureSubst)
def upgrade64k(self, reverseGlyphMap):
	# These are handled in otTables
	pass

@add_method(otTables.ReverseChainSingleSubst,
		otTables.SinglePos,
		otTables.CursivePos)
def upgrade64k(self, reverseGlyphMap):
	# Nothing to do
	pass

@add_method(otTables.PairPos)
def upgrade64k(self, reverseGlyphMap):
	upgrade = False

	if self.Format == 1:
		if self.PairSetCount > 65535:
			upgrade = True
		if not upgrade:
			for ps in self.PairSet:
				if not ps: continue
				for pvr in ps.PairValueRecord:
					if reverseGlyphMap[pvr.SecondGlyph] > 65535:
						upgrade = True
						break
				if upgrade: break

		if upgrade:
			self.PairSet = _convertList(self.PairSet, otTables.PairSet, otTables.PairSet24)
			for ps in self.PairSet:
				if not ps: continue
				ps.PairValueRecord = _convertList(ps.PairValueRecord, otTables.PairValueRecord, otTables.PairValue24Record)

	elif self.Format == 2:
		# To use longer offsets
		upgrade = True

	if upgrade:
		self.Format += 2

@add_method(otTables.MarkBasePos,
		otTables.MarkLigPos,
		otTables.MarkMarkPos)
def upgrade64k(self, reverseGlyphMap):
	# To use longer offsets
	if self.Format == 1:
		self.Format = 2

@add_method(otTables.ContextSubst,
		otTables.ChainContextSubst,
		otTables.ContextPos,
		otTables.ChainContextPos)
def upgrade64k(self, reverseGlyphMap):
	upgrade = False
	c = self.__merge_classify_context()

	if self.Format == 1:
		for rs in getattr(self, c.RuleSet):
			if not rs: continue
			for r in getattr(rs, c.Rule):
				if not r: continue
				for s in ['Backtrack', 'Input', 'LookAhead']:
					if not hasattr(r, s): continue
					seq = getattr(r, s)
					for glyph in seq:
						if reverseGlyphMap[glyph] > 65535:
							upgrade = True
							break
				if upgrade: break
			if upgrade: break

		if upgrade:
			rss = getattr(self, c.RuleSet)
			rss = _convertList(rss, getattr(otTables, c.RuleSet), getattr(otTables, c.RuleSet+'24'))
			setattr(self, c.RuleSet, rss)
			for rs in rss:
				if not rs: continue
				r = getattr(rs, c.Rule)
				r = _convertList(r, getattr(otTables, c.Rule), getattr(otTables, c.Rule+'24'))
				setattr(rs, c.Rule, r)

	elif self.Format == 2:
		# To use longer offsets
		upgrade = True

	if upgrade:
		self.Format += 3

@add_method(otTables.ExtensionSubst,
		otTables.ExtensionPos)
def upgrade64k(self, reverseGlyphMap):
	if self.Format == 1:
		self.ExtSubTable.upgrade64k(reverseGlyphMap)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(otTables.Lookup)
def upgrade64k(self, reverseGlyphMap):
	for st in self.SubTable:
		if not st: continue
		st.upgrade64k(reverseGlyphMap)

@add_method(otTables.LookupList24)
def upgrade64k(self, reverseGlyphMap):
	for l in self.Lookup:
		if not l: continue
		l.upgrade64k(reverseGlyphMap)

@add_method(otTables.GSUB,
		otTables.GPOS)
def upgrade64k(self, reverseGlyphMap):
	if self.Version < 0x00020000:
		self.ScriptList24 = self.ScriptList
		self.FeatureList24 = self.FeatureList
		self.LookupList24 = otTables.LookupList24()
		self.LookupList24.Lookup = self.LookupList.Lookup
		self.Version = 0x00020000
	self.LookupList24.upgrade64k(reverseGlyphMap)

@add_method(otTables.GDEF)
def upgrade64k(self, reverseGlyphMap):
	if self.Version < 0x00020000:
		self.GlyphClassDef24 = self.GlyphClassDef
		self.AttachList24 = self.AttachList
		self.LigCaretList24 = self.LigCaretList
		self.MarkAttachClassDef24 = self.MarkAttachClassDef
		self.MarkGlyphSetsDef24 = self.MarkGlyphSetsDef
		self.Version = 0x00020000
