# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Google Author(s): Behdad Esfahbod, Roozbeh Pournader

from fontTools import ttLib
from fontTools.merge.base import *
from fontTools.merge.cmap import *
from fontTools.merge.layout import *
from fontTools.merge.options import *
from fontTools.merge.util import *
from fontTools.misc.loggingTools import Timer
from functools import reduce
import sys
import logging


log = logging.getLogger("fontTools.merge")
timer = Timer(logger=logging.getLogger(__name__+".timer"), level=logging.INFO)


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
		megaGlyphOrder = computeMegaGlyphOrder(self, glyphOrders)

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

		computeMegaCmap(self, [font['cmap'] for font in fonts])

		allTags = reduce(set.union, (list(font.keys()) for font in fonts), set())
		allTags.remove('GlyphOrder')

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
				featureMap = GregariousIdentityDict(t.table.FeatureList.FeatureRecord)
				t.table.ScriptList.mapFeatures(featureMap)

				# Record used features.
				featureMap = AttendanceRecordingIdentityDict(t.table.FeatureList.FeatureRecord)
				t.table.ScriptList.mapFeatures(featureMap)
				usedIndices = featureMap.s

				# Remove unused features
				t.table.FeatureList.FeatureRecord = [f for i,f in enumerate(t.table.FeatureList.FeatureRecord) if i in usedIndices]

				# Map back to indices.
				featureMap = NonhashableDict(t.table.FeatureList.FeatureRecord)
				t.table.ScriptList.mapFeatures(featureMap)

				t.table.FeatureList.FeatureCount = len(t.table.FeatureList.FeatureRecord)

			if t.table.LookupList:

				# Collect unregistered (new) lookups.
				lookupMap = GregariousIdentityDict(t.table.LookupList.Lookup)
				t.table.FeatureList.mapLookups(lookupMap)
				t.table.LookupList.mapLookups(lookupMap)

				# Record used lookups.
				lookupMap = AttendanceRecordingIdentityDict(t.table.LookupList.Lookup)
				t.table.FeatureList.mapLookups(lookupMap)
				t.table.LookupList.mapLookups(lookupMap)
				usedIndices = lookupMap.s

				# Remove unused lookups
				t.table.LookupList.Lookup = [l for i,l in enumerate(t.table.LookupList.Lookup) if i in usedIndices]

				# Map back to indices.
				lookupMap = NonhashableDict(t.table.LookupList.Lookup)
				t.table.FeatureList.mapLookups(lookupMap)
				t.table.LookupList.mapLookups(lookupMap)

				t.table.LookupList.LookupCount = len(t.table.LookupList.Lookup)

				if GDEF and GDEF.table.Version >= 0x00010002:
					markFilteringSetMap = NonhashableDict(GDEF.table.MarkGlyphSetsDef.Coverage)
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
