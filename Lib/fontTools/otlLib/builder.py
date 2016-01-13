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

def buildLigatureSubst(mapping):
	self = ot.LigatureSubst()
	# The following single line can replace the rest of this function with fontTools >= 3.1
	#self.ligatures = dict(mapping)
	self.ligatures = {}
	for seq,ligGlyph in mapping.items():
		firstGlyph, otherComponents = seq[0], seq[1:]
		ligature = ot.Ligature()
		ligature.Component = otherComponents
		ligature.CompCount = len(ligature.Component) + 1
		ligature.LigGlyph = ligGlyph
		self.ligatures.setdefault(firstGlyph, []).append(ligature)
	return self
