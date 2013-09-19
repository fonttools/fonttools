# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Google Author(s): Behdad Esfahbod

"""Font merger.
"""

import sys

import fontTools
from fontTools import misc, ttLib, cffLib

def _add_method(*clazzes):
  """Returns a decorator function that adds a new method to one or
  more classes."""
  def wrapper(method):
    for clazz in clazzes:
      assert clazz.__name__ != 'DefaultTable', 'Oops, table class not found.'
      assert not hasattr(clazz, method.func_name), \
          "Oops, class '%s' has method '%s'." % (clazz.__name__,
                                                 method.func_name)
      setattr(clazz, method.func_name, method)
    return None
  return wrapper


@_add_method(fontTools.ttLib.getTableClass('maxp'))
def merge(self, tables, fonts):
	# TODO When we correctly merge hinting data, update these values:
	# maxFunctionDefs, maxInstructionDefs, maxSizeOfInstructions
	# TODO Assumes that all tables have format 1.0; safe assumption.
	for key in set(sum((vars(table).keys() for table in tables), [])):
			setattr(self, key, max(getattr(table, key) for table in tables))
	return True

@_add_method(fontTools.ttLib.getTableClass('hhea'))
def merge(self, tables, fonts):
	# TODO Check that ascent, descent, slope, etc are the same.
	minMembers = ['descent', 'minLeftSideBearing', 'minRightSideBearing']
	# Negate some members
	for key in minMembers:
		for table in tables:
			setattr(table, key, -getattr(table, key))
	# Get max over members
	for key in set(sum((vars(table).keys() for table in tables), [])):
		setattr(self, key, max(getattr(table, key) for table in tables))
	# Negate them back
	for key in minMembers:
		for table in tables:
			setattr(table, key, -getattr(table, key))
		setattr(self, key, -getattr(self, key))
	return True

@_add_method(fontTools.ttLib.getTableClass('vmtx'),
             fontTools.ttLib.getTableClass('hmtx'))
def merge(self, tables, fonts):
	self.metrics = {}
	for table in tables:
		self.metrics.update(table.metrics)
	return True

@_add_method(fontTools.ttLib.getTableClass('loca'))
def merge(self, tables, fonts):
	return False # Will be computed automatically

class Merger:

	def __init__(self, fontfiles):
		self.fontfiles = fontfiles

	def merge(self):

		mega = ttLib.TTFont()

		#
		# Settle on a mega glyph order.
		#
		fonts = [ttLib.TTFont(fontfile) for fontfile in self.fontfiles]
		glyphOrders = [font.getGlyphOrder() for font in fonts]
		megaGlyphOrder = self._mergeGlyphOrders(glyphOrders)
		# Reload fonts and set new glyph names on them.
		# TODO Is it necessary to reload font?  I think it is.  At least
		# it's safer, in case tables were loaded to provide glyph names.
		fonts = [ttLib.TTFont(fontfile) for fontfile in self.fontfiles]
		map(ttLib.TTFont.setGlyphOrder, fonts, glyphOrders)
		mega.setGlyphOrder(megaGlyphOrder)

		cmaps = [self._get_cmap(font) for font in fonts]

		allTags = set(sum([font.keys() for font in fonts], []))
		allTags.remove('GlyphOrder')
		for tag in allTags:
			clazz = ttLib.getTableClass(tag)

			if not hasattr(clazz, 'merge'):
				print "Don't know how to merge '%s', dropped." % tag
				continue

			# TODO For now assume all fonts have the same tables.
			tables = [font[tag] for font in fonts]
			table = clazz(tag)
			if table.merge (tables, fonts):
				mega[tag] = table
				print "Merged '%s'." % tag
			else:
				print "Dropped '%s'.  No need to merge explicitly." % tag

		return mega

	def _get_cmap(self, font):
		cmap = font['cmap']
		tables = [t for t in cmap.tables
			    if t.platformID == 3 and t.platEncID in [1, 10]]
		# XXX Handle format=14
		assert len(tables)
		# Pick table that has largest coverage
		table = max(tables, key=lambda t: len(t.cmap))
		return table

	def _mergeGlyphOrders(self, glyphOrders):
		"""Modifies passed-in glyphOrders to reflect new glyph names."""
		# Simply append font index to the glyph name for now.
		mega = []
		for n,glyphOrder in enumerate(glyphOrders):
			for i,glyphName in enumerate(glyphOrder):
				glyphName += "#" + `n`
				glyphOrder[i] = glyphName
				mega.append(glyphName)
		return mega

def main(args):
	if len(args) < 1:
		print >>sys.stderr, "usage: pyftmerge font..."
		sys.exit(1)
	merger = Merger(args)
	font = merger.merge()
	outfile = 'merged.ttf'
	font.save(outfile)

if __name__ == "__main__":
	main(sys.argv[1:])
