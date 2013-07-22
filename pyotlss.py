#!/usr/bin/python

# Python OpenType Layout Subsetter
# Writte by: Behdad Esfahbod

import fontTools.ttx


def add_method (*clazzes):
	def wrapper(method):
		for clazz in clazzes:
			setattr (clazz, method.func_name, method)
	return wrapper

# Subset

@add_method(fontTools.ttLib.tables.otTables.Coverage)
def subset (self, glyphs):
	indices = [i for (i,g) in enumerate (self.glyphs) if g in glyphs]
	self.glyphs = [g for g in self.glyphs if g in glyphs]
	return indices
	return True

@add_method(fontTools.ttLib.tables.otTables.ClassDef)
def subset (self, glyphs):
	self.classDefs = {g:v for g,v in self.classDefs.items() if g in glyphs}
	return True

@add_method(fontTools.ttLib.tables.otTables.SingleSubst)
def subset (self, glyphs):
	if self.Format in [1, 2]:
		self.mapping = {g:v for g,v in self.mapping.items() if g in glyphs}
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.MultipleSubst)
def subset (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset (glyphs)
		self.Sequence = [self.Sequence[i] for i in indices]
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.AlternateSubst)
def subset (self, glyphs):
	if self.Format == 1:
		self.alternates = {g:v for g,v in self.alternates.items() if g in glyphs}
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.LigatureSubst)
def subset (self, glyphs):
	self.ligatures = {g:v for g,v in self.ligatures.items() if g in glyphs}
	self.ligatures = {g:[seq for seq in seqs if all(c in glyphs for c in seq.Component)]
			  for g,seqs in self.ligatures.items()}
	self.ligatures = {g:v for g,v in self.ligatures.items() if v}
	return True

@add_method(fontTools.ttLib.tables.otTables.ReverseChainSingleSubst)
def subset (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset (glyphs)
		self.Substitute = [self.Substitute[i] for i in indices]
		self.GlyphCount = len (self.Substitute)
		for c in self.LookAheadCoverage:
			c.subset (glyphs)
		for c in self.BacktrackCoverage:
			c.subset (glyphs)
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.SinglePos)
def subset (self, glyphs):
	if self.Format == 1:
		self.Coverage.subset (glyphs)
	elif self.Format == 2:
		indices = self.Coverage.subset (glyphs)
		self.Value = [self.Value[i] for i in indices]
		self.ValueCount = len (self.Value)
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.PairPos)
def subset (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset (glyphs)
		self.PairSet = [self.PairSet[i] for i in indices]
		for p in self.PairSet:
			p.PairValueRecord = [r for r in p.PairValueRecord if r.SecondGlyph in glyphs]
			p.PairValueCount = len (p.PairValueRecord)
		# TODO Prune empty rules
		self.PairSetCount = len (self.PairSet)
	elif self.Format == 2:
		self.Coverage.subset (glyphs)
		self.ClassDef1.subset (glyphs)
		self.ClassDef2.subset (glyphs)
		# TODO Prune empty classes
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.CursivePos)
def subset (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset (glyphs)
		self.EntryExitRecord = [self.EntryExitRecord[i] for i in indices]
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.MarkBasePos)
def subset (self, glyphs):
	if self.Format == 1:
		mark_indices = self.MarkCoverage.subset (glyphs)
		self.MarkArray.MarkRecord = [self.MarkArray.MarkRecord[i] for i in mark_indices]
		self.MarkArray.MarkCount = len (self.MarkArray.MarkRecord)
		base_indices = self.BaseCoverage.subset (glyphs)
		self.BaseArray.BaseRecord = [self.BaseArray.BaseRecord[i] for i in base_indices]
		self.BaseArray.BaseCount = len (self.BaseArray.BaseRecord)
		# TODO Prune empty classes
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.MarkLigPos)
def subset (self, glyphs):
	if self.Format == 1:
		mark_indices = self.MarkCoverage.subset (glyphs)
		self.MarkArray.MarkRecord = [self.MarkArray.MarkRecord[i] for i in mark_indices]
		self.MarkArray.MarkCount = len (self.MarkArray.MarkRecord)
		ligature_indices = self.LigatureCoverage.subset (glyphs)
		self.LigatureArray.LigatureAttach = [self.LigatureArray.LigatureAttach[i] for i in ligature_indices]
		self.LigatureArray.LigatureCount = len (self.LigatureArray.LigatureAttach)
		# TODO Prune empty classes
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.MarkMarkPos)
def subset (self, glyphs):
	if self.Format == 1:
		mark1_indices = self.Mark1Coverage.subset (glyphs)
		self.Mark1Array.MarkRecord = [self.Mark1Array.MarkRecord[i] for i in mark1_indices]
		self.Mark1Array.MarkCount = len (self.Mark1Array.MarkRecord)
		mark2_indices = self.Mark2Coverage.subset (glyphs)
		self.Mark2Array.Mark2Record = [self.Mark2Array.Mark2Record[i] for i in mark2_indices]
		self.Mark2Array.MarkCount = len (self.Mark2Array.Mark2Record)
		# TODO Prune empty classes
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.ContextSubst, fontTools.ttLib.tables.otTables.ContextPos)
def subset (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset (glyphs)
		self.SubRuleSet = [self.SubRuleSet[i] for i in indices]
		self.SubRuleSetCount = len (self.SubRuleSet)
		for rs in self.SubRuleSet:
			rs.SubRule = [r for r in rs.SubRule
				      if all (g in glyphs for g in r.Input)]
			rs.SubRuleCount = len (rs.SubRule)
	elif self.Format == 2:
		self.Coverage.subset (glyphs)
		self.ClassDef.subset (glyphs)
		pass
	elif self.Format == 3:
		for c in self.Coverage:
			c.subset (glyphs)
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.ChainContextSubst, fontTools.ttLib.tables.otTables.ChainContextPos)
def subset (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset (glyphs)
		self.ChainSubRuleSet = [self.ChainSubRuleSet[i] for i in indices]
		self.ChainSubRuleSetCount = len (self.ChainSubRuleSet)
		for rs in self.ChainSubRuleSet:
			rs.ChainSubRule = [r for r in rs.ChainSubRule
					   if all (g in glyphs for g in r.Backtrack + r.Input + r.LookAhead)]
			rs.ChainSubRuleCount = len (rs.ChainSubRule)
	elif self.Format == 2:
		self.Coverage.subset (glyphs)
		self.LookAheadClassDef.subset (glyphs)
		self.BacktrackClassDef.subset (glyphs)
		self.InputClassDef.subset (glyphs)
	elif self.Format == 3:
		for c in self.InputCoverage:
			c.subset (glyphs)
		for c in self.LookAheadCoverage:
			c.subset (glyphs)
		for c in self.BacktrackCoverage:
			c.subset (glyphs)
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.ExtensionSubst, fontTools.ttLib.tables.otTables.ExtensionPos)
def subset (self, glyphs):
	if self.Format == 1:
		self.ExtSubTable.subset (glyphs)
	else:
		assert 0, "unknown format: %s" % self.Format
	return True

@add_method(fontTools.ttLib.tables.otTables.Lookup)
def subset (self, glyphs):
	self.SubTable = [s for s in self.SubTable if s.subset (glyphs)]
	return any (self.SubTable)

@add_method(fontTools.ttLib.tables.otTables.GSUB, fontTools.ttLib.tables.otTables.GPOS)
def subset (self, glyphs):
	self.LookupList.Lookup = [l for l in self.LookupList.Lookup if l.subset (glyphs)]

@add_method(fontTools.ttLib.tables.otTables.GDEF)
def subset (self, glyphs):
	if self.LigCaretList:
		indices = self.LigCaretList.Coverage.subset (glyphs)
		self.LigCaretList.LigGlyph = [self.LigCaretList.LigGlyph[i] for i in indices]
		self.LigCaretList.LigGlyphCount = len (self.LigCaretList.LigGlyph)
	if self.MarkAttachClassDef:
		self.MarkAttachClassDef.classDefs = {g:v for g,v in self.MarkAttachClassDef.classDefs.items() if g in glyphs}
	if self.GlyphClassDef:
		self.GlyphClassDef.classDefs = {g:v for g,v in self.GlyphClassDef.classDefs.items() if g in glyphs}
	if self.AttachList:
		indices = self.AttachList.Coverage.subset (glyphs)
		self.AttachList.AttachPoint = [self.AttachList.AttachPoint[i] for i in indices]
		self.AttachList.GlyphCount = len (self.AttachList.AttachPoint)


if __name__ == '__main__':

	import sys

	if len (sys.argv) < 3:
		print >>sys.stderr, "usage: pyotlss.py font-file glyph..."
		sys.exit (1)

	fontfile = sys.argv[1]
	glyphs   = sys.argv[2:]

	font = fontTools.ttx.TTFont (fontfile)

	names = font.getGlyphNames()
	# Convert to glyph names
	glyphs = [g if g in names else font.getGlyphName(int(g)) for g in glyphs]

	for Gtag in ['GDEF', 'GSUB', 'GPOS']:
		if Gtag not in font:
			continue
		font[Gtag].table.subset (glyphs)
