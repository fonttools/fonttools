"""fontTools.ttLib.tables.otTables -- A collection of classes representing the various
OpenType subtables.

Most are constructed upon import from data in otData.py, all are populated with
converter objects from otConverters.py.
"""

from otBase import BaseTable, FormatSwitchingBaseTable


class LookupOrder(BaseTable):
	"""Dummy class; this table isn't defined, but is used, and is always NULL."""


class FeatureParams(BaseTable):
	"""Dummy class; this table isn't defined, but is used, and is always NULL."""
	# XXX The above is no longer true; the 'size' feature uses FeatureParams now.


class Coverage(FormatSwitchingBaseTable):
	
	# manual implementation to get rid of glyphID dependencies
	
	def postRead(self, rawTable, font):
		if self.Format == 1:
			self.glyphs = rawTable["GlyphArray"]
		elif self.Format == 2:
			glyphs = self.glyphs = []
			ranges = rawTable["RangeRecord"]
			for r in ranges:
				assert r.StartCoverageIndex == len(glyphs), \
					(r.StartCoverageIndex, len(glyphs))
				start = r.Start
				end = r.End
				startID = font.getGlyphID(start)
				endID = font.getGlyphID(end)
				glyphs.append(start)
				for glyphID in range(startID + 1, endID):
					glyphs.append(font.getGlyphName(glyphID))
				if start != end:
					glyphs.append(end)
		else:
			assert 0, "unknown format: %s" % self.Format
	
	def preWrite(self, font):
		format = 1
		rawTable = {"GlyphArray": self.glyphs}
		if self.glyphs:
			# find out whether Format 2 is more compact or not
			glyphIDs = []
			for glyphName in self.glyphs:
				glyphIDs.append(font.getGlyphID(glyphName))
			
			last = glyphIDs[0]
			ranges = [[last]]
			for glyphID in glyphIDs[1:]:
				if glyphID != last + 1:
					ranges[-1].append(last)
					ranges.append([glyphID])
				last = glyphID
			ranges[-1].append(last)
			
			if len(ranges) * 3 < len(self.glyphs):  # 3 words vs. 1 word
				# Format 2 is more compact
				index = 0
				for i in range(len(ranges)):
					start, end = ranges[i]
					r = RangeRecord()
					r.Start = font.getGlyphName(start)
					r.End = font.getGlyphName(end)
					r.StartCoverageIndex = index
					ranges[i] = r
					index = index + end - start + 1
				format = 2
				rawTable = {"RangeRecord": ranges}
			#else:
			#	fallthrough; Format 1 is more compact
		self.Format = format
		return rawTable
	
	def toXML2(self, xmlWriter, font):
		for glyphName in self.glyphs:
			xmlWriter.simpletag("Glyph", value=glyphName)
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), font):
		glyphs = getattr(self, "glyphs", None)
		if glyphs is None:
			glyphs = []
			self.glyphs = glyphs
		glyphs.append(attrs["value"])


class SingleSubst(FormatSwitchingBaseTable):

	def postRead(self, rawTable, font):
		mapping = {}
		input = rawTable["Coverage"].glyphs
		if self.Format == 1:
			delta = rawTable["DeltaGlyphID"]
			for inGlyph in input:
				glyphID = font.getGlyphID(inGlyph)
				mapping[inGlyph] = font.getGlyphName(glyphID + delta)
		elif self.Format == 2:
			assert len(input) == rawTable["GlyphCount"], \
					"invalid SingleSubstFormat2 table"
			subst = rawTable["Substitute"]
			for i in range(len(input)):
				mapping[input[i]] = subst[i]
		else:
			assert 0, "unknown format: %s" % self.Format
		self.mapping = mapping
	
	def preWrite(self, font):
		items = self.mapping.items()
		for i in range(len(items)):
			inGlyph, outGlyph = items[i]
			items[i] = font.getGlyphID(inGlyph), font.getGlyphID(outGlyph), \
					inGlyph, outGlyph
		items.sort()
		
		format = 2
		delta = None
		for inID, outID, inGlyph, outGlyph in items:
			if delta is None:
				delta = outID - inID
			else:
				if delta != outID - inID:
					break
		else:
			format = 1
		
		rawTable = {}
		self.Format = format
		cov = Coverage()
		cov.glyphs = input = []
		subst = []
		for inID, outID, inGlyph, outGlyph in items:
			input.append(inGlyph)
			subst.append(outGlyph)
		rawTable["Coverage"] = cov
		if format == 1:
			assert delta is not None
			rawTable["DeltaGlyphID"] = delta
		else:
			rawTable["Substitute"] = subst
		return rawTable
	
	def toXML2(self, xmlWriter, font):
		items = self.mapping.items()
		items.sort()
		for inGlyph, outGlyph in items:
			xmlWriter.simpletag("Substitution",
					[("in", inGlyph), ("out", outGlyph)])
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), font):
		mapping = getattr(self, "mapping", None)
		if mapping is None:
			mapping = {}
			self.mapping = mapping
		mapping[attrs["in"]] = attrs["out"]


class ClassDef(FormatSwitchingBaseTable):
	
	def postRead(self, rawTable, font):
		classDefs = {}
		if self.Format == 1:
			start = rawTable["StartGlyph"]
			glyphID = font.getGlyphID(start)
			for cls in rawTable["ClassValueArray"]:
				classDefs[cls] = font.getGlyphName(glyphID)
				glyphID = glyphID + 1
		elif self.Format == 2:
			records = rawTable["ClassRangeRecord"]
			for rec in records:
				start = rec.Start
				end = rec.End
				cls = rec.Class
				classDefs[start] = cls
				for glyphID in range(font.getGlyphID(start) + 1,
						font.getGlyphID(end)):
					classDefs[font.getGlyphName(glyphID)] = cls
				classDefs[end] = cls
		else:
			assert 0, "unknown format: %s" % self.Format
		self.classDefs = classDefs
	
	def preWrite(self, font):
		items = self.classDefs.items()
		for i in range(len(items)):
			glyphName, cls = items[i]
			items[i] = font.getGlyphID(glyphName), glyphName, cls
		items.sort()
		last, lastName, lastCls = items[0]
		rec = ClassRangeRecord()
		rec.Start = lastName
		rec.Class = lastCls
		ranges = [rec]
		for glyphID, glyphName, cls in items[1:]:
			if glyphID != last + 1 or cls != lastCls:
				rec.End = lastName
				rec = ClassRangeRecord()
				rec.Start = glyphName
				rec.Class = cls
				ranges.append(rec)
			last = glyphID
			lastName = glyphName
			lastCls = cls
		rec.End = lastName
		self.Format = 2  # currently no support for Format 1
		return {"ClassRangeRecord": ranges}
	
	def toXML2(self, xmlWriter, font):
		items = self.classDefs.items()
		items.sort()
		for glyphName, cls in items:
			xmlWriter.simpletag("ClassDef", [("glyph", glyphName), ("class", cls)])
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), font):
		classDefs = getattr(self, "classDefs", None)
		if classDefs is None:
			classDefs = {}
			self.classDefs = classDefs
		classDefs[attrs["glyph"]] = int(attrs["class"])


#
# For each subtable format there is a class. However, we don't really distinguish
# between "field name" and "format name": often these are the same. Yet there's
# a whole bunch of fields with different names. The following dict is a mapping
# from "format name" to "field name". _buildClasses() uses this to create a
# subclass for each alternate field name.
#
_equivalents = {
	'MarkArray': ("Mark1Array",),
	'LangSys': ('DefaultLangSys',),
	'Coverage': ('MarkCoverage', 'BaseCoverage', 'LigatureCoverage', 'Mark1Coverage',
			'Mark2Coverage', 'BacktrackCoverage', 'InputCoverage',
			'LookaheadCoverage'),
	'ClassDef': ('ClassDef1', 'ClassDef2', 'BacktrackClassDef', 'InputClassDef',
			'LookaheadClassDef', 'GlyphClassDef', 'MarkAttachClassDef'),
	'Anchor': ('EntryAnchor', 'ExitAnchor', 'BaseAnchor', 'LigatureAnchor',
			'Mark2Anchor', 'MarkAnchor'),
	'Device': ('XPlaDevice', 'YPlaDevice', 'XAdvDevice', 'YAdvDevice',
			'XDeviceTable', 'YDeviceTable', 'DeviceTable'),
	'Axis': ('HorizAxis', 'VertAxis',),
	'MinMax': ('DefaultMinMax',),
	'BaseCoord': ('MinCoord', 'MaxCoord',),
	'JstfLangSys': ('DefJstfLangSys',),
	'JstfGSUBModList': ('ShrinkageEnableGSUB', 'ShrinkageDisableGSUB', 'ExtensionEnableGSUB',
			'ExtensionDisableGSUB',),
	'JstfGPOSModList': ('ShrinkageEnableGPOS', 'ShrinkageDisableGPOS', 'ExtensionEnableGPOS',
			'ExtensionDisableGPOS',),
	'JstfMax': ('ShrinkageJstfMax', 'ExtensionJstfMax',),
}


def _buildClasses():
	import new, re
	from otData import otData
	
	formatPat = re.compile("([A-Za-z0-9]+)Format(\d+)$")
	namespace = globals()
	
	# populate module with classes
	for name, table in otData:
		baseClass = BaseTable
		m = formatPat.match(name)
		if m:
			# XxxFormatN subtable, we only add the "base" table
			name = m.group(1)
			baseClass = FormatSwitchingBaseTable
		if not namespace.has_key(name):
			# the class doesn't exist yet, so the base implementation is used.
			cls = new.classobj(name, (baseClass,), {})
			namespace[name] = cls
	
	for base, alts in _equivalents.items():
		base = namespace[base]
		for alt in alts:
			namespace[alt] = new.classobj(alt, (base,), {})
	
	global lookupTypes
	lookupTypes = {
		'GSUB': {
			1: SingleSubst,
			2: MultipleSubst,
			3: AlternateSubst,
			4: LigatureSubst,
			5: ContextSubst,
			6: ChainContextSubst,
			7: ExtensionSubst,
		},
		'GPOS': {
			1: SinglePos,
			2: PairPos,
			3: CursivePos,
			4: MarkBasePos,
			5: MarkLigPos,
			6: MarkMarkPos,
			7: ContextPos,
			8: ChainContextPos,
			9: ExtensionPos,
		},
	}
	lookupTypes['JSTF'] = lookupTypes['GPOS']  # JSTF contains GPOS
	for lookupEnum in lookupTypes.values():
		for enum, cls in lookupEnum.items():
			cls.LookupType = enum
	
	# add converters to classes
	from otConverters import buildConverters
	for name, table in otData:
		m = formatPat.match(name)
		if m:
			# XxxFormatN subtable, add converter to "base" table
			name, format = m.groups()
			format = int(format)
			cls = namespace[name]
			if not hasattr(cls, "converters"):
				cls.converters = {}
				cls.convertersByName = {}
			converters, convertersByName = buildConverters(table[1:], namespace)
			cls.converters[format] = converters
			cls.convertersByName[format] = convertersByName
		else:
			cls = namespace[name]
			cls.converters, cls.convertersByName = buildConverters(table, namespace)


_buildClasses()
