import otCommon


class table_G_S_U_B_(otCommon.base_GPOS_GSUB):
	
	def getLookupTypeClass(self, lookupType):
		return lookupTypeClasses[lookupType]


class SingleSubst:
	
	def decompile(self, reader, otFont):
		self.format = reader.readUShort()
		if self.format == 1:
			self.decompileFormat1(reader, otFont)
		elif self.format == 2:
			self.decompileFormat2(reader, otFont)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown SingleSub format: %d" % self.format
	
	def decompileFormat1(self, reader, otFont):
		coverage = reader.readTable(otCommon.CoverageTable, otFont)
		glyphIDs = coverage.getGlyphIDs()
		glyphNames = coverage.getGlyphNames()
		self.substitutions = substitutions = {}
		deltaGlyphID = reader.readShort()
		for i in range(len(glyphIDs)):
			input = glyphNames[i]
			output = otFont.getGlyphName(glyphIDs[i] + deltaGlyphID)
			substitutions[input] = output
	
	def decompileFormat2(self, reader, otFont):
		coverage = reader.readTable(otCommon.CoverageTable, otFont)
		glyphNames = coverage.getGlyphNames()
		glyphCount = reader.readUShort()
		self.substitutions = substitutions = {}
		for i in range(glyphCount):
			glyphID = reader.readUShort()
			output = otFont.getGlyphName(glyphID)
			input = glyphNames[i]
			substitutions[input] = output
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		substitutions = self.substitutions.items()
		substitutions.sort()
		for input, output in substitutions:
			xmlWriter.simpletag("Subst", [("in", input), ("out", output)])
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), otFont):
		xxx


class MultipleSubst:
	
	def decompile(self, reader, otFont):
		format = reader.readUShort()
		if format <> 1:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown MultipleSubst format: %d" % format
		glyphNames = reader.readTable(otCommon.CoverageTable, otFont).getGlyphNames()
		sequenceCount = reader.readUShort()
		self.substitutions = substitutions = {}
		for i in range(sequenceCount):
			sequence = reader.readTable(Sequence, otFont)
			substitutions[glyphNames[i]] = sequence.glyphs
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		import string
		items = self.substitutions.items()
		items.sort()
		for input, output in items:
			xmlWriter.simpletag("Subst", [("in", input), ("out", string.join(output, ","))])
			xmlWriter.newline()


class Sequence:
	
	def decompile(self, reader, otFont):
		self.glyphs = []
		for i in range(reader.readUShort()):
			self.glyphs.append(otFont.getGlyphName(reader.readUShort()))
	
	def compile(self, otFont):
		xxx


class AlternateSubst:
	
	def decompile(self, reader, otFont):
		format = reader.readUShort()
		if format <> 1:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown AlternateSubst format: %d" % format
		coverage = reader.readTable(otCommon.CoverageTable, otFont)
		glyphNames = coverage.getGlyphNames()
		alternateSetCount = reader.readUShort()
		self.alternateSet = alternateSet = {}
		for i in range(alternateSetCount):
			set = reader.readTable(AlternateSet, otFont)
			alternateSet[glyphNames[i]] = set.glyphs
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		alternates = self.alternateSet.items()
		alternates.sort()
		for input, substList in alternates:
			xmlWriter.begintag("AlternateSet", [("in", input)])
			xmlWriter.newline()
			for output in substList:
				xmlWriter.simpletag("Subst", out=output)
				xmlWriter.newline()
			xmlWriter.endtag("AlternateSet")
			xmlWriter.newline()


class AlternateSet:
	
	def decompile(self, reader, otFont):
		glyphCount = reader.readUShort()
		glyphIDs = reader.readUShortArray(glyphCount)
		self.glyphs = map(otFont.getGlyphName, glyphIDs)
	
	def compile(self, otFont):
		xxx


class LigatureSubst:
	
	def decompile(self, reader, otFont):
		format = reader.readUShort()
		if format <> 1:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown LigatureSubst format: %d" % format
		coverage = reader.readTable(otCommon.CoverageTable, otFont)
		glyphNames = coverage.getGlyphNames()
		ligSetCount = reader.readUShort()
		self.ligatures = ligatures = []
		for i in range(ligSetCount):
			firstGlyph = glyphNames[i]
			ligSet = reader.readTable(LigatureSet, otFont)
			for ligatureGlyph, components in ligSet.ligatures:
				ligatures.append(((firstGlyph,) + tuple(components)), ligatureGlyph)
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		import string
		for input, output in self.ligatures:
			xmlWriter.simpletag("Subst", [("in", string.join(input, ",")), ("out", output)])
			xmlWriter.newline()


class LigatureSet:
	
	def decompile(self, reader, otFont):
		ligatureCount = reader.readUShort()
		self.ligatures = ligatures = []
		for i in range(ligatureCount):
			lig = reader.readTable(Ligature, otFont)
			ligatures.append((lig.ligatureGlyph, lig.components))
	
	def compile(self, otFont):
		xxx


class Ligature:
	
	def decompile(self, reader, otFont):
		self.ligatureGlyph = otFont.getGlyphName(reader.readUShort())
		compCount = reader.readUShort()
		self.components = components = []
		for i in range(compCount-1):
			components.append(otFont.getGlyphName(reader.readUShort()))
	
	def compile(self, otFont):
		xxx


class ContextSubst:
	
	def decompile(self, reader, otFont):
		format = reader.readUShort()
		if format == 1:
			self.decompileFormat1(reader, otFont)
		elif format == 2:
			self.decompileFormat2(reader, otFont)
		elif format == 3:
			self.decompileFormat3(reader, otFont)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown ContextSubst format: %d" % format
	
	def decompileFormat1(self, reader, otFont):
		xxx
	
	def decompileFormat2(self, reader, otFont):
		xxx
	
	def decompileFormat3(self, reader, otFont):
		glyphCount = reader.readUShort()
		substCount = reader.readUShort()
		coverage = []
		for i in range(glyphCount):
			coverage.append(reader.readTable(otCommon.CoverageTable, otFont))
		self.substitutions = substitutions = []
		for i in range(substCount):
			lookupRecord = SubstLookupRecord()
			lookupRecord.decompile(reader, otFont)
			substitutions.append((coverage[i].getGlyphNames(), lookupRecord))
	
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("XXX")
		xmlWriter.newline()


class ChainContextSubst:
	
	def decompile(self, reader, otFont):
		self.format = reader.readUShort()
		if self.format == 1:
			self.decompileFormat1(reader, otFont)
		elif self.format == 2:
			self.decompileFormat2(reader, otFont)
		elif self.format == 3:
			self.decompileFormat3(reader, otFont)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown ChainContextSubst format: %d" % self.format
	
	def decompileFormat1(self, reader, otFont):
		pass
	
	def decompileFormat2(self, reader, otFont):
		pass
	
	def decompileFormat3(self, reader, otFont):
		pass
		
	def compile(self, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("XXX")
		xmlWriter.newline()


lookupTypeClasses = {
	1: SingleSubst,
	2: MultipleSubst,
	3: AlternateSubst,
	4: LigatureSubst,
	5: ContextSubst,
	6: ChainContextSubst,
}


#
# Shared classes
#

class SubstLookupRecord:
	
	def decompile(self, reader, otFont):
		self.sequenceIndex = reader.readUShort()
		self.lookupListIndex = reader.readUShort()
	
	def compile(self, otFont):
		xxx

