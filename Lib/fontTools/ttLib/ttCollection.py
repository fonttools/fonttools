from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.ttLib.sfnt import readTTCHeader
import logging

log = logging.getLogger(__name__)


class TTCollection(object):

	"""Object representing a TrueType Collection / OpenType Collection.
	The main API is self.fonts being a list of TTFont instances.

	If shareTables is True, then different fonts in the collection
	might point to the same table object if the data for the table was
	the same in the font file.  Note, however, that this might result
	in suprises and incorrect behavior if the different fonts involved
	have different GlyphOrder.  Use only if you know what you are doing.
	"""

	def __init__(self, file=None, shareTables=False, **kwargs):
		fonts = self.fonts = []
		if file is None:
			return

		assert 'fontNumber' not in kwargs, kwargs

		if not hasattr(file, "read"):
			file = open(file, "rb")

		tableCache = {} if shareTables else None

		file.seek(0)
		sfntVersion = file.read(4)
		file.seek(0)
		if sfntVersion != b"ttcf":
			raise TTLibError("Not a Font Collection")

		from fontTools.ttLib import TTFont
		header = readTTCHeader(file)
		for i in range(header.numFonts):
			font = TTFont(file, fontNumber=i, _tableCache=tableCache, **kwargs)
			fonts.append(font)

	def __getitem__(self, item):
		return self.fonts[item]

	def __setitem__(self, item, value):
		self.fonts[item] = values

	def __delitem__(self, item):
		return self.fonts[item]

	def __len__(self):
		return len(self.fonts)

	def __iter__(self):
		return iter(self.fonts)
