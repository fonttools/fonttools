import struct, sstruct
import string
import types


# FontRec header
nfntHeaderFormat = """
	>  # big endian
	fontType:    h     # font type
	firstChar:   h     # ASCII code of first character
	lastChar:    h     # ASCII code of last character
	widMax:      h     # maximum character width
	kernMax:     h     # negative of maximum character kern
	nDescent:    h     # negative of descent
	fRectWidth:  h     # width of font rectangle
	fRectHeight: h     # height of font rectangle
	owTLoc:      H     # offset to offset/width table (in words from _this_ point)
	ascent:      h     # ascent
	descent:     h     # descent
	leading:     h     # leading
	rowWords:    h     # row width of bit image / 2
"""
headerSize = sstruct.calcsize(nfntHeaderFormat)
assert headerSize == 26


class NFNT:
	
	def __init__(self, data=None):
		if data is not None:
			self.decompile(data)
	
	def decompile(self, data):
		# header; FontRec
		sstruct.unpack(nfntHeaderFormat, data[:headerSize], self)
		
		#assert self.fRectHeight == (self.ascent + self.descent)
		
		# rest
		tableSize = 2 * (self.lastChar - self.firstChar + 3)
		bitmapSize = 2 * self.rowWords * self.fRectHeight
		
		self.bits = data[headerSize:headerSize + bitmapSize]
		
		# XXX deal with self.nDescent being a positive number
		assert (headerSize + bitmapSize + tableSize - 16) / 2 == self.owTLoc  # ugh...
		
		locTable = data[headerSize + bitmapSize:headerSize + bitmapSize + tableSize]
		if len(locTable) <> tableSize:
			raise ValueError, 'invalid NFNT format'
		
		owTable = data[headerSize + bitmapSize + tableSize:headerSize + bitmapSize + 2 * tableSize]
		if len(owTable) <> tableSize:
			raise ValueError, 'invalid NFNT format'
		
		# fill tables
		self.offsetTable = []
		self.widthTable = []
		self.locTable = []
		for i in range(0, tableSize, 2):
			self.offsetTable.append(ord(owTable[i]))
			self.widthTable.append(ord(owTable[i+1]))
			loc, = struct.unpack("h", locTable[i:i+2])
			self.locTable.append(loc)
	
	def compile(self):
		header = sstruct.pack(nfntHeaderFormat, self)
		nEntries = len(self.widthTable)
		owTable = [None] * nEntries
		locTable = [None] * nEntries
		for i in range(nEntries):
			owTable[i] = chr(self.offsetTable[i]) + chr(self.widthTable[i])
			locTable[i] = struct.pack("h", self.locTable[i])
		owTable = string.join(owTable, "")
		locTable = string.join(locTable, "")
		assert len(locTable) == len(owTable) == 2 * (self.lastChar - self.firstChar + 3)
		return header + self.bits + locTable + owTable
	
	def unpackGlyphs(self):
		import numpy
		nGlyphs = len(self.locTable) - 1
		self.glyphs = [None] * nGlyphs
		
		rowBytes = self.rowWords * 2
		imageWidth = self.rowWords * 16
		imageHeight = self.fRectHeight
		bits = self.bits
		bitImage = numpy.zeros((imageWidth, imageHeight), numpy.int8)
		
		for y in range(imageHeight):
			for xByte in range(rowBytes):
				byte = bits[y * rowBytes + xByte]
				for xBit in range(8):
					x = 8 * xByte + xBit
					bit = (ord(byte) >> (7 - xBit)) & 0x01
					bitImage[x, y] = bit
		
		for i in range(nGlyphs):
			width = self.widthTable[i]
			offset = self.offsetTable[i]
			if width == 255 and offset == 255:
				self.glyphs[i] = None
			else:
				imageL = self.locTable[i]
				imageR = self.locTable[i+1]
				imageWidth = imageR - imageL
				offset = offset + self.kernMax
				self.glyphs[i] = glyph = Glyph(width, offset, bitImage[imageL:imageR])
	
	def packGlyphs(self):
		import numpy
		imageWidth = 0
		kernMax = 0
		imageHeight = None
		widMax = 0
		fRectWidth = 0
		for glyph in self.glyphs:
			if glyph is None:
				continue
			if imageHeight is None:
				imageHeight = glyph.pixels.shape[1]
			else:
				assert imageHeight == glyph.pixels.shape[1]
			imageWidth = imageWidth + glyph.pixels.shape[0]
			kernMax = min(kernMax, glyph.offset)
			widMax = max(widMax, glyph.width)
			fRectWidth = max(fRectWidth, glyph.pixels.shape[0] + glyph.offset)
		
		fRectWidth = fRectWidth - kernMax
		imageWidth = 16 * ((imageWidth - 1) / 16 + 1)
		rowBytes = imageWidth / 8
		rowWords = rowBytes / 2
		bitImage = numpy.zeros((imageWidth, imageHeight), numpy.int8)
		locTable = []
		widthTable = []
		offsetTable = []
		loc = 0
		for glyph in self.glyphs:
			locTable.append(loc)
			if glyph is None:
				widthTable.append(255)
				offsetTable.append(255)
				continue
			widthTable.append(glyph.width)
			offsetTable.append(glyph.offset - kernMax)
			imageWidth = glyph.pixels.shape[0]
			bitImage[loc:loc+imageWidth] = glyph.pixels
			loc = loc + imageWidth
		
		locTable.append(loc)
		widthTable.append(255)
		offsetTable.append(255)
		
		bits = []
		for y in range(imageHeight):
			for xByte in range(rowBytes):
				byte = 0
				for x in range(8):
					byte = byte | ((bitImage[8 * xByte + x, y] & 0x01) << (7 - x))
				bits.append(chr(byte))
		bits = string.join(bits, "")
		
		# assign values
		self.fontType = 0x9000
		self.lastChar = self.firstChar + len(self.glyphs) - 2
		self.widMax = widMax
		self.kernMax = kernMax
		self.descent = imageHeight - self.ascent
		self.nDescent = -self.descent
		self.fRectWidth = fRectWidth
		self.fRectHeight = imageHeight
		self.rowWords = rowWords
		
		tableSize = 2 * (self.lastChar - self.firstChar + 3)
		self.owTLoc = (headerSize + len(bits) + tableSize - 16) / 2
		
		self.bits = bits
		self.locTable = locTable
		self.widthTable = widthTable
		self.offsetTable = offsetTable
	
	def getMissing(self):
		return self.glyphs[-1]
	
	def __getitem__(self, charNum):
		if charNum > self.lastChar or charNum < 0:
			raise IndexError, "no such character"
		index = charNum - self.firstChar
		if index < 0:
			return None
		return self.glyphs[index]
	
	def __setitem__(self, charNum, glyph):
		if charNum > self.lastChar or charNum < 0:
			raise IndexError, "no such character"
		index = charNum - self.firstChar
		if index < 0:
			raise IndexError, "no such character"
		self.glyphs[index] = glyph
	
	def __len__(self):
		return len(self.locTable) - 2 + self.firstChar
	
	#
	# XXX old cruft
	#
	
	def createQdBitImage(self):
		import Qd
		self.bitImage = Qd.BitMap(self.bits, 2 * self.rowWords, (0, 0, self.rowWords * 16, self.fRectHeight))
	
	def drawstring(self, astring, destbits, xOffset=0, yOffset=0):
		drawchar = self.drawchar
		for ch in astring:
			xOffset = drawchar(ch, destbits, xOffset, yOffset)
		return xOffset
	
	def drawchar(self, ch, destbits, xOffset, yOffset=0):
		import Qd
		width, bounds, destbounds = self.getcharbounds(ch)
		destbounds = Qd.OffsetRect(destbounds, xOffset, yOffset)
		Qd.CopyBits(self.bitImage, destbits, bounds, destbounds, 1, None)
		return xOffset + width
	
	def stringwidth(self, astring):
		charwidth = self.charwidth
		width = 0
		for ch in astring:
			width = width + charwidth(ch)
		return width
	
	def charwidth(self, ch):
		cindex = ord(ch) - self.firstChar
		if cindex > self.lastChar or 	\
				(self.offsetTable[cindex] == 255 and self.widthTable[cindex] == 255):
			cindex = -2		# missing char
		return self.widthTable[cindex]
	
	def getcharbounds(self, ch):
		cindex = ord(ch) - self.firstChar
		if cindex > self.lastChar or 	\
				(self.offsetTable[cindex] == 255 and self.widthTable[cindex] == 255):
			return self.getcharboundsindex(-2)	# missing char
		return self.getcharboundsindex(cindex)
	
	def getcharboundsindex(self, cindex):
		offset = self.offsetTable[cindex]
		width = self.widthTable[cindex]
		if offset == 255 and width == 255:
			raise ValueError, "character not defined"
		location0 = self.locTable[cindex]
		location1 = self.locTable[cindex + 1]
		srcbounds = (location0, 0, location1, self.fRectHeight)
		destbounds = (	offset + self.kernMax, 
					0, 
					offset + self.kernMax + location1 - location0, 
					self.fRectHeight	)
		return width, srcbounds, destbounds


class Glyph:
	
	def __init__(self, width, offset, pixels=None, pixelDepth=1):
		self.width = width
		self.offset = offset
		self.pixelDepth = pixelDepth
		self.pixels = pixels


def dataFromFile(pathOrFSSpec, nameOrID="", resType='NFNT'):
	from Carbon import Res
	import macfs
	if type(pathOrFSSpec) == types.StringType:
		fss = macfs.FSSpec(pathOrFSSpec)
	else:
		fss = pathOrFSSpec
	resref = Res.FSpOpenResFile(fss, 1)	# readonly
	try:
		Res.UseResFile(resref)
		if not nameOrID:
			# just take the first in the file
			res = Res.Get1IndResource(resType, 1)
		elif type(nameOrID) == types.IntType:
			res = Res.Get1Resource(resType, nameOrID)
		else:
			res = Res.Get1NamedResource(resType, nameOrID)
		theID, theType, name = res.GetResInfo()
		data = res.data
	finally:
		Res.CloseResFile(resref)
	return data


def fromFile(pathOrFSSpec, nameOrID="", resType='NFNT'):
	data = dataFromFile(pathOrFSSpec, nameOrID, resType)
	return NFNT(data)


if __name__ == "__main__":
	import macfs
	fss, ok = macfs.StandardGetFile('FFIL')
	if ok:
		data = dataFromFile(fss)
		font = NFNT(data)
		font.unpackGlyphs()
		font.packGlyphs()
		data2 = font.compile()
		print "xxxxx", data == data2, len(data) == len(data2)
