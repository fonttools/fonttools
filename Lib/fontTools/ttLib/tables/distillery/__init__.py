"""This module helps with distilling a set of objects (aka tables) linked together through
a set of object references (represented eventually by offsets) into a bytestream in a compact
and efficient manner.  This is useful for compiling tables like GSUB/GPOS/GDEF and other
tables represented in the otData.py module."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

from fibonacci_heap_mod import Fibonacci_heap


def sortMeOut(table):
	distillery = Distillery()
	return distillery.distill(table)

class ObjectSet(object):

	def __init__(self):
		self._s = set()
		self._d = dict()

	def add(self, obj):
		self._s.add(id(obj))
		self._d[id(obj)] = obj

	def remove(self, obj):
		self._s.remove(id(obj))
		del self._d[id(obj)]

	def issubset(self, other):
		assert type(other) == ObjectSet
		return self._s.issubset(other._s)

	def __iter__(self):
		return iter(self._d.values())

	def __contains__(self, obj):
		return id(obj) in self._s

	def __bool__(self):
		return bool(self._s)

	__nonzero__ = __bool__

	def __len__(self):
		return len(self._s)

	def __repr__(self):
		return repr(self._s)

class Distillery(object):

	def __init__(self):
		self.packedS = ObjectSet()
		self.readyQ = Fibonacci_heap()
		self.readyS = ObjectSet()
		#self.awaitQ = Fibonacci_heap()
		#self.awaitS = ObjectSet()

	def _itemPriority(self, item):
		leashLen = (65536)**2 if item.offsetSize == 4 else 65536
		packedParentsPos = [p.pos for p in item.parents if p in self.packedS]
		leashStart = min(packedParentsPos) if packedParentsPos else (65536)**2 * 2
		itemLen = len(item)
		return (leashStart + leashLen + itemLen)# / 4

	def _itemIsReady(self, item):
		return item.parents.issubset(self.packedS)

	def _readyEnqueue(self, item):
		item.node = self.readyQ.enqueue(item, self._itemPriority(item))
		self.readyS.add(item)

	#def _awaitEnqueue(self, item):
	#	item.node = self.awaitQ.enqueue(item, self._itemPriority(item))
	#	self.awaitS.add(item)

	#def _awaitDelete(self, item):
	#	assert item in self.awaitS
	#	self.awaitS.remove(item)
	#	self.awaitQ.delete(item.node)
	#	del item.node

	def _setParents(self, root, done):
		done.add(root)
		root.parents = ObjectSet()
		for item in root.items:
			if not hasattr(item, 'getData'):
				continue
			if item not in done:
				self._setParents(item, done)
			item.parents.add(root)

	def distill(self, root):
		self._setParents(root, ObjectSet())

		out = []

		self._readyEnqueue(root)

		pos = 0
		while self.readyQ:
			entry = self.readyQ.dequeue_min()
			obj = entry.get_value()
			self.readyS.remove(obj)
			prio = entry.get_priority()
			del entry
			del obj.node

			out.append(obj)
			obj.pos = pos
			self.packedS.add(obj)

			for item in obj.items:
				if not hasattr(item, "getData"):
					continue

				assert item not in self.packedS
				if item in self.readyS:
					continue

				if self._itemIsReady(item):
					#if hasattr(item, 'node'):
					#	self._awaitDelete(item)

					self._readyEnqueue(item)
				else:
					pass
					#if hasattr(item, 'node'):
					#	self.awaitQ.decrease_key(item.node, self._itemPriority(item))
					#else:
					#	self._awaitEnqueue(item)

			pos += len(obj)

		#assert not self.awaitS, self.awaitS
		#assert not self.awaitQ, self.awaitQ
		assert not self.readyS, self.readyS
		assert not self.readyQ, self.readyQ

		return out
