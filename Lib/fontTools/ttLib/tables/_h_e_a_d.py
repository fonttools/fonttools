from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval, num2binary, binary2num
from . import DefaultTable
import time
import calendar


headFormat = """
		>	# big endian
		tableVersion:       16.16F
		fontRevision:       16.16F
		checkSumAdjustment: I
		magicNumber:        I
		flags:              H
		unitsPerEm:         H
		created:            Q
		modified:           Q
		xMin:               h
		yMin:               h
		xMax:               h
		yMax:               h
		macStyle:           H
		lowestRecPPEM:      H
		fontDirectionHint:  h
		indexToLocFormat:   h
		glyphDataFormat:    h
"""

class table__h_e_a_d(DefaultTable.DefaultTable):
	
	dependencies = ['maxp', 'loca']
	
	def decompile(self, data, ttFont):
		dummy, rest = sstruct.unpack2(headFormat, data, self)
		if rest:
			# this is quite illegal, but there seem to be fonts out there that do this
			assert rest == "\0\0"
	
	def compile(self, ttFont):
		if ttFont.recalcTimestamp:
			self.modified = int(time.time() - mac_epoch_diff)
		data = sstruct.pack(headFormat, self)
		return data
	
	def toXML(self, writer, ttFont):
		writer.comment("Most of this table will be recalculated by the compiler")
		writer.newline()
		formatstring, names, fixes = sstruct.getformat(headFormat)
		for name in names:
			value = getattr(self, name)
			if name in ("created", "modified"):
				try:
					value = time.asctime(time.gmtime(max(0, value + mac_epoch_diff)))
				except ValueError:
					value = time.asctime(time.gmtime(0))
			if name in ("magicNumber", "checkSumAdjustment"):
				if value < 0:
					value = value + 0x100000000
				value = hex(value)
				if value[-1:] == "L":
					value = value[:-1]
			elif name in ("macStyle", "flags"):
				value = num2binary(value, 16)
			writer.simpletag(name, value=value)
			writer.newline()
	
	def fromXML(self, name, attrs, content, ttFont):
		value = attrs["value"]
		if name in ("created", "modified"):
			value = calendar.timegm(time.strptime(value)) - mac_epoch_diff
		elif name in ("macStyle", "flags"):
			value = binary2num(value)
		else:
			value = safeEval(value)
		setattr(self, name, value)


# Difference between the original Mac epoch (1904) to the epoch on this machine.
mac_epoch_diff = calendar.timegm((1904, 1, 1, 0, 0, 0, 0, 0, 0))
