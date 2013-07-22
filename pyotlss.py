#!/usr/bin/python

# Python OpenType Layout Subsetter
# Written by: Behdad Esfahbod

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

@add_method(fontTools.ttLib.tables.otTables.Coverage)
def __nonzero__ (self):
	return bool (self.glyphs)

@add_method(fontTools.ttLib.tables.otTables.ClassDef)
def subset (self, glyphs):
	"Returns ascending list of remaining classes."
	self.classDefs = {g:v for g,v in self.classDefs.items() if g in glyphs}
	return {v:1 for v in self.classDefs.values ()}.keys ()

@add_method(fontTools.ttLib.tables.otTables.ClassDef)
def remap (self, class_map):
	"Remaps classes."
	self.classDefs = {g:class_map.index (v) for g,v in self.classDefs.items()}

@add_method(fontTools.ttLib.tables.otTables.ClassDef)
def __nonzero__ (self):
	return bool (self.classDefs)

@add_method(fontTools.ttLib.tables.otTables.SingleSubst)
def subset (self, glyphs):
	if self.Format in [1, 2]:
		self.mapping = {g:v for g,v in self.mapping.items() if g in glyphs}
		return len (self.mapping)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.MultipleSubst)
def subset (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset (glyphs)
		self.Sequence = [self.Sequence[i] for i in indices]
		self.SequenceCount = len (self.Sequence)
		return self.SequenceCount
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.AlternateSubst)
def subset (self, glyphs):
	if self.Format == 1:
		self.alternates = {g:v for g,v in self.alternates.items() if g in glyphs}
		return len (self.alternates)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.LigatureSubst)
def subset (self, glyphs):
	if self.Format == 1:
		self.ligatures = {g:v for g,v in self.ligatures.items() if g in glyphs}
		self.ligatures = {g:[seq for seq in seqs if all(c in glyphs for c in seq.Component)]
				  for g,seqs in self.ligatures.items()}
		self.ligatures = {g:v for g,v in self.ligatures.items() if v}
		return len (self.ligatures)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.ReverseChainSingleSubst)
def subset (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset (glyphs)
		self.Substitute = [self.Substitute[i] for i in indices]
		self.GlyphCount = len (self.Substitute)
		return self.GlyphCount and all (c.subset (glyphs) for c in self.LookAheadCoverage + self.BacktrackCoverage)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.SinglePos)
def subset (self, glyphs):
	if self.Format == 1:
		return len (self.Coverage.subset (glyphs))
	elif self.Format == 2:
		indices = self.Coverage.subset (glyphs)
		self.Value = [self.Value[i] for i in indices]
		self.ValueCount = len (self.Value)
		return self.ValueCount
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.PairPos)
def subset (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset (glyphs)
		self.PairSet = [self.PairSet[i] for i in indices]
		for p in self.PairSet:
			p.PairValueRecord = [r for r in p.PairValueRecord if r.SecondGlyph in glyphs]
			p.PairValueCount = len (p.PairValueRecord)
		self.PairSet = [p for p in self.PairSet if p.PairValueCount]
		self.PairSetCount = len (self.PairSet)
		return self.PairSetCount
	elif self.Format == 2:
		self.Coverage.subset (glyphs)
		class1_map = self.ClassDef1.subset (glyphs)
		class2_map = self.ClassDef2.subset (glyphs)
		self.ClassDef1.remap (class1_map)
		self.ClassDef2.remap (class2_map)
		self.Class1Record = [self.Class1Record[i] for i in class1_map]
		for c in self.Class1Record:
			c.Class2Record = [c.Class2Record[i] for i in class2_map]
		self.Class1Count = len (class1_map)
		self.Class2Count = len (class2_map)
		return self.Coverage and self.Class1Count and self.Class2Count
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.CursivePos)
def subset (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset (glyphs)
		self.EntryExitRecord = [self.EntryExitRecord[i] for i in indices]
		self.EntryExitCount = len (self.EntryExitRecord)
		return self.EntryExitCount
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.MarkBasePos)
def subset (self, glyphs):
	if self.Format == 1:
		mark_indices = self.MarkCoverage.subset (glyphs)
		self.MarkArray.MarkRecord = [self.MarkArray.MarkRecord[i] for i in mark_indices]
		self.MarkArray.MarkCount = len (self.MarkArray.MarkRecord)
		base_indices = self.BaseCoverage.subset (glyphs)
		self.BaseArray.BaseRecord = [self.BaseArray.BaseRecord[i] for i in base_indices]
		self.BaseArray.BaseCount = len (self.BaseArray.BaseRecord)
		# Prune empty classes
		class_indices = {v.Class:1 for v in self.MarkArray.MarkRecord}.keys ()
		self.ClassCount = len (class_indices)
		for m in self.MarkArray.MarkRecord:
			m.Class = class_indices.index (m.Class)
		for b in self.BaseArray.BaseRecord:
			b.BaseAnchor = [b.BaseAnchor[i] for i in class_indices]
		return self.ClassCount and self.MarkArray.MarkCount and self.BaseArray.BaseCount
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.MarkLigPos)
def subset (self, glyphs):
	if self.Format == 1:
		mark_indices = self.MarkCoverage.subset (glyphs)
		self.MarkArray.MarkRecord = [self.MarkArray.MarkRecord[i] for i in mark_indices]
		self.MarkArray.MarkCount = len (self.MarkArray.MarkRecord)
		ligature_indices = self.LigatureCoverage.subset (glyphs)
		self.LigatureArray.LigatureAttach = [self.LigatureArray.LigatureAttach[i] for i in ligature_indices]
		self.LigatureArray.LigatureCount = len (self.LigatureArray.LigatureAttach)
		# Prune empty classes
		class_indices = {v.Class:1 for v in self.MarkArray.MarkRecord}.keys ()
		self.ClassCount = len (class_indices)
		for m in self.MarkArray.MarkRecord:
			m.Class = class_indices.index (m.Class)
		for l in self.LigatureArray.LigatureAttach:
			for c in l.ComponentRecord:
				c.LigatureAnchor = [c.LigatureAnchor[i] for i in class_indices]
		return self.ClassCount and self.MarkArray.MarkCount and self.LigatureArray.LigatureCount
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.MarkMarkPos)
def subset (self, glyphs):
	if self.Format == 1:
		mark1_indices = self.Mark1Coverage.subset (glyphs)
		self.Mark1Array.MarkRecord = [self.Mark1Array.MarkRecord[i] for i in mark1_indices]
		self.Mark1Array.MarkCount = len (self.Mark1Array.MarkRecord)
		mark2_indices = self.Mark2Coverage.subset (glyphs)
		self.Mark2Array.Mark2Record = [self.Mark2Array.Mark2Record[i] for i in mark2_indices]
		self.Mark2Array.MarkCount = len (self.Mark2Array.Mark2Record)
		# Prune empty classes
		class_indices = {v.Class:1 for v in self.Mark1Array.MarkRecord}.keys ()
		self.ClassCount = len (class_indices)
		for m in self.Mark1Array.MarkRecord:
			m.Class = class_indices.index (m.Class)
		for b in self.Mark2Array.Mark2Record:
			b.Mark2Anchor = [b.Mark2Anchor[i] for i in class_indices]
		return self.ClassCount and self.Mark1Array.MarkCount and self.Mark2Array.MarkCount
	else:
		assert 0, "unknown format: %s" % self.Format

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
		# Prune empty subrulesets
		return self.SubRuleSetCount
	elif self.Format == 2:
		return self.Coverage.subset (glyphs) and self.ClassDef.subset (glyphs)
	elif self.Format == 3:
		return all (c.subset (glyphs) for c in self.Coverage)
	else:
		assert 0, "unknown format: %s" % self.Format

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
		# Prune empty subrulesets
		return self.ChainSubRuleSetCount
	elif self.Format == 2:
		return self.Coverage.subset (glyphs) and \
		       self.LookAheadClassDef.subset (glyphs) and \
		       self.BacktrackClassDef.subset (glyphs) and \
		       self.InputClassDef.subset (glyphs)
	elif self.Format == 3:
		return all (c.subset (glyphs) for c in self.InputCoverage + self.LookAheadCoverage + self.BacktrackCoverage)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.ExtensionSubst, fontTools.ttLib.tables.otTables.ExtensionPos)
def subset (self, glyphs):
	if self.Format == 1:
		return self.ExtSubTable.subset (glyphs)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.Lookup)
def subset (self, glyphs):
	self.SubTable = [s for s in self.SubTable if s.subset (glyphs)]
	self.SubTableCount = len (self.SubTable)
	return self.SubTableCount

@add_method(fontTools.ttLib.tables.otTables.LookupList)
def subset (self, glyphs):
	"Returns the indices of nonempty lookups."
	return [i for (i,l) in enumerate (self.Lookup) if l.subset (glyphs)]

@add_method(fontTools.ttLib.tables.otTables.LookupList)
def subset_lookups (self, lookup_indices):
	self.Lookup = [self.Lookup[i] for i in lookup_indices]
	self.LookupCount = len (self.Lookup)

@add_method(fontTools.ttLib.tables.otTables.Feature)
def subset_lookups (self, lookup_indices):
	self.LookupListIndex = [l for l in self.LookupListIndex if l in lookup_indices]
	# Now map them.
	self.LookupListIndex = [lookup_indices.index (l) for l in self.LookupListIndex]
	self.LookupCount = len (self.LookupListIndex)
	return self.LookupCount

@add_method(fontTools.ttLib.tables.otTables.FeatureList)
def subset_lookups (self, lookup_indices):
	"Returns the indices of nonempty features."
	feature_indices = [i for (i,f) in enumerate (self.FeatureRecord) if f.Feature.subset_lookups (lookup_indices)]
	self.FeatureRecord = [self.FeatureRecord[i] for i in feature_indices]
	self.FeatureCount = len (self.FeatureRecord)
	return feature_indices

@add_method(fontTools.ttLib.tables.otTables.DefaultLangSys, fontTools.ttLib.tables.otTables.LangSys)
def subset_features (self, feature_indices):
	if self.ReqFeatureIndex not in feature_indices:
		self.ReqFeatureIndex = 65535
	self.FeatureIndex = [f for f in self.FeatureIndex if f in feature_indices]
	self.FeatureCount = len (self.FeatureIndex)
	return self.FeatureCount

@add_method(fontTools.ttLib.tables.otTables.Script)
def subset_features (self, feature_indices):
	if self.DefaultLangSys and not self.DefaultLangSys.subset_features (feature_indices):
		self.DefaultLangSys = None
	self.LangSysRecord = [l for l in self.LangSysRecord if l.LangSys.subset_features (feature_indices)]
	self.LangSysCount = len (self.LangSysRecord)
	return self.LangSysCount

@add_method(fontTools.ttLib.tables.otTables.ScriptList)
def subset_features (self, feature_indices):
	self.ScriptRecord = [s for s in self.ScriptRecord if s.Script.subset_features (feature_indices)]
	self.ScriptCount = len (self.ScriptRecord)
	return self.ScriptCount

@add_method(fontTools.ttLib.getTableClass('GSUB'), fontTools.ttLib.getTableClass('GPOS'))
def subset (self, glyphs):
	lookup_indices = self.table.LookupList.subset (glyphs)
	self.subset_lookups (lookup_indices)
	return True # Retain the possibly empty table

@add_method(fontTools.ttLib.getTableClass('GSUB'), fontTools.ttLib.getTableClass('GPOS'))
def subset_lookups (self, lookup_indices):
	"Retrains specified lookups, then removes empty features, language systems, and scripts."
	self.table.LookupList.subset_lookups (lookup_indices)
	feature_indices = self.table.FeatureList.subset_lookups (lookup_indices)
	self.table.ScriptList.subset_features (feature_indices)

@add_method(fontTools.ttLib.getTableClass('GDEF'))
def subset (self, glyphs):
	table = self.table
	if table.LigCaretList:
		indices = table.LigCaretList.Coverage.subset (glyphs)
		table.LigCaretList.LigGlyph = [table.LigCaretList.LigGlyph[i] for i in indices]
		table.LigCaretList.LigGlyphCount = len (table.LigCaretList.LigGlyph)
		if not table.LigCaretList.LigGlyphCount:
			table.LigCaretList = None
	if table.MarkAttachClassDef:
		table.MarkAttachClassDef.classDefs = {g:v for g,v in table.MarkAttachClassDef.classDefs.items() if g in glyphs}
		if not table.MarkAttachClassDef.classDefs:
			table.MarkAttachClassDef = None
	if table.GlyphClassDef:
		table.GlyphClassDef.classDefs = {g:v for g,v in table.GlyphClassDef.classDefs.items() if g in glyphs}
		if not table.GlyphClassDef.classDefs:
			table.GlyphClassDef = None
	if table.AttachList:
		indices = table.AttachList.Coverage.subset (glyphs)
		table.AttachList.AttachPoint = [table.AttachList.AttachPoint[i] for i in indices]
		table.AttachList.GlyphCount = len (table.AttachList.AttachPoint)
		if not table.AttachList.GlyphCount:
			table.AttachList = None
	return table.LigCaretList or table.MarkAttachClassDef or table.GlyphClassDef or table.AttachList

@add_method(fontTools.ttLib.getTableClass('kern'))
def subset (self, glyphs):
	for t in self.kernTables:
		t.kernTable = {(a,b):v for ((a,b),v) in t.kernTable.items() if a in glyphs and b in glyphs}
	self.kernTables = [t for t in self.kernTables if t.kernTable]
	return self.kernTables

@add_method(fontTools.ttLib.getTableClass('hmtx'))
def subset (self, glyphs):
	self.metrics = {g:v for (g,v) in self.metrics.items() if g in glyphs}
	return len (self.metrics)


if __name__ == '__main__':

	import sys

	verbose = False
	if "--verbose" in sys.argv:
		verbose = True
		sys.argv.remove ("--verbose")
	xml = False
	if "--xml" in sys.argv:
		xml = True
		sys.argv.remove ("--xml")

	if len (sys.argv) < 3:
		print >>sys.stderr, "usage: pyotlss.py font-file glyph..."
		sys.exit (1)

	fontfile = sys.argv[1]
	glyphs   = sys.argv[2:]

	# Always include .notdef; anything else?
	if '.notdef' not in glyphs:
		glyphs.append ('.notdef')

	font = fontTools.ttx.TTFont (fontfile)

	names = font.getGlyphNames()
	# Convert to glyph names
	glyphs = [g if g in names else font.getGlyphName(int(g)) for g in glyphs]

	if xml:
		import xmlWriter
		writer = xmlWriter.XMLWriter (sys.stdout)

	drop_tables = ['BASE', 'JSTF', 'DSIG', 'EBDT', 'EBLC', 'EBSC', 'PCLT', 'LTSH']
	noneed_tables = ['gasp', 'head', 'hhea', 'name', 'vhea', 'OS/2']

	for tag in font.keys():

		if tag == 'GlyphOrder':
			continue

		if tag in drop_tables:
			if verbose:
				print tag, "dropped."
			del font[tag]
			continue

		if tag in noneed_tables:
			if verbose:
				print tag, "intact."
			continue

		clazz = fontTools.ttLib.getTableClass(tag)
		if 'subset' not in vars (clazz):
			if verbose:
				print tag, "skipped."
			continue

		table = font[tag]
		if not table.subset (glyphs):
			del font[tag]
			if verbose:
				print tag, "subset empty; dropped."
		else:
			if xml:
				writer.begintag (tag)
				writer.newline ()
				font[tag].toXML(writer, font)
				writer.endtag (tag)
				writer.newline ()
			if verbose:
				print tag, "subsetted."

	glyphOrder = font.getGlyphOrder()
	glyphOrder = [g for g in glyphOrder if g in glyphs]
	font.setGlyphOrder (glyphOrder)
	font._buildReverseGlyphOrderDict ()

	font.save (fontfile + '.subset')
