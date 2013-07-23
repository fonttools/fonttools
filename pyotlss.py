#!/usr/bin/python

# Python OpenType Layout Subsetter
#
# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Google Author(s): Behdad Esfahbod
#

import fontTools.ttx


def add_method (*clazzes):
	def wrapper(method):
		for clazz in clazzes:
			setattr (clazz, method.func_name, method)
	return wrapper

def unique_sorted (l):
	return sorted ({v:1 for v in l}.keys ())


@add_method(fontTools.ttLib.tables.otTables.Coverage)
def subset_glyphs (self, glyphs):
	"Returns ascending list of remaining coverage values."
	indices = [i for (i,g) in enumerate (self.glyphs) if g in glyphs]
	self.glyphs = [g for g in self.glyphs if g in glyphs]
	return indices

@add_method(fontTools.ttLib.tables.otTables.ClassDef)
def subset_glyphs (self, glyphs):
	"Returns ascending list of remaining classes."
	self.classDefs = {g:v for g,v in self.classDefs.items() if g in glyphs}
	return unique_sorted (self.classDefs.values ())

@add_method(fontTools.ttLib.tables.otTables.ClassDef)
def remap (self, class_map):
	"Remaps classes."
	self.classDefs = {g:class_map.index (v) for g,v in self.classDefs.items()}

@add_method(fontTools.ttLib.tables.otTables.SingleSubst)
def subset_glyphs (self, glyphs):
	if self.Format in [1, 2]:
		self.mapping = {g:v for g,v in self.mapping.items() if g in glyphs}
		return bool (self.mapping)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.MultipleSubst)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset_glyphs (glyphs)
		self.Sequence = [self.Sequence[i] for i in indices]
		self.SequenceCount = len (self.Sequence)
		return bool (self.SequenceCount)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.AlternateSubst)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		self.alternates = {g:v for g,v in self.alternates.items() if g in glyphs}
		return bool (self.alternates)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.LigatureSubst)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		self.ligatures = {g:v for g,v in self.ligatures.items() if g in glyphs}
		self.ligatures = {g:[seq for seq in seqs if all(c in glyphs for c in seq.Component)]
				  for g,seqs in self.ligatures.items()}
		self.ligatures = {g:v for g,v in self.ligatures.items() if v}
		return bool (self.ligatures)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.ReverseChainSingleSubst)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset_glyphs (glyphs)
		self.Substitute = [self.Substitute[i] for i in indices]
		self.GlyphCount = len (self.Substitute)
		return bool (self.GlyphCount and all (c.subset_glyphs (glyphs) for c in self.LookAheadCoverage + self.BacktrackCoverage))
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.SinglePos)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		return len (self.Coverage.subset_glyphs (glyphs))
	elif self.Format == 2:
		indices = self.Coverage.subset_glyphs (glyphs)
		self.Value = [self.Value[i] for i in indices]
		self.ValueCount = len (self.Value)
		return bool (self.ValueCount)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.PairPos)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset_glyphs (glyphs)
		self.PairSet = [self.PairSet[i] for i in indices]
		for p in self.PairSet:
			p.PairValueRecord = [r for r in p.PairValueRecord if r.SecondGlyph in glyphs]
			p.PairValueCount = len (p.PairValueRecord)
		self.PairSet = [p for p in self.PairSet if p.PairValueCount]
		self.PairSetCount = len (self.PairSet)
		return bool (self.PairSetCount)
	elif self.Format == 2:
		class1_map = self.ClassDef1.subset_glyphs (glyphs)
		class2_map = self.ClassDef2.subset_glyphs (glyphs)
		self.ClassDef1.remap (class1_map)
		self.ClassDef2.remap (class2_map)
		self.Class1Record = [self.Class1Record[i] for i in class1_map]
		for c in self.Class1Record:
			c.Class2Record = [c.Class2Record[i] for i in class2_map]
		self.Class1Count = len (class1_map)
		self.Class2Count = len (class2_map)
		return bool (self.Class1Count and self.Class2Count and self.Coverage.subset_glyphs (glyphs))
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.CursivePos)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset_glyphs (glyphs)
		self.EntryExitRecord = [self.EntryExitRecord[i] for i in indices]
		self.EntryExitCount = len (self.EntryExitRecord)
		return bool (self.EntryExitCount)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.MarkBasePos)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		mark_indices = self.MarkCoverage.subset_glyphs (glyphs)
		self.MarkArray.MarkRecord = [self.MarkArray.MarkRecord[i] for i in mark_indices]
		self.MarkArray.MarkCount = len (self.MarkArray.MarkRecord)
		base_indices = self.BaseCoverage.subset_glyphs (glyphs)
		self.BaseArray.BaseRecord = [self.BaseArray.BaseRecord[i] for i in base_indices]
		self.BaseArray.BaseCount = len (self.BaseArray.BaseRecord)
		# Prune empty classes
		class_indices = unique_sorted (v.Class for v in self.MarkArray.MarkRecord)
		self.ClassCount = len (class_indices)
		for m in self.MarkArray.MarkRecord:
			m.Class = class_indices.index (m.Class)
		for b in self.BaseArray.BaseRecord:
			b.BaseAnchor = [b.BaseAnchor[i] for i in class_indices]
		return bool (self.ClassCount and self.MarkArray.MarkCount and self.BaseArray.BaseCount)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.MarkLigPos)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		mark_indices = self.MarkCoverage.subset_glyphs (glyphs)
		self.MarkArray.MarkRecord = [self.MarkArray.MarkRecord[i] for i in mark_indices]
		self.MarkArray.MarkCount = len (self.MarkArray.MarkRecord)
		ligature_indices = self.LigatureCoverage.subset_glyphs (glyphs)
		self.LigatureArray.LigatureAttach = [self.LigatureArray.LigatureAttach[i] for i in ligature_indices]
		self.LigatureArray.LigatureCount = len (self.LigatureArray.LigatureAttach)
		# Prune empty classes
		class_indices = unique_sorted (v.Class for v in self.MarkArray.MarkRecord)
		self.ClassCount = len (class_indices)
		for m in self.MarkArray.MarkRecord:
			m.Class = class_indices.index (m.Class)
		for l in self.LigatureArray.LigatureAttach:
			for c in l.ComponentRecord:
				c.LigatureAnchor = [c.LigatureAnchor[i] for i in class_indices]
		return bool (self.ClassCount and self.MarkArray.MarkCount and self.LigatureArray.LigatureCount)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.MarkMarkPos)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		mark1_indices = self.Mark1Coverage.subset_glyphs (glyphs)
		self.Mark1Array.MarkRecord = [self.Mark1Array.MarkRecord[i] for i in mark1_indices]
		self.Mark1Array.MarkCount = len (self.Mark1Array.MarkRecord)
		mark2_indices = self.Mark2Coverage.subset_glyphs (glyphs)
		self.Mark2Array.Mark2Record = [self.Mark2Array.Mark2Record[i] for i in mark2_indices]
		self.Mark2Array.MarkCount = len (self.Mark2Array.Mark2Record)
		# Prune empty classes
		class_indices = unique_sorted (v.Class for v in self.Mark1Array.MarkRecord)
		self.ClassCount = len (class_indices)
		for m in self.Mark1Array.MarkRecord:
			m.Class = class_indices.index (m.Class)
		for b in self.Mark2Array.Mark2Record:
			b.Mark2Anchor = [b.Mark2Anchor[i] for i in class_indices]
		return bool (self.ClassCount and self.Mark1Array.MarkCount and self.Mark2Array.MarkCount)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.SingleSubst,
            fontTools.ttLib.tables.otTables.MultipleSubst,
            fontTools.ttLib.tables.otTables.AlternateSubst,
            fontTools.ttLib.tables.otTables.LigatureSubst,
            fontTools.ttLib.tables.otTables.ReverseChainSingleSubst,
            fontTools.ttLib.tables.otTables.SinglePos,
            fontTools.ttLib.tables.otTables.PairPos,
            fontTools.ttLib.tables.otTables.CursivePos,
            fontTools.ttLib.tables.otTables.MarkBasePos,
            fontTools.ttLib.tables.otTables.MarkLigPos,
            fontTools.ttLib.tables.otTables.MarkMarkPos)
def subset_lookups (self, lookup_indices):
	pass

@add_method(fontTools.ttLib.tables.otTables.SingleSubst,
            fontTools.ttLib.tables.otTables.MultipleSubst,
            fontTools.ttLib.tables.otTables.AlternateSubst,
            fontTools.ttLib.tables.otTables.LigatureSubst,
            fontTools.ttLib.tables.otTables.ReverseChainSingleSubst,
            fontTools.ttLib.tables.otTables.SinglePos,
            fontTools.ttLib.tables.otTables.PairPos,
            fontTools.ttLib.tables.otTables.CursivePos,
            fontTools.ttLib.tables.otTables.MarkBasePos,
            fontTools.ttLib.tables.otTables.MarkLigPos,
            fontTools.ttLib.tables.otTables.MarkMarkPos)
def collect_lookups (self):
	return []

@add_method(fontTools.ttLib.tables.otTables.ContextSubst, fontTools.ttLib.tables.otTables.ContextPos)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset_glyphs (glyphs)
		self.SubRuleSet = [self.SubRuleSet[i] for i in indices]
		self.SubRuleSetCount = len (self.SubRuleSet)
		for rs in self.SubRuleSet:
			rs.SubRule = [r for r in rs.SubRule
				      if all (g in glyphs for g in r.Input)]
			rs.SubRuleCount = len (rs.SubRule)
		# Prune empty subrulesets
		return bool (self.SubRuleSetCount)
	elif self.Format == 2:
		return bool (self.Coverage.subset_glyphs (glyphs) and self.ClassDef.subset_glyphs (glyphs))
	elif self.Format == 3:
		return all (c.subset_glyphs (glyphs) for c in self.Coverage)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.ChainContextSubst, fontTools.ttLib.tables.otTables.ChainContextPos)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		indices = self.Coverage.subset_glyphs (glyphs)
		self.ChainSubRuleSet = [self.ChainSubRuleSet[i] for i in indices]
		self.ChainSubRuleSetCount = len (self.ChainSubRuleSet)
		for rs in self.ChainSubRuleSet:
			rs.ChainSubRule = [r for r in rs.ChainSubRule
					   if all (g in glyphs for g in r.Backtrack + r.Input + r.LookAhead)]
			rs.ChainSubRuleCount = len (rs.ChainSubRule)
		# Prune empty subrulesets
		return self.ChainSubRuleSetCount
	elif self.Format == 2:
		return self.Coverage.subset_glyphs (glyphs) and \
		       self.LookAheadClassDef.subset_glyphs (glyphs) and \
		       self.BacktrackClassDef.subset_glyphs (glyphs) and \
		       self.InputClassDef.subset_glyphs (glyphs)
	elif self.Format == 3:
		return all (c.subset_glyphs (glyphs) for c in self.InputCoverage + self.LookAheadCoverage + self.BacktrackCoverage)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.ContextSubst, fontTools.ttLib.tables.otTables.ChainContextSubst)
def subset_lookups (self, lookup_indices):
	self.SubstLookupRecord = [ll for ll in self.SubstLookupRecord if ll.LookupListIndex in lookup_indices]
	for ll in self.SubstLookupRecord:
		ll.LookupListIndex = lookup_indices.index (ll.LookupListIndex)

@add_method(fontTools.ttLib.tables.otTables.ContextPos, fontTools.ttLib.tables.otTables.ChainContextPos)
def subset_lookups (self, lookup_indices):
	self.PosLookupRecord = [ll for ll in self.PosLookupRecord if ll.LookupListIndex in lookup_indices]
	for ll in self.PosLookupRecord:
		ll.LookupListIndex = lookup_indices.index (ll.LookupListIndex)

@add_method(fontTools.ttLib.tables.otTables.ContextSubst, fontTools.ttLib.tables.otTables.ChainContextSubst)
def collect_lookups (self):
	return [ll.LookupListIndex for ll in self.SubstLookupRecord]

@add_method(fontTools.ttLib.tables.otTables.ContextPos, fontTools.ttLib.tables.otTables.ChainContextPos)
def collect_lookups (self):
	return [ll.LookupListIndex for ll in self.PosLookupRecord]

@add_method(fontTools.ttLib.tables.otTables.ExtensionSubst, fontTools.ttLib.tables.otTables.ExtensionPos)
def subset_glyphs (self, glyphs):
	if self.Format == 1:
		return self.ExtSubTable.subset_glyphs (glyphs)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.ExtensionSubst, fontTools.ttLib.tables.otTables.ExtensionPos)
def subset_lookups (self, lookup_indices):
	if self.Format == 1:
		self.ExtSubTable.subset_lookups (lookup_indices)
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.ExtensionSubst, fontTools.ttLib.tables.otTables.ExtensionPos)
def collect_lookups (self):
	if self.Format == 1:
		return self.ExtSubTable.collect_lookups ()
	else:
		assert 0, "unknown format: %s" % self.Format

@add_method(fontTools.ttLib.tables.otTables.Lookup)
def subset_glyphs (self, glyphs):
	self.SubTable = [s for s in self.SubTable if s.subset_glyphs (glyphs)]
	self.SubTableCount = len (self.SubTable)
	return bool (self.SubTableCount)

@add_method(fontTools.ttLib.tables.otTables.Lookup)
def subset_lookups (self, lookup_indices):
	for s in self.SubTable:
		s.subset_lookups (lookup_indices)

@add_method(fontTools.ttLib.tables.otTables.Lookup)
def collect_lookups (self):
	return unique_sorted (sum ((s.collect_lookups () for s in self.SubTable), []))

@add_method(fontTools.ttLib.tables.otTables.LookupList)
def subset_glyphs (self, glyphs):
	"Returns the indices of nonempty lookups."
	return [i for (i,l) in enumerate (self.Lookup) if l.subset_glyphs (glyphs)]

@add_method(fontTools.ttLib.tables.otTables.LookupList)
def subset_lookups (self, lookup_indices):
	self.Lookup = [self.Lookup[i] for i in lookup_indices]
	self.LookupCount = len (self.Lookup)
	for l in self.Lookup:
		l.subset_lookups (lookup_indices)

@add_method(fontTools.ttLib.tables.otTables.LookupList)
def closure_lookups (self, lookup_indices):
	while True:
		recurse_lookups = sum ((self.Lookup[i].collect_lookups () for i in lookup_indices), [])
		recurse_lookups = [l for l in recurse_lookups if l not in lookup_indices]
		if not recurse_lookups:
			return lookup_indices
		lookup_indices = unique_sorted (lookup_indices + recurse_lookups)

@add_method(fontTools.ttLib.tables.otTables.Feature)
def subset_lookups (self, lookup_indices):
	self.LookupListIndex = [l for l in self.LookupListIndex if l in lookup_indices]
	# Now map them.
	self.LookupListIndex = [lookup_indices.index (l) for l in self.LookupListIndex]
	self.LookupCount = len (self.LookupListIndex)
	return self.LookupCount

@add_method(fontTools.ttLib.tables.otTables.Feature)
def collect_lookups (self):
	return self.LookupListIndex[:]

@add_method(fontTools.ttLib.tables.otTables.FeatureList)
def subset_lookups (self, lookup_indices):
	"Returns the indices of nonempty features."
	feature_indices = [i for (i,f) in enumerate (self.FeatureRecord) if f.Feature.subset_lookups (lookup_indices)]
	self.subset_features (feature_indices)
	return feature_indices

@add_method(fontTools.ttLib.tables.otTables.FeatureList)
def collect_lookups (self, feature_indices):
	return unique_sorted (sum ((self.FeatureRecord[i].Feature.collect_lookups () for i in feature_indices
				    if i < self.FeatureCount), []))

@add_method(fontTools.ttLib.tables.otTables.FeatureList)
def subset_features (self, feature_indices):
	self.FeatureRecord = [self.FeatureRecord[i] for i in feature_indices]
	self.FeatureCount = len (self.FeatureRecord)
	return bool (self.FeatureCount)

@add_method(fontTools.ttLib.tables.otTables.DefaultLangSys, fontTools.ttLib.tables.otTables.LangSys)
def subset_features (self, feature_indices):
	if self.ReqFeatureIndex in feature_indices:
		self.ReqFeatureIndex = feature_indices.index (self.ReqFeatureIndex)
	else:
		self.ReqFeatureIndex = 65535
	self.FeatureIndex = [f for f in self.FeatureIndex if f in feature_indices]
	# Now map them.
	self.FeatureIndex = [feature_indices.index (f) for f in self.FeatureIndex if f in feature_indices]
	self.FeatureCount = len (self.FeatureIndex)
	return bool (self.FeatureCount or self.ReqFeatureIndex != 65535)

@add_method(fontTools.ttLib.tables.otTables.DefaultLangSys, fontTools.ttLib.tables.otTables.LangSys)
def collect_features (self):
	feature_indices = self.FeatureIndex[:]
	if self.ReqFeatureIndex != 65535:
		feature_indices.append (self.ReqFeatureIndex)
	return unique_sorted (feature_indices)

@add_method(fontTools.ttLib.tables.otTables.Script)
def subset_features (self, feature_indices):
	if self.DefaultLangSys and not self.DefaultLangSys.subset_features (feature_indices):
		self.DefaultLangSys = None
	self.LangSysRecord = [l for l in self.LangSysRecord if l.LangSys.subset_features (feature_indices)]
	self.LangSysCount = len (self.LangSysRecord)
	return bool (self.LangSysCount or self.DefaultLangSys)

@add_method(fontTools.ttLib.tables.otTables.Script)
def collect_features (self):
	feature_indices = [l.LangSys.collect_features () for l in self.LangSysRecord]
	if self.DefaultLangSys:
		feature_indices.append (self.DefaultLangSys.collect_features ())
	return unique_sorted (sum (feature_indices, []))

@add_method(fontTools.ttLib.tables.otTables.ScriptList)
def subset_features (self, feature_indices):
	self.ScriptRecord = [s for s in self.ScriptRecord if s.Script.subset_features (feature_indices)]
	self.ScriptCount = len (self.ScriptRecord)
	return bool (self.ScriptCount)

@add_method(fontTools.ttLib.tables.otTables.ScriptList)
def collect_features (self):
	return unique_sorted (sum ((s.Script.collect_features () for s in self.ScriptRecord), []))

@add_method(fontTools.ttLib.getTableClass('GSUB'), fontTools.ttLib.getTableClass('GPOS'))
def subset_glyphs (self, glyphs):
	lookup_indices = self.table.LookupList.subset_glyphs (glyphs)
	self.subset_lookups (lookup_indices)
	self.prune_lookups ()
	return True

@add_method(fontTools.ttLib.getTableClass('GSUB'), fontTools.ttLib.getTableClass('GPOS'))
def subset_lookups (self, lookup_indices):
	"Retrains specified lookups, then removes empty features, language systems, and scripts."
	self.table.LookupList.subset_lookups (lookup_indices)
	feature_indices = self.table.FeatureList.subset_lookups (lookup_indices)
	self.table.ScriptList.subset_features (feature_indices)

@add_method(fontTools.ttLib.getTableClass('GSUB'), fontTools.ttLib.getTableClass('GPOS'))
def prune_lookups (self):
	"Remove unreferenced lookups"
	feature_indices = self.table.ScriptList.collect_features ()
	lookup_indices = self.table.FeatureList.collect_lookups (feature_indices)
	lookup_indices = self.table.LookupList.closure_lookups (lookup_indices)
	self.subset_lookups (lookup_indices)

@add_method(fontTools.ttLib.getTableClass('GSUB'), fontTools.ttLib.getTableClass('GPOS'))
def subset_feature_tags (self, feature_tags):
	feature_indices = [i for (i,f) in enumerate (self.table.FeatureList.FeatureRecord) if f.FeatureTag in feature_tags]
	self.table.FeatureList.subset_features (feature_indices)
	self.table.ScriptList.subset_features (feature_indices)

@add_method(fontTools.ttLib.getTableClass('GSUB'), fontTools.ttLib.getTableClass('GPOS'))
def prune_pre_subset (self, options):
	if 'layout-features' in options:
		self.subset_feature_tags (options['layout-features'])
	self.prune_lookups ()
	return True

@add_method(fontTools.ttLib.getTableClass('GDEF'))
def subset_glyphs (self, glyphs):
	table = self.table
	if table.LigCaretList:
		indices = table.LigCaretList.Coverage.subset_glyphs (glyphs)
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
		indices = table.AttachList.Coverage.subset_glyphs (glyphs)
		table.AttachList.AttachPoint = [table.AttachList.AttachPoint[i] for i in indices]
		table.AttachList.GlyphCount = len (table.AttachList.AttachPoint)
		if not table.AttachList.GlyphCount:
			table.AttachList = None
	return bool (table.LigCaretList or table.MarkAttachClassDef or table.GlyphClassDef or table.AttachList)

@add_method(fontTools.ttLib.getTableClass('kern'))
def subset_glyphs (self, glyphs):
	for t in self.kernTables:
		t.kernTable = {(a,b):v for ((a,b),v) in t.kernTable.items() if a in glyphs and b in glyphs}
	self.kernTables = [t for t in self.kernTables if t.kernTable]
	return bool (self.kernTables)

@add_method(fontTools.ttLib.getTableClass('hmtx'), fontTools.ttLib.getTableClass('vmtx'))
def subset_glyphs (self, glyphs):
	self.metrics = {g:v for (g,v) in self.metrics.items() if g in glyphs}
	return bool (self.metrics)

@add_method(fontTools.ttLib.getTableClass('hdmx'))
def subset_glyphs (self, glyphs):
	self.hdmx = {s:{g:v for (g,v) in l.items() if g in glyphs} for (s,l) in self.hdmx.items()}
	return bool (self.hdmx)

@add_method(fontTools.ttLib.getTableClass('VORG'))
def subset_glyphs (self, glyphs):
	self.VOriginRecords = {g:v for (g,v) in self.VOriginRecords.items() if g in glyphs}
	self.numVertOriginYMetrics = len (self.VOriginRecords)
	return True # Never drop; has default metrics

@add_method(fontTools.ttLib.getTableClass('post'))
def subset_glyphs (self, glyphs):
	# TODO Drop names?  How?
	self.extraNames = []
	return True

@add_method(fontTools.ttLib.getTableClass('glyf'))
def subset_glyphs (self, glyphs):
	self.glyphs = {g:v for (g,v) in self.glyphs.items() if g in glyphs}
	self.glyphOrder = [g for g in self.glyphOrder if g in glyphs]
	return bool (self.glyphs)

@add_method(fontTools.ttLib.getTableClass('glyf'))
def prune_post_subset (self, options):
	if 'hinting' in options and not options['hinting']:
		for g in self.glyphs.values ():
			g.expand (self)
			g.program = fontTools.ttLib.tables.ttProgram.Program()
			g.program.fromBytecode([])
	return True

@add_method(fontTools.ttLib.getTableClass('cmap'))
def subset_glyphs (self, glyphs):
	for t in self.tables:
		# For reasons I don't understand I need this here
		# to force decompilation of the cmap format 14.
		try:
			getattr (t, "asdf")
		except AttributeError:
			pass
		if t.format == 14:
			# XXX We drop all the default-UVS mappings (g==None)
			t.uvsDict = {v:[(u,g) for (u,g) in l if g in glyphs] for (v,l) in t.uvsDict.items()}
			t.uvsDict = {v:l for (v,l) in t.uvsDict.items() if l}
		else:
			t.cmap = {u:g for (u,g) in t.cmap.items() if g in glyphs}
	self.tables = [t for t in self.tables if (t.cmap if t.format != 14 else t.uvsDict)]
	# XXX Convert formats when needed
	return bool (self.tables)


@add_method(fontTools.ttLib.getTableClass('cmap'))
def prune_pre_subset (self, options):
	# Drop non-Unicode / non-Symbol cmaps
	# TODO Add option for this
	# TODO Only keep one subtable?
	self.tables = [t for t in self.tables if t.platformID == 3 and t.platEncID in [0, 1, 10]]
	# For now, drop format=0 which can't be subset_glyphs easily?
	self.tables = [t for t in self.tables if t.format != 0]
	return bool (self.tables)

@add_method(fontTools.ttLib.getTableClass('name'))
def prune_pre_subset (self, options):
	# TODO Make sure something remains?
	# TODO Add option for this.
	# TODO Drop even more (license, etc)? / Drop completely?
	self.names = [n for n in self.names if n.platformID == 3 and n.platEncID == 1 and n.langID == 0x0409]
	return bool (self.names)


@add_method(fontTools.ttLib.getTableClass('glyf'))
def closure_glyphs (self, glyphs):
	glyphs = unique_sorted (glyphs)
	decompose = glyphs
	# I don't know if component glyphs can be composite themselves.
	# We handle them anyway.
	while True:
		components = []
		for g in decompose:
			gl = self[g]
			if gl.isComposite ():
				for c in gl.components:
					if c.glyphName not in glyphs:
						components.append (c.glyphName)
		components = [c for c in components if c not in glyphs]
		if not components:
			return glyphs
		decompose = unique_sorted (components)
		glyphs.extend (components)


drop_tables_default = ['BASE', 'JSTF', 'DSIG', 'EBDT', 'EBLC', 'EBSC', 'PCLT', 'LTSH', 'VDMX']
no_subset_tables = ['gasp', 'head', 'hhea', 'maxp', 'vhea', 'OS/2', 'loca', 'name', 'cvt ', 'fpgm', 'prep']
hinting_tables = ['cvt ', 'fpgm', 'prep']

# Based on HarfBuzz shapers
layout_features_dict = {
	# Default shaper
	'common':	['ccmp', 'liga', 'locl', 'mark', 'mkmk', 'rlig'],
	'horizontal':	['calt', 'clig', 'curs', 'kern', 'rclt'],
	'vertical':	['valt', 'vert', 'vkrn', 'vpal', 'vrt2'],
	'ltr':		['ltra', 'ltrm'],
	'rtl':		['rtla', 'rtlm'],
	# Complex shapers
	'arabic':	['init', 'medi', 'fina', 'isol', 'med2', 'fin2', 'fin3'],
	'hangul':	['ljmo', 'vjmo', 'tjmo'],
	'tibetal':	['abvs', 'blws', 'abvm', 'blwm'],
	'indic':	['nukt', 'akhn', 'rphf', 'rkrf', 'pref', 'blwf', 'half', 'abvf', 'pstf', 'cfar', 'vatu', 'cjct',
		         'init', 'pres', 'abvs', 'blws', 'psts', 'haln', 'dist', 'abvm', 'blwm'],
}
layout_features_all = unique_sorted (sum (layout_features_dict.values (), []))


# TODO OS/2 ulUnicodeRange / ulCodePageRange?
# TODO Drop unneeded GSUB/GPOS entries

if __name__ == '__main__':

	import sys, time

	start_time = time.time ()
	last_time = start_time

	verbose = False
	if "--verbose" in sys.argv:
		verbose = True
		sys.argv.remove ("--verbose")
	xml = False
	if "--xml" in sys.argv:
		xml = True
		sys.argv.remove ("--xml")
	timing = False
	if "--timing" in sys.argv:
		timing = True
		sys.argv.remove ("--timing")

	def lapse (what):
		if not timing:
			return
		global last_time
		new_time = time.time ()
		print "Took %0.3fs to %s" % (new_time - last_time, what)
		last_time = new_time

	if len (sys.argv) < 3:
		print >>sys.stderr, "usage: pyotlss.py font-file glyph..."
		sys.exit (1)

	fontfile = sys.argv[1]
	glyphs   = sys.argv[2:]

	# Always include .notdef; anything else?
	glyphs.append ('.notdef')

	font = fontTools.ttx.TTFont (fontfile)
	font.disassembleInstructions = False
	lapse ("load font")

	names = font.getGlyphNames()
	# Convert to glyph names
	glyphs = [g if g in names else font.getGlyphName(int(g)) for g in glyphs]
	lapse ("compile glyph list")

	glyphs_requested = glyphs[:]
	# Close over composite glyphs
	if 'glyf' in font:
		if verbose:
			print "Closing glyph list over 'glyf' components."
		glyphs_closed = font['glyf'].closure_glyphs (glyphs)
		if verbose:
			print "Before: %d glyphs; after: %d glyphs" % (len (glyphs_requested), len (glyphs_closed))
		lapse ("close glyph list over 'glyf' components")
	else:
		glyphs_closed = glyphs
	del glyphs

	if verbose:
		print "Retaining %d glyphs: " % len (glyphs_closed)

	if xml:
		import xmlWriter
		writer = xmlWriter.XMLWriter (sys.stdout)

	options = {
		'layout-features': layout_features_all,
		'hinting': False,
		'drop-tables': drop_tables_default
	}

	for tag in font.keys():

		if tag == 'GlyphOrder':
			continue

		if tag in options['drop-tables'] or \
		   (not options['hinting'] and tag in hinting_tables):
			if verbose:
				print tag, "dropped."
			del font[tag]
			continue

		clazz = fontTools.ttLib.getTableClass(tag)

		if hasattr (clazz, 'prune_pre_subset'):
			table = font[tag]
			retain = table.prune_pre_subset (options)
			lapse ("prune  '%s'" % tag)
			if not retain:
				if verbose:
					print tag, "pruned to empty; dropped."
				del font[tag]
				continue
			else:
				if verbose:
					print tag, "pruned."

		if tag in no_subset_tables:
			if verbose:
				print tag, "subsetting not needed."
		elif hasattr (clazz, 'subset_glyphs'):
			table = font[tag]
			if tag in ['GSUB', 'GPOS', 'GDEF', 'cmap', 'kern', 'post', 'cmap']: # What else?
				glyphs = glyphs_requested
			else:
				glyphs = glyphs_closed
			retain = table.subset_glyphs (glyphs)
			lapse ("subset '%s'" % tag)
			if not retain:
				if verbose:
					print tag, "subsetted to empty; dropped."
				del font[tag]
				continue
			else:
				if verbose:
					print tag, "subsetted."
			del glyphs
		else:
			if verbose:
				print tag, "NOT subset; don't know how to subset."
			continue

		if hasattr (clazz, 'prune_post_subset'):
			table = font[tag]
			retain = table.prune_post_subset (options)
			lapse ("prune  '%s'" % tag)
			if not retain:
				if verbose:
					print tag, "pruned to empty; dropped."
				del font[tag]
				continue
			else:
				if verbose:
					print tag, "pruned."



	glyphOrder = font.getGlyphOrder()
	glyphOrder = [g for g in glyphOrder if g in glyphs_closed]
	font.setGlyphOrder (glyphOrder)
	font._buildReverseGlyphOrderDict ()
	lapse ("subset GlyphOrder")

	if xml:
		for tag in font.keys():
			writer.begintag (tag)
			writer.newline ()
			font[tag].toXML(writer, font)
			writer.endtag (tag)
			writer.newline ()

	font.save (fontfile + '.subset')
	lapse ("compile and save font")

	last_time = start_time
	lapse ("make one with everything (TOTAL TIME)")
