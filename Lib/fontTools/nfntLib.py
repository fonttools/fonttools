import Res
import macfs
import struct
import Qd
from types import *


class NFNT:
	
	def __init__(self, nfnt, name = "", _type = 'NFNT'):
		if type(nfnt) == type(Res.Resource("")):
			theID, theType, name = nfnt.GetResInfo()
			if theType <> _type:
				raise TypeError, 'resource of wrong type; expected ' + _type
			data = nfnt.data
		elif type(nfnt) == StringType:
			fss = macfs.FSSpec(nfnt)
			data = readnfntresource(nfnt, name, _type)
		elif type(nfnt) == type(macfs.FSSpec(':')):
			data = readnfntresource(nfnt, name, _type)
		else:
			raise TypeError, 'expected resource, string or fss; found ' + type(nfnt).__name__
		self.parse_nfnt(data)
	
	def parse_nfnt(self, data):
		# header; FontRec
		(	self.fontType,
			self.firstChar,
			self.lastChar,
			self.widMax,
			self.kernMax,
			self.nDescent,
			fRectWidth,
			self.fRectHeight,
			owTLoc,
			self.ascent,
			self.descent,
			self.leading,
			self.rowWords	) = struct.unpack("13h", data[:26])
		if owTLoc < 0:
			owTLoc = owTLoc + 0x8000	# unsigned short
		
		# rest
		tablesize = 2 * (self.lastChar - self.firstChar + 3)
		bitmapsize = 2 * self.rowWords * self.fRectHeight
		
		self.bits = data[26:26 + bitmapsize]
		self.bitImage = Qd.BitMap(self.bits, 2 * self.rowWords, (0, 0, self.rowWords * 16, self.fRectHeight))
		
		owTable = data[26 + bitmapsize + tablesize:26 + bitmapsize + 2 * tablesize]
		if len(owTable) <> tablesize:
			raise ValueError, 'invalid NFNT resource'
		
		locTable = data[26 + bitmapsize:26 + bitmapsize + tablesize]
		if len(locTable) <> tablesize:
			raise ValueError, 'invalid NFNT resource'
		
		# fill tables
		self.offsettable = []
		self.widthtable = []
		self.locationtable = []
		for i in range(0, tablesize, 2):
			self.offsettable.append(ord(owTable[i]))
			self.widthtable.append(ord(owTable[i+1]))
			loc, = struct.unpack('h', locTable[i:i+2])
			self.locationtable.append(loc)
	
	def drawstring(self, astring, destbits, xoffset = 0, yoffset = 0):
		drawchar = self.drawchar
		for ch in astring:
			xoffset = drawchar(ch, destbits, xoffset, yoffset)
		return xoffset
	
	def drawchar(self, ch, destbits, xoffset, yoffset = 0):
		width, bounds, destbounds = self.getcharbounds(ch)
		destbounds = Qd.OffsetRect(destbounds, xoffset, yoffset)
		Qd.CopyBits(self.bitImage, destbits, bounds, destbounds, 1, None)
		return xoffset + width
	
	def stringwidth(self, astring):
		charwidth = self.charwidth
		width = 0
		for ch in astring:
			width = width + charwidth(ch)
		return width
	
	def charwidth(self, ch):
		cindex = ord(ch) - self.firstChar
		if cindex > self.lastChar or 	\
				(self.offsettable[cindex] == 255 and self.widthtable[cindex] == 255):
			cindex = -2		# missing char
		return self.widthtable[cindex]
	
	def getcharbounds(self, ch):
		cindex = ord(ch) - self.firstChar
		if cindex > self.lastChar or 	\
				(self.offsettable[cindex] == 255 and self.widthtable[cindex] == 255):
			return self.getcharboundsindex(-2)	# missing char
		return self.getcharboundsindex(cindex)
	
	def getcharboundsindex(self, cindex):
		offset = self.offsettable[cindex]
		width = self.widthtable[cindex]
		if offset == 255 and width == 255:
			raise ValueError, "character not defined"
		location0 = self.locationtable[cindex]
		location1 = self.locationtable[cindex + 1]
		srcbounds = (location0, 0, location1, self.fRectHeight)
		destbounds = (	offset + self.kernMax, 
					0, 
					offset + self.kernMax + location1 - location0, 
					self.fRectHeight	)
		return width, srcbounds, destbounds


def readnfntresource(fss, name, _type = 'NFNT'):
	resref = Res.FSpOpenResFile(fss, 1)	# readonly
	Res.UseResFile(resref)
	try:
		if name:
			res = Res.Get1NamedResource(_type, name)
		else:
			# just take the first in the file
			res = Res.Get1IndResource(_type, 1)
		theID, theType, name = res.GetResInfo()
		if theType <> _type:
			raise TypeError, 'resource of wrong type; expected ' + _type
		data = res.data
	finally:
		Res.CloseResFile(resref)
	return data


if 0:
	import Win
	fss, ok = macfs.StandardGetFile('FFIL')
	if ok:
		n = NFNT(fss)
		s = "!!!ABCDEFGHIJKLMN01234 hemeltje lief...x.."
		x = 10
		y = 40
		destbits = Win.FrontWindow().GetWindowPort().portBits
		n.drawstring(s, destbits, x, y)
		print n.stringwidth(s)
