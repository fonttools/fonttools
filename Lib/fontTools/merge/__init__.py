# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Google Author(s): Behdad Esfahbod, Roozbeh Pournader

from fontTools import ttLib
from fontTools.merge.base import *
from fontTools.merge.layout import *
from fontTools.merge.unicode import *
from fontTools.merge.util import *
from fontTools.misc.loggingTools import Timer
from fontTools.pens.recordingPen import DecomposingRecordingPen
from functools import reduce
import sys
import logging


log = logging.getLogger("fontTools.merge")
timer = Timer(logger=logging.getLogger(__name__+".timer"), level=logging.INFO)


def _glyphsAreSame(glyphSet1, glyphSet2, glyph1, glyph2,
                   advanceTolerance=.05,
                   advanceToleranceEmpty=.20):
	pen1 = DecomposingRecordingPen(glyphSet1)
	pen2 = DecomposingRecordingPen(glyphSet2)
	g1 = glyphSet1[glyph1]
	g2 = glyphSet2[glyph2]
	g1.draw(pen1)
	g2.draw(pen2)
	if pen1.value != pen2.value:
		return False
	# Allow more width tolerance for glyphs with no ink
	tolerance = advanceTolerance if pen1.value else advanceToleranceEmpty
    # TODO Warn if advances not the same but within tolerance.
	if abs(g1.width - g2.width) > g1.width * tolerance:
		return False
	if hasattr(g1, 'height') and g1.height is not None:
		if abs(g1.height - g2.height) > g1.height * tolerance:
			return False
	return True

# Valid (format, platformID, platEncID) triplets for cmap subtables containing
# Unicode BMP-only and Unicode Full Repertoire semantics.
# Cf. OpenType spec for "Platform specific encodings":
# https://docs.microsoft.com/en-us/typography/opentype/spec/name
class CmapUnicodePlatEncodings:
	BMP = {(4, 3, 1), (4, 0, 3), (4, 0, 4), (4, 0, 6)}
	FullRepertoire = {(12, 3, 10), (12, 0, 4), (12, 0, 6)}



@add_method(ttLib.getTableClass('cmap'))
def merge(self, m, tables):
	# TODO Handle format=14.
	# Only merge format 4 and 12 Unicode subtables, ignores all other subtables
	# If there is a format 12 table for the same font, ignore the format 4 table
	cmapTables = []
	for fontIdx,table in enumerate(tables):
		format4 = None
		format12 = None
		for subtable in table.tables:
			properties = (subtable.format, subtable.platformID, subtable.platEncID)
			if properties in CmapUnicodePlatEncodings.BMP:
				format4 = subtable
			elif properties in CmapUnicodePlatEncodings.FullRepertoire:
				format12 = subtable
			else:
				log.warning(
					"Dropped cmap subtable from font [%s]:\t"
					"format %2s, platformID %2s, platEncID %2s",
					fontIdx, subtable.format, subtable.platformID, subtable.platEncID
				)
		if format12 is not None:
			cmapTables.append((format12, fontIdx))
		elif format4 is not None:
			cmapTables.append((format4, fontIdx))

	# Build a unicode mapping, then decide which format is needed to store it.
	cmap = {}
	fontIndexForGlyph = {}
	glyphSets = [None for f in m.fonts] if hasattr(m, 'fonts') else None
	for table,fontIdx in cmapTables:
		# handle duplicates
		for uni,gid in table.cmap.items():
			oldgid = cmap.get(uni, None)
			if oldgid is None:
				cmap[uni] = gid
				fontIndexForGlyph[gid] = fontIdx
			elif is_Default_Ignorable(uni) or uni in (0x25CC,): # U+25CC DOTTED CIRCLE
				continue
			elif oldgid != gid:
				# Char previously mapped to oldgid, now to gid.
				# Record, to fix up in GSUB 'locl' later.
				if m.duplicateGlyphsPerFont[fontIdx].get(oldgid) is None:
					if glyphSets is not None:
						oldFontIdx = fontIndexForGlyph[oldgid]
						for idx in (fontIdx, oldFontIdx):
							if glyphSets[idx] is None:
								glyphSets[idx] = m.fonts[idx].getGlyphSet()
						#if _glyphsAreSame(glyphSets[oldFontIdx], glyphSets[fontIdx], oldgid, gid):
						#	continue
					m.duplicateGlyphsPerFont[fontIdx][oldgid] = gid
				elif m.duplicateGlyphsPerFont[fontIdx][oldgid] != gid:
					# Char previously mapped to oldgid but oldgid is already remapped to a different
					# gid, because of another Unicode character.
					# TODO: Try harder to do something about these.
					log.warning("Dropped mapping from codepoint %#06X to glyphId '%s'", uni, gid)

	cmapBmpOnly = {uni: gid for uni,gid in cmap.items() if uni <= 0xFFFF}
	self.tables = []
	module = ttLib.getTableModule('cmap')
	if len(cmapBmpOnly) != len(cmap):
		# format-12 required.
		cmapTable = module.cmap_classes[12](12)
		cmapTable.platformID = 3
		cmapTable.platEncID = 10
		cmapTable.language = 0
		cmapTable.cmap = cmap
		self.tables.append(cmapTable)
	# always create format-4
	cmapTable = module.cmap_classes[4](4)
	cmapTable.platformID = 3
	cmapTable.platEncID = 1
	cmapTable.language = 0
	cmapTable.cmap = cmapBmpOnly
	# ordered by platform then encoding
	self.tables.insert(0, cmapTable)
	self.tableVersion = 0
	self.numSubTables = len(self.tables)
	return self




class Options(object):

	class UnknownOptionError(Exception):
		pass

	def __init__(self, **kwargs):

		self.verbose = False
		self.timing = False
		self.drop_tables = []

		self.set(**kwargs)

	def set(self, **kwargs):
		for k,v in kwargs.items():
			if not hasattr(self, k):
				raise self.UnknownOptionError("Unknown option '%s'" % k)
			setattr(self, k, v)

	def parse_opts(self, argv, ignore_unknown=[]):
		ret = []
		opts = {}
		for a in argv:
			orig_a = a
			if not a.startswith('--'):
				ret.append(a)
				continue
			a = a[2:]
			i = a.find('=')
			op = '='
			if i == -1:
				if a.startswith("no-"):
					k = a[3:]
					v = False
				else:
					k = a
					v = True
			else:
				k = a[:i]
				if k[-1] in "-+":
					op = k[-1]+'='  # Ops is '-=' or '+=' now.
					k = k[:-1]
				v = a[i+1:]
			ok = k
			k = k.replace('-', '_')
			if not hasattr(self, k):
				if ignore_unknown is True or ok in ignore_unknown:
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
				vv = v.split(',')
				if vv == ['']:
					vv = []
				vv = [int(x, 0) if len(x) and x[0] in "0123456789" else x for x in vv]
				if op == '=':
					v = vv
				elif op == '+=':
					v = ov
					v.extend(vv)
				elif op == '-=':
					v = ov
					for x in vv:
						if x in v:
							v.remove(x)
				else:
					assert 0

			opts[k] = v
		self.set(**opts)

		return ret

class _AttendanceRecordingIdentityDict(object):
	"""A dictionary-like object that records indices of items actually accessed
	from a list."""

	def __init__(self, lst):
		self.l = lst
		self.d = {id(v):i for i,v in enumerate(lst)}
		self.s = set()

	def __getitem__(self, v):
		self.s.add(self.d[id(v)])
		return v

class _GregariousIdentityDict(object):
	"""A dictionary-like object that welcomes guests without reservations and
	adds them to the end of the guest list."""

	def __init__(self, lst):
		self.l = lst
		self.s = set(id(v) for v in lst)

	def __getitem__(self, v):
		if id(v) not in self.s:
			self.s.add(id(v))
			self.l.append(v)
		return v

class _NonhashableDict(object):
	"""A dictionary-like object mapping objects to values."""

	def __init__(self, keys, values=None):
		if values is None:
			self.d = {id(v):i for i,v in enumerate(keys)}
		else:
			self.d = {id(k):v for k,v in zip(keys, values)}

	def __getitem__(self, k):
		return self.d[id(k)]

	def __setitem__(self, k, v):
		self.d[id(k)] = v

	def __delitem__(self, k):
		del self.d[id(k)]

class Merger(object):
	"""Font merger.

	This class merges multiple files into a single OpenType font, taking into
	account complexities such as OpenType layout (``GSUB``/``GPOS``) tables and
	cross-font metrics (e.g. ``hhea.ascent`` is set to the maximum value across
	all the fonts).

	If multiple glyphs map to the same Unicode value, and the glyphs are considered
	sufficiently different (that is, they differ in any of paths, widths, or
	height), then subsequent glyphs are renamed and a lookup in the ``locl``
	feature will be created to disambiguate them. For example, if the arguments
	are an Arabic font and a Latin font and both contain a set of parentheses,
	the Latin glyphs will be renamed to ``parenleft#1`` and ``parenright#1``,
	and a lookup will be inserted into the to ``locl`` feature (creating it if
	necessary) under the ``latn`` script to substitute ``parenleft`` with
	``parenleft#1`` etc.

	Restrictions:

	- All fonts must have the same units per em.
	- If duplicate glyph disambiguation takes place as described above then the
		fonts must have a ``GSUB`` table.

	Attributes:
		options: Currently unused.
	"""

	def __init__(self, options=None):

		if not options:
			options = Options()

		self.options = options

	def merge(self, fontfiles):
		"""Merges fonts together.

		Args:
			fontfiles: A list of file names to be merged

		Returns:
			A :class:`fontTools.ttLib.TTFont` object. Call the ``save`` method on
			this to write it out to an OTF file.
		"""
		#
		# Settle on a mega glyph order.
		#
		fonts = [ttLib.TTFont(fontfile) for fontfile in fontfiles]
		glyphOrders = [font.getGlyphOrder() for font in fonts]
		megaGlyphOrder = self._mergeGlyphOrders(glyphOrders)

		# Take first input file sfntVersion
		sfntVersion = fonts[0].sfntVersion

		cffTables = [None] * len(fonts)
		if sfntVersion == "OTTO":
			for i, font in enumerate(fonts):
				cffTables[i] = font['CFF ']

		# Reload fonts and set new glyph names on them.
		# TODO Is it necessary to reload font?  I think it is.  At least
		# it's safer, in case tables were loaded to provide glyph names.
		fonts = [ttLib.TTFont(fontfile) for fontfile in fontfiles]
		for font, glyphOrder, cffTable in zip(fonts, glyphOrders, cffTables):
			font.setGlyphOrder(glyphOrder)
			if cffTable:
				# Rename CFF CharStrings to match the new glyphOrder.
				# Using cffTable from before reloading the fonts, because reasons.
				self._renameCFFCharStrings(glyphOrder, cffTable)
				font['CFF '] = cffTable

		mega = ttLib.TTFont(sfntVersion=sfntVersion)
		mega.setGlyphOrder(megaGlyphOrder)

		for font in fonts:
			self._preMerge(font)

		self.fonts = fonts
		self.duplicateGlyphsPerFont = [{} for _ in fonts]

		allTags = reduce(set.union, (list(font.keys()) for font in fonts), set())
		allTags.remove('GlyphOrder')

		# Make sure we process cmap before GSUB as we have a dependency there.
		if 'GSUB' in allTags:
			allTags.remove('GSUB')
			allTags = ['GSUB'] + list(allTags)
		if 'cmap' in allTags:
			allTags.remove('cmap')
			allTags = ['cmap'] + list(allTags)

		for tag in allTags:
			if tag in self.options.drop_tables:
				continue

			with timer("merge '%s'" % tag):
				tables = [font.get(tag, NotImplemented) for font in fonts]

				log.info("Merging '%s'.", tag)
				clazz = ttLib.getTableClass(tag)
				table = clazz(tag).merge(self, tables)
				# XXX Clean this up and use:  table = mergeObjects(tables)

				if table is not NotImplemented and table is not False:
					mega[tag] = table
					log.info("Merged '%s'.", tag)
				else:
					log.info("Dropped '%s'.", tag)

		del self.duplicateGlyphsPerFont
		del self.fonts

		self._postMerge(mega)

		return mega

	def _mergeGlyphOrders(self, glyphOrders):
		"""Modifies passed-in glyphOrders to reflect new glyph names.
		Returns glyphOrder for the merged font."""
		mega = {}
		for glyphOrder in glyphOrders:
			for i,glyphName in enumerate(glyphOrder):
				if glyphName in mega:
					n = mega[glyphName]
					while (glyphName + "#" + repr(n)) in mega:
						n += 1
					mega[glyphName] = n
					glyphName += "#" + repr(n)
					glyphOrder[i] = glyphName
				mega[glyphName] = 1
		return list(mega.keys())

	def _renameCFFCharStrings(self, glyphOrder, cffTable):
		"""Rename topDictIndex charStrings based on glyphOrder."""
		td = cffTable.cff.topDictIndex[0]
		charStrings = {}
		for i, v in enumerate(td.CharStrings.charStrings.values()):
			glyphName = glyphOrder[i]
			charStrings[glyphName] = v
		cffTable.cff.topDictIndex[0].CharStrings.charStrings = charStrings

	def mergeObjects(self, returnTable, logic, tables):
		# Right now we don't use self at all.  Will use in the future
		# for options and logging.

		allKeys = set.union(set(), *(vars(table).keys() for table in tables if table is not NotImplemented))
		for key in allKeys:
			try:
				mergeLogic = logic[key]
			except KeyError:
				try:
					mergeLogic = logic['*']
				except KeyError:
					raise Exception("Don't know how to merge key %s of class %s" %
							(key, returnTable.__class__.__name__))
			if mergeLogic is NotImplemented:
				continue
			value = mergeLogic(getattr(table, key, NotImplemented) for table in tables)
			if value is not NotImplemented:
				setattr(returnTable, key, value)

		return returnTable

	def _preMerge(self, font):

		# Map indices to references

		GDEF = font.get('GDEF')
		GSUB = font.get('GSUB')
		GPOS = font.get('GPOS')

		for t in [GSUB, GPOS]:
			if not t: continue

			if t.table.LookupList:
				lookupMap = {i:v for i,v in enumerate(t.table.LookupList.Lookup)}
				t.table.LookupList.mapLookups(lookupMap)
				t.table.FeatureList.mapLookups(lookupMap)

				if GDEF and GDEF.table.Version >= 0x00010002:
					markFilteringSetMap = {i:v for i,v in enumerate(GDEF.table.MarkGlyphSetsDef.Coverage)}
					t.table.LookupList.mapMarkFilteringSets(markFilteringSetMap)

			if t.table.FeatureList and t.table.ScriptList:
				featureMap = {i:v for i,v in enumerate(t.table.FeatureList.FeatureRecord)}
				t.table.ScriptList.mapFeatures(featureMap)

		# TODO FeatureParams nameIDs

	def _postMerge(self, font):

		# Map references back to indices

		GDEF = font.get('GDEF')
		GSUB = font.get('GSUB')
		GPOS = font.get('GPOS')

		for t in [GSUB, GPOS]:
			if not t: continue

			if t.table.FeatureList and t.table.ScriptList:

				# Collect unregistered (new) features.
				featureMap = _GregariousIdentityDict(t.table.FeatureList.FeatureRecord)
				t.table.ScriptList.mapFeatures(featureMap)

				# Record used features.
				featureMap = _AttendanceRecordingIdentityDict(t.table.FeatureList.FeatureRecord)
				t.table.ScriptList.mapFeatures(featureMap)
				usedIndices = featureMap.s

				# Remove unused features
				t.table.FeatureList.FeatureRecord = [f for i,f in enumerate(t.table.FeatureList.FeatureRecord) if i in usedIndices]

				# Map back to indices.
				featureMap = _NonhashableDict(t.table.FeatureList.FeatureRecord)
				t.table.ScriptList.mapFeatures(featureMap)

				t.table.FeatureList.FeatureCount = len(t.table.FeatureList.FeatureRecord)

			if t.table.LookupList:

				# Collect unregistered (new) lookups.
				lookupMap = _GregariousIdentityDict(t.table.LookupList.Lookup)
				t.table.FeatureList.mapLookups(lookupMap)
				t.table.LookupList.mapLookups(lookupMap)

				# Record used lookups.
				lookupMap = _AttendanceRecordingIdentityDict(t.table.LookupList.Lookup)
				t.table.FeatureList.mapLookups(lookupMap)
				t.table.LookupList.mapLookups(lookupMap)
				usedIndices = lookupMap.s

				# Remove unused lookups
				t.table.LookupList.Lookup = [l for i,l in enumerate(t.table.LookupList.Lookup) if i in usedIndices]

				# Map back to indices.
				lookupMap = _NonhashableDict(t.table.LookupList.Lookup)
				t.table.FeatureList.mapLookups(lookupMap)
				t.table.LookupList.mapLookups(lookupMap)

				t.table.LookupList.LookupCount = len(t.table.LookupList.Lookup)

				if GDEF and GDEF.table.Version >= 0x00010002:
					markFilteringSetMap = _NonhashableDict(GDEF.table.MarkGlyphSetsDef.Coverage)
					t.table.LookupList.mapMarkFilteringSets(markFilteringSetMap)


		# TODO FeatureParams nameIDs


__all__ = [
	'Options',
	'Merger',
	'main'
]

@timer("make one with everything (TOTAL TIME)")
def main(args=None):
	"""Merge multiple fonts into one"""
	from fontTools import configLogger

	if args is None:
		args = sys.argv[1:]

	options = Options()
	args = options.parse_opts(args, ignore_unknown=['output-file'])
	outfile = 'merged.ttf'
	fontfiles = []
	for g in args:
		if g.startswith('--output-file='):
			outfile = g[14:]
			continue
		fontfiles.append(g)

	if len(args) < 1:
		print("usage: pyftmerge font...", file=sys.stderr)
		return 1

	configLogger(level=logging.INFO if options.verbose else logging.WARNING)
	if options.timing:
		timer.logger.setLevel(logging.DEBUG)
	else:
		timer.logger.disabled = True

	merger = Merger(options=options)
	font = merger.merge(fontfiles)
	with timer("compile and save font"):
		font.save(outfile)


if __name__ == "__main__":
	sys.exit(main())
