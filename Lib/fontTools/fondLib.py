import os
import struct, sstruct
import string
try:
	from Carbon import Res
except ImportError:
	import Res


error = "fondLib.error"

DEBUG = 0

headerformat = """
	>
	ffFlags:	h
	ffFamID:	h
	ffFirstChar:	h
	ffLastChar:	h
	ffAscent:	h
	ffDescent:	h
	ffLeading:	h
	ffWidMax:	h
	ffWTabOff:	l
	ffKernOff:	l
	ffStylOff:	l
"""

FONDheadersize = 52

class FontFamily:
	
	def __init__(self, theRes, mode = 'r'):
		self.ID, type, self.name = theRes.GetResInfo()
		if type <> 'FOND':
			raise ValueError, "FOND resource required"
		self.FOND = theRes
		self.mode = mode
		self.changed = 0
		
		if DEBUG:
			self.parsedthings = []
	
	def parse(self):
		self._getheader()
		self._getfontassociationtable()
		self._getoffsettable()
		self._getboundingboxtable()
		self._getglyphwidthtable()
		self._getstylemappingtable()
		self._getglyphencodingsubtable()
		self._getkerningtables()
	
	def minimalparse(self):
		self._getheader()
		self._getglyphwidthtable()
		self._getstylemappingtable()
	
	def __repr__(self):
		return "<FontFamily instance of %s>" % self.name
	
	def getflags(self):
		return self.fondClass
	
	def setflags(self, flags):
		self.changed = 1
		self.fondClass = flags
	
	def save(self, destresfile = None):
		if self.mode <> 'w':
			raise error, "can't save font: no write permission"
		self._buildfontassociationtable()
		self._buildoffsettable()
		self._buildboundingboxtable()
		self._buildglyphwidthtable()
		self._buildkerningtables()
		self._buildstylemappingtable()
		self._buildglyphencodingsubtable()
		rawnames = [	"_rawheader", 
					"_rawfontassociationtable", 
					"_rawoffsettable", 
					"_rawglyphwidthtable", 
					"_rawstylemappingtable", 
					"_rawglyphencodingsubtable",
					"_rawkerningtables"
				]
		for name in rawnames[1:]:	# skip header
			data = getattr(self, name)
			if len(data) & 1:
				setattr(self, name, data + '\0')
		
		self.ffWTabOff = FONDheadersize + len(self._rawfontassociationtable) + len(self._rawoffsettable)
		self.ffStylOff = self.ffWTabOff + len(self._rawglyphwidthtable)
		self.ffKernOff = self.ffStylOff + len(self._rawstylemappingtable) + len(self._rawglyphencodingsubtable)
		self.glyphTableOffset = len(self._rawstylemappingtable)
		
		if not self._rawglyphwidthtable:
			self.ffWTabOff = 0
		if not self._rawstylemappingtable:
			self.ffStylOff = 0
		if not self._rawglyphencodingsubtable:
			self.glyphTableOffset = 0
		if not self._rawkerningtables:
			self.ffKernOff = 0
		
		self._buildheader()
		
		# glyphTableOffset has only just been calculated
		self._updatestylemappingtable()
		
		newdata = ""
		for name in rawnames:
			newdata = newdata + getattr(self, name)
		if destresfile is None:
			self.FOND.data = newdata
			self.FOND.ChangedResource()
			self.FOND.WriteResource()
		else:
			ID, type, name = self.FOND.GetResInfo()
			self.FOND.DetachResource()
			self.FOND.data = newdata
			saveref = Res.CurResFile()
			Res.UseResFile(destresfile)
			self.FOND.AddResource(type, ID, name)
			Res.UseResFile(saveref)
		self.changed = 0
	
	def _getheader(self):
		data = self.FOND.data
		sstruct.unpack(headerformat, data[:28], self)
		self.ffProperty = struct.unpack(">9h", data[28:46])
		self.ffIntl = struct.unpack(">hh", data[46:50])
		self.ffVersion, = struct.unpack(">h", data[50:FONDheadersize])
		
		if DEBUG:
			self._rawheader = data[:FONDheadersize]
			self.parsedthings.append((0, FONDheadersize, 'header'))
	
	def _buildheader(self):
		header = sstruct.pack(headerformat, self)
		header = header + apply(struct.pack, (">9h",) + self.ffProperty)
		header = header + apply(struct.pack, (">hh",) + self.ffIntl)
		header = header + struct.pack(">h", self.ffVersion)
		if DEBUG:
			print "header is the same?", self._rawheader == header and 'yes.' or 'no.'
			if self._rawheader <> header:
				print len(self._rawheader), len(header)
		self._rawheader = header
	
	def _getfontassociationtable(self):
		data = self.FOND.data
		offset = FONDheadersize
		numberofentries, = struct.unpack(">h", data[offset:offset+2])
		numberofentries = numberofentries + 1
		size = numberofentries * 6
		self.fontAssoc = []
		for i in range(offset + 2, offset + size, 6):
			self.fontAssoc.append(struct.unpack(">3h", data[i:i+6]))
		
		self._endoffontassociationtable = offset + size + 2
		if DEBUG:
			self._rawfontassociationtable = data[offset:self._endoffontassociationtable]
			self.parsedthings.append((offset, self._endoffontassociationtable, 'fontassociationtable'))
	
	def _buildfontassociationtable(self):
		data = struct.pack(">h", len(self.fontAssoc) - 1)
		for size, stype, ID in self.fontAssoc:
			data = data + struct.pack(">3h", size, stype, ID)
		
		if DEBUG:
			print "font association table is the same?", self._rawfontassociationtable == data and 'yes.' or 'no.'
			if self._rawfontassociationtable <> data:
				print len(self._rawfontassociationtable), len(data)
		self._rawfontassociationtable = data
	
	def _getoffsettable(self):
		if self.ffWTabOff == 0:
			self._rawoffsettable = ""
			return
		data = self.FOND.data
		# Quick'n'Dirty. What's the spec anyway? Can't find it...
		offset = self._endoffontassociationtable
		count = self.ffWTabOff
		self._rawoffsettable = data[offset:count]
		if DEBUG:
			self.parsedthings.append((offset, count, 'offsettable&bbtable'))
	
	def _buildoffsettable(self):
		if not hasattr(self, "_rawoffsettable"):
			self._rawoffsettable = ""
	
	def _getboundingboxtable(self):
		self.boundingBoxes = None
		if self._rawoffsettable[:6] <> '\0\0\0\0\0\6':  # XXX ????
			return
		boxes = {}
		data = self._rawoffsettable[6:]
		numstyles = struct.unpack(">h", data[:2])[0] + 1
		data = data[2:]
		for i in range(numstyles):
			style, l, b, r, t = struct.unpack(">hhhhh", data[:10])
			boxes[style] = (l, b, r, t)
			data = data[10:]
		self.boundingBoxes = boxes
	
	def _buildboundingboxtable(self):
		if self.boundingBoxes and self._rawoffsettable[:6] == '\0\0\0\0\0\6':
			boxes = self.boundingBoxes.items()
			boxes.sort()
			data = '\0\0\0\0\0\6' + struct.pack(">h", len(boxes) - 1)
			for style, (l, b, r, t) in boxes:
				data = data + struct.pack(">hhhhh", style, l, b, r, t)
			self._rawoffsettable = data
	
	def _getglyphwidthtable(self):
		self.widthTables = {}
		if self.ffWTabOff == 0:
			return
		data = self.FOND.data
		offset = self.ffWTabOff
		numberofentries, = struct.unpack(">h", data[offset:offset+2])
		numberofentries = numberofentries + 1
		count = offset + 2
		for i in range(numberofentries):
			stylecode, = struct.unpack(">h", data[count:count+2])
			widthtable = self.widthTables[stylecode] = []
			count = count + 2
			for j in range(3 + self.ffLastChar - self.ffFirstChar):
				width, = struct.unpack(">h", data[count:count+2])
				widthtable.append(width)
				count = count + 2
		
		if DEBUG:
			self._rawglyphwidthtable = data[offset:count]
			self.parsedthings.append((offset, count, 'glyphwidthtable'))
	
	def _buildglyphwidthtable(self):
		if not self.widthTables:
			self._rawglyphwidthtable = ""
			return
		numberofentries = len(self.widthTables)
		data = struct.pack('>h', numberofentries - 1)
		tables = self.widthTables.items()
		tables.sort()
		for stylecode, table in tables:
			data = data + struct.pack('>h', stylecode)
			if len(table) <> (3 + self.ffLastChar - self.ffFirstChar):
				raise error, "width table has wrong length"
			for width in table:
				data = data + struct.pack('>h', width)
		if DEBUG:
			print "glyph width table is the same?", self._rawglyphwidthtable == data and 'yes.' or 'no.'
		self._rawglyphwidthtable = data
	
	def _getkerningtables(self):
		self.kernTables = {}
		if self.ffKernOff == 0:
			return
		data = self.FOND.data
		offset = self.ffKernOff
		numberofentries, = struct.unpack(">h", data[offset:offset+2])
		numberofentries = numberofentries + 1
		count = offset + 2
		for i in range(numberofentries):
			stylecode, = struct.unpack(">h", data[count:count+2])
			count = count + 2
			numberofpairs, = struct.unpack(">h", data[count:count+2])
			count = count + 2
			kerntable = self.kernTables[stylecode] = []
			for j in range(numberofpairs):
				firstchar, secondchar, kerndistance = struct.unpack(">cch", data[count:count+4])
				kerntable.append((ord(firstchar), ord(secondchar), kerndistance))
				count = count + 4
		
		if DEBUG:
			self._rawkerningtables = data[offset:count]
			self.parsedthings.append((offset, count, 'kerningtables'))
	
	def _buildkerningtables(self):
		if self.kernTables == {}:
			self._rawkerningtables = ""
			self.ffKernOff = 0
			return
		numberofentries = len(self.kernTables)
		data = [struct.pack('>h', numberofentries - 1)]
		tables = self.kernTables.items()
		tables.sort()
		for stylecode, table in tables:
			data.append(struct.pack('>h', stylecode))
			data.append(struct.pack('>h', len(table)))  # numberofpairs
			for firstchar, secondchar, kerndistance in table:
				data.append(struct.pack(">cch", chr(firstchar), chr(secondchar), kerndistance))
		
		data = string.join(data, '')
		
		if DEBUG:
			print "kerning table is the same?", self._rawkerningtables == data and 'yes.' or 'no.'
			if self._rawkerningtables <> data:
				print len(self._rawkerningtables), len(data)
		self._rawkerningtables = data
	
	def _getstylemappingtable(self):
		offset = self.ffStylOff
		self.styleStrings = []
		self.styleIndices = ()
		self.glyphTableOffset = 0
		self.fondClass = 0
		if offset == 0:
			return
		data = self.FOND.data
		self.fondClass, self.glyphTableOffset, self.styleMappingReserved, = \
				struct.unpack(">hll", data[offset:offset+10])
		self.styleIndices = struct.unpack('>48b', data[offset + 10:offset + 58])
		stringcount, = struct.unpack('>h', data[offset+58:offset+60])
		
		count = offset + 60
		for i in range(stringcount):
			str_len = ord(data[count])
			self.styleStrings.append(data[count + 1:count + 1 + str_len])
			count = count + 1 + str_len
		
		self._unpackstylestrings()
		
		data = data[offset:count]
		if len(data) % 2:
			data = data + '\0'
		if DEBUG:
			self._rawstylemappingtable = data
			self.parsedthings.append((offset, count, 'stylemappingtable'))
	
	def _buildstylemappingtable(self):
		if not self.styleIndices:
			self._rawstylemappingtable = ""
			return
		data = struct.pack(">hll", self.fondClass, self.glyphTableOffset, 
					self.styleMappingReserved)
		
		self._packstylestrings()
		data = data + apply(struct.pack, (">48b",) + self.styleIndices)
		
		stringcount = len(self.styleStrings)
		data = data + struct.pack(">h", stringcount)
		for string in self.styleStrings:
			data = data + chr(len(string)) + string
		
		if len(data) % 2:
			data = data + '\0'
		
		if DEBUG:
			print "style mapping table is the same?", self._rawstylemappingtable == data and 'yes.' or 'no.'
		self._rawstylemappingtable = data
	
	def _unpackstylestrings(self):
		psNames = {}
		self.ffFamilyName = self.styleStrings[0]
		for i in self.widthTables.keys():
			index = self.styleIndices[i]
			if index == 1:
				psNames[i] = self.styleStrings[0]
			else:
				style = self.styleStrings[0]
				codes = map(ord, self.styleStrings[index - 1])
				for code in codes:
					style = style + self.styleStrings[code - 1]
				psNames[i] = style
		self.psNames = psNames
	
	def _packstylestrings(self):
		nameparts = {}
		splitnames = {}
		for style, name in self.psNames.items():
			split = splitname(name, self.ffFamilyName)
			splitnames[style] = split
			for part in split:
				nameparts[part] = None
		del nameparts[self.ffFamilyName]
		nameparts = nameparts.keys()
		nameparts.sort()
		items = splitnames.items()
		items.sort()
		numindices = 0
		for style, split in items:
			if len(split) > 1:
				numindices = numindices + 1
		numindices = max(numindices, max(self.styleIndices) - 1)
		styleStrings = [self.ffFamilyName] + numindices * [""] + nameparts
		# XXX the next bit goes wrong for MM fonts.
		for style, split in items:
			if len(split) == 1:
				continue
			indices = ""
			for part in split[1:]:
				indices = indices + chr(nameparts.index(part) + numindices + 2)
			styleStrings[self.styleIndices[style] - 1] = indices
		self.styleStrings = styleStrings
	
	def _updatestylemappingtable(self):
		# Update the glyphTableOffset field.
		# This is neccesary since we have to build this table to 
		# know what the glyphTableOffset will be.
		# And we don't want to build it twice, do we?
		data = self._rawstylemappingtable
		if not data:
			return
		data = data[:2] + struct.pack(">l", self.glyphTableOffset) + data[6:]
		self._rawstylemappingtable = data
	
	def _getglyphencodingsubtable(self):
		glyphEncoding = self.glyphEncoding = {}
		if not self.glyphTableOffset:
			return
		offset = self.ffStylOff + self.glyphTableOffset
		data = self.FOND.data
		numberofentries, = struct.unpack(">h", data[offset:offset+2])
		count = offset + 2
		for i in range(numberofentries):
			glyphcode = ord(data[count])
			count = count + 1
			strlen = ord(data[count])
			count = count + 1
			glyphname = data[count:count+strlen]
			glyphEncoding[glyphcode] = glyphname
			count = count + strlen
		
		if DEBUG:
			self._rawglyphencodingsubtable = data[offset:count]
			self.parsedthings.append((offset, count, 'glyphencodingsubtable'))
	
	def _buildglyphencodingsubtable(self):
		if not self.glyphEncoding:
			self._rawglyphencodingsubtable = ""
			return
		numberofentries = len(self.glyphEncoding)
		data = struct.pack(">h", numberofentries)
		items = self.glyphEncoding.items()
		items.sort()
		for glyphcode, glyphname in items:
			data = data + chr(glyphcode) + chr(len(glyphname)) + glyphname
		self._rawglyphencodingsubtable = data
	

uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def splitname(name, famname = None):
	# XXX this goofs up MM font names: but how should it be done??
	if famname:
		if name[:len(famname)] <> famname:
			raise error, "first part of name should be same as family name"
		name = name[len(famname):]
		split = [famname]
	else:
		split = []
	current = ""
	for c in name:
		if c == '-' or c in uppercase:
			if current:
				split.append(current)
				current = ""
		current = current + c
	if current:
		split.append(current)
	return split

def makeLWFNfilename(name):
	split = splitname(name)
	lwfnname = split[0][:5]
	for part in split[1:]:
		if part <> '-':
			lwfnname = lwfnname + part[:3]
	return lwfnname

class BitmapFontFile:
	
	def __init__(self, path, mode='r'):
		import macfs
		
		if mode == 'r':
			permission = 1	# read only
		elif mode == 'w':
			permission = 3	# exclusive r/w
		else:
			raise error, 'mode should be either "r" or "w"'
		self.mode = mode
		fss = macfs.FSSpec(path)
		self.resref = Res.FSpOpenResFile(fss, permission)
		Res.UseResFile(self.resref)
		self.path = path
		self.fonds = []
		self.getFONDs()
	
	def getFONDs(self):
		FONDcount = Res.Count1Resources('FOND')
		for i in range(FONDcount):
			fond = FontFamily(Res.Get1IndResource('FOND', i + 1), self.mode)
			self.fonds.append(fond)
	
	def parse(self):
		self.fondsbyname = {}
		for fond in self.fonds:
			fond.parse()
			if hasattr(fond, "psNames") and fond.psNames:
				psNames = fond.psNames.values()
				psNames.sort()
				self.fondsbyname[psNames[0]] = fond
	
	def minimalparse(self):
		for fond in self.fonds:
			fond.minimalparse()
	
	def close(self):
		if self.resref <> None:
			try:
				Res.CloseResFile(self.resref)
			except Res.Error:
				pass
			self.resref = None


class FondSelector:
	
	def __init__(self, fondlist):
		import W
		if not fondlist:
			raise ValueError, "expected at least one FOND entry"
		if len(fondlist) == 1:
			self.choice = 0
			return
		fonds = []
		for fond in fondlist:
			fonds.append(fond.name)
		self.w = W.ModalDialog((200, 200), "aaa")
		self.w.donebutton = W.Button((-70, -26, 60, 16), "Done", self.close)
		self.w.l = W.List((10, 10, -10, -36), fonds, self.listhit)
		self.w.setdefaultbutton(self.w.donebutton)
		self.w.l.setselection([0])
		self.w.open()
	
	def close(self):
		self.checksel()
		sel = self.w.l.getselection()
		self.choice = sel[0]
		self.w.close()
	
	def listhit(self, isDbl):
		if isDbl:
			self.w.donebutton.push()
		else:
			self.checksel()
	
	def checksel(self):
		sel = self.w.l.getselection()
		if not sel:
			self.w.l.setselection([0])
		elif len(sel) <> 1:
			self.w.l.setselection([sel[0]])
			
