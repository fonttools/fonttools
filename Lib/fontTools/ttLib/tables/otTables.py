"""fontTools.ttLib.tables.otTables -- A collection of classes representing the various
OpenType subtables.

Most are constructed upon import from data in otData.py, all are populated with
converter objects from otConverters.py.
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from .otBase import BaseTable, FormatSwitchingBaseTable
import operator
import warnings


class LookupOrder(BaseTable):
	"""Dummy class; this table isn't defined, but is used, and is always NULL."""

class FeatureParams(BaseTable):

	def compile(self, writer, font):
		assert featureParamTypes.get(writer['FeatureTag']) == self.__class__, "Wrong FeatureParams type for feature '%s': %s" % (writer['FeatureTag'], self.__class__.__name__)
		BaseTable.compile(self, writer, font)

	def toXML(self, xmlWriter, font, attrs=None, name=None):
		BaseTable.toXML(self, xmlWriter, font, attrs, name=self.__class__.__name__)

class FeatureParamsSize(FeatureParams):
	pass

class FeatureParamsStylisticSet(FeatureParams):
	pass

class FeatureParamsCharacterVariants(FeatureParams):
	pass

class Coverage(FormatSwitchingBaseTable):
	
	# manual implementation to get rid of glyphID dependencies
	
	def postRead(self, rawTable, font):
		if self.Format == 1:
			# TODO only allow glyphs that are valid?
			self.glyphs = rawTable["GlyphArray"]
		elif self.Format == 2:
			glyphs = self.glyphs = []
			ranges = rawTable["RangeRecord"]
			glyphOrder = font.getGlyphOrder()
			# Some SIL fonts have coverage entries that don't have sorted
			# StartCoverageIndex.  If it is so, fixup and warn.  We undo
			# this when writing font out.
			sorted_ranges = sorted(ranges, key=lambda a: a.StartCoverageIndex)
			if ranges != sorted_ranges:
				warnings.warn("GSUB/GPOS Coverage is not sorted by glyph ids.")
				ranges = sorted_ranges
			del sorted_ranges
			for r in ranges:
				assert r.StartCoverageIndex == len(glyphs), \
					(r.StartCoverageIndex, len(glyphs))
				start = r.Start
				end = r.End
				try:
					startID = font.getGlyphID(start, requireReal=True)
				except KeyError:
					warnings.warn("Coverage table has start glyph ID out of range: %s." % start)
					continue
				try:
					endID = font.getGlyphID(end, requireReal=True) + 1
				except KeyError:
					# Apparently some tools use 65535 to "match all" the range
					if end != 'glyph65535':
						warnings.warn("Coverage table has end glyph ID out of range: %s." % end)
					# NOTE: We clobber out-of-range things here.  There are legit uses for those,
					# but none that we have seen in the wild.
					endID = len(glyphOrder)
				glyphs.extend(glyphOrder[glyphID] for glyphID in range(startID, endID))
		else:
			assert 0, "unknown format: %s" % self.Format
		del self.Format # Don't need this anymore
	
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
			brokenOrder = sorted(glyphIDs) != glyphIDs
			
			last = glyphIDs[0]
			ranges = [[last]]
			for glyphID in glyphIDs[1:]:
				if glyphID != last + 1:
					ranges[-1].append(last)
					ranges.append([glyphID])
				last = glyphID
			ranges[-1].append(last)
			
			if brokenOrder or len(ranges) * 3 < len(glyphs):  # 3 words vs. 1 word
				# Format 2 is more compact
				index = 0
				for i in range(len(ranges)):
					start, end = ranges[i]
					r = RangeRecord()
					r.StartID = start
					r.Start = font.getGlyphName(start)
					r.End = font.getGlyphName(end)
					r.StartCoverageIndex = index
					ranges[i] = r
					index = index + end - start + 1
				if brokenOrder:
					warnings.warn("GSUB/GPOS Coverage is not sorted by glyph ids.")
					ranges.sort(key=lambda a: a.StartID)
				for r in ranges:
					del r.StartID
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
	
	def fromXML(self, name, attrs, content, font):
		glyphs = getattr(self, "glyphs", None)
		if glyphs is None:
			glyphs = []
			self.glyphs = glyphs
		glyphs.append(attrs["value"])


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
			outGIDS = [ glyphID + delta for glyphID in inputGIDS ]
			outGIDS = map(doModulo, outGIDS)
			outNames = [ font.getGlyphName(glyphID) for glyphID in outGIDS ]
			list(map(operator.setitem, [mapping]*lenMapping, input, outNames))
		elif self.Format == 2:
			assert len(input) == rawTable["GlyphCount"], \
					"invalid SingleSubstFormat2 table"
			subst = rawTable["Substitute"]
			list(map(operator.setitem, [mapping]*lenMapping, input, subst))
		else:
			assert 0, "unknown format: %s" % self.Format
		self.mapping = mapping
		del self.Format # Don't need this anymore
	
	def preWrite(self, font):
		mapping = getattr(self, "mapping", None)
		if mapping is None:
			mapping = self.mapping = {}
		items = list(mapping.items())
		getGlyphID = font.getGlyphID
		gidItems = [(getGlyphID(a), getGlyphID(b)) for a,b in items]
		sortableItems = sorted(zip(gidItems, items))

		# figure out format
		format = 2
		delta = None
		for inID, outID in gidItems:
			if delta is None:
				delta = outID - inID
				if delta < -32768:
					delta += 65536
				elif delta > 32767:
					delta -= 65536
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
		items = sorted(self.mapping.items())
		for inGlyph, outGlyph in items:
			xmlWriter.simpletag("Substitution",
					[("in", inGlyph), ("out", outGlyph)])
			xmlWriter.newline()
	
	def fromXML(self, name, attrs, content, font):
		mapping = getattr(self, "mapping", None)
		if mapping is None:
			mapping = {}
			self.mapping = mapping
		mapping[attrs["in"]] = attrs["out"]


class ClassDef(FormatSwitchingBaseTable):
	
	def postRead(self, rawTable, font):
		classDefs = {}
		glyphOrder = font.getGlyphOrder()

		if self.Format == 1:
			start = rawTable["StartGlyph"]
			classList = rawTable["ClassValueArray"]
			try:
				startID = font.getGlyphID(start, requireReal=True)
			except KeyError:
				warnings.warn("ClassDef table has start glyph ID out of range: %s." % start)
				startID = len(glyphOrder)
			endID = startID + len(classList)
			if endID > len(glyphOrder):
				warnings.warn("ClassDef table has entries for out of range glyph IDs: %s,%s." % (start, len(classList)))
				# NOTE: We clobber out-of-range things here.  There are legit uses for those,
				# but none that we have seen in the wild.
				endID = len(glyphOrder)

			for glyphID, cls in zip(range(startID, endID), classList):
				classDefs[glyphOrder[glyphID]] = cls

		elif self.Format == 2:
			records = rawTable["ClassRangeRecord"]
			for rec in records:
				start = rec.Start
				end = rec.End
				cls = rec.Class
				try:
					startID = font.getGlyphID(start, requireReal=True)
				except KeyError:
					warnings.warn("ClassDef table has start glyph ID out of range: %s." % start)
					continue
				try:
					endID = font.getGlyphID(end, requireReal=True) + 1
				except KeyError:
					# Apparently some tools use 65535 to "match all" the range
					if end != 'glyph65535':
						warnings.warn("ClassDef table has end glyph ID out of range: %s." % end)
					# NOTE: We clobber out-of-range things here.  There are legit uses for those,
					# but none that we have seen in the wild.
					endID = len(glyphOrder)
				for glyphID in range(startID, endID):
					classDefs[glyphOrder[glyphID]] = cls
		else:
			assert 0, "unknown format: %s" % self.Format
		self.classDefs = classDefs
		del self.Format # Don't need this anymore
	
	def preWrite(self, font):
		classDefs = getattr(self, "classDefs", None)
		if classDefs is None:
			classDefs = self.classDefs = {}
		items = list(classDefs.items())
		format = 2
		rawTable = {"ClassRangeRecord": []}
		getGlyphID = font.getGlyphID
		for i in range(len(items)):
			glyphName, cls = items[i]
			items[i] = getGlyphID(glyphName), glyphName, cls
		items.sort()
		if items:
			last, lastName, lastCls = items[0]
			ranges = [[lastCls, last, lastName]]
			for glyphID, glyphName, cls in items[1:]:
				if glyphID != last + 1 or cls != lastCls:
					ranges[-1].extend([last, lastName])
					ranges.append([cls, glyphID, glyphName])
				last = glyphID
				lastName = glyphName
				lastCls = cls
			ranges[-1].extend([last, lastName])

			startGlyph = ranges[0][1]
			endGlyph = ranges[-1][3]
			glyphCount = endGlyph - startGlyph + 1
			if len(ranges) * 3 < glyphCount + 1:
				# Format 2 is more compact
				for i in range(len(ranges)):
					cls, start, startName, end, endName = ranges[i]
					rec = ClassRangeRecord()
					rec.Start = startName
					rec.End = endName
					rec.Class = cls
					ranges[i] = rec
				format = 2
				rawTable = {"ClassRangeRecord": ranges}
			else:
				# Format 1 is more compact
				startGlyphName = ranges[0][2]
				classes = [0] * glyphCount
				for cls, start, startName, end, endName in ranges:
					for g in range(start - startGlyph, end - startGlyph + 1):
						classes[g] = cls
				format = 1
				rawTable = {"StartGlyph": startGlyphName, "ClassValueArray": classes}
		self.Format = format
		return rawTable
	
	def toXML2(self, xmlWriter, font):
		items = sorted(self.classDefs.items())
		for glyphName, cls in items:
			xmlWriter.simpletag("ClassDef", [("glyph", glyphName), ("class", cls)])
			xmlWriter.newline()
	
	def fromXML(self, name, attrs, content, font):
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
		del self.Format # Don't need this anymore
	
	def preWrite(self, font):
		self.Format = 1
		alternates = getattr(self, "alternates", None)
		if alternates is None:
			alternates = self.alternates = {}
		items = list(alternates.items())
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
		items = sorted(self.alternates.items())
		for glyphName, alternates in items:
			xmlWriter.begintag("AlternateSet", glyph=glyphName)
			xmlWriter.newline()
			for alt in alternates:
				xmlWriter.simpletag("Alternate", glyph=alt)
				xmlWriter.newline()
			xmlWriter.endtag("AlternateSet")
			xmlWriter.newline()
	
	def fromXML(self, name, attrs, content, font):
		alternates = getattr(self, "alternates", None)
		if alternates is None:
			alternates = {}
			self.alternates = alternates
		glyphName = attrs["glyph"]
		set = []
		alternates[glyphName] = set
		for element in content:
			if not isinstance(element, tuple):
				continue
			name, attrs, content = element
			set.append(attrs["glyph"])


class LigatureSubst(FormatSwitchingBaseTable):
	
	def postRead(self, rawTable, font):
		ligatures = {}
		if self.Format == 1:
			input = _getGlyphsFromCoverageTable(rawTable["Coverage"])
			ligSets = rawTable["LigatureSet"]
			assert len(input) == len(ligSets)
			for i in range(len(input)):
				ligatures[input[i]] = ligSets[i].Ligature
		else:
			assert 0, "unknown format: %s" % self.Format
		self.ligatures = ligatures
		del self.Format # Don't need this anymore
	
	def preWrite(self, font):
		self.Format = 1
		ligatures = getattr(self, "ligatures", None)
		if ligatures is None:
			ligatures = self.ligatures = {}
		items = list(ligatures.items())
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
		items = sorted(self.ligatures.items())
		for glyphName, ligSets in items:
			xmlWriter.begintag("LigatureSet", glyph=glyphName)
			xmlWriter.newline()
			for lig in ligSets:
				xmlWriter.simpletag("Ligature", glyph=lig.LigGlyph,
					components=",".join(lig.Component))
				xmlWriter.newline()
			xmlWriter.endtag("LigatureSet")
			xmlWriter.newline()
	
	def fromXML(self, name, attrs, content, font):
		ligatures = getattr(self, "ligatures", None)
		if ligatures is None:
			ligatures = {}
			self.ligatures = ligatures
		glyphName = attrs["glyph"]
		ligs = []
		ligatures[glyphName] = ligs
		for element in content:
			if not isinstance(element, tuple):
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
			'LookAheadCoverage', 'VertGlyphCoverage', 'HorizGlyphCoverage',
			'TopAccentCoverage', 'ExtendedShapeCoverage', 'MathKernCoverage'),
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
	'MathKern': ('TopRightMathKern', 'TopLeftMathKern', 'BottomRightMathKern',
			'BottomLeftMathKern'),
	'MathGlyphConstruction': ('VertGlyphConstruction', 'HorizGlyphConstruction'),
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
	If the offset to a lookup overflowed (SubTableIndex is None)
		we must promote the *previous*	lookup to an Extension type.
	If the offset from a lookup to subtable overflowed, then we must promote it 
		to an Extension Lookup type.
	"""
	ok = 0
	lookupIndex = overflowRecord.LookupListIndex
	if (overflowRecord.SubTableIndex is None):
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
	while lookup.SubTable[0].__class__.LookupType == extType:
		lookupIndex = lookupIndex -1
		if lookupIndex < 0:
			return ok
		lookup = lookups[lookupIndex]
		
	for si in range(len(lookup.SubTable)):
		subTable = lookup.SubTable[si]
		extSubTableClass = lookupTypes[overflowRecord.tableType][extType]
		extSubTable = extSubTableClass()
		extSubTable.Format = 1
		extSubTable.ExtSubTable = subTable
		lookup.SubTable[si] = extSubTable
	ok = 1
	return ok

def splitAlternateSubst(oldSubTable, newSubTable, overflowRecord):
	ok = 1
	newSubTable.Format = oldSubTable.Format
	if hasattr(oldSubTable, 'sortCoverageLast'):
		newSubTable.sortCoverageLast = oldSubTable.sortCoverageLast
	
	oldAlts = sorted(oldSubTable.alternates.items())
	oldLen = len(oldAlts)

	if overflowRecord.itemName in [ 'Coverage', 'RangeRecord']:
		# Coverage table is written last. overflow is to or within the
		# the coverage table. We will just cut the subtable in half.
		newLen = oldLen//2

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
	oldLigs = sorted(oldSubTable.ligatures.items())
	oldLen = len(oldLigs)

	if overflowRecord.itemName in [ 'Coverage', 'RangeRecord']:
		# Coverage table is written last. overflow is to or within the
		# the coverage table. We will just cut the subtable in half.
		newLen = oldLen//2

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

		subTableType = subtable.ExtSubTable.__class__.LookupType
		extSubTable = subtable
		subtable = extSubTable.ExtSubTable
		newExtSubTableClass = lookupTypes[overflowRecord.tableType][subtable.__class__.LookupType]
		newExtSubTable = newExtSubTableClass()
		newExtSubTable.Format = extSubTable.Format
		lookup.SubTable.insert(subIndex + 1, newExtSubTable)

		newSubTableClass = lookupTypes[overflowRecord.tableType][subTableType]
		newSubTable = newSubTableClass()
		newExtSubTable.ExtSubTable = newSubTable
	else:
		subTableType = subtable.__class__.LookupType
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
	import re
	from .otData import otData
	
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
		if name not in namespace:
			# the class doesn't exist yet, so the base implementation is used.
			cls = type(name, (baseClass,), {})
			namespace[name] = cls
	
	for base, alts in _equivalents.items():
		base = namespace[base]
		for alt in alts:
			namespace[alt] = type(alt, (base,), {})
	
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

	global featureParamTypes
	featureParamTypes = {
		'size': FeatureParamsSize,
	}
	for i in range(1, 20+1):
		featureParamTypes['ss%02d' % i] = FeatureParamsStylisticSet
	for i in range(1, 99+1):
		featureParamTypes['cv%02d' % i] = FeatureParamsCharacterVariants
	
	# add converters to classes
	from .otConverters import buildConverters
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
