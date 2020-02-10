# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Google Author(s): Behdad Esfahbod

from fontTools.misc.py23 import *
from fontTools.misc.textTools import safeEval
from . import DefaultTable


class table_C_O_L_R_(DefaultTable.DefaultTable):

	""" This table is structured so that you can treat it like a dictionary keyed by glyph name.
	ttFont['COLR'][<glyphName>] will return the color layers for any glyph
	ttFont['COLR'][<glyphName>] = <value> will set the color layers for any glyph.
	"""

	def decompile(self, data, ttFont):
		from .otBase import OTTableReader
		from . import otTables

		reader = OTTableReader(data, tableTag=self.tableTag)
		tableClass = getattr(otTables, self.tableTag)
		table = tableClass()
		table.decompile(reader, ttFont)

		self.getGlyphName = ttFont.getGlyphName # for use in get/set item functions, for access by GID
		self.version = table.Version
		assert (self.version == 0), "Version of COLR table is higher than I know how to handle"

		baseGlyphNames = []
		layerLists = []
		layerRecords = table.LayerRecordArray.LayerRecord
		numLayerRecords = len(layerRecords)
		for baseRec in table.BaseGlyphRecordArray.BaseGlyphRecord:
			baseGlyph = baseRec.BaseGlyph
			firstLayerIndex = baseRec.FirstLayerIndex
			numLayers = baseRec.NumLayers
			baseGlyphNames.append(baseGlyph)
			assert (firstLayerIndex + numLayers <= numLayerRecords)
			layers = []
			for i in range(firstLayerIndex, firstLayerIndex+numLayers):
				layerRec = layerRecords[i]
				layers.append(LayerRecord(layerRec.LayerGlyph, layerRec.PaletteIndex))
			layerLists.append(layers)

		self.ColorLayers = colorLayerLists = {}
		for name, layerList in zip(baseGlyphNames, layerLists):
			colorLayerLists[name] = layerList

	def compile(self, ttFont):
		from .otBase import OTTableWriter
		from . import otTables

		ttFont.getReverseGlyphMap(rebuild=True)

		tableClass = getattr(otTables, self.tableTag)
		table = tableClass()

		table.Version = self.version

		table.BaseGlyphRecordArray = otTables.BaseGlyphRecordArray()
		table.BaseGlyphRecordArray.BaseGlyphRecord = baseGlyphRecords = []
		table.LayerRecordArray = otTables.LayerRecordArray()
		table.LayerRecordArray.LayerRecord = layerRecords = []

		for baseGlyph in sorted(self.ColorLayers.keys(), key=ttFont.getGlyphID):
			layers = self.ColorLayers[baseGlyph]

			baseRec = otTables.BaseGlyphRecord()
			baseRec.BaseGlyph = baseGlyph
			baseRec.FirstLayerIndex = len(layerRecords)
			baseRec.NumLayers = len(layers)
			baseGlyphRecords.append(baseRec)

			for layer in layers:
				layerRec = otTables.LayerRecord()
				layerRec.LayerGlyph = layer.name
				layerRec.PaletteIndex = layer.colorID
				layerRecords.append(layerRec)

		writer = OTTableWriter(tableTag=self.tableTag)
		table.compile(writer, ttFont)
		return writer.getAllData()

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
			self[glyphName] = layers
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
