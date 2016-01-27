from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval, num2binary, binary2num
from fontTools.misc.timeTools import timestampFromString, timestampToString, timestampNow
from fontTools.misc.timeTools import epoch_diff as mac_epoch_diff # For backward compat
from . import DefaultTable
import warnings


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
			warnings.warn("extra bytes at the end of 'head' table")
			#assert rest == "\0\0"

		# For timestamp fields, ignore the top four bytes.  Some fonts have
		# bogus values there.  Since till 2038 those bytes only can be zero,
		# ignore them.
		#
		# https://github.com/behdad/fonttools/issues/99#issuecomment-66776810
		for stamp in 'created', 'modified':
			value = getattr(self, stamp)
			if value > 0xFFFFFFFF:
				warnings.warn("'%s' timestamp out of range; ignoring top bytes" % stamp)
				value &= 0xFFFFFFFF
				setattr(self, stamp, value)
			if value < 0x7C259DC0: # January 1, 1970 00:00:00
				warnings.warn("'%s' timestamp seems very low; regarding as unix timestamp" % stamp)
				value += 0x7C259DC0
				setattr(self, stamp, value)

	def compile(self, ttFont):
		if ttFont.recalcTimestamp:
			self.modified = timestampNow()
		data = sstruct.pack(headFormat, self)
		return data

	def toXML(self, writer, ttFont):
		writer.comment("Most of this table will be recalculated by the compiler")
		writer.newline()
		formatstring, names, fixes = sstruct.getformat(headFormat)
		for name in names:
			value = getattr(self, name)
			if name in ("created", "modified"):
				value = timestampToString(value)
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
			value = timestampFromString(value)
		elif name in ("macStyle", "flags"):
			value = binary2num(value)
		else:
			value = safeEval(value)
		setattr(self, name, value)
