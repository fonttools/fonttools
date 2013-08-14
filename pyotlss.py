#!/usr/bin/python

# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0(the "License");
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

"""Python OpenType Layout Subsetter.

Later grown into full OpenType subsetter, supporting all standard tables.
"""


# Try running on PyPy
try:
  import numpypy
except ImportError:
  pass

import sys
import struct
import time

import fontTools.ttx


def _add_method(*clazzes):
  """Returns a decorator function that adds a new method to one or
  more classes."""
  def wrapper(method):
    for clazz in clazzes:
      assert clazz.__name__ != 'DefaultTable', 'Oops, table class not found.'
      setattr(clazz, method.func_name, method)
    return None
  return wrapper

def _uniq_sort(l):
  return sorted(set(l))


@_add_method(fontTools.ttLib.tables.otTables.Coverage)
def intersect(self, glyphs):
  "Returns ascending list of matching coverage values."
  return [i for(i,g) in enumerate(self.glyphs) if g in glyphs]

@_add_method(fontTools.ttLib.tables.otTables.Coverage)
def intersect_glyphs(self, glyphs):
  "Returns set of intersecting glyphs."
  return set(g for g in self.glyphs if g in glyphs)

@_add_method(fontTools.ttLib.tables.otTables.Coverage)
def subset(self, glyphs):
  "Returns ascending list of remaining coverage values."
  indices = self.intersect(glyphs)
  self.glyphs = [g for g in self.glyphs if g in glyphs]
  return indices

@_add_method(fontTools.ttLib.tables.otTables.Coverage)
def remap(self, coverage_map):
  "Remaps coverage."
  self.glyphs = [self.glyphs[i] for i in coverage_map]

@_add_method(fontTools.ttLib.tables.otTables.ClassDef)
def intersect(self, glyphs):
  "Returns ascending list of matching class values."
  return _uniq_sort(
     ([0] if any(g not in self.classDefs for g in glyphs) else []) +
      [v for g,v in self.classDefs.iteritems() if g in glyphs])

@_add_method(fontTools.ttLib.tables.otTables.ClassDef)
def intersect_class(self, glyphs, klass):
  "Returns set of glyphs matching class."
  if klass == 0:
    return set(g for g in glyphs if g not in self.classDefs)
  return set(g for g,v in self.classDefs.iteritems()
              if v == klass and g in glyphs)

@_add_method(fontTools.ttLib.tables.otTables.ClassDef)
def subset(self, glyphs, remap=False):
  "Returns ascending list of remaining classes."
  self.classDefs = {g:v for g,v in self.classDefs.iteritems() if g in glyphs}
  # Note: while class 0 has the special meaning of "not matched",
  # if no glyph will ever /not match/, we can optimize class 0 out too.
  indices = _uniq_sort(
     ([0] if any(g not in self.classDefs for g in glyphs) else []) +
      self.classDefs.itervalues())
  if remap:
    self.remap(indices)
  return indices

@_add_method(fontTools.ttLib.tables.otTables.ClassDef)
def remap(self, class_map):
  "Remaps classes."
  self.classDefs = {g:class_map.index(v)
                    for g,v in self.classDefs.iteritems()}

@_add_method(fontTools.ttLib.tables.otTables.SingleSubst)
def closure_glyphs(self, s, cur_glyphs=None):
  if cur_glyphs == None: cur_glyphs = s.glyphs
  if self.Format in [1, 2]:
    s.glyphs.update(v for g,v in self.mapping.iteritems() if g in cur_glyphs)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.SingleSubst)
def subset_glyphs(self, s):
  if self.Format in [1, 2]:
    self.mapping = {g:v for g,v in self.mapping.iteritems()
                    if g in s.glyphs and v in s.glyphs}
    return bool(self.mapping)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.MultipleSubst)
def closure_glyphs(self, s, cur_glyphs=None):
  if cur_glyphs == None: cur_glyphs = s.glyphs
  if self.Format == 1:
    indices = self.Coverage.intersect(cur_glyphs)
    s.glyphs.update(*(self.Sequence[i].Substitute for i in indices))
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.MultipleSubst)
def subset_glyphs(self, s):
  if self.Format == 1:
    indices = self.Coverage.subset(s.glyphs)
    self.Sequence = [self.Sequence[i] for i in indices]
    # Now drop rules generating glyphs we don't want
    indices = [i for i,seq in enumerate(self.Sequence)
         if all(sub in s.glyphs for sub in seq.Substitute)]
    self.Sequence = [self.Sequence[i] for i in indices]
    self.Coverage.remap(indices)
    self.SequenceCount = len(self.Sequence)
    return bool(self.SequenceCount)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.AlternateSubst)
def closure_glyphs(self, s, cur_glyphs=None):
  if cur_glyphs == None: cur_glyphs = s.glyphs
  if self.Format == 1:
    s.glyphs.update(*(vlist for g,vlist in self.alternates.iteritems()
                       if g in cur_glyphs))
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.AlternateSubst)
def subset_glyphs(self, s):
  if self.Format == 1:
    self.alternates = {g:vlist for g,vlist in self.alternates.iteritems()
           if g in s.glyphs and all(v in s.glyphs for v in vlist)}
    return bool(self.alternates)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.LigatureSubst)
def closure_glyphs(self, s, cur_glyphs=None):
  if cur_glyphs == None: cur_glyphs = s.glyphs
  if self.Format == 1:
    s.glyphs.update(*([seq.LigGlyph for seq in seqs
                        if all(c in s.glyphs for c in seq.Component)]
                       for g,seqs in self.ligatures.iteritems()
                       if g in cur_glyphs))
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.LigatureSubst)
def subset_glyphs(self, s):
  if self.Format == 1:
    self.ligatures = {g:v for g,v in self.ligatures.iteritems()
                      if g in s.glyphs}
    self.ligatures = {g:[seq for seq in seqs
             if seq.LigGlyph in s.glyphs and
                all(c in s.glyphs for c in seq.Component)]
          for g,seqs in self.ligatures.iteritems()}
    self.ligatures = {g:v for g,v in self.ligatures.iteritems() if v}
    return bool(self.ligatures)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.ReverseChainSingleSubst)
def closure_glyphs(self, s, cur_glyphs=None):
  if cur_glyphs == None: cur_glyphs = s.glyphs
  if self.Format == 1:
    indices = self.Coverage.intersect(cur_glyphs)
    if(not indices or
        not all(c.intersect(s.glyphs)
                 for c in self.LookAheadCoverage + self.BacktrackCoverage)):
      return
    s.glyphs.update(self.Substitute[i] for i in indices)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.ReverseChainSingleSubst)
def subset_glyphs(self, s):
  if self.Format == 1:
    indices = self.Coverage.subset(s.glyphs)
    self.Substitute = [self.Substitute[i] for i in indices]
    # Now drop rules generating glyphs we don't want
    indices = [i for i,sub in enumerate(self.Substitute)
         if sub in s.glyphs]
    self.Substitute = [self.Substitute[i] for i in indices]
    self.Coverage.remap(indices)
    self.GlyphCount = len(self.Substitute)
    return bool(self.GlyphCount and
                 all(c.subset(s.glyphs)
                      for c in self.LookAheadCoverage+self.BacktrackCoverage))
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.SinglePos)
def subset_glyphs(self, s):
  if self.Format == 1:
    return len(self.Coverage.subset(s.glyphs))
  elif self.Format == 2:
    indices = self.Coverage.subset(s.glyphs)
    self.Value = [self.Value[i] for i in indices]
    self.ValueCount = len(self.Value)
    return bool(self.ValueCount)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.PairPos)
def subset_glyphs(self, s):
  if self.Format == 1:
    indices = self.Coverage.subset(s.glyphs)
    self.PairSet = [self.PairSet[i] for i in indices]
    for p in self.PairSet:
      p.PairValueRecord = [r for r in p.PairValueRecord
                           if r.SecondGlyph in s.glyphs]
      p.PairValueCount = len(p.PairValueRecord)
    self.PairSet = [p for p in self.PairSet if p.PairValueCount]
    self.PairSetCount = len(self.PairSet)
    return bool(self.PairSetCount)
  elif self.Format == 2:
    class1_map = self.ClassDef1.subset(s.glyphs, remap=True)
    class2_map = self.ClassDef2.subset(s.glyphs, remap=True)
    self.Class1Record = [self.Class1Record[i] for i in class1_map]
    for c in self.Class1Record:
      c.Class2Record = [c.Class2Record[i] for i in class2_map]
    self.Class1Count = len(class1_map)
    self.Class2Count = len(class2_map)
    return bool(self.Class1Count and
                 self.Class2Count and
                 self.Coverage.subset(s.glyphs))
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.CursivePos)
def subset_glyphs(self, s):
  if self.Format == 1:
    indices = self.Coverage.subset(s.glyphs)
    self.EntryExitRecord = [self.EntryExitRecord[i] for i in indices]
    self.EntryExitCount = len(self.EntryExitRecord)
    return bool(self.EntryExitCount)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.MarkBasePos)
def subset_glyphs(self, s):
  if self.Format == 1:
    mark_indices = self.MarkCoverage.subset(s.glyphs)
    self.MarkArray.MarkRecord = [self.MarkArray.MarkRecord[i]
                                 for i in mark_indices]
    self.MarkArray.MarkCount = len(self.MarkArray.MarkRecord)
    base_indices = self.BaseCoverage.subset(s.glyphs)
    self.BaseArray.BaseRecord = [self.BaseArray.BaseRecord[i]
                                 for i in base_indices]
    self.BaseArray.BaseCount = len(self.BaseArray.BaseRecord)
    # Prune empty classes
    class_indices = _uniq_sort(v.Class for v in self.MarkArray.MarkRecord)
    self.ClassCount = len(class_indices)
    for m in self.MarkArray.MarkRecord:
      m.Class = class_indices.index(m.Class)
    for b in self.BaseArray.BaseRecord:
      b.BaseAnchor = [b.BaseAnchor[i] for i in class_indices]
    return bool(self.ClassCount and
                 self.MarkArray.MarkCount and
                 self.BaseArray.BaseCount)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.MarkLigPos)
def subset_glyphs(self, s):
  if self.Format == 1:
    mark_indices = self.MarkCoverage.subset(s.glyphs)
    self.MarkArray.MarkRecord = [self.MarkArray.MarkRecord[i]
                                 for i in mark_indices]
    self.MarkArray.MarkCount = len(self.MarkArray.MarkRecord)
    ligature_indices = self.LigatureCoverage.subset(s.glyphs)
    self.LigatureArray.LigatureAttach = [self.LigatureArray.LigatureAttach[i]
                                         for i in ligature_indices]
    self.LigatureArray.LigatureCount = len(self.LigatureArray.LigatureAttach)
    # Prune empty classes
    class_indices = _uniq_sort(v.Class for v in self.MarkArray.MarkRecord)
    self.ClassCount = len(class_indices)
    for m in self.MarkArray.MarkRecord:
      m.Class = class_indices.index(m.Class)
    for l in self.LigatureArray.LigatureAttach:
      for c in l.ComponentRecord:
        c.LigatureAnchor = [c.LigatureAnchor[i] for i in class_indices]
    return bool(self.ClassCount and
                 self.MarkArray.MarkCount and
                 self.LigatureArray.LigatureCount)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.MarkMarkPos)
def subset_glyphs(self, s):
  if self.Format == 1:
    mark1_indices = self.Mark1Coverage.subset(s.glyphs)
    self.Mark1Array.MarkRecord = [self.Mark1Array.MarkRecord[i]
                                  for i in mark1_indices]
    self.Mark1Array.MarkCount = len(self.Mark1Array.MarkRecord)
    mark2_indices = self.Mark2Coverage.subset(s.glyphs)
    self.Mark2Array.Mark2Record = [self.Mark2Array.Mark2Record[i]
                                   for i in mark2_indices]
    self.Mark2Array.MarkCount = len(self.Mark2Array.Mark2Record)
    # Prune empty classes
    class_indices = _uniq_sort(v.Class for v in self.Mark1Array.MarkRecord)
    self.ClassCount = len(class_indices)
    for m in self.Mark1Array.MarkRecord:
      m.Class = class_indices.index(m.Class)
    for b in self.Mark2Array.Mark2Record:
      b.Mark2Anchor = [b.Mark2Anchor[i] for i in class_indices]
    return bool(self.ClassCount and
                 self.Mark1Array.MarkCount and
                 self.Mark2Array.MarkCount)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.SingleSubst,
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
def subset_lookups(self, lookup_indices):
  pass

@_add_method(fontTools.ttLib.tables.otTables.SingleSubst,
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
def collect_lookups(self):
  return []

@_add_method(fontTools.ttLib.tables.otTables.SingleSubst,
             fontTools.ttLib.tables.otTables.AlternateSubst,
             fontTools.ttLib.tables.otTables.ReverseChainSingleSubst)
def may_have_non_1to1(self):
  return False

@_add_method(fontTools.ttLib.tables.otTables.MultipleSubst,
             fontTools.ttLib.tables.otTables.LigatureSubst,
             fontTools.ttLib.tables.otTables.ContextSubst,
             fontTools.ttLib.tables.otTables.ChainContextSubst)
def may_have_non_1to1(self):
  return True

@_add_method(fontTools.ttLib.tables.otTables.ContextSubst,
             fontTools.ttLib.tables.otTables.ChainContextSubst,
             fontTools.ttLib.tables.otTables.ContextPos,
             fontTools.ttLib.tables.otTables.ChainContextPos)
def __classify_context(self):

  class ContextHelper(object):
    def __init__(self, klass, Format):
      if klass.__name__.endswith('Subst'):
        Typ = 'Sub'
        Type = 'Subst'
      else:
        Typ = 'Pos'
        Type = 'Pos'
      if klass.__name__.startswith('Chain'):
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
        ChainContextData = lambda r:(r.LookAheadClassDef,
                                      r.InputClassDef,
                                      r.BacktrackClassDef)
        RuleData = lambda r:(r.Class,)
        ChainRuleData = lambda r:(r.LookAhead, r.Input, r.Backtrack)
        def SetRuleData(r, d):(r.Class,) = d
        def ChainSetRuleData(r, d):(r.LookAhead, r.Input, r.Backtrack) = d
      elif Format == 3:
        Coverage = lambda r: r.Coverage[0]
        ChainCoverage = lambda r: r.InputCoverage[0]
        ContextData = None
        ChainContextData = None
        RuleData = lambda r: r.Coverage
        ChainRuleData = lambda r:(r.LookAheadCoverage +
                                   r.InputCoverage +
                                   r.BacktrackCoverage)
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
        self.Intersect = lambda glyphs, c, r: c.intersect_class(glyphs, r)

        self.ClassDef = 'InputClassDef' if Chain else 'ClassDef'
        self.Input = 'Input' if Chain else 'Class'

  if self.Format not in [1, 2, 3]:
    return None  # Don't shoot the messenger; let it go
  if not hasattr(self.__class__, "__ContextHelpers"):
    self.__class__.__ContextHelpers = {}
  if self.Format not in self.__class__.__ContextHelpers:
    helper = ContextHelper(self.__class__, self.Format)
    self.__class__.__ContextHelpers[self.Format] = helper
  return self.__class__.__ContextHelpers[self.Format]

@_add_method(fontTools.ttLib.tables.otTables.ContextSubst,
             fontTools.ttLib.tables.otTables.ChainContextSubst)
def closure_glyphs(self, s, cur_glyphs=None):
  if cur_glyphs == None: cur_glyphs = s.glyphs
  c = self.__classify_context()

  indices = c.Coverage(self).intersect(s.glyphs)
  if not indices:
    return []
  cur_glyphs = c.Coverage(self).intersect_glyphs(s.glyphs);

  if self.Format == 1:
    ContextData = c.ContextData(self)
    rss = getattr(self, c.RuleSet)
    for i in indices:
      if not rss[i]: continue
      for r in getattr(rss[i], c.Rule):
        if not r: continue
        if all(all(c.Intersect(s.glyphs, cd, k) for k in klist)
          for cd,klist in zip(ContextData, c.RuleData(r))):
          chaos = False
          for ll in getattr(r, c.LookupRecord):
            if not ll: continue
            seqi = ll.SequenceIndex
            if seqi == 0:
              pos_glyphs = set([c.Coverage(self).glyphs[i]])
            else:
              if chaos:
                pos_glyphs = s.glyphs
              else:
                pos_glyphs = set([r.Input[seqi - 1]])
            lookup = s.table.LookupList.Lookup[ll.LookupListIndex]
            chaos = chaos or lookup.may_have_non_1to1()
            lookup.closure_glyphs(s, cur_glyphs=pos_glyphs)
  elif self.Format == 2:
    ClassDef = getattr(self, c.ClassDef)
    indices = ClassDef.intersect(cur_glyphs)
    ContextData = c.ContextData(self)
    rss = getattr(self, c.RuleSet)
    for i in indices:
      if not rss[i]: continue
      for r in getattr(rss[i], c.Rule):
        if not r: continue
        if all(all(c.Intersect(s.glyphs, cd, k) for k in klist)
          for cd,klist in zip(ContextData, c.RuleData(r))):
          chaos = False
          for ll in getattr(r, c.LookupRecord):
            if not ll: continue
            seqi = ll.SequenceIndex
            if seqi == 0:
              pos_glyphs = ClassDef.intersect_class(cur_glyphs, i)
            else:
              if chaos:
                pos_glyphs = s.glyphs
              else:
                pos_glyphs = ClassDef.intersect_class(s.glyphs,
                                                      getattr(r, c.Input)[seqi - 1])
            lookup = s.table.LookupList.Lookup[ll.LookupListIndex]
            chaos = chaos or lookup.may_have_non_1to1()
            lookup.closure_glyphs(s, cur_glyphs=pos_glyphs)
  elif self.Format == 3:
    if not all(x.intersect(s.glyphs) for x in c.RuleData(self)):
      return []
    r = self
    chaos = False
    for ll in getattr(r, c.LookupRecord):
      if not ll: continue
      seqi = ll.SequenceIndex
      if seqi == 0:
        pos_glyphs = cur_glyphs
      else:
        if chaos:
          pos_glyphs = s.glyphs
        else:
          pos_glyphs = r.InputCoverage[seqi].intersect_glyphs(s.glyphs)
      lookup = s.table.LookupList.Lookup[ll.LookupListIndex]
      chaos = chaos or lookup.may_have_non_1to1()
      lookup.closure_glyphs(s, cur_glyphs=pos_glyphs)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.ContextSubst,
             fontTools.ttLib.tables.otTables.ContextPos,
             fontTools.ttLib.tables.otTables.ChainContextSubst,
             fontTools.ttLib.tables.otTables.ChainContextPos)
def subset_glyphs(self, s):
  c = self.__classify_context()

  if self.Format == 1:
    indices = self.Coverage.subset(s.glyphs)
    rss = getattr(self, c.RuleSet)
    rss = [rss[i] for i in indices]
    for rs in rss:
      if not rs: continue
      ss = getattr(rs, c.Rule)
      ss = [r for r in ss
            if r and all(all(g in s.glyphs for g in glist)
              for glist in c.RuleData(r))]
      setattr(rs, c.Rule, ss)
      setattr(rs, c.RuleCount, len(ss))
    # Prune empty subrulesets
    rss = [rs for rs in rss if rs and getattr(rs, c.Rule)]
    setattr(self, c.RuleSet, rss)
    setattr(self, c.RuleSetCount, len(rss))
    return bool(rss)
  elif self.Format == 2:
    if not self.Coverage.subset(s.glyphs):
      return False
    indices = getattr(self, c.ClassDef).subset(self.Coverage.glyphs,
                                                 remap=False)
    rss = getattr(self, c.RuleSet)
    rss = [rss[i] for i in indices]
    ContextData = c.ContextData(self)
    klass_maps = [x.subset(s.glyphs, remap=True) for x in ContextData]
    for rs in rss:
      if not rs: continue
      ss = getattr(rs, c.Rule)
      ss = [r for r in ss
            if r and all(all(k in klass_map for k in klist)
              for klass_map,klist in zip(klass_maps, c.RuleData(r)))]
      setattr(rs, c.Rule, ss)
      setattr(rs, c.RuleCount, len(ss))

      # Remap rule classes
      for r in ss:
        c.SetRuleData(r, [[klass_map.index(k) for k in klist]
               for klass_map,klist in zip(klass_maps, c.RuleData(r))])
    # Prune empty subrulesets
    rss = [rs for rs in rss if rs and getattr(rs, c.Rule)]
    setattr(self, c.RuleSet, rss)
    setattr(self, c.RuleSetCount, len(rss))
    return bool(rss)
  elif self.Format == 3:
    return all(x.subset(s.glyphs) for x in c.RuleData(self))
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.ContextSubst,
             fontTools.ttLib.tables.otTables.ChainContextSubst,
             fontTools.ttLib.tables.otTables.ContextPos,
             fontTools.ttLib.tables.otTables.ChainContextPos)
def subset_lookups(self, lookup_indices):
  c = self.__classify_context()

  if self.Format in [1, 2]:
    for rs in getattr(self, c.RuleSet):
      if not rs: continue
      for r in getattr(rs, c.Rule):
        if not r: continue
        setattr(r, c.LookupRecord,
                 [ll for ll in getattr(r, c.LookupRecord)
                  if ll and ll.LookupListIndex in lookup_indices])
        for ll in getattr(r, c.LookupRecord):
          if not ll: continue
          ll.LookupListIndex = lookup_indices.index(ll.LookupListIndex)
  elif self.Format == 3:
    setattr(self, c.LookupRecord,
             [ll for ll in getattr(self, c.LookupRecord)
              if ll and ll.LookupListIndex in lookup_indices])
    for ll in getattr(self, c.LookupRecord):
      if not ll: continue
      ll.LookupListIndex = lookup_indices.index(ll.LookupListIndex)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.ContextSubst,
             fontTools.ttLib.tables.otTables.ChainContextSubst,
             fontTools.ttLib.tables.otTables.ContextPos,
             fontTools.ttLib.tables.otTables.ChainContextPos)
def collect_lookups(self):
  c = self.__classify_context()

  if self.Format in [1, 2]:
    return [ll.LookupListIndex
      for rs in getattr(self, c.RuleSet) if rs
      for r in getattr(rs, c.Rule) if r
      for ll in getattr(r, c.LookupRecord) if ll]
  elif self.Format == 3:
    return [ll.LookupListIndex
      for ll in getattr(self, c.LookupRecord) if ll]
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.ExtensionSubst)
def closure_glyphs(self, s, cur_glyphs=None):
  if self.Format == 1:
    self.ExtSubTable.closure_glyphs(s, cur_glyphs)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.ExtensionSubst)
def may_have_non_1to1(self):
  if self.Format == 1:
    return self.ExtSubTable.may_have_non_1to1()
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.ExtensionSubst,
             fontTools.ttLib.tables.otTables.ExtensionPos)
def subset_glyphs(self, s):
  if self.Format == 1:
    return self.ExtSubTable.subset_glyphs(s)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.ExtensionSubst,
             fontTools.ttLib.tables.otTables.ExtensionPos)
def subset_lookups(self, lookup_indices):
  if self.Format == 1:
    return self.ExtSubTable.subset_lookups(lookup_indices)
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.ExtensionSubst,
             fontTools.ttLib.tables.otTables.ExtensionPos)
def collect_lookups(self):
  if self.Format == 1:
    return self.ExtSubTable.collect_lookups()
  else:
    assert 0, "unknown format: %s" % self.Format

@_add_method(fontTools.ttLib.tables.otTables.Lookup)
def closure_glyphs(self, s, cur_glyphs=None):
  for st in self.SubTable:
    if not st: continue
    st.closure_glyphs(s, cur_glyphs)

@_add_method(fontTools.ttLib.tables.otTables.Lookup)
def subset_glyphs(self, s):
  self.SubTable = [st for st in self.SubTable if st and st.subset_glyphs(s)]
  self.SubTableCount = len(self.SubTable)
  return bool(self.SubTableCount)

@_add_method(fontTools.ttLib.tables.otTables.Lookup)
def subset_lookups(self, lookup_indices):
  for s in self.SubTable:
    s.subset_lookups(lookup_indices)

@_add_method(fontTools.ttLib.tables.otTables.Lookup)
def collect_lookups(self):
  return _uniq_sort(sum((st.collect_lookups() for st in self.SubTable
                         if st), []))

@_add_method(fontTools.ttLib.tables.otTables.Lookup)
def may_have_non_1to1(self):
  return any(st.may_have_non_1to1() for st in self.SubTable if st)

@_add_method(fontTools.ttLib.tables.otTables.LookupList)
def subset_glyphs(self, s):
  "Returns the indices of nonempty lookups."
  return [i for(i,l) in enumerate(self.Lookup) if l and l.subset_glyphs(s)]

@_add_method(fontTools.ttLib.tables.otTables.LookupList)
def subset_lookups(self, lookup_indices):
  self.Lookup = [self.Lookup[i] for i in lookup_indices
                 if i < self.LookupCount]
  self.LookupCount = len(self.Lookup)
  for l in self.Lookup:
    l.subset_lookups(lookup_indices)

@_add_method(fontTools.ttLib.tables.otTables.LookupList)
def closure_lookups(self, lookup_indices):
  lookup_indices = _uniq_sort(lookup_indices)
  recurse = lookup_indices
  while True:
    recurse_lookups = sum((self.Lookup[i].collect_lookups()
                            for i in recurse if i < self.LookupCount), [])
    recurse_lookups = [l for l in recurse_lookups
                       if l not in lookup_indices and l < self.LookupCount]
    if not recurse_lookups:
      return _uniq_sort(lookup_indices)
    recurse_lookups = _uniq_sort(recurse_lookups)
    lookup_indices.extend(recurse_lookups)
    recurse = recurse_lookups

@_add_method(fontTools.ttLib.tables.otTables.Feature)
def subset_lookups(self, lookup_indices):
  self.LookupListIndex = [l for l in self.LookupListIndex
                          if l in lookup_indices]
  # Now map them.
  self.LookupListIndex = [lookup_indices.index(l)
                          for l in self.LookupListIndex]
  self.LookupCount = len(self.LookupListIndex)
  return self.LookupCount

@_add_method(fontTools.ttLib.tables.otTables.Feature)
def collect_lookups(self):
  return self.LookupListIndex[:]

@_add_method(fontTools.ttLib.tables.otTables.FeatureList)
def subset_lookups(self, lookup_indices):
  "Returns the indices of nonempty features."
  feature_indices = [i for(i,f) in enumerate(self.FeatureRecord)
                     if f.Feature.subset_lookups(lookup_indices)]
  self.subset_features(feature_indices)
  return feature_indices

@_add_method(fontTools.ttLib.tables.otTables.FeatureList)
def collect_lookups(self, feature_indices):
  return _uniq_sort(sum((self.FeatureRecord[i].Feature.collect_lookups()
                         for i in feature_indices
                          if i < self.FeatureCount), []))

@_add_method(fontTools.ttLib.tables.otTables.FeatureList)
def subset_features(self, feature_indices):
  self.FeatureRecord = [self.FeatureRecord[i] for i in feature_indices]
  self.FeatureCount = len(self.FeatureRecord)
  return bool(self.FeatureCount)

@_add_method(fontTools.ttLib.tables.otTables.DefaultLangSys,
             fontTools.ttLib.tables.otTables.LangSys)
def subset_features(self, feature_indices):
  if self.ReqFeatureIndex in feature_indices:
    self.ReqFeatureIndex = feature_indices.index(self.ReqFeatureIndex)
  else:
    self.ReqFeatureIndex = 65535
  self.FeatureIndex = [f for f in self.FeatureIndex if f in feature_indices]
  # Now map them.
  self.FeatureIndex = [feature_indices.index(f) for f in self.FeatureIndex
                       if f in feature_indices]
  self.FeatureCount = len(self.FeatureIndex)
  return bool(self.FeatureCount or self.ReqFeatureIndex != 65535)

@_add_method(fontTools.ttLib.tables.otTables.DefaultLangSys,
             fontTools.ttLib.tables.otTables.LangSys)
def collect_features(self):
  feature_indices = self.FeatureIndex[:]
  if self.ReqFeatureIndex != 65535:
    feature_indices.append(self.ReqFeatureIndex)
  return _uniq_sort(feature_indices)

@_add_method(fontTools.ttLib.tables.otTables.Script)
def subset_features(self, feature_indices):
  if(self.DefaultLangSys and
      not self.DefaultLangSys.subset_features(feature_indices)):
    self.DefaultLangSys = None
  self.LangSysRecord = [l for l in self.LangSysRecord
                        if l.LangSys.subset_features(feature_indices)]
  self.LangSysCount = len(self.LangSysRecord)
  return bool(self.LangSysCount or self.DefaultLangSys)

@_add_method(fontTools.ttLib.tables.otTables.Script)
def collect_features(self):
  feature_indices = [l.LangSys.collect_features() for l in self.LangSysRecord]
  if self.DefaultLangSys:
    feature_indices.append(self.DefaultLangSys.collect_features())
  return _uniq_sort(sum(feature_indices, []))

@_add_method(fontTools.ttLib.tables.otTables.ScriptList)
def subset_features(self, feature_indices):
  self.ScriptRecord = [s for s in self.ScriptRecord
                       if s.Script.subset_features(feature_indices)]
  self.ScriptCount = len(self.ScriptRecord)
  return bool(self.ScriptCount)

@_add_method(fontTools.ttLib.tables.otTables.ScriptList)
def collect_features(self):
  return _uniq_sort(sum((s.Script.collect_features()
                         for s in self.ScriptRecord), []))

@_add_method(fontTools.ttLib.getTableClass('GSUB'))
def closure_glyphs(self, s):
  s.table = self.table
  feature_indices = self.table.ScriptList.collect_features()
  lookup_indices = self.table.FeatureList.collect_lookups(feature_indices)
  while True:
    orig_glyphs = s.glyphs.copy()
    for i in lookup_indices:
      if i >= self.table.LookupList.LookupCount: continue
      if not self.table.LookupList.Lookup[i]: continue
      self.table.LookupList.Lookup[i].closure_glyphs(s)
    if orig_glyphs == s.glyphs:
      break
  del s.table

@_add_method(fontTools.ttLib.getTableClass('GSUB'),
             fontTools.ttLib.getTableClass('GPOS'))
def subset_glyphs(self, s):
  s.glyphs = s.glyphs_gsubed
  lookup_indices = self.table.LookupList.subset_glyphs(s)
  self.subset_lookups(lookup_indices)
  self.prune_lookups()
  return True

@_add_method(fontTools.ttLib.getTableClass('GSUB'),
             fontTools.ttLib.getTableClass('GPOS'))
def subset_lookups(self, lookup_indices):
  """Retrains specified lookups, then removes empty features, language
     systems, and scripts."""
  self.table.LookupList.subset_lookups(lookup_indices)
  feature_indices = self.table.FeatureList.subset_lookups(lookup_indices)
  self.table.ScriptList.subset_features(feature_indices)

@_add_method(fontTools.ttLib.getTableClass('GSUB'),
             fontTools.ttLib.getTableClass('GPOS'))
def prune_lookups(self):
  "Remove unreferenced lookups"
  feature_indices = self.table.ScriptList.collect_features()
  lookup_indices = self.table.FeatureList.collect_lookups(feature_indices)
  lookup_indices = self.table.LookupList.closure_lookups(lookup_indices)
  self.subset_lookups(lookup_indices)

@_add_method(fontTools.ttLib.getTableClass('GSUB'),
             fontTools.ttLib.getTableClass('GPOS'))
def subset_feature_tags(self, feature_tags):
  feature_indices = [i for(i,f) in
                     enumerate(self.table.FeatureList.FeatureRecord)
                     if f.FeatureTag in feature_tags]
  self.table.FeatureList.subset_features(feature_indices)
  self.table.ScriptList.subset_features(feature_indices)

@_add_method(fontTools.ttLib.getTableClass('GSUB'),
             fontTools.ttLib.getTableClass('GPOS'))
def prune_pre_subset(self, options):
  if options.layout_features and '*' not in options.layout_features:
    self.subset_feature_tags(options.layout_features)
  self.prune_lookups()
  return True

@_add_method(fontTools.ttLib.getTableClass('GDEF'))
def subset_glyphs(self, s):
  glyphs = s.glyphs_gsubed
  table = self.table
  if table.LigCaretList:
    indices = table.LigCaretList.Coverage.subset(glyphs)
    table.LigCaretList.LigGlyph = [table.LigCaretList.LigGlyph[i]
                                   for i in indices]
    table.LigCaretList.LigGlyphCount = len(table.LigCaretList.LigGlyph)
    if not table.LigCaretList.LigGlyphCount:
      table.LigCaretList = None
  if table.MarkAttachClassDef:
    table.MarkAttachClassDef.classDefs = {g:v for g,v in
                                          table.MarkAttachClassDef.classDefs.iteritems()
                                          if g in glyphs}
    if not table.MarkAttachClassDef.classDefs:
      table.MarkAttachClassDef = None
  if table.GlyphClassDef:
    table.GlyphClassDef.classDefs = {g:v for g,v in
                                     table.GlyphClassDef.classDefs.iteritems()
                                     if g in glyphs}
    if not table.GlyphClassDef.classDefs:
      table.GlyphClassDef = None
  if table.AttachList:
    indices = table.AttachList.Coverage.subset(glyphs)
    table.AttachList.AttachPoint = [table.AttachList.AttachPoint[i]
                                    for i in indices]
    table.AttachList.GlyphCount = len(table.AttachList.AttachPoint)
    if not table.AttachList.GlyphCount:
      table.AttachList = None
  return bool(table.LigCaretList or
               table.MarkAttachClassDef or
               table.GlyphClassDef or
               table.AttachList)

@_add_method(fontTools.ttLib.getTableClass('kern'))
def prune_pre_subset(self, options):
  # Prune unknown kern table types
  self.kernTables = [t for t in self.kernTables if hasattr(t, 'kernTable')]
  return bool(self.kernTables)

@_add_method(fontTools.ttLib.getTableClass('kern'))
def subset_glyphs(self, s):
  glyphs = s.glyphs_gsubed
  for t in self.kernTables:
    t.kernTable = {(a,b):v for((a,b),v) in t.kernTable.iteritems()
                   if a in glyphs and b in glyphs}
  self.kernTables = [t for t in self.kernTables if t.kernTable]
  return bool(self.kernTables)

@_add_method(fontTools.ttLib.getTableClass('hmtx'),
             fontTools.ttLib.getTableClass('vmtx'))
def subset_glyphs(self, s):
  self.metrics = {g:v for g,v in self.metrics.iteritems() if g in s.glyphs}
  return bool(self.metrics)

@_add_method(fontTools.ttLib.getTableClass('hdmx'))
def subset_glyphs(self, s):
  self.hdmx = {sz:{g:v for g,v in l.iteritems() if g in s.glyphs}
               for(sz,l) in self.hdmx.iteritems()}
  return bool(self.hdmx)

@_add_method(fontTools.ttLib.getTableClass('VORG'))
def subset_glyphs(self, s):
  self.VOriginRecords = {g:v for g,v in self.VOriginRecords.iteritems()
                         if g in s.glyphs}
  self.numVertOriginYMetrics = len(self.VOriginRecords)
  return True  # Never drop; has default metrics

@_add_method(fontTools.ttLib.getTableClass('post'))
def prune_pre_subset(self, options):
  if not options.glyph_names:
    self.formatType = 3.0
  return True

@_add_method(fontTools.ttLib.getTableClass('post'))
def subset_glyphs(self, s):
  self.extraNames = []  # This seems to do it
  return True

@_add_method(fontTools.ttLib.getTableModule('glyf').Glyph)
def getComponentNamesFast(self, glyfTable):
  if struct.unpack(">h", self.data[:2])[0] >= 0:
    return []  # Not composite
  data = self.data
  i = 10
  components = []
  more = 1
  while more:
    flags, glyphID = struct.unpack(">HH", data[i:i+4])
    i += 4
    flags = int(flags)
    components.append(glyfTable.getGlyphName(int(glyphID)))

    if flags & 0x0001: i += 4  # ARG_1_AND_2_ARE_WORDS
    else: i += 2
    if flags & 0x0008: i += 2  # WE_HAVE_A_SCALE
    elif flags & 0x0040: i += 4  # WE_HAVE_AN_X_AND_Y_SCALE
    elif flags & 0x0080: i += 8  # WE_HAVE_A_TWO_BY_TWO
    more = flags & 0x0020  # MORE_COMPONENTS

  return components

@_add_method(fontTools.ttLib.getTableModule('glyf').Glyph)
def remapComponentsFast(self, indices):
  if struct.unpack(">h", self.data[:2])[0] >= 0:
    return  # Not composite
  data = bytearray(self.data)
  i = 10
  more = 1
  while more:
    flags =(data[i] << 8) | data[i+1]
    glyphID =(data[i+2] << 8) | data[i+3]
    # Remap
    glyphID = indices.index(glyphID)
    data[i+2] = glyphID >> 8
    data[i+3] = glyphID & 0xFF
    i += 4
    flags = int(flags)

    if flags & 0x0001: i += 4  # ARG_1_AND_2_ARE_WORDS
    else: i += 2
    if flags & 0x0008: i += 2  # WE_HAVE_A_SCALE
    elif flags & 0x0040: i += 4  # WE_HAVE_AN_X_AND_Y_SCALE
    elif flags & 0x0080: i += 8  # WE_HAVE_A_TWO_BY_TWO
    more = flags & 0x0020  # MORE_COMPONENTS

  self.data = str(data)

@_add_method(fontTools.ttLib.getTableModule('glyf').Glyph)
def dropInstructionsFast(self):
  numContours = struct.unpack(">h", self.data[:2])[0]
  data = bytearray(self.data)
  i = 10
  if numContours >= 0:
    i += 2 * numContours  # endPtsOfContours
    instructionLen =(data[i] << 8) | data[i+1]
    # Zero it
    data[i] = data [i+1] = 0
    i += 2
    if instructionLen:
      # Splice it out
      data = data[:i] + data[i+instructionLen:]
  else:
    more = 1
    while more:
      flags =(data[i] << 8) | data[i+1]
      # Turn instruction flag off
      flags &= ~0x0100  # WE_HAVE_INSTRUCTIONS
      data[i+0] = flags >> 8
      data[i+1] = flags & 0xFF
      i += 4
      flags = int(flags)

      if flags & 0x0001: i += 4  # ARG_1_AND_2_ARE_WORDS
      else: i += 2
      if flags & 0x0008: i += 2  # WE_HAVE_A_SCALE
      elif flags & 0x0040: i += 4  # WE_HAVE_AN_X_AND_Y_SCALE
      elif flags & 0x0080: i += 8  # WE_HAVE_A_TWO_BY_TWO
      more = flags & 0x0020  # MORE_COMPONENTS

    # Cut off
    data = data[:i]
  if len(data) % 4:
    # add pad bytes
    nPadBytes = 4 -(len(data) % 4)
    for i in range(nPadBytes):
      data.append(0)
  self.data = str(data)

@_add_method(fontTools.ttLib.getTableClass('glyf'))
def closure_glyphs(self, s):
  decompose = s.glyphs
  # I don't know if component glyphs can be composite themselves.
  # We handle them anyway.
  while True:
    components = set()
    for g in decompose:
      if g not in self.glyphs:
        continue
      gl = self.glyphs[g]
      if hasattr(gl, "data"):
        for c in gl.getComponentNamesFast(self):
          if c not in s.glyphs:
            components.add(c)
      else:
        # TTX seems to expand gid0..3 always
        if gl.isComposite():
          for c in gl.components:
            if c.glyphName not in s.glyphs:
              components.add(c.glyphName)
    components = set(c for c in components if c not in s.glyphs)
    if not components:
      break
    decompose = components
    s.glyphs.update(components)

@_add_method(fontTools.ttLib.getTableClass('glyf'))
def subset_glyphs(self, s):
  self.glyphs = {g:v for g,v in self.glyphs.iteritems() if g in s.glyphs}
  indices = [i for i,g in enumerate(self.glyphOrder) if g in s.glyphs]
  for v in self.glyphs.itervalues():
    if hasattr(v, "data"):
      v.remapComponentsFast(indices)
    else:
      pass  # No need
  self.glyphOrder = [g for g in self.glyphOrder if g in s.glyphs]
  return bool(self.glyphs)

@_add_method(fontTools.ttLib.getTableClass('glyf'))
def prune_post_subset(self, options):
  if not options.hinting:
    for v in self.glyphs.itervalues():
      if hasattr(v, "data"):
        v.dropInstructionsFast()
      else:
        v.program = fontTools.ttLib.tables.ttProgram.Program()
        v.program.fromBytecode([])
  return True

@_add_method(fontTools.ttLib.getTableClass('CFF '))
def prune_pre_subset(self, options):
  cff = self.cff
  # CFF table should have one font only
  cff.fontNames = cff.fontNames[:1]
  return bool(cff.fontNames)

@_add_method(fontTools.ttLib.getTableClass('CFF '))
def subset_glyphs(self, s):
  cff = self.cff
  for fontname in cff.keys():
    font = cff[fontname]
    cs = font.CharStrings

    # Load all glyphs
    for g in font.charset:
      if g not in s.glyphs: continue
      c,sel = cs.getItemAndSelector(g)

    if cs.charStringsAreIndexed:
      indices = [i for i,g in enumerate(font.charset) if g in s.glyphs]
      csi = cs.charStringsIndex
      csi.items = [csi.items[i] for i in indices]
      csi.count = len(csi.items)
      del csi.file, csi.offsets
      if hasattr(font, "FDSelect"):
        sel = font.FDSelect
        sel.format = None
        sel.gidArray = [sel.gidArray[i] for i in indices]
      cs.charStrings = {g:indices.index(v)
                        for g,v in cs.charStrings.iteritems()
                        if g in s.glyphs}
    else:
      cs.charStrings = {g:v
                        for g,v in cs.charStrings.iteritems()
                        if g in s.glyphs}
    font.charset = [g for g in font.charset if g in s.glyphs]
    font.numGlyphs = len(font.charset)

  return any(cff[fontname].numGlyphs for fontname in cff.keys())

@_add_method(fontTools.ttLib.getTableClass('CFF '))
def prune_post_subset(self, options):
  cff = self.cff

  class _MarkingT2Decompiler(fontTools.misc.psCharStrings.SimpleT2Decompiler):

    def __init__(self, localSubrs, globalSubrs):
      fontTools.misc.psCharStrings.SimpleT2Decompiler.__init__(self,
                                                               localSubrs,
                                                               globalSubrs)
      for subrs in [localSubrs, globalSubrs]:
        if subrs and not hasattr(subrs, "_used"):
          subrs._used = set()

    def op_callsubr(self, index):
      self.localSubrs._used.add(self.operandStack[-1]+self.localBias)
      fontTools.misc.psCharStrings.SimpleT2Decompiler.op_callsubr(self, index)

    def op_callgsubr(self, index):
      self.globalSubrs._used.add(self.operandStack[-1]+self.globalBias)
      fontTools.misc.psCharStrings.SimpleT2Decompiler.op_callgsubr(self, index)

  for fontname in cff.keys():
    font = cff[fontname]
    cs = font.CharStrings

    # Mark all used subroutines
    for g in font.charset:
      c,sel = cs.getItemAndSelector(g)
      subrs = getattr(c.private, "Subrs", [])
      decompiler = _MarkingT2Decompiler(subrs, c.globalSubrs)
      decompiler.execute(c)

    emptyCharString = fontTools.misc.psCharStrings.T2CharString (bytecode='\x0B')
    all_subrs = [font.GlobalSubrs]
    all_subrs.extend(fd.Private.Subrs for fd in font.FDArray if hasattr(fd.Private, 'Subrs'))
    for subrs in all_subrs:
      if not subrs: continue
      if not hasattr(subrs, '_used'):
        subrs._used = set()
      for i in range (subrs.count):
        if i not in subrs._used:
          subrs.items[i] = emptyCharString
        else:
          subrs[i]  # It ought to be loaded alreay, but just in case...
      del subrs._used
      # TODO(behdad) renumber subroutines
      #del subrs.file, subrs.offsets
      #subrs.offsets = []

    if hasattr(font, "FDSelect"):
      # TODO(behdad) Drop unused FDArray items; remap FDSelect'ors
      sel = font.FDSelect
      indices = _uniq_sort(sel.gidArray)
      sel.gidArray = [indices.index (ss) for ss in sel.gidArray]
      arr = font.FDArray
      for i in indices:
        arr[i]  # Make sure it's loaded
      arr.items = [arr.items[i] for i in indices]
      arr.count = len(arr.items)
      del arr.file, arr.offsets

    if not options.hinting:
      pass  # Drop hints

  return True

@_add_method(fontTools.ttLib.getTableClass('cmap'))
def closure_glyphs(self, s):
  tables = [t for t in self.tables
            if t.platformID == 3 and t.platEncID in [1, 10]]
  for u in s.unicodes_requested:
    found = False
    for table in tables:
      if u in table.cmap:
        s.glyphs.add(table.cmap[u])
        found = True
        break
    if not found:
      s.log("No glyph for Unicode value %s; skipping." % u)

@_add_method(fontTools.ttLib.getTableClass('cmap'))
def prune_pre_subset(self, options):
  if not options.legacy_cmap:
    # Drop non-Unicode / non-Symbol cmaps
    self.tables = [t for t in self.tables
                   if t.platformID == 3 and t.platEncID in [0, 1, 10]]
  if not options.symbol_cmap:
    self.tables = [t for t in self.tables
                   if t.platformID == 3 and t.platEncID in [1, 10]]
  # TODO(behdad) Only keep one subtable?
  # For now, drop format=0 which can't be subset_glyphs easily?
  self.tables = [t for t in self.tables if t.format != 0]
  return bool(self.tables)

@_add_method(fontTools.ttLib.getTableClass('cmap'))
def subset_glyphs(self, s):
  s.glyphs = s.glyphs_cmaped
  for t in self.tables:
    # For reasons I don't understand I need this here
    # to force decompilation of the cmap format 14.
    try:
      getattr(t, "asdf")
    except AttributeError:
      pass
    if t.format == 14:
      # TODO(behdad) XXX We drop all the default-UVS mappings(g==None).
      t.uvsDict = {v:[(u,g) for(u,g) in l if g in s.glyphs]
                   for(v,l) in t.uvsDict.iteritems()}
      t.uvsDict = {v:l for(v,l) in t.uvsDict.iteritems() if l}
    else:
      t.cmap = {u:g for(u,g) in t.cmap.iteritems()
                if g in s.glyphs_requested or u in s.unicodes_requested}
  self.tables = [t for t in self.tables
                 if(t.cmap if t.format != 14 else t.uvsDict)]
  # TODO(behdad) Convert formats when needed.
  # In particular, if we have a format=12 without non-BMP
  # characters, either drop format=12 one or convert it
  # to format=4 if there's not one.
  return bool(self.tables)

@_add_method(fontTools.ttLib.getTableClass('name'))
def prune_pre_subset(self, options):
  if '*' not in options.name_IDs:
    self.names = [n for n in self.names if n.nameID in options.name_IDs]
  if not options.name_legacy:
    self.names = [n for n in self.names
                  if n.platformID == 3 and n.platEncID == 1]
  if '*' not in options.name_languages:
    self.names = [n for n in self.names if n.langID in options.name_languages]
  return True  # Retain even if empty


# TODO(behdad) OS/2 ulUnicodeRange / ulCodePageRange?
# TODO(behdad) Drop unneeded GSUB/GPOS Script/LangSys entries.
# TODO(behdad) Avoid recursing too much.
# TODO(behdad) Text direction considerations.
# TODO(behdad) Text script / language considerations.
# TODO(behdad) Drop unknown tables?  Using DefaultTable.prune?
# TODO(behdad) Drop GPOS Device records if not hinting?
# TODO(behdad) Move font name loading hack to Subsetter?


class Options(object):

  class UnknownOptionError(Exception):
    pass

  _drop_tables_default = ['BASE', 'JSTF', 'DSIG', 'EBDT', 'EBLC', 'EBSC',
                          'PCLT', 'LTSH']
  _drop_tables_default += ['Feat', 'Glat', 'Gloc', 'Silf', 'Sill']  # Graphite
  _drop_tables_default += ['CBLC', 'CBDT', 'sbix', 'COLR', 'CPAL']  # Color
  _no_subset_tables_default = ['gasp', 'head', 'hhea', 'maxp', 'vhea', 'OS/2',
                               'loca', 'name', 'cvt ', 'fpgm', 'prep']
  _hinting_tables_default = ['cvt ', 'fpgm', 'prep', 'hdmx', 'VDMX']

  # Based on HarfBuzz shapers
  _layout_features_groups = {
    # Default shaper
    'common': ['ccmp', 'liga', 'locl', 'mark', 'mkmk', 'rlig'],
    'horizontal': ['calt', 'clig', 'curs', 'kern', 'rclt'],
    'vertical':  ['valt', 'vert', 'vkrn', 'vpal', 'vrt2'],
    'ltr': ['ltra', 'ltrm'],
    'rtl': ['rtla', 'rtlm'],
    # Complex shapers
    'arabic': ['init', 'medi', 'fina', 'isol', 'med2', 'fin2', 'fin3',
               'cswh', 'mset'],
    'hangul': ['ljmo', 'vjmo', 'tjmo'],
    'tibetal': ['abvs', 'blws', 'abvm', 'blwm'],
    'indic': ['nukt', 'akhn', 'rphf', 'rkrf', 'pref', 'blwf', 'half',
              'abvf', 'pstf', 'cfar', 'vatu', 'cjct', 'init', 'pres',
              'abvs', 'blws', 'psts', 'haln', 'dist', 'abvm', 'blwm'],
  }
  _layout_features_default = _uniq_sort(sum(
      _layout_features_groups.itervalues(), []))

  drop_tables = _drop_tables_default
  no_subset_tables = _no_subset_tables_default
  hinting_tables = _hinting_tables_default
  layout_features = _layout_features_default
  hinting = False
  glyph_names = False
  legacy_cmap = False
  symbol_cmap = False
  name_IDs = [1, 2]  # Family and Style
  name_legacy = False
  name_languages = [0x0409]  # English
  mandatory_glyphs = True  # First four for TrueType, .notdef for CFF
  recalc_bboxes = False  # Slows us down

  def __init__(self, **kwargs):

    self.set(**kwargs)

  def set(self, **kwargs):
    for k,v in kwargs.iteritems():
      if not hasattr(self, k):
        raise self.UnknownOptionError("Unknown option '%s'" % k)
      setattr(self, k, v)

  def parse_opts(self, argv, ignore_unknown=False):
    ret = []
    opts = {}
    for a in argv:
      orig_a = a
      if not a.startswith('--'):
        ret.append(a)
        continue
      a = a[2:]
      i = a.find('=')
      if i == -1:
        if a.startswith("no-"):
          k = a[3:]
          v = False
        else:
          k = a
          v = True
      else:
        k = a[:i]
        v = a[i+1:]
      k = k.replace('-', '_')
      if not hasattr(self, k):
        if ignore_unknown == True or k in ignore_unknown:
          ret.append(orig_a)
          continue
        else:
          raise self.UnknownOptionError("Unknown option '%s'" % a)

      ov = getattr(self, k)
      if isinstance(ov, bool):
        v = bool(v)
      elif isinstance(ov, int):
        v = int(v)
      elif isinstance(ov, list):
        v = v.split(',')
        v = [int(x, 0) if x[0] in range(10) else x for x in v]

      opts[k] = v
    self.set(**opts)

    return ret


class Subsetter(object):

  def __init__(self, options=None, log=None):

    if not log:
      log = Logger()
    if not options:
      options = Options()

    self.options = options
    self.log = log
    self.unicodes_requested = set()
    self.glyphs_requested = set()
    self.glyphs = set()

  def populate(self, glyphs=[], unicodes=[], text=""):
    self.unicodes_requested.update(unicodes)
    if isinstance(text, str):
      text = text.decode("utf8")
    for u in text:
      self.unicodes_requested.add(ord(u))
    self.glyphs_requested.update(glyphs)
    self.glyphs.update(glyphs)

  def _prune_pre_subset(self, font):

    for tag in font.keys():
      if tag == 'GlyphOrder': continue

      if(tag in self.options.drop_tables or
         (tag in self.options.hinting_tables and not self.options.hinting)):
        self.log(tag, "dropped")
        del font[tag]
        continue

      clazz = fontTools.ttLib.getTableClass(tag)

      if hasattr(clazz, 'prune_pre_subset'):
        table = font[tag]
        retain = table.prune_pre_subset(self.options)
        self.log.lapse("prune  '%s'" % tag)
        if not retain:
          self.log(tag, "pruned to empty; dropped")
          del font[tag]
          continue
        else:
          self.log(tag, "pruned")

  def _closure_glyphs(self, font):

    self.glyphs = self.glyphs_requested.copy()

    if 'cmap' in font:
      font['cmap'].closure_glyphs(self)
    self.glyphs_cmaped = self.glyphs

    if self.options.mandatory_glyphs:
      if 'glyf' in font:
        for i in range(4):
          self.glyphs.add(font.getGlyphName(i))
        self.log("Added first four glyphs to subset")
      else:
        self.glyphs.add('.notdef')
        self.log("Added .notdef glyph to subset")

    if 'GSUB' in font:
      self.log("Closing glyph list over 'GSUB': %d glyphs before" %
                len(self.glyphs))
      self.log.glyphs(self.glyphs, font=font)
      font['GSUB'].closure_glyphs(self)
      self.log("Closed  glyph list over 'GSUB': %d glyphs after" %
                len(self.glyphs))
      self.log.glyphs(self.glyphs, font=font)
      self.log.lapse("close glyph list over 'GSUB'")
    self.glyphs_gsubed = self.glyphs.copy()

    if 'glyf' in font:
      self.log("Closing glyph list over 'glyf': %d glyphs before" %
                len(self.glyphs))
      self.log.glyphs(self.glyphs, font=font)
      font['glyf'].closure_glyphs(self)
      self.log("Closed  glyph list over 'glyf': %d glyphs after" %
                len(self.glyphs))
      self.log.glyphs(self.glyphs, font=font)
      self.log.lapse("close glyph list over 'glyf'")
    self.glyphs_glyfed = self.glyphs.copy()

    self.glyphs_all = self.glyphs.copy()

    self.log("Retaining %d glyphs: " % len(self.glyphs_all))

  def _subset_glyphs(self, font):
    for tag in font.keys():
      if tag == 'GlyphOrder': continue
      clazz = fontTools.ttLib.getTableClass(tag)

      if tag in self.options.no_subset_tables:
        self.log(tag, "subsetting not needed")
      elif hasattr(clazz, 'subset_glyphs'):
        table = font[tag]
        self.glyphs = self.glyphs_all
        retain = table.subset_glyphs(self)
        self.glyphs = self.glyphs_all
        self.log.lapse("subset '%s'" % tag)
        if not retain:
          self.log(tag, "subsetted to empty; dropped")
          del font[tag]
        else:
          self.log(tag, "subsetted")
      else:
        self.log(tag, "NOT subset; don't know how to subset; dropped")
        del font[tag]

    glyphOrder = font.getGlyphOrder()
    glyphOrder = [g for g in glyphOrder if g in self.glyphs_all]
    font.setGlyphOrder(glyphOrder)
    font._buildReverseGlyphOrderDict()
    self.log.lapse("subset GlyphOrder")

  def _prune_post_subset(self, font):
    for tag in font.keys():
      if tag == 'GlyphOrder': continue
      clazz = fontTools.ttLib.getTableClass(tag)
      if hasattr(clazz, 'prune_post_subset'):
        table = font[tag]
        retain = table.prune_post_subset(self.options)
        self.log.lapse("prune  '%s'" % tag)
        if not retain:
          self.log(tag, "pruned to empty; dropped")
          del font[tag]
        else:
          self.log(tag, "pruned")

  def subset(self, font):

    font.recalcBBoxes = self.options.recalc_bboxes

    self._prune_pre_subset(font)
    self._closure_glyphs(font)
    self._subset_glyphs(font)
    self._prune_post_subset(font)


class Logger(object):

  def __init__(self, verbose=False, xml=False, timing=False):
    self.verbose = verbose
    self.xml = xml
    self.timing = timing
    self.last_time = self.start_time = time.time()

  def parse_opts(self, argv):
    argv = argv[:]
    for v in ['verbose', 'xml', 'timing']:
      if "--"+v in argv:
        setattr(self, v, True)
        argv.remove("--"+v)
    return argv

  def __call__(self, *things):
    if not self.verbose:
      return
    print ' '.join(str(x) for x in things)

  def lapse(self, *things):
    if not self.timing:
      return
    new_time = time.time()
    print "Took %0.3fs to %s" %(new_time - self.last_time,
                                 ' '.join(str(x) for x in things))
    self.last_time = new_time

  def glyphs(self, glyphs, font=None):
    self("Names: ", sorted(glyphs))
    if font:
      reverseGlyphMap = font.getReverseGlyphMap()
      self("Gids : ", sorted(reverseGlyphMap[g] for g in glyphs))

  def font(self, font, file=sys.stdout):
    if not self.xml:
      return
    import xmlWriter
    writer = xmlWriter.XMLWriter(file)
    font.disassembleInstructions = False  # Work around ttx bug
    for tag in font.keys():
      writer.begintag(tag)
      writer.newline()
      font[tag].toXML(writer, font)
      writer.endtag(tag)
      writer.newline()


def load_font(fontfile, dont_load_glyph_names=False):

  # TODO(behdad) Option for ignoreDecompileErrors?

  font = fontTools.ttx.TTFont(fontfile)

  # Hack:
  #
  # If we don't need glyph names, change 'post' class to not try to
  # load them.  It avoid lots of headache with broken fonts as well
  # as loading time.
  #
  # Ideally ttLib should provide a way to ask it to skip loading
  # glyph names.  But it currently doesn't provide such a thing.
  #
  if dont_load_glyph_names:
    post = fontTools.ttLib.getTableClass('post')
    saved = post.decode_format_2_0
    post.decode_format_2_0 = post.decode_format_3_0
    f = font['post']
    if f.formatType == 2.0:
      f.formatType = 3.0
    post.decode_format_2_0 = saved

  return font


# Cleanup module space
l = locals()
for k,v in l.items():
  if v == None:
    del l[k]
del k, v, l


def main(args=None):

  if args == None: args = sys.argv
  arg0, args = args[0], args[1:]

  log = Logger()
  args = log.parse_opts(args)

  options = Options()
  args = options.parse_opts(args, ignore_unknown=['text'])

  if len(args) < 2:
    print >>sys.stderr, "usage: %s font-file glyph..." % arg0
    sys.exit(1)

  fontfile = args[0]
  args = args[1:]

  dont_load_glyph_names =(not options.glyph_names and
         all(any(g.startswith(p)
             for p in ['gid', 'glyph', 'uni', 'U+'])
              for g in args))

  font = load_font(fontfile, dont_load_glyph_names=dont_load_glyph_names)
  subsetter = Subsetter(options=options, log=log)
  log.lapse("load font")

  names = font.getGlyphNames()
  log.lapse("loading glyph names")

  glyphs = []
  unicodes = []
  text = ""
  for g in args:
    if g in names:
      glyphs.append(g)
      continue
    if g.startswith('--text='):
      text += g[7:]
      continue
    if g.startswith('uni') or g.startswith('U+'):
      if g.startswith('uni') and len(g) > 3:
        g = g[3:]
      elif g.startswith('U+') and len(g) > 2:
        g = g[2:]
      u = int(g, 16)
      unicodes.append(u)
      continue
    if g.startswith('gid') or g.startswith('glyph'):
      if g.startswith('gid') and len(g) > 3:
        g = g[3:]
      elif g.startswith('glyph') and len(g) > 5:
        g = g[5:]
      try:
        glyphs.append(font.getGlyphName(int(g), requireReal=1))
      except ValueError:
        raise Exception("Invalid glyph identifier: %s" % g)
      continue
    raise Exception("Invalid glyph identifier: %s" % g)
  log.lapse("compile glyph list")
  log("Unicodes:", unicodes)
  log("Glyphs:", glyphs)

  subsetter.populate(glyphs=glyphs, unicodes=unicodes, text=text)
  subsetter.subset(font)

  outfile = fontfile + '.subset'

  font.save(outfile)
  log.lapse("compile and save font")

  log.last_time = log.start_time
  log.lapse("make one with everything(TOTAL TIME)")

  if log.verbose:
    import os
    log("Input  font: %d bytes" % os.path.getsize(fontfile))
    log("Subset font: %d bytes" % os.path.getsize(outfile))

  log.font(font)

  font.close()

if __name__ == '__main__':
  main()
