# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Google Author(s): Behdad Esfahbod

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.textTools import safeEval
from . import DefaultTable
import operator
import struct


class table_C_O_L_R_(DefaultTable.DefaultTable):

	""" This table is structured so that you can treat it like a dictionary keyed by glyph name.
	ttFont['COLR'][<glyphName>] will return the color layers for any glyph
	ttFont['COLR'][<glyphName>] = <value> will set the color layers for any glyph.
	"""

	def decompile(self, data, ttFont):
		self.getGlyphName = ttFont.getGlyphName # for use in get/set item functions, for access by GID
		self.version, numBaseGlyphRecords, offsetBaseGlyphRecord, offsetLayerRecord, numLayerRecords = struct.unpack(">HHLLH", data[:14])
		assert (self.version == 0), "Version of COLR table is higher than I know how to handle"
		glyphOrder = ttFont.getGlyphOrder()
		gids = []
		layerLists = []
		glyphPos = offsetBaseGlyphRecord
		for i in range(numBaseGlyphRecords):
			gid, firstLayerIndex, numLayers = struct.unpack(">HHH", data[glyphPos:glyphPos+6])
			glyphPos += 6
			gids.append(gid)
			assert (firstLayerIndex + numLayers <= numLayerRecords)
			layerPos = offsetLayerRecord + firstLayerIndex * 4
			layers = []
			for j in range(numLayers):
				layerGid, colorID = struct.unpack(">HH", data[layerPos:layerPos+4])
				try:
					layerName = glyphOrder[layerGid]
				except IndexError:
					layerName = self.getGlyphName(layerGid)
				layerPos += 4
				layers.append(LayerRecord(layerName, colorID))
			layerLists.append(layers)

		self.ColorLayers = colorLayerLists = {}
		try:
			names = list(map(operator.getitem, [glyphOrder]*numBaseGlyphRecords, gids))
		except IndexError:
			getGlyphName = self.getGlyphName
			names = list(map(getGlyphName, gids ))

		list(map(operator.setitem, [colorLayerLists]*numBaseGlyphRecords, names, layerLists))

	def compile(self, ttFont):
		ordered = []
		ttFont.getReverseGlyphMap(rebuild=True)
		glyphNames = self.ColorLayers.keys()
		for glyphName in glyphNames:
			try:
				gid = ttFont.getGlyphID(glyphName)
			except:
				assert 0, "COLR table contains a glyph name not in ttFont.getGlyphNames(): " + str(glyphName)
			ordered.append([gid, glyphName, self.ColorLayers[glyphName]])
		ordered.sort()

		glyphMap = []
		layerMap = []
		for (gid, glyphName, layers) in ordered:
			glyphMap.append(struct.pack(">HHH", gid, len(layerMap), len(layers)))
			for layer in layers:
				layerMap.append(struct.pack(">HH", ttFont.getGlyphID(layer.name), layer.colorID))

		dataList = [struct.pack(">HHLLH", self.version, len(glyphMap), 14, 14+6*len(glyphMap), len(layerMap))]
		dataList.extend(glyphMap)
		dataList.extend(layerMap)
		data = bytesjoin(dataList)
		return data

	def toXML(self, writer, ttFont):
		writer.simpletag("version", value=self.version)
		writer.newline()
		ordered = []
		glyphNames = self.ColorLayers.keys()
		for glyphName in glyphNames:
			try:
				gid = ttFont.getGlyphID(glyphName)
			except:
				assert 0, "COLR table contains a glyph name not in ttFont.getGlyphNames(): " + str(glyphName)
			ordered.append([gid, glyphName, self.ColorLayers[glyphName]])
		ordered.sort()
		for entry in ordered:
			writer.begintag("ColorGlyph", name=entry[1])
			writer.newline()
			for layer in entry[2]:
				layer.toXML(writer, ttFont)
			writer.endtag("ColorGlyph")
			writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if not hasattr(self, "ColorLayers"):
			self.ColorLayers = {}
		self.getGlyphName = ttFont.getGlyphName # for use in get/set item functions, for access by GID
		if name == "ColorGlyph":
			glyphName = attrs["name"]
			for element in content:
				if isinstance(element, basestring):
					continue
			layers = []
			for element in content:
				if isinstance(element, basestring):
					continue
				layer = LayerRecord()
				layer.fromXML(element[0], element[1], element[2], ttFont)
				layers.append (layer)
			operator.setitem(self, glyphName, layers)
		elif "value" in attrs:
			setattr(self, name, safeEval(attrs["value"]))

	def __getitem__(self, glyphSelector):
		if isinstance(glyphSelector, int):
			# its a gid, convert to glyph name
			glyphSelector = self.getGlyphName(glyphSelector)

		if glyphSelector not in self.ColorLayers:
			return None

		return self.ColorLayers[glyphSelector]

	def __setitem__(self, glyphSelector, value):
		if isinstance(glyphSelector, int):
			# its a gid, convert to glyph name
			glyphSelector = self.getGlyphName(glyphSelector)

		if  value:
			self.ColorLayers[glyphSelector] = value
		elif glyphSelector in self.ColorLayers:
			del self.ColorLayers[glyphSelector]

	def __delitem__(self, glyphSelector):
		del self.ColorLayers[glyphSelector]

class LayerRecord(object):

	def __init__(self, name=None, colorID=None):
		self.name = name
		self.colorID = colorID

	def toXML(self, writer, ttFont):
		writer.simpletag("layer", name=self.name, colorID=self.colorID)
		writer.newline()

	def fromXML(self, eltname, attrs, content, ttFont):
		for (name, value) in attrs.items():
			if name == "name":
				if isinstance(value, int):
					value = ttFont.getGlyphName(value)
				setattr(self, name, value)
			else:
				setattr(self, name, safeEval(value))
