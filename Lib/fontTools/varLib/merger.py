"""
Merge OpenType Layout tables (GDEF / GPOS / GSUB).
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.DefaultTable import DefaultTable

def _add_method(*clazzes):
	"""Returns a decorator function that adds a new method to one or
	more classes."""
	def wrapper(method):
		done = []
		for clazz in clazzes:
			if clazz in done: continue # Support multiple names of a clazz
			done.append(clazz)
			assert method.__name__ not in clazz.__dict__, \
				"Oops, class '%s' has method '%s'." % (clazz.__name__, method.__name__)
			setattr(clazz, method.__name__, method)
		return None
	return wrapper

def mergeObjects(self, lst, merger):
	keys = vars(self).keys()
	assert all(vars(table).keys() == keys for table in lst)
	for key in keys:
		value = getattr(self, key)
		values = [getattr(table, key) for table in lst]
		mergeThings(value, values, merger)

def mergeLists(self, lst, merger):
	count = len(self)
	assert all(count == len(v) for v in lst), (count, [len(v) for v in lst])
	for value,values in zip(self, zip(*lst)):
		mergeThings(value, values, merger)

def mergeThings(self, lst, merger):
	clazz = type(self)
	assert all(type(item) == clazz for item in lst), lst
	mergerFunc = getattr(type(self), 'merge', None)
	if mergerFunc is None:
		if hasattr(self, '__dict__'):
			mergerFunc = mergeObjects
		elif isinstance(self, list):
			mergerFunc = mergeLists
		else:
			assert all(self == v for v in lst), lst
			return
	mergerFunc(self, lst, merger)

@_add_method(ot.Anchor)
def merge(self, lst, merger):
	XCoords = [a.XCoordinate for a in lst]
	YCoords = [a.YCoordinate for a in lst]
	model = merger.model
	location = merger.location
	self.XCoordinate = round(model.interpolateFromMasters(location, XCoords))
	self.YCoordinate = round(model.interpolateFromMasters(location, YCoords))

def merge_tables(font, merger, master_ttfs, axes, base_idx, tables):

	print("Merging OpenType Layout tables")
	for tag in tables:
		print('Merging', tag)
		mergeThings(font[tag], [m[tag] for m in master_ttfs], merger)
