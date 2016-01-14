from __future__ import print_function, division, absolute_import
from fontTools import ttLib
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otBase import ValueRecord, valueRecordFormatDict

# GSUB

def buildSingleSubst(mapping):
	self = ot.SingleSubst()
	self.mapping = dict(mapping)
	return self

def buildMultipleSubst(mapping):
	self = ot.MultipleSubst()
	self.mapping = dict(mapping)
	return self

def buildAlternateSubst(mapping):
	self = ot.AlternateSubst()
	self.alternates = dict(mapping)
	return self

def getLigatureKey(components):
	"""Computes a key for ordering ligatures in a GSUB Type-4 lookup.

	When building the OpenType lookup, we need to make sure that
	the longest sequence of components is listed first, so we
	use the negative length as the primary key for sorting.
	To make buildLigatureSubst() deterministic, we use the
	component sequence as the secondary key.

	For example, this will sort (f,f,f) < (f,f,i) < (f,f) < (f,i) < (f,l).
	"""
	return (-len(components), components)

def buildLigatureSubst(mapping):
	self = ot.LigatureSubst()
	# The following single line can replace the rest of this function
	# with fontTools >= 3.1
	#self.ligatures = dict(mapping)
	self.ligatures = {}
	for components in sorted(mapping.keys(), key=getLigatureKey):
		ligature = ot.Ligature()
		ligature.Component = components[1:]
		ligature.CompCount = len(components)
		ligature.LigGlyph = mapping[components]
		firstGlyph = components[0]
		self.ligatures.setdefault(firstGlyph, []).append(ligature)
	return self
