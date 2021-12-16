# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Google Author(s): Behdad Esfahbod, Roozbeh Pournader

from fontTools.misc.timeTools import timestampNow
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from functools import reduce
import operator
import logging


log = logging.getLogger("fontTools.merge")

def add_method(*clazzes, **kwargs):
	"""Returns a decorator function that adds a new method to one or
	more classes."""
	allowDefault = kwargs.get('allowDefaultTable', False)
	def wrapper(method):
		done = []
		for clazz in clazzes:
			if clazz in done: continue # Support multiple names of a clazz
			done.append(clazz)
			assert allowDefault or clazz != DefaultTable, 'Oops, table class not found.'
			assert method.__name__ not in clazz.__dict__, \
				"Oops, class '%s' has method '%s'." % (clazz.__name__, method.__name__)
			setattr(clazz, method.__name__, method)
		return None
	return wrapper

# General utility functions for merging values from different fonts

def equal(lst):
	lst = list(lst)
	t = iter(lst)
	first = next(t)
	assert all(item == first for item in t), "Expected all items to be equal: %s" % lst
	return first

def first(lst):
	return next(iter(lst))

def recalculate(lst):
	return NotImplemented

def current_time(lst):
	return timestampNow()

def bitwise_and(lst):
	return reduce(operator.and_, lst)

def bitwise_or(lst):
	return reduce(operator.or_, lst)

def avg_int(lst):
	lst = list(lst)
	return sum(lst) // len(lst)

def onlyExisting(func):
	"""Returns a filter func that when called with a list,
	only calls func on the non-NotImplemented items of the list,
	and only so if there's at least one item remaining.
	Otherwise returns NotImplemented."""

	def wrapper(lst):
		items = [item for item in lst if item is not NotImplemented]
		return func(items) if items else NotImplemented

	return wrapper

def sumLists(lst):
	l = []
	for item in lst:
		l.extend(item)
	return l

def sumDicts(lst):
	d = {}
	for item in lst:
		d.update(item)
	return d

def mergeObjects(lst):
	lst = [item for item in lst if item is not NotImplemented]
	if not lst:
		return NotImplemented
	lst = [item for item in lst if item is not None]
	if not lst:
		return None

	clazz = lst[0].__class__
	assert all(type(item) == clazz for item in lst), lst

	logic = clazz.mergeMap
	returnTable = clazz()
	returnDict = {}

	allKeys = set.union(set(), *(vars(table).keys() for table in lst))
	for key in allKeys:
		try:
			mergeLogic = logic[key]
		except KeyError:
			try:
				mergeLogic = logic['*']
			except KeyError:
				raise Exception("Don't know how to merge key %s of class %s" %
						(key, clazz.__name__))
		if mergeLogic is NotImplemented:
			continue
		value = mergeLogic(getattr(table, key, NotImplemented) for table in lst)
		if value is not NotImplemented:
			returnDict[key] = value

	returnTable.__dict__ = returnDict

	return returnTable

def mergeBits(bitmap):

	def wrapper(lst):
		lst = list(lst)
		returnValue = 0
		for bitNumber in range(bitmap['size']):
			try:
				mergeLogic = bitmap[bitNumber]
			except KeyError:
				try:
					mergeLogic = bitmap['*']
				except KeyError:
					raise Exception("Don't know how to merge bit %s" % bitNumber)
			shiftedBit = 1 << bitNumber
			mergedValue = mergeLogic(bool(item & shiftedBit) for item in lst)
			returnValue |= mergedValue << bitNumber
		return returnValue

	return wrapper


@add_method(DefaultTable, allowDefaultTable=True)
def merge(self, m, tables):
	if not hasattr(self, 'mergeMap'):
		log.info("Don't know how to merge '%s'.", self.tableTag)
		return NotImplemented

	logic = self.mergeMap

	if isinstance(logic, dict):
		return m.mergeObjects(self, self.mergeMap, tables)
	else:
		return logic(tables)


class AttendanceRecordingIdentityDict(object):
	"""A dictionary-like object that records indices of items actually accessed
	from a list."""

	def __init__(self, lst):
		self.l = lst
		self.d = {id(v):i for i,v in enumerate(lst)}
		self.s = set()

	def __getitem__(self, v):
		self.s.add(self.d[id(v)])
		return v

class GregariousIdentityDict(object):
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

class NonhashableDict(object):
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

