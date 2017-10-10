from __future__ import print_function, division, absolute_import
from numbers import Number
from fontTools.misc.py23 import *
from fontTools.misc.textTools import safeEval
from . import DefaultTable
import sys
import array

class table__c_v_t(DefaultTable.DefaultTable):

	def decompile(self, data, ttFont):
		values = array.array("h")
		values.fromstring(data)
		if sys.byteorder != "big":
			values.byteswap()
		self.values = values

	def compile(self, ttFont):
		values = self.values[:]
		if sys.byteorder != "big":
			values.byteswap()
		return values.tostring()

	def toXML(self, writer, ttFont):
		for i in range(len(self.values)):
			value = self.values[i]
			writer.simpletag("cv", value=value, index=i)
			writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if not hasattr(self, "values"):
			self.values = array.array("h")
		if name == "cv":
			index = safeEval(attrs["index"])
			value = safeEval(attrs["value"])
			for i in range(1 + index - len(self.values)):
				self.values.append(0)
			self.values[index] = value

	def __len__(self):
		return len(self.values)

	def __getitem__(self, index):
		return self.values[index]

	def __setitem__(self, index, value):
		self.values[index] = value

	def __delitem__(self, index):
		del self.values[index]


class CVTValues(object):
	""" This is used in varLib for calculating control value deltas"""

	def __init__(self, values):
		self.values = list(values)

	def __getitem__(self, index):
		return self.values[index]

	def __len__(self):
		return len(self.values)

	def __repr__(self):
		return u"CVTValues(%s)" % self.values

	def __isub__(self, other):
		if isinstance(other, CVTValues):
			assert len(self.values) == len(other)
			self.values = [self.values[i] - other.values[i] for i in range(len(self.values))]
			return self
		if isinstance(other, Number):
			self.values = [v - other for v in self.values]
			return self
		return NotImplemented

	def __mul__(self, other):
		if isinstance(other, Number):
			return CVTValues([v * other for v in self.values])
		return NotImplemented
