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
	
	def compile(self, writer, otFont):
		writer.writeUShort(self.format)
		if self.format == 1:
			self.compileFormat1(writer, otFont)
		elif self.format == 2:
			self.compileFormat2(writer, otFont)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown SingleSub format: %d" % self.format
	
	def compileFormat1(self, writer, otFont):
		xxx
	
	def compileFormat2(self, writer, otFont):
		substitutions = self.substitutions
		coverage = otCommon.CoverageTable()
		glyphNames = substitutions.keys()
		glyphNames = coverage.setGlyphNames(glyphNames, otFont)
		
		writer.writeTable(coverage, otFont)
		writer.writeUShort(len(substitutions))
		
		for i in range(len(substitutions)):
			glyphName = glyphNames[i]
			output = substitutions[glyphName]
			writer.writeUShort(otFont.getGlyphID(output))
	
	def toXML(self, xmlWriter, otFont):
		substitutions = self.substitutions.items()
		substitutions.sort()
		for input, output in substitutions:
			xmlWriter.simpletag("Subst", [("in", input), ("out", output)])
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), otFont):
		raise NotImplementedError


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
			substitutions[glyphNames[i]] = sequence.getGlyphs()
	
	def compile(self, writer, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		import string
		items = self.substitutions.items()
		items.sort()
		for input, output in items:
			xmlWriter.simpletag("Subst", [("in", input), ("out", string.join(output, ","))])
			xmlWriter.newline()


class Sequence:
	
	def getGlyphs(self):
		return self.glyphs
	
	def decompile(self, reader, otFont):
		self.glyphs = []
		for i in range(reader.readUShort()):
			self.glyphs.append(otFont.getGlyphName(reader.readUShort()))
	
	def compile(self, writer, otFont):
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
		self.alternateSets = alternateSets = {}
		for i in range(alternateSetCount):
			set = reader.readTable(AlternateSet, otFont)
			alternateSets[glyphNames[i]] = set.getGlyphs()
	
	def compile(self, writer, otFont):
		writer.writeUShort(1)  # format = 1
		alternateSets = self.alternateSets
		alternateSetCount = len(alternateSets)
		glyphNames = alternateSets.keys()
		coverage = otCommon.CoverageTable()
		glyphNames = coverage.setGlyphNames(glyphNames, otFont)
		
		writer.writeTable(coverage, otFont)
		writer.writeUShort(alternateSetCount)
		
		for i in range(alternateSetCount):
			glyphName = glyphNames[i]
			set = AlternateSet()
			set.setGlyphs(alternateSets[glyphName])
			writer.writeTable(set, otFont)
	
	def toXML(self, xmlWriter, otFont):
		alternates = self.alternateSets.items()
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
	
	def getGlyphs(self):
		return self.glyphs
	
	def setGlyphs(self, glyphs):
		self.glyphs = glyphs
	
	def decompile(self, reader, otFont):
		glyphCount = reader.readUShort()
		glyphIDs = reader.readUShortArray(glyphCount)
		self.glyphs = map(otFont.getGlyphName, glyphIDs)
	
	def compile(self, writer, otFont):
		glyphs = self.glyphs
		writer.writeUShort(len(glyphs))
		glyphIDs = map(otFont.getGlyphID, glyphs)
		writer.writeUShortArray(glyphIDs)


class LigatureSubst:
	
	def decompile(self, reader, otFont):
		self.format = reader.readUShort()
		if self.format <> 1:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown LigatureSubst format: %d" % self.format
		coverage = reader.readTable(otCommon.CoverageTable, otFont)
		glyphNames = coverage.getGlyphNames()
		ligSetCount = reader.readUShort()
		self.ligatures = ligatures = []
		for i in range(ligSetCount):
			firstGlyph = glyphNames[i]
			ligSet = reader.readTable(LigatureSet, otFont)
			for components, ligatureGlyph in ligSet.getLigatures():
				ligatures.append((((firstGlyph,) + tuple(components)), ligatureGlyph))
	
	def compile(self, writer, otFont):
		lastGlyph = None
		sets = {}
		currentSet = None
		for input, output in self.ligatures:
			firstGlyph = input[0]
			if firstGlyph <> lastGlyph:
				assert not sets.has_key(firstGlyph)
				currentSet = LigatureSet()
				sets[firstGlyph] = currentSet
				lastGlyph = firstGlyph
			currentSet.appendLigature(input[1:], output)
		
		glyphNames = sets.keys()
		coverage = otCommon.CoverageTable()
		glyphNames = coverage.setGlyphNames(glyphNames, otFont)
		
		writer.writeUShort(self.format)
		writer.writeTable(coverage, otFont)
		writer.writeUShort(len(sets))
		
		for i in range(len(glyphNames)):
			set = sets[glyphNames[i]]
			writer.writeTable(set, otFont)
	
	def toXML(self, xmlWriter, otFont):
		import string
		for input, output in self.ligatures:
			xmlWriter.simpletag("Subst", [("in", string.join(input, ",")), ("out", output)])
			xmlWriter.newline()


class LigatureSet:
	
	def __init__(self):
		self.ligatures = []
	
	def getLigatures(self):
		return self.ligatures
	
	def appendLigature(self, components, ligatureGlyph):
		self.ligatures.append((components, ligatureGlyph))
	
	def decompile(self, reader, otFont):
		ligatureCount = reader.readUShort()
		self.ligatures = ligatures = []
		for i in range(ligatureCount):
			lig = reader.readTable(Ligature, otFont)
			ligatures.append(lig.get())
	
	def compile(self, writer, otFont):
		writer.writeUShort(len(self.ligatures))
		
		for components, output in self.ligatures:
			lig = Ligature()
			lig.set(components, output)
			writer.writeTable(lig, otFont)


class Ligature:
	
	def get(self):
		return self.components, self.ligatureGlyph
	
	def set(self, components, ligatureGlyph):
		self.components, self.ligatureGlyph = components, ligatureGlyph
	
	def decompile(self, reader, otFont):
		self.ligatureGlyph = otFont.getGlyphName(reader.readUShort())
		compCount = reader.readUShort()
		self.components = components = []
		for i in range(compCount-1):
			components.append(otFont.getGlyphName(reader.readUShort()))
	
	def compile(self, writer, otFont):
		ligGlyphID = otFont.getGlyphID(self.ligatureGlyph)
		writer.writeUShort(ligGlyphID)
		writer.writeUShort(len(self.components) + 1)
		for compo in self.components:
			writer.writeUShort(otFont.getGlyphID(compo))


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
	
	def compile(self, writer, otFont):
		xxx
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("NotImplemented")
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
		XXX
	
	def decompileFormat2(self, reader, otFont):
		XXX
	
	def decompileFormat3(self, reader, otFont):
		backtrackGlyphCount = reader.readUShort()
		backtrackCoverage = reader.readTableArray(backtrackGlyphCount, otCommon.CoverageTable, otFont)
		self.backtrack = otCommon.unpackCoverageArray(backtrackCoverage)
		
		inputGlyphCount = reader.readUShort()
		inputCoverage = reader.readTableArray(inputGlyphCount, otCommon.CoverageTable, otFont)
		self.input = otCommon.unpackCoverageArray(inputCoverage)
		
		lookaheadGlyphCount = reader.readUShort()
		lookaheadCoverage = reader.readTableArray(lookaheadGlyphCount, otCommon.CoverageTable, otFont)
		self.lookahead = otCommon.unpackCoverageArray(lookaheadCoverage)
		
		substCount = reader.readUShort()
		self.substitutions = reader.readTableArray(substCount, SubstLookupRecord, otFont)
	
	def compile(self, writer, otFont):
		writer.writeUShort(self.format)
		if self.format == 1:
			self.compileFormat1(writer, otFont)
		elif self.format == 2:
			self.compileFormat2(writer, otFont)
		elif self.format == 3:
			self.compileFormat3(writer, otFont)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError, "unknown ChainContextSubst format: %d" % self.format
	
	def compileFormat1(self, writer, otFont):
		XXX
	
	def compileFormat2(self, writer, otFont):
		XXX
	
	def compileFormat3(self, writer, otFont):
		writer.writeUShort(len(self.backtrack))
		backtrack = otCommon.buildCoverageArray(self.backtrack, otFont)
		writer.writeTableArray(backtrack, otFont)
		
		writer.writeUShort(len(self.input))
		input = otCommon.buildCoverageArray(self.input, otFont)
		writer.writeTableArray(input, otFont)
		
		writer.writeUShort(len(self.lookahead))
		lookahead = otCommon.buildCoverageArray(self.lookahead, otFont)
		writer.writeTableArray(lookahead, otFont)
		
		writer.writeUShort(len(self.substitutions))
		writer.writeTableArray(self.substitutions, otFont)
	
	def toXML(self, xmlWriter, otFont):
		xmlWriter.comment("NotImplemented")
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
	
	def compile(self, writer, otFont):
		writer.writeUShort(self.sequenceIndex)
		writer.writeUShort(self.lookupListIndex)

