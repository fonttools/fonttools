# coding: utf-8
"""fontTools.ttLib.tables.otTables -- A collection of classes representing the various
OpenType subtables.

Most are constructed upon import from data in otData.py, all are populated with
converter objects from otConverters.py.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
from fontTools.misc.py23 import *
from fontTools.misc.textTools import safeEval
from .otBase import BaseTable, FormatSwitchingBaseTable, ValueRecord
import operator
import logging
import struct


log = logging.getLogger(__name__)


class AATStateTable(object):
	def __init__(self):
		self.GlyphClasses = {}  # GlyphID --> GlyphClass
		self.States = []  # List of AATState, indexed by state number
		self.PerGlyphLookups = []  # [{GlyphID:GlyphID}, ...]


class AATState(object):
	def __init__(self):
		self.Transitions = {}  # GlyphClass --> AATAction


class AATAction(object):
	_FLAGS = None

	def _writeFlagsToXML(self, xmlWriter):
		flags = [f for f in self._FLAGS if self.__dict__[f]]
		if flags:
			xmlWriter.simpletag("Flags", value=",".join(flags))
			xmlWriter.newline()
		if self.ReservedFlags != 0:
			xmlWriter.simpletag(
				"ReservedFlags",
				value='0x%04X' % self.ReservedFlags)
			xmlWriter.newline()

	def _setFlag(self, flag):
		assert flag in self._FLAGS, "unsupported flag %s" % flag
		self.__dict__[flag] = True


class RearrangementMorphAction(AATAction):
	staticSize = 4
	_FLAGS = ["MarkFirst", "DontAdvance", "MarkLast"]

	_VERBS = {
		0: "no change",
		1: "Ax ⇒ xA",
		2: "xD ⇒ Dx",
		3: "AxD ⇒ DxA",
		4: "ABx ⇒ xAB",
		5: "ABx ⇒ xBA",
		6: "xCD ⇒ CDx",
		7: "xCD ⇒ DCx",
		8: "AxCD ⇒ CDxA",
		9: "AxCD ⇒ DCxA",
		10: "ABxD ⇒ DxAB",
		11: "ABxD ⇒ DxBA",
		12: "ABxCD ⇒ CDxAB",
		13: "ABxCD ⇒ CDxBA",
		14: "ABxCD ⇒ DCxAB",
		15: "ABxCD ⇒ DCxBA",
        }

	def __init__(self):
		self.NewState = 0
		self.Verb = 0
		self.MarkFirst = False
		self.DontAdvance = False
		self.MarkLast = False
		self.ReservedFlags = 0

	def compile(self, writer, font, actionIndex):
		assert actionIndex is None
		writer.writeUShort(self.NewState)
		assert self.Verb >= 0 and self.Verb <= 15, self.Verb
		flags = self.Verb | self.ReservedFlags
		if self.MarkFirst: flags |= 0x8000
		if self.DontAdvance: flags |= 0x4000
		if self.MarkLast: flags |= 0x2000
		writer.writeUShort(flags)

	def decompile(self, reader, font, actionReader):
		assert actionReader is None
		self.NewState = reader.readUShort()
		flags = reader.readUShort()
		self.Verb = flags & 0xF
		self.MarkFirst = bool(flags & 0x8000)
		self.DontAdvance = bool(flags & 0x4000)
		self.MarkLast = bool(flags & 0x2000)
		self.ReservedFlags = flags & 0x1FF0

	def toXML(self, xmlWriter, font, attrs, name):
		xmlWriter.begintag(name, **attrs)
		xmlWriter.newline()
		xmlWriter.simpletag("NewState", value=self.NewState)
		xmlWriter.newline()
		self._writeFlagsToXML(xmlWriter)
		xmlWriter.simpletag("Verb", value=self.Verb)
		verbComment = self._VERBS.get(self.Verb)
		if verbComment is not None:
			xmlWriter.comment(verbComment)
		xmlWriter.newline()
		xmlWriter.endtag(name)
		xmlWriter.newline()

	def fromXML(self, name, attrs, content, font):
		self.NewState = self.Verb = self.ReservedFlags = 0
		self.MarkFirst = self.DontAdvance = self.MarkLast = False
		content = [t for t in content if isinstance(t, tuple)]
		for eltName, eltAttrs, eltContent in content:
			if eltName == "NewState":
				self.NewState = safeEval(eltAttrs["value"])
			elif eltName == "Verb":
				self.Verb = safeEval(eltAttrs["value"])
			elif eltName == "ReservedFlags":
				self.ReservedFlags = safeEval(eltAttrs["value"])
			elif eltName == "Flags":
				for flag in eltAttrs["value"].split(","):
					self._setFlag(flag.strip())


class ContextualMorphAction(AATAction):
	staticSize = 8
	_FLAGS = ["SetMark", "DontAdvance"]

	def __init__(self):
		self.NewState = 0
		self.SetMark, self.DontAdvance = False, False
		self.ReservedFlags = 0
		self.MarkIndex, self.CurrentIndex = 0xFFFF, 0xFFFF

	def compile(self, writer, font, actionIndex):
		assert actionIndex is None
		writer.writeUShort(self.NewState)
		flags = self.ReservedFlags
		if self.SetMark: flags |= 0x8000
		if self.DontAdvance: flags |= 0x4000
		writer.writeUShort(flags)
		writer.writeUShort(self.MarkIndex)
		writer.writeUShort(self.CurrentIndex)

	def decompile(self, reader, font, actionReader):
		assert actionReader is None
		self.NewState = reader.readUShort()
		flags = reader.readUShort()
		self.SetMark = bool(flags & 0x8000)
		self.DontAdvance = bool(flags & 0x4000)
		self.ReservedFlags = flags & 0x3FFF
		self.MarkIndex = reader.readUShort()
		self.CurrentIndex = reader.readUShort()

	def toXML(self, xmlWriter, font, attrs, name):
		xmlWriter.begintag(name, **attrs)
		xmlWriter.newline()
		xmlWriter.simpletag("NewState", value=self.NewState)
		xmlWriter.newline()
		self._writeFlagsToXML(xmlWriter)
		xmlWriter.simpletag("MarkIndex", value=self.MarkIndex)
		xmlWriter.newline()
		xmlWriter.simpletag("CurrentIndex",
		                    value=self.CurrentIndex)
		xmlWriter.newline()
		xmlWriter.endtag(name)
		xmlWriter.newline()

	def fromXML(self, name, attrs, content, font):
		self.NewState = self.ReservedFlags = 0
		self.SetMark = self.DontAdvance = False
		self.MarkIndex, self.CurrentIndex = 0xFFFF, 0xFFFF
		content = [t for t in content if isinstance(t, tuple)]
		for eltName, eltAttrs, eltContent in content:
			if eltName == "NewState":
				self.NewState = safeEval(eltAttrs["value"])
			elif eltName == "Flags":
				for flag in eltAttrs["value"].split(","):
					self._setFlag(flag.strip())
			elif eltName == "ReservedFlags":
				self.ReservedFlags = safeEval(eltAttrs["value"])
			elif eltName == "MarkIndex":
				self.MarkIndex = safeEval(eltAttrs["value"])
			elif eltName == "CurrentIndex":
				self.CurrentIndex = safeEval(eltAttrs["value"])


class LigAction(object):
	def __init__(self):
		self.Store = False
		# GlyphIndexDelta is a (possibly negative) delta that gets
		# added to the glyph ID at the top of the AAT runtime
		# execution stack. It is *not* a byte offset into the
		# morx table. The result of the addition, which is performed
		# at run time by the shaping engine, is an index into
		# the ligature components table. See 'morx' specification.
		# In the AAT specification, this field is called Offset;
		# but its meaning is quite different from other offsets
		# in either AAT or OpenType, so we use a different name.
		self.GlyphIndexDelta = 0


class LigatureMorphAction(AATAction):
	staticSize = 6
	_FLAGS = ["SetComponent", "DontAdvance"]

	def __init__(self):
		self.NewState = 0
		self.SetComponent, self.DontAdvance = False, False
		self.ReservedFlags = 0
		self.Actions = []

	def compile(self, writer, font, actionIndex):
		assert actionIndex is not None
		writer.writeUShort(self.NewState)
		flags = self.ReservedFlags
		if self.SetComponent: flags |= 0x8000
		if self.DontAdvance: flags |= 0x4000
		if len(self.Actions) > 0: flags |= 0x2000
		writer.writeUShort(flags)
		if len(self.Actions) > 0:
			actions = self.compileLigActions()
			writer.writeUShort(actionIndex[actions])
		else:
			writer.writeUShort(0)

	def decompile(self, reader, font, actionReader):
		assert actionReader is not None
		self.NewState = reader.readUShort()
		flags = reader.readUShort()
		self.SetComponent = bool(flags & 0x8000)
		self.DontAdvance = bool(flags & 0x4000)
		performAction = bool(flags & 0x2000)
		# As of 2017-09-12, the 'morx' specification says that
		# the reserved bitmask in ligature subtables is 0x3FFF.
		# However, the specification also defines a flag 0x2000,
		# so the reserved value should actually be 0x1FFF.
		# TODO: Report this specification bug to Apple.
		self.ReservedFlags = flags & 0x1FFF
		actionIndex = reader.readUShort()
		if performAction:
			self.Actions = self._decompileLigActions(
				actionReader, actionIndex)
		else:
			self.Actions = []

	def compileLigActions(self):
		result = []
		for i, action in enumerate(self.Actions):
			last = (i == len(self.Actions) - 1)
			value = action.GlyphIndexDelta & 0x3FFFFFFF
			value |= 0x80000000 if last else 0
			value |= 0x40000000 if action.Store else 0
			result.append(struct.pack(">L", value))
		return bytesjoin(result)

	def _decompileLigActions(self, actionReader, actionIndex):
		actions = []
		last = False
		reader = actionReader.getSubReader(
			actionReader.pos + actionIndex * 4)
		while not last:
			value = reader.readULong()
			last = bool(value & 0x80000000)
			action = LigAction()
			actions.append(action)
			action.Store = bool(value & 0x40000000)
			delta = value & 0x3FFFFFFF
			if delta >= 0x20000000: # sign-extend 30-bit value
				delta = -0x40000000 + delta
			action.GlyphIndexDelta = delta
		return actions

	def fromXML(self, name, attrs, content, font):
		self.NewState = self.ReservedFlags = 0
		self.SetComponent = self.DontAdvance = False
		self.ReservedFlags = 0
		self.Actions = []
		content = [t for t in content if isinstance(t, tuple)]
		for eltName, eltAttrs, eltContent in content:
			if eltName == "NewState":
				self.NewState = safeEval(eltAttrs["value"])
			elif eltName == "Flags":
				for flag in eltAttrs["value"].split(","):
					self._setFlag(flag.strip())
			elif eltName == "ReservedFlags":
				self.ReservedFlags = safeEval(eltAttrs["value"])
			elif eltName == "Action":
				action = LigAction()
				flags = eltAttrs.get("Flags", "").split(",")
				flags = [f.strip() for f in flags]
				action.Store = "Store" in flags
				action.GlyphIndexDelta = safeEval(
					eltAttrs["GlyphIndexDelta"])
				self.Actions.append(action)

	def toXML(self, xmlWriter, font, attrs, name):
		xmlWriter.begintag(name, **attrs)
		xmlWriter.newline()
		xmlWriter.simpletag("NewState", value=self.NewState)
		xmlWriter.newline()
		self._writeFlagsToXML(xmlWriter)
		for action in self.Actions:
			attribs = [("GlyphIndexDelta", action.GlyphIndexDelta)]
			if action.Store:
				attribs.append(("Flags", "Store"))
			xmlWriter.simpletag("Action", attribs)
			xmlWriter.newline()
		xmlWriter.endtag(name)
		xmlWriter.newline()


class InsertionMorphAction(AATAction):
	staticSize = 8

	_FLAGS = ["SetMark", "DontAdvance",
	          "CurrentIsKashidaLike", "MarkedIsKashidaLike",
	          "CurrentInsertBefore", "MarkedInsertBefore"]

	def __init__(self):
		self.NewState = 0
		for flag in self._FLAGS:
			setattr(self, flag, False)
		self.ReservedFlags = 0
		self.CurrentInsertionAction, self.MarkedInsertionAction = [], []

	def compile(self, writer, font, actionIndex):
		assert actionIndex is not None
		writer.writeUShort(self.NewState)
		flags = self.ReservedFlags
		if self.SetMark: flags |= 0x8000
		if self.DontAdvance: flags |= 0x4000
		if self.CurrentIsKashidaLike: flags |= 0x2000
		if self.MarkedIsKashidaLike: flags |= 0x1000
		if self.CurrentInsertBefore: flags |= 0x0800
		if self.MarkedInsertBefore: flags |= 0x0400
		flags |= len(self.CurrentInsertionAction) << 5
		flags |= len(self.MarkedInsertionAction)
		writer.writeUShort(flags)
		if len(self.CurrentInsertionAction) > 0:
			currentIndex = actionIndex[
				tuple(self.CurrentInsertionAction)]
		else:
			currentIndex = 0xFFFF
		writer.writeUShort(currentIndex)
		if len(self.MarkedInsertionAction) > 0:
			markedIndex = actionIndex[
				tuple(self.MarkedInsertionAction)]
		else:
			markedIndex = 0xFFFF
		writer.writeUShort(markedIndex)

	def decompile(self, reader, font, actionReader):
		assert actionReader is not None
		self.NewState = reader.readUShort()
		flags = reader.readUShort()
		self.SetMark = bool(flags & 0x8000)
		self.DontAdvance = bool(flags & 0x4000)
		self.CurrentIsKashidaLike = bool(flags & 0x2000)
		self.MarkedIsKashidaLike = bool(flags & 0x1000)
		self.CurrentInsertBefore = bool(flags & 0x0800)
		self.MarkedInsertBefore = bool(flags & 0x0400)
		self.CurrentInsertionAction = self._decompileInsertionAction(
			actionReader, font,
			index=reader.readUShort(),
			count=((flags & 0x03E0) >> 5))
		self.MarkedInsertionAction = self._decompileInsertionAction(
			actionReader, font,
			index=reader.readUShort(),
			count=(flags & 0x001F))

	def _decompileInsertionAction(self, actionReader, font, index, count):
		if index == 0xFFFF or count == 0:
			return []
		reader = actionReader.getSubReader(
			actionReader.pos + index * 2)
		return [font.getGlyphName(glyphID)
		        for glyphID in reader.readUShortArray(count)]

	def toXML(self, xmlWriter, font, attrs, name):
		xmlWriter.begintag(name, **attrs)
		xmlWriter.newline()
		xmlWriter.simpletag("NewState", value=self.NewState)
		xmlWriter.newline()
		self._writeFlagsToXML(xmlWriter)
		for g in self.CurrentInsertionAction:
			xmlWriter.simpletag("CurrentInsertionAction", glyph=g)
			xmlWriter.newline()
		for g in self.MarkedInsertionAction:
			xmlWriter.simpletag("MarkedInsertionAction", glyph=g)
			xmlWriter.newline()
		xmlWriter.endtag(name)
		xmlWriter.newline()

	def fromXML(self, name, attrs, content, font):
		self.__init__()
		content = [t for t in content if isinstance(t, tuple)]
		for eltName, eltAttrs, eltContent in content:
			if eltName == "NewState":
				self.NewState = safeEval(eltAttrs["value"])
			elif eltName == "Flags":
				for flag in eltAttrs["value"].split(","):
					self._setFlag(flag.strip())
			elif eltName == "CurrentInsertionAction":
				self.CurrentInsertionAction.append(
					eltAttrs["glyph"])
			elif eltName == "MarkedInsertionAction":
				self.MarkedInsertionAction.append(
					eltAttrs["glyph"])
			else:
				assert False, eltName


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

	def populateDefaults(self, propagator=None):
		if not hasattr(self, 'glyphs'):
			self.glyphs = []

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
				log.warning("GSUB/GPOS Coverage is not sorted by glyph ids.")
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
					log.warning("Coverage table has start glyph ID out of range: %s.", start)
					continue
				try:
					endID = font.getGlyphID(end, requireReal=True) + 1
				except KeyError:
					# Apparently some tools use 65535 to "match all" the range
					if end != 'glyph65535':
						log.warning("Coverage table has end glyph ID out of range: %s.", end)
					# NOTE: We clobber out-of-range things here.  There are legit uses for those,
					# but none that we have seen in the wild.
					endID = len(glyphOrder)
				glyphs.extend(glyphOrder[glyphID] for glyphID in range(startID, endID))
		else:
			self.glyphs = []
			log.warning("Unknown Coverage format: %s" % self.Format)

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
					log.warning("GSUB/GPOS Coverage is not sorted by glyph ids.")
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


class VarIdxMap(BaseTable):

	def populateDefaults(self, propagator=None):
		if not hasattr(self, 'mapping'):
			self.mapping = {}

	def postRead(self, rawTable, font):
		assert (rawTable['EntryFormat'] & 0xFFC0) == 0
		glyphOrder = font.getGlyphOrder()
		mapList = rawTable['mapping']
		mapList.extend([mapList[-1]] * (len(glyphOrder) - len(mapList)))
		self.mapping = dict(zip(glyphOrder, mapList))

	def preWrite(self, font):
		mapping = getattr(self, "mapping", None)
		if mapping is None:
			mapping = self.mapping = {}

		glyphOrder = font.getGlyphOrder()
		mapping = [mapping[g] for g in glyphOrder]
		while len(mapping) > 1 and mapping[-2] == mapping[-1]:
			del mapping[-1]

		rawTable = { 'mapping': mapping }
		rawTable['MappingCount'] = len(mapping)

		ored = 0
		for idx in mapping:
			ored |= idx

		inner = ored & 0xFFFF
		innerBits = 0
		while inner:
			innerBits += 1
			inner >>= 1
		innerBits = max(innerBits, 1)
		assert innerBits <= 16

		ored = (ored >> (16-innerBits)) | (ored & ((1<<innerBits)-1))
		if   ored <= 0x000000FF:
			entrySize = 1
		elif ored <= 0x0000FFFF:
			entrySize = 2
		elif ored <= 0x00FFFFFF:
			entrySize = 3
		else:
			entrySize = 4

		entryFormat = ((entrySize - 1) << 4) | (innerBits - 1)

		rawTable['EntryFormat'] = entryFormat
		return rawTable

	def toXML2(self, xmlWriter, font):
		for glyph, value in sorted(getattr(self, "mapping", {}).items()):
			attrs = (
				('glyph', glyph),
				('outer', value >> 16),
				('inner', value & 0xFFFF),
			)
			xmlWriter.simpletag("Map", attrs)
			xmlWriter.newline()

	def fromXML(self, name, attrs, content, font):
		mapping = getattr(self, "mapping", None)
		if mapping is None:
			mapping = {}
			self.mapping = mapping
		try:
			glyph = attrs['glyph']
		except: # https://github.com/fonttools/fonttools/commit/21cbab8ce9ded3356fef3745122da64dcaf314e9#commitcomment-27649836
			glyph = font.getGlyphOrder()[attrs['index']]
		outer = safeEval(attrs['outer'])
		inner = safeEval(attrs['inner'])
		assert inner <= 0xFFFF
		mapping[glyph] = (outer << 16) | inner


class SingleSubst(FormatSwitchingBaseTable):

	def populateDefaults(self, propagator=None):
		if not hasattr(self, 'mapping'):
			self.mapping = {}

	def postRead(self, rawTable, font):
		mapping = {}
		input = _getGlyphsFromCoverageTable(rawTable["Coverage"])
		lenMapping = len(input)
		if self.Format == 1:
			delta = rawTable["DeltaGlyphID"]
			inputGIDS =  [ font.getGlyphID(name) for name in input ]
			outGIDS = [ (glyphID + delta) % 65536 for glyphID in inputGIDS ]
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
				delta = (outID - inID) % 65536

			if (inID + delta) % 65536 != outID:
					break
		else:
			if delta is None:
				# the mapping is empty, better use format 2
				format = 2
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


class MultipleSubst(FormatSwitchingBaseTable):

	def populateDefaults(self, propagator=None):
		if not hasattr(self, 'mapping'):
			self.mapping = {}

	def postRead(self, rawTable, font):
		mapping = {}
		if self.Format == 1:
			glyphs = _getGlyphsFromCoverageTable(rawTable["Coverage"])
			subst = [s.Substitute for s in rawTable["Sequence"]]
			mapping = dict(zip(glyphs, subst))
		else:
			assert 0, "unknown format: %s" % self.Format
		self.mapping = mapping

	def preWrite(self, font):
		mapping = getattr(self, "mapping", None)
		if mapping is None:
			mapping = self.mapping = {}
		cov = Coverage()
		cov.glyphs = sorted(list(mapping.keys()), key=font.getGlyphID)
		self.Format = 1
		rawTable = {
                        "Coverage": cov,
                        "Sequence": [self.makeSequence_(mapping[glyph])
                                     for glyph in cov.glyphs],
                }
		return rawTable

	def toXML2(self, xmlWriter, font):
		items = sorted(self.mapping.items())
		for inGlyph, outGlyphs in items:
			out = ",".join(outGlyphs)
			xmlWriter.simpletag("Substitution",
					[("in", inGlyph), ("out", out)])
			xmlWriter.newline()

	def fromXML(self, name, attrs, content, font):
		mapping = getattr(self, "mapping", None)
		if mapping is None:
			mapping = {}
			self.mapping = mapping

		# TTX v3.0 and earlier.
		if name == "Coverage":
			self.old_coverage_ = []
			for element in content:
				if not isinstance(element, tuple):
					continue
				element_name, element_attrs, _ = element
				if element_name == "Glyph":
					self.old_coverage_.append(element_attrs["value"])
			return
		if name == "Sequence":
			index = int(attrs.get("index", len(mapping)))
			glyph = self.old_coverage_[index]
			glyph_mapping = mapping[glyph] = []
			for element in content:
				if not isinstance(element, tuple):
					continue
				element_name, element_attrs, _ = element
				if element_name == "Substitute":
					glyph_mapping.append(element_attrs["value"])
			return

                # TTX v3.1 and later.
		outGlyphs = attrs["out"].split(",") if attrs["out"] else []
		mapping[attrs["in"]] = [g.strip() for g in outGlyphs]

	@staticmethod
	def makeSequence_(g):
		seq = Sequence()
		seq.Substitute = g
		return seq


class ClassDef(FormatSwitchingBaseTable):

	def populateDefaults(self, propagator=None):
		if not hasattr(self, 'classDefs'):
			self.classDefs = {}

	def postRead(self, rawTable, font):
		classDefs = {}
		glyphOrder = font.getGlyphOrder()

		if self.Format == 1:
			start = rawTable["StartGlyph"]
			classList = rawTable["ClassValueArray"]
			try:
				startID = font.getGlyphID(start, requireReal=True)
			except KeyError:
				log.warning("ClassDef table has start glyph ID out of range: %s.", start)
				startID = len(glyphOrder)
			endID = startID + len(classList)
			if endID > len(glyphOrder):
				log.warning("ClassDef table has entries for out of range glyph IDs: %s,%s.",
					start, len(classList))
				# NOTE: We clobber out-of-range things here.  There are legit uses for those,
				# but none that we have seen in the wild.
				endID = len(glyphOrder)

			for glyphID, cls in zip(range(startID, endID), classList):
				if cls:
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
					log.warning("ClassDef table has start glyph ID out of range: %s.", start)
					continue
				try:
					endID = font.getGlyphID(end, requireReal=True) + 1
				except KeyError:
					# Apparently some tools use 65535 to "match all" the range
					if end != 'glyph65535':
						log.warning("ClassDef table has end glyph ID out of range: %s.", end)
					# NOTE: We clobber out-of-range things here.  There are legit uses for those,
					# but none that we have seen in the wild.
					endID = len(glyphOrder)
				for glyphID in range(startID, endID):
					if cls:
						classDefs[glyphOrder[glyphID]] = cls
		else:
			assert 0, "unknown format: %s" % self.Format
		self.classDefs = classDefs

	def _getClassRanges(self, font):
		classDefs = getattr(self, "classDefs", None)
		if classDefs is None:
			self.classDefs = {}
			return
		getGlyphID = font.getGlyphID
		items = []
		for glyphName, cls in classDefs.items():
			if not cls:
				continue
			items.append((getGlyphID(glyphName), glyphName, cls))
		if items:
			items.sort()
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
			return ranges

	def preWrite(self, font):
		format = 2
		rawTable = {"ClassRangeRecord": []}
		ranges = self._getClassRanges(font)
		if ranges:
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

	def populateDefaults(self, propagator=None):
		if not hasattr(self, 'alternates'):
			self.alternates = {}

	def postRead(self, rawTable, font):
		alternates = {}
		if self.Format == 1:
			input = _getGlyphsFromCoverageTable(rawTable["Coverage"])
			alts = rawTable["AlternateSet"]
			assert len(input) == len(alts)
			for inp,alt in zip(input,alts):
				alternates[inp] = alt.Alternate
		else:
			assert 0, "unknown format: %s" % self.Format
		self.alternates = alternates

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
		for set in setList:
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

	def populateDefaults(self, propagator=None):
		if not hasattr(self, 'ligatures'):
			self.ligatures = {}

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

	def preWrite(self, font):
		self.Format = 1
		ligatures = getattr(self, "ligatures", None)
		if ligatures is None:
			ligatures = self.ligatures = {}

		if ligatures and isinstance(next(iter(ligatures)), tuple):
			# New high-level API in v3.1 and later.  Note that we just support compiling this
			# for now.  We don't load to this API, and don't do XML with it.

			# ligatures is map from components-sequence to lig-glyph
			newLigatures = dict()
			for comps,lig in sorted(ligatures.items(), key=lambda item: (-len(item[0]), item[0])):
				ligature = Ligature()
				ligature.Component = comps[1:]
				ligature.CompCount = len(comps)
				ligature.LigGlyph = lig
				newLigatures.setdefault(comps[0], []).append(ligature)
			ligatures = newLigatures

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
			components = attrs["components"]
			lig.Component = components.split(",") if components else []
			ligs.append(lig)


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

	lookup.LookupType = extType
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
		newLen = overflowRecord.itemIndex - 1

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
		newLen = overflowRecord.itemIndex - 1

	newSubTable.ligatures = {}
	for i in range(newLen, oldLen):
		item = oldLigs[i]
		key = item[0]
		newSubTable.ligatures[key] = item[1]
		del oldSubTable.ligatures[key]

	return ok


def splitPairPos(oldSubTable, newSubTable, overflowRecord):
	st = oldSubTable
	ok = False
	newSubTable.Format = oldSubTable.Format
	if oldSubTable.Format == 1 and len(oldSubTable.PairSet) > 1:
		for name in 'ValueFormat1', 'ValueFormat2':
			setattr(newSubTable, name, getattr(oldSubTable, name))

		# Move top half of coverage to new subtable

		newSubTable.Coverage = oldSubTable.Coverage.__class__()

		coverage = oldSubTable.Coverage.glyphs
		records = oldSubTable.PairSet

		oldCount = len(oldSubTable.PairSet) // 2

		oldSubTable.Coverage.glyphs = coverage[:oldCount]
		oldSubTable.PairSet = records[:oldCount]

		newSubTable.Coverage.glyphs = coverage[oldCount:]
		newSubTable.PairSet = records[oldCount:]

		oldSubTable.PairSetCount = len(oldSubTable.PairSet)
		newSubTable.PairSetCount = len(newSubTable.PairSet)

		ok = True

	elif oldSubTable.Format == 2 and len(oldSubTable.Class1Record) > 1:
		if not hasattr(oldSubTable, 'Class2Count'):
			oldSubTable.Class2Count = len(oldSubTable.Class1Record[0].Class2Record)
		for name in 'Class2Count', 'ClassDef2', 'ValueFormat1', 'ValueFormat2':
			setattr(newSubTable, name, getattr(oldSubTable, name))

		# The two subtables will still have the same ClassDef2 and the table
		# sharing will still cause the sharing to overflow.  As such, disable
		# sharing on the one that is serialized second (that's oldSubTable).
		oldSubTable.DontShare = True

		# Move top half of class numbers to new subtable

		newSubTable.Coverage = oldSubTable.Coverage.__class__()
		newSubTable.ClassDef1 = oldSubTable.ClassDef1.__class__()

		coverage = oldSubTable.Coverage.glyphs
		classDefs = oldSubTable.ClassDef1.classDefs
		records = oldSubTable.Class1Record

		oldCount = len(oldSubTable.Class1Record) // 2
		newGlyphs = set(k for k,v in classDefs.items() if v >= oldCount)

		oldSubTable.Coverage.glyphs = [g for g in coverage if g not in newGlyphs]
		oldSubTable.ClassDef1.classDefs = {k:v for k,v in classDefs.items() if v < oldCount}
		oldSubTable.Class1Record = records[:oldCount]

		newSubTable.Coverage.glyphs = [g for g in coverage if g in newGlyphs]
		newSubTable.ClassDef1.classDefs = {k:(v-oldCount) for k,v in classDefs.items() if v > oldCount}
		newSubTable.Class1Record = records[oldCount:]

		oldSubTable.Class1Count = len(oldSubTable.Class1Record)
		newSubTable.Class1Count = len(newSubTable.Class1Record)

		ok = True

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
					2: splitPairPos,
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

	# First, try not sharing anything for this subtable...
	if not hasattr(subtable, "DontShare"):
		subtable.DontShare = True
		return True

	if hasattr(subtable, 'ExtSubTable'):
		# We split the subtable of the Extension table, and add a new Extension table
		# to contain the new subtable.

		subTableType = subtable.ExtSubTable.__class__.LookupType
		extSubTable = subtable
		subtable = extSubTable.ExtSubTable
		newExtSubTableClass = lookupTypes[overflowRecord.tableType][extSubTable.__class__.LookupType]
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
			if name in ('GSUB', 'GPOS'):
				cls.DontShare = True
			namespace[name] = cls

	for base, alts in _equivalents.items():
		base = namespace[base]
		for alt in alts:
			namespace[alt] = base

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
		'mort': {
			4: NoncontextualMorph,
		},
		'morx': {
			0: RearrangementMorph,
			1: ContextualMorph,
			2: LigatureMorph,
			# 3: Reserved,
			4: NoncontextualMorph,
			# 5: InsertionMorph,
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
			# XXX Add staticSize?
		else:
			cls = namespace[name]
			cls.converters, cls.convertersByName = buildConverters(table, namespace)
			# XXX Add staticSize?


_buildClasses()


def _getGlyphsFromCoverageTable(coverage):
	if coverage is None:
		# empty coverage table
		return []
	else:
		return coverage.glyphs
