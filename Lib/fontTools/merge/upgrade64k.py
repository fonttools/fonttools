
from fontTools import ttLib
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.ttLib.tables import otTables
from fontTools.merge.base import add_method, mergeObjects
from fontTools.merge.util import *
import fontTools.merge.classify_context

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

	elif self.Format == 2:
		# To use longer offsets
		upgrade = True

	if upgrade:
		self.Format += 2

@add_method(otTables.SingleSubst,
		otTables.MultipleSubst,
		otTables.AlternateSubst,
		otTables.LigatureSubst,
		otTables.ReverseChainSingleSubst,
		otTables.SinglePos,
		otTables.CursivePos,
		otTables.MarkBasePos,
		otTables.MarkLigPos,
		otTables.MarkMarkPos)
def upgrade64k(self, reverseGlyphMap):
	NotImplemented

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

@add_method(otTables.LookupList)
def upgrade64k(self, reverseGlyphMap):
	for l in self.Lookup:
		if not l: continue
		l.upgrade64k(reverseGlyphMap)

