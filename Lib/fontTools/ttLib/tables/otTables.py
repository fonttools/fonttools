"""fontTools.ttLib.tables.otTables -- A collection of classes representing the various
OpenType subtables.

Most are constructed upon import from data in otData.py, all are populated with
converter objects from otConverters.py.
"""
import operator
from otBase import BaseTable, FormatSwitchingBaseTable
from types import TupleType


class LookupOrder(BaseTable):
	"""Dummy class; this table isn't defined, but is used, and is always NULL."""


class FeatureParams(BaseTable):
	"""This class has been used by Adobe, but but this one implementation was done wrong.
	No other use has been made, becuase there is no way to know how to interpret
	the data at the offset.. For now, if we see one, just skip the data on
	decompiling and dumping to XML. """
	# XXX The above is no longer true; the 'size' feature uses FeatureParams now.
	def __init__(self):
		BaseTable.__init__(self)
		self.converters = []

class Coverage(FormatSwitchingBaseTable):
	
	# manual implementation to get rid of glyphID dependencies
	
	def postRead(self, rawTable, font):
		if self.Format == 1:
			self.glyphs = rawTable["GlyphArray"]
		elif self.Format == 2:
			glyphs = self.glyphs = []
			ranges = rawTable["RangeRecord"]
			getGlyphName = font.getGlyphName
			for r in ranges:
				assert r.StartCoverageIndex == len(glyphs), \
					(r.StartCoverageIndex, len(glyphs))
				start = r.Start
				end = r.End
				startID = font.getGlyphID(start)
				endID = font.getGlyphID(end)
				glyphs.append(start)
				rangeList = [getGlyphName(glyphID) for glyphID in range(startID + 1, endID) ]
				glyphs += rangeList
				if start != end:
					glyphs.append(end)
		else:
			assert 0, "unknown format: %s" % self.Format
	
	def preWrite(self, font):
		glyphs = getattr(self, "glyphs", None)
		if glyphs is None:
			glyphs = self.glyphs = []
		format = 1
		rawTable = {"GlyphArray": glyphs}
		getGlyphID = font.getGlyphID
		if glyphs:
			# find out whether Format 2 is more compact or not
			glyphIDs = [getGlyphID(glyphName) for glyphName in glyphs ]
			
			last = glyphIDs[0]
			ranges = [[last]]
			for glyphID in glyphIDs[1:]:
				if glyphID != last + 1:
					ranges[-1].append(last)
					ranges.append([glyphID])
				last = glyphID
			ranges[-1].append(last)
			
			if len(ranges) * 3 < len(glyphs):  # 3 words vs. 1 word
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
		for glyphName in getattr(self, "glyphs", []):
			xmlWriter.simpletag("Glyph", value=glyphName)
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), font):
		glyphs = getattr(self, "glyphs", None)
		if glyphs is None:
			glyphs = []
			self.glyphs = glyphs
		glyphs.append(attrs["value"])


class LookupList(BaseTable):
	def preCompile(self):
		""" This function is used to optimize writing out extension subtables. This is useful
		when a font has been read in, modified, and we are now writing out a new version. If the
		the extension subtables have not been touched (proof being that they have not been decompiled)
		then we can write them out using the original data, and do not have to recompile them. This can save
		20-30% of the compile time for fonts with large extension tables, such as Japanese Pro fonts."""

		if hasattr(self, 'LookupCount'): #not defined if loading from xml
			lookupCount = self.LookupCount
		else:
			return # The optimization of not recompiling extension lookup subtables is not possible
					# when reading from XML.
 
		liRange = range(lookupCount)
		extTables = []
		for li in liRange:
			lookup = self.Lookup[li]
			if hasattr(lookup, 'SubTableCount'): #not defined if loading from xml
				subtableCount = lookup.SubTableCount
			else:
				subtableCount = len(lookup.SubTable)
			siRange = range(subtableCount)
			for si in siRange:
				subtable = lookup.SubTable[si]
				if hasattr(subtable, 'ExtSubTable'):
					extTable = subtable.ExtSubTable
					extTables.append([extTable.start, extTable] )

		# Since offsets in one subtable can and do point forward into later
		# subtables, we can afford to simply copy data only for the last subtables 
		# which were not decompiled. So we start figuring out the
		# data segments starting with the last subtTable, and work our way towards
		# the first subtable, and then quit as soon as we see a subtable that was decompiled.
		if  extTables:
			extTables.sort()
			extTables.reverse()
			lastTable = extTables[0][1]
			if lastTable.compileStatus == 1:
				lastTable.end = len(lastTable.reader.data)
				lastTable.compileStatus = 3
				for i in range(1, len(extTables)):
					extTable = extTables[i][1]
					if extTable.compileStatus != 1:
						break
					extTable.end = lastTable.start
					extTable.compileStatus = 3
					lastTable = extTable

def doModulo(value):
	if value < 0:
		return value + 65536
	return value

class SingleSubst(FormatSwitchingBaseTable):

	def postRead(self, rawTable, font):
		mapping = {}
		input = _getGlyphsFromCoverageTable(rawTable["Coverage"])
		lenMapping = len(input)
		if self.Format == 1:
			delta = rawTable["DeltaGlyphID"]
			inputGIDS =  [ font.getGlyphID(name) for name in input ]
			inputGIDS = map(doModulo, inputGIDS) 
			outGIDS = [ glyphID + delta for glyphID in inputGIDS ]
			outGIDS = map(doModulo, outGIDS) 
			outNames = [ font.getGlyphName(glyphID) for glyphID in outGIDS ]
			map(operator.setitem, [mapping]*lenMapping, input, outNames)
		elif self.Format == 2:
			assert len(input) == rawTable["GlyphCount"], \
					"invalid SingleSubstFormat2 table"
			subst = rawTable["Substitute"]
			map(operator.setitem, [mapping]*lenMapping, input, subst)
		else:
			assert 0, "unknown format: %s" % self.Format
		self.mapping = mapping
	
	def preWrite(self, font):
		mapping = getattr(self, "mapping", None)
		if mapping is None:
			mapping = self.mapping = {}
		items = mapping.items()
		getGlyphID = font.getGlyphID
		gidItems = [(getGlyphID(item[0]), getGlyphID(item[1])) for item in items]
		sortableItems = zip(gidItems, items)
		sortableItems.sort()

		# figure out format
		format = 2
		delta = None
		for inID, outID in gidItems:
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
		input =  [ item [1][0] for item in sortableItems]
		subst =  [ item [1][1] for item in sortableItems]
		cov.glyphs = input
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
		getGlyphName = font.getGlyphName

		if self.Format == 1:
			start = rawTable["StartGlyph"]
			classList = rawTable["ClassValueArray"]
			lenList = len(classList)
			glyphID = font.getGlyphID(start)
			gidList = range(glyphID, glyphID + len(classList))
			keyList = [getGlyphName(glyphID) for glyphID in gidList]

			map(operator.setitem, [classDefs]*lenList, keyList, classList)

		elif self.Format == 2:
			records = rawTable["ClassRangeRecord"]
			for rec in records:
				start = rec.Start
				end = rec.End
				cls = rec.Class
				classDefs[start] = cls
				glyphIDs = range(font.getGlyphID(start) + 1, font.getGlyphID(end))
				lenList = len(glyphIDs)
				keyList = [getGlyphName(glyphID) for glyphID in glyphIDs]
				map(operator.setitem,  [classDefs]*lenList, keyList, [cls]*lenList)
				classDefs[end] = cls
		else:
			assert 0, "unknown format: %s" % self.Format
		self.classDefs = classDefs
	
	def preWrite(self, font):
		classDefs = getattr(self, "classDefs", None)
		if classDefs is None:
			classDefs = self.classDefs = {}
		items = classDefs.items()
		getGlyphID = font.getGlyphID
		for i in range(len(items)):
			glyphName, cls = items[i]
			items[i] = getGlyphID(glyphName), glyphName, cls
		items.sort()
		if items:
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
		else:
			ranges = []
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


class AlternateSubst(FormatSwitchingBaseTable):
	
	def postRead(self, rawTable, font):
		alternates = {}
		if self.Format == 1:
			input = _getGlyphsFromCoverageTable(rawTable["Coverage"])
			alts = rawTable["AlternateSet"]
			if len(input) != len(alts):
				assert len(input) == len(alts)
			for i in range(len(input)):
				alternates[input[i]] = alts[i].Alternate
		else:
			assert 0, "unknown format: %s" % self.Format
		self.alternates = alternates
	
	def preWrite(self, font):
		self.Format = 1
		alternates = getattr(self, "alternates", None)
		if alternates is None:
			alternates = self.alternates = {}
		items = alternates.items()
		for i in range(len(items)):
			glyphName, set = items[i]
			items[i] = font.getGlyphID(glyphName), glyphName, set
		items.sort()
		cov = Coverage()
		cov.glyphs = [ item[1] for item in items]
		alternates = []
		setList = [ item[-1] for item in items]
		for  set in setList:
			alts = AlternateSet()
			alts.Alternate = set
			alternates.append(alts)
		# a special case to deal with the fact that several hundred Adobe Japan1-5
		# CJK fonts will overflow an offset if the coverage table isn't pushed to the end.
		# Also useful in that when splitting a sub-table because of an offset overflow
		# I don't need to calculate the change in the subtable offset due to the change in the coverage table size.
		# Allows packing more rules in subtable.
		self.sortCoverageLast = 1 
		return {"Coverage": cov, "AlternateSet": alternates}
	
	def toXML2(self, xmlWriter, font):
		items = self.alternates.items()
		items.sort()
		for glyphName, alternates in items:
			xmlWriter.begintag("AlternateSet", glyph=glyphName)
			xmlWriter.newline()
			for alt in alternates:
				xmlWriter.simpletag("Alternate", glyph=alt)
				xmlWriter.newline()
			xmlWriter.endtag("AlternateSet")
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), font):
		alternates = getattr(self, "alternates", None)
		if alternates is None:
			alternates = {}
			self.alternates = alternates
		glyphName = attrs["glyph"]
		set = []
		alternates[glyphName] = set
		for element in content:
			if type(element) != TupleType:
				continue
			name, attrs, content = element
			set.append(attrs["glyph"])


class LigatureSubst(FormatSwitchingBaseTable):
	
	def postRead(self, rawTable, font):
		ligatures = {}
		if self.Format == 1:
			input = rawTable["Coverage"].glyphs
			ligSets = rawTable["LigatureSet"]
			assert len(input) == len(ligSets)
			for i in range(len(input)):
				ligatures[input[i]] = ligSets[i].Ligature
		else:
			assert 0, "unknown format: %s" % self.Format
		self.ligatures = ligatures
	
	def preWrite(self, font):
		ligatures = getattr(self, "ligatures", None)
		if ligatures is None:
			ligatures = self.ligatures = {}
		items = ligatures.items()
		for i in range(len(items)):
			glyphName, set = items[i]
			items[i] = font.getGlyphID(glyphName), glyphName, set
		items.sort()
		cov = Coverage()
		cov.glyphs = [ item[1] for item in items]

		ligSets = []
		setList = [ item[-1] for item in items ]
		for set in setList:
			ligSet = LigatureSet()
			ligs = ligSet.Ligature = []
			for lig in set:
				ligs.append(lig)
			ligSets.append(ligSet)
		# Useful in that when splitting a sub-table because of an offset overflow
		# I don't need to calculate the change in subtabl offset due to the coverage table size.
		# Allows packing more rules in subtable.
		self.sortCoverageLast = 1 
		return {"Coverage": cov, "LigatureSet": ligSets}
	
	def toXML2(self, xmlWriter, font):
		items = self.ligatures.items()
		items.sort()
		for glyphName, ligSets in items:
			xmlWriter.begintag("LigatureSet", glyph=glyphName)
			xmlWriter.newline()
			for lig in ligSets:
				xmlWriter.simpletag("Ligature", glyph=lig.LigGlyph,
					components=",".join(lig.Component))
				xmlWriter.newline()
			xmlWriter.endtag("LigatureSet")
			xmlWriter.newline()
	
	def fromXML(self, (name, attrs, content), font):
		ligatures = getattr(self, "ligatures", None)
		if ligatures is None:
			ligatures = {}
			self.ligatures = ligatures
		glyphName = attrs["glyph"]
		ligs = []
		ligatures[glyphName] = ligs
		for element in content:
			if type(element) != TupleType:
				continue
			name, attrs, content = element
			lig = Ligature()
			lig.LigGlyph = attrs["glyph"]
			lig.Component = attrs["components"].split(",")
			ligs.append(lig)


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
			'LookAheadCoverage'),
	'ClassDef': ('ClassDef1', 'ClassDef2', 'BacktrackClassDef', 'InputClassDef',
			'LookAheadClassDef', 'GlyphClassDef', 'MarkAttachClassDef'),
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

#
# OverFlow logic, to automatically create ExtensionLookups
# XXX This should probably move to otBase.py
#

def fixLookupOverFlows(ttf, overflowRecord):
	""" Either the offset from the LookupList to a lookup overflowed, or
	an offset from a lookup to a subtable overflowed. 
	The table layout is:
	GPSO/GUSB
		Script List
		Feature List
		LookUpList
			Lookup[0] and contents
				SubTable offset list
					SubTable[0] and contents
					...
					SubTable[n] and contents
			...
			Lookup[n] and contents
				SubTable offset list
					SubTable[0] and contents
					...
					SubTable[n] and contents
	If the offset to a lookup overflowed (SubTableIndex == None)
		we must promote the *previous*	lookup to an Extension type.
	If the offset from a lookup to subtable overflowed, then we must promote it 
		to an Extension Lookup type.
	"""
	ok = 0
	lookupIndex = overflowRecord.LookupListIndex
	if (overflowRecord.SubTableIndex == None):
		lookupIndex = lookupIndex - 1
	if lookupIndex < 0:
		return ok
	if overflowRecord.tableType == 'GSUB':
		extType = 7
	elif overflowRecord.tableType == 'GPOS':
		extType = 9

	lookups = ttf[overflowRecord.tableType].table.LookupList.Lookup
	lookup = lookups[lookupIndex]
	# If the previous lookup is an extType, look further back. Very unlikely, but possible.
	while lookup.LookupType == extType:
		lookupIndex = lookupIndex -1
		if lookupIndex < 0:
			return ok
		lookup = lookups[lookupIndex]
		
	for si in range(len(lookup.SubTable)):
		subTable = lookup.SubTable[si]
		extSubTableClass = lookupTypes[overflowRecord.tableType][extType]
		extSubTable = extSubTableClass()
		extSubTable.Format = 1
		extSubTable.ExtensionLookupType = lookup.LookupType
		extSubTable.ExtSubTable = subTable
		lookup.SubTable[si] = extSubTable
	lookup.LookupType = extType
	ok = 1
	return ok

def splitAlternateSubst(oldSubTable, newSubTable, overflowRecord):
	ok = 1
	newSubTable.Format = oldSubTable.Format
	if hasattr(oldSubTable, 'sortCoverageLast'):
		newSubTable.sortCoverageLast = oldSubTable.sortCoverageLast
	
	oldAlts = oldSubTable.alternates.items()
	oldAlts.sort()
	oldLen = len(oldAlts)

	if overflowRecord.itemName in [ 'Coverage', 'RangeRecord']:
		# Coverage table is written last. overflow is to or within the
		# the coverage table. We will just cut the subtable in half.
		newLen = int(oldLen/2)

	elif overflowRecord.itemName == 'AlternateSet':
		# We just need to back up by two items 
		# from the overflowed AlternateSet index to make sure the offset
		# to the Coverage table doesn't overflow.
		newLen  = overflowRecord.itemIndex - 1

	newSubTable.alternates = {}
	for i in range(newLen, oldLen):
		item = oldAlts[i]
		key = item[0]
		newSubTable.alternates[key] = item[1]
		del oldSubTable.alternates[key]


	return ok


def splitLigatureSubst(oldSubTable, newSubTable, overflowRecord):
	ok = 1
	newSubTable.Format = oldSubTable.Format
	oldLigs = oldSubTable.ligatures.items()
	oldLigs.sort()
	oldLen = len(oldLigs)

	if overflowRecord.itemName in [ 'Coverage', 'RangeRecord']:
		# Coverage table is written last. overflow is to or within the
		# the coverage table. We will just cut the subtable in half.
		newLen = int(oldLen/2)

	elif overflowRecord.itemName == 'LigatureSet':
		# We just need to back up by two items 
		# from the overflowed AlternateSet index to make sure the offset
		# to the Coverage table doesn't overflow.
		newLen  = overflowRecord.itemIndex - 1

	newSubTable.ligatures = {}
	for i in range(newLen, oldLen):
		item = oldLigs[i]
		key = item[0]
		newSubTable.ligatures[key] = item[1]
		del oldSubTable.ligatures[key]

	return ok


splitTable = {	'GSUB': {
#					1: splitSingleSubst,
#					2: splitMultipleSubst,
					3: splitAlternateSubst,
					4: splitLigatureSubst,
#					5: splitContextSubst,
#					6: splitChainContextSubst,
#					7: splitExtensionSubst,
#					8: splitReverseChainSingleSubst,
					},
				'GPOS': {
#					1: splitSinglePos,
#					2: splitPairPos,
#					3: splitCursivePos,
#					4: splitMarkBasePos,
#					5: splitMarkLigPos,
#					6: splitMarkMarkPos,
#					7: splitContextPos,
#					8: splitChainContextPos,
#					9: splitExtensionPos,
					}

			}

def fixSubTableOverFlows(ttf, overflowRecord):
	""" 
	An offset has overflowed within a sub-table. We need to divide this subtable into smaller parts.
	"""
	ok = 0
	table = ttf[overflowRecord.tableType].table
	lookup = table.LookupList.Lookup[overflowRecord.LookupListIndex]
	subIndex = overflowRecord.SubTableIndex
	subtable = lookup.SubTable[subIndex]

	if hasattr(subtable, 'ExtSubTable'):
		# We split the subtable of the Extension table, and add a new Extension table
		# to contain the new subtable.

		subTableType = subtable.ExtensionLookupType
		extSubTable = subtable
		subtable = extSubTable.ExtSubTable
		newExtSubTableClass = lookupTypes[overflowRecord.tableType][lookup.LookupType]
		newExtSubTable = newExtSubTableClass()
		newExtSubTable.Format = extSubTable.Format
		newExtSubTable.ExtensionLookupType = extSubTable.ExtensionLookupType
		lookup.SubTable.insert(subIndex + 1, newExtSubTable)

		newSubTableClass = lookupTypes[overflowRecord.tableType][subTableType]
		newSubTable = newSubTableClass()
		newExtSubTable.ExtSubTable = newSubTable
	else:
		subTableType = lookup.LookupType
		newSubTableClass = lookupTypes[overflowRecord.tableType][subTableType]
		newSubTable = newSubTableClass()
		lookup.SubTable.insert(subIndex + 1, newSubTable)

	if hasattr(lookup, 'SubTableCount'): # may not be defined yet.
		lookup.SubTableCount = lookup.SubTableCount + 1

	try:
		splitFunc = splitTable[overflowRecord.tableType][subTableType]
	except KeyError:
		return ok

	ok = splitFunc(subtable, newSubTable, overflowRecord)
	return ok

# End of OverFlow logic


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
			8: ReverseChainSingleSubst,
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


def _getGlyphsFromCoverageTable(coverage):
	if coverage is None:
		# empty coverage table
		return []
	else:
		return coverage.glyphs
