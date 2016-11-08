"""
Merge OpenType Layout tables (GDEF / GPOS / GSUB).
"""
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.DefaultTable import DefaultTable

class Merger(object):

	mergers = None

	def __init__(self, font=None):
		self.font = font

	@classmethod
	def merger(celf, clazzes, attrs=(None,)):
		assert celf != Merger, 'Subclass Merger instead.'
		if celf.mergers is None:
			celf.mergers = {}
		if type(clazzes) == type:
			clazzes = (clazzes,)
		if type(attrs) == str:
			attrs = (attrs,)
		def wrapper(method):
			assert method.__name__ == 'merge'
			done = []
			for clazz in clazzes:
				if clazz in done: continue # Support multiple names of a clazz
				done.append(clazz)
				mergers = celf.mergers.setdefault(clazz, {})
				for attr in attrs:
					assert attr not in mergers, \
						"Oops, class '%s' has merge function for '%s' defined already." % (clazz.__name__, attr)
					mergers[attr] = method
			return None
		return wrapper

	def mergeObjects(self, out, lst, exclude=(), _default={}):
		keys = sorted(vars(out).keys())
		assert all(keys == sorted(vars(v).keys()) for v in lst), \
			(keys, [sorted(vars(v).keys()) for v in lst])
		mergers = self.mergers.get(type(out), _default)
		defaultMerger = mergers.get('*', self.__class__.mergeThings)
		try:
			for key in keys:
				if key in exclude: continue
				value = getattr(out, key)
				values = [getattr(table, key) for table in lst]
				mergerFunc = mergers.get(key, defaultMerger)
				mergerFunc(self, value, values)
		except Exception as e:
			e.args = e.args + ('.'+key,)
			raise

	def mergeLists(self, out, lst):
		count = len(out)
		assert all(count == len(v) for v in lst), (count, [len(v) for v in lst])
		for value,values in zip(out, zip(*lst)):
			self.mergeThings(value, values)

	def mergeThings(self, out, lst, _default={None:None}):
		clazz = type(out)
		try:
			assert all(type(item) == clazz for item in lst), (out, lst)
			mergerFunc = self.mergers.get(type(out), _default).get(None, None)
			if mergerFunc is not None:
				mergerFunc(self, out, lst)
			elif hasattr(out, '__dict__'):
				self.mergeObjects(out, lst)
			elif isinstance(out, list):
				self.mergeLists(out, lst)
			else:
				assert all(out == v for v in lst), (out, lst)
		except Exception as e:
			e.args = e.args + (clazz.__name__,)
			raise

def merge_tables(font, merger, master_ttfs, axes, base_idx, tables):

	for tag in tables:
		if tag not in font: continue
		print('Merging', tag)
		merger.mergeThings(font[tag], [m[tag] for m in master_ttfs])
