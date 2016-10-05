"""
Merge OpenType Layout tables (GDEF / GPOS / GSUB).
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.DefaultTable import DefaultTable

class Merger(object):

	mergers = None

	@classmethod
	def merger(celf, *clazzes):
		assert celf != Merger, 'Subclass Merger instead.'
		if celf.mergers is None:
			celf.mergers = {}
		def wrapper(method):
			assert method.__name__ == 'merge'
			done = []
			for clazz in clazzes:
				if clazz in done: continue # Support multiple names of a clazz
				done.append(clazz)
				assert clazz not in celf.mergers, \
					"Oops, class '%s' has merge function defined already." % (clazz.__name__)
				celf.mergers[clazz] = method
			return None
		return wrapper

	def mergeObjects(self, out, lst):
		keys = vars(out).keys()
		assert all(vars(table).keys() == keys for table in lst)
		try:
			for key in keys:
				value = getattr(out, key)
				values = [getattr(table, key) for table in lst]
				self.mergeThings(value, values)
		except Exception as e:
			e.args = e.args + ('.'+key,)
			raise

	def mergeLists(self, out, lst):
		count = len(out)
		assert all(count == len(v) for v in lst), (count, [len(v) for v in lst])
		for value,values in zip(out, zip(*lst)):
			self.mergeThings(value, values)

	def mergeThings(self, out, lst):
		clazz = type(out)
		try:
			assert all(type(item) == clazz for item in lst), lst
			mergerFunc = self.mergers.get(type(out), None)
			if mergerFunc is not None:
				mergerFunc(self, out, lst)
			elif hasattr(out, '__dict__'):
				self.mergeObjects(out, lst)
			elif isinstance(out, list):
				self.mergeLists(out, lst)
			else:
				assert all(out == v for v in lst), lst
		except Exception as e:
			e.args = e.args + (clazz.__name__,)
			raise

def merge_tables(font, merger, master_ttfs, axes, base_idx, tables):

	for tag in tables:
		print('Merging', tag)
		merger.mergeThings(font[tag], [m[tag] for m in master_ttfs])
