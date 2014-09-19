from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import readHex
import struct


sbixBitmapHeaderFormat = """
	>
	usReserved1:     H    # 00 00
	usReserved2:     H    #       00 00
	imageFormatTag:  4s   # e.g. "png "
"""

sbixBitmapHeaderFormatSize = sstruct.calcsize(sbixBitmapHeaderFormat)


class Bitmap(object):
	def __init__(self, glyphName=None, referenceGlyphName=None, usReserved1=0, usReserved2=0, imageFormatTag=None, imageData=None, rawdata=None, gid=0):
		self.gid = gid
		self.glyphName = glyphName
		self.referenceGlyphName = referenceGlyphName
		self.usReserved1 = usReserved1
		self.usReserved2 = usReserved2
		self.rawdata = rawdata
		self.imageFormatTag = imageFormatTag
		self.imageData = imageData

	def decompile(self, ttFont):
		self.glyphName = ttFont.getGlyphName(self.gid)
		if self.rawdata is None:
			from fontTools import ttLib
			raise ttLib.TTLibError("No table data to decompile")
		if len(self.rawdata) > 0:
			if len(self.rawdata) < sbixBitmapHeaderFormatSize:
				from fontTools import ttLib
				#print "Bitmap %i header too short: Expected %x, got %x." % (self.gid, sbixBitmapHeaderFormatSize, len(self.rawdata))
				raise ttLib.TTLibError("Bitmap header too short.")

			sstruct.unpack(sbixBitmapHeaderFormat, self.rawdata[:sbixBitmapHeaderFormatSize], self)

			if self.imageFormatTag == "dupe":
				# bitmap is a reference to another glyph's bitmap
				gid, = struct.unpack(">H", self.rawdata[sbixBitmapHeaderFormatSize:])
				self.referenceGlyphName = ttFont.getGlyphName(gid)
			else:
				self.imageData = self.rawdata[sbixBitmapHeaderFormatSize:]
				self.referenceGlyphName = None
		# clean up
		del self.rawdata
		del self.gid

	def compile(self, ttFont):
		if self.glyphName is None:
			from fontTools import ttLib
			raise ttLib.TTLibError("Can't compile bitmap without glyph name")
			# TODO: if ttFont has no maxp, cmap etc., ignore glyph names and compile by index?
			# (needed if you just want to compile the sbix table on its own)
		self.gid = struct.pack(">H", ttFont.getGlyphID(self.glyphName))
		if self.imageFormatTag is None:
			self.rawdata = ""
		else:
			self.rawdata = sstruct.pack(sbixBitmapHeaderFormat, self) + self.imageData

	def toXML(self, xmlWriter, ttFont):
		if self.imageFormatTag == None:
			# TODO: ignore empty bitmaps?
			# a bitmap entry is required for each glyph,
			# but empty ones can be calculated at compile time
			xmlWriter.simpletag("bitmap", glyphname=self.glyphName)
			xmlWriter.newline()
			return
		xmlWriter.begintag("bitmap", format=self.imageFormatTag, glyphname=self.glyphName)
		xmlWriter.newline()
		#xmlWriter.simpletag("usReserved1", value=self.usReserved1)
		#xmlWriter.newline()
		#xmlWriter.simpletag("usReserved2", value=self.usReserved2)
		#xmlWriter.newline()
		if self.imageFormatTag == "dupe":
			# format == "dupe" is apparently a reference to another glyph id.
			xmlWriter.simpletag("ref", glyphname=self.referenceGlyphName)
		else:
			xmlWriter.begintag("hexdata")
			xmlWriter.newline()
			xmlWriter.dumphex(self.imageData)
			xmlWriter.endtag("hexdata")
		xmlWriter.newline()
		xmlWriter.endtag("bitmap")
		xmlWriter.newline()

	def fromXML(self, name, attrs, content, ttFont):
		#if name in ["usReserved1", "usReserved2"]:
		#	setattr(self, name, int(attrs["value"]))
		#elif
		if name == "ref":
			# bitmap is a "dupe", i.e. a reference to another bitmap.
			# in this case imageData contains the glyph id of the reference glyph
			# get glyph id from glyphname
			self.imageData = struct.pack(">H", ttFont.getGlyphID(attrs["glyphname"]))
		elif name == "hexdata":
			self.imageData = readHex(content)
		else:
			from fontTools import ttLib
			raise ttLib.TTLibError("can't handle '%s' element" % name)
