"""_g_l_y_f.py -- Converter classes for the 'glyf' table."""


#
# The Apple and MS rasterizers behave differently for 
# scaled composite components: one does scale first and then translate
# and the other does it vice versa. MS defined some flags to indicate
# the difference, but it seems nobody actually _sets_ those flags.
#
# Funny thing: Apple seems to _only_ do their thing in the
# WE_HAVE_A_SCALE (eg. Chicago) case, and not when it's WE_HAVE_AN_X_AND_Y_SCALE 
# (eg. Charcoal)...
#
SCALE_COMPONENT_OFFSET_DEFAULT = 0   # 0 == MS, 1 == Apple


import struct, sstruct
import DefaultTable
from fontTools import ttLib
from fontTools.misc.textTools import safeEval, readHex
import array
import Numeric
import types

class table__g_l_y_f(DefaultTable.DefaultTable):
	
	def decompile(self, data, ttFont):
		loca = ttFont['loca']
		last = loca[0]
		self.glyphs = {}
		self.glyphOrder = []
		self.glyphOrder = glyphOrder = ttFont.getGlyphOrder()
		for i in range(0, len(loca)-1):
			glyphName = glyphOrder[i]
			next = loca[i+1]
			glyphdata = data[last:next]
			if len(glyphdata) <> (next - last):
				raise ttLib.TTLibError, "not enough 'glyf' table data"
			glyph = Glyph(glyphdata)
			self.glyphs[glyphName] = glyph
			last = next
		if len(data) > next:
			raise ttLib.TTLibError, "too much 'glyf' table data"
	
	def compile(self, ttFont):
		import string
		locations = []
		currentLocation = 0
		dataList = []
		for glyphName in ttFont.getGlyphOrder():
			glyph = self[glyphName]
			glyphData = glyph.compile(self)
			locations.append(currentLocation)
			currentLocation = currentLocation + len(glyphData)
			dataList.append(glyphData)
		locations.append(currentLocation)
		data = string.join(dataList, "")
		ttFont['loca'].set(locations)
		ttFont['maxp'].numGlyphs = len(self.glyphs)
		return data
	
	def toXML(self, writer, ttFont, progress=None, compactGlyphs=0):
		writer.newline()
		glyphOrder = ttFont.getGlyphOrder()
		writer.begintag("GlyphOrder")
		writer.newline()
		for i in range(len(glyphOrder)):
			glyphName = glyphOrder[i]
			writer.simpletag("GlyphID", id=i, name=glyphName)
			writer.newline()
		writer.endtag("GlyphOrder")
		writer.newline()
		writer.newline()
		glyphNames = ttFont.getGlyphNames()
		writer.comment("The xMin, yMin, xMax and yMax values\nwill be recalculated by the compiler.")
		writer.newline()
		writer.newline()
		for glyphName in glyphNames:
			if progress:
				progress.setlabel("Dumping 'glyf' table... (%s)" % glyphName)
				progress.increment()
			glyph = self[glyphName]
			if glyph.numberOfContours:
				writer.begintag('TTGlyph', [
						("name", glyphName),
						("xMin", glyph.xMin),
						("yMin", glyph.yMin),
						("xMax", glyph.xMax),
						("yMax", glyph.yMax),
						])
				writer.newline()
				glyph.toXML(writer, ttFont)
				if compactGlyphs:
					glyph.compact(self)
				writer.endtag('TTGlyph')
				writer.newline()
			else:
				writer.simpletag('TTGlyph', name=glyphName)
				writer.comment("contains no outline data")
				writer.newline()
			writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		if name == "GlyphOrder":
			glyphOrder = []
			for element in content:
				if type(element) == types.StringType:
					continue
				name, attrs, content = element
				if name == "GlyphID":
					index = safeEval(attrs["id"])
					glyphName = attrs["name"]
					glyphOrder = glyphOrder + (1 + index - len(glyphOrder)) * [".notdef"]
					glyphOrder[index] = glyphName
			ttFont.setGlyphOrder(glyphOrder)
		elif name == "TTGlyph":
			if not hasattr(self, "glyphs"):
				self.glyphs = {}
			glyphName = attrs["name"]
			if ttFont.verbose:
				ttLib.debugmsg("unpacking glyph '%s'" % glyphName)
			glyph = Glyph()
			for attr in ['xMin', 'yMin', 'xMax', 'yMax']:
				setattr(glyph, attr, safeEval(attrs.get(attr, '0')))
			self.glyphs[glyphName] = glyph
			for element in content:
				if type(element) == types.StringType:
					continue
				glyph.fromXML(element, ttFont)
	
	def setGlyphOrder(self, glyphOrder):
		self.glyphOrder = glyphOrder
	
	def getGlyphName(self, glyphID):
		return self.glyphOrder[glyphID]
	
	def getGlyphID(self, glyphName):
		# XXX optimize with reverse dict!!!
		return self.glyphOrder.index(glyphName)
	
	#def keys(self):
	#	return self.glyphOrder[:]
	#
	#def has_key(self, glyphName):
	#	return self.glyphs.has_key(glyphName)
	#
	def __getitem__(self, glyphName):
		glyph = self.glyphs[glyphName]
		glyph.expand(self)
		return glyph
	
	def __setitem__(self, glyphName, glyph):
		self.glyphs[glyphName] = glyph
		if glyphName not in self.glyphOrder:
			self.glyphOrder.append(glyphName)
	
	def __delitem__(self, glyphName):
		del self.glyphs[glyphName]
		self.glyphOrder.remove(glyphName)
	
	def __len__(self):
		assert len(self.glyphOrder) == len(self.glyphs)
		return len(self.glyphs)


glyphHeaderFormat = """
		>	# big endian
		numberOfContours:	h
		xMin:				h
		yMin:				h
		xMax:				h
		yMax:				h
"""

# flags
flagOnCurve = 0x01
flagXShort = 0x02
flagYShort = 0x04
flagRepeat = 0x08
flagXsame =  0x10
flagYsame = 0x20
flagReserved1 = 0x40
flagReserved2 = 0x80


ARG_1_AND_2_ARE_WORDS      = 0x0001  # if set args are words otherwise they are bytes 
ARGS_ARE_XY_VALUES         = 0x0002  # if set args are xy values, otherwise they are points 
ROUND_XY_TO_GRID           = 0x0004  # for the xy values if above is true 
WE_HAVE_A_SCALE            = 0x0008  # Sx = Sy, otherwise scale == 1.0 
NON_OVERLAPPING            = 0x0010  # set to same value for all components (obsolete!)
MORE_COMPONENTS            = 0x0020  # indicates at least one more glyph after this one 
WE_HAVE_AN_X_AND_Y_SCALE   = 0x0040  # Sx, Sy 
WE_HAVE_A_TWO_BY_TWO       = 0x0080  # t00, t01, t10, t11 
WE_HAVE_INSTRUCTIONS       = 0x0100  # instructions follow 
USE_MY_METRICS             = 0x0200  # apply these metrics to parent glyph 
OVERLAP_COMPOUND           = 0x0400  # used by Apple in GX fonts 
SCALED_COMPONENT_OFFSET    = 0x0800  # composite designed to have the component offset scaled (designed for Apple) 
UNSCALED_COMPONENT_OFFSET  = 0x1000  # composite designed not to have the component offset scaled (designed for MS) 


class Glyph:
	
	def __init__(self, data=""):
		if not data:
			# empty char
			self.numberOfContours = 0
			return
		self.data = data
	
	def compact(self, glyfTable):
		data = self.compile(glyfTable)
		self.__dict__.clear()
		self.data = data
	
	def expand(self, glyfTable):
		if not hasattr(self, "data"):
			# already unpacked
			return
		dummy, data = sstruct.unpack2(glyphHeaderFormat, self.data, self)
		del self.data
		if self.numberOfContours == -1:
			self.decompileComponents(data, glyfTable)
		else:
			self.decompileCoordinates(data)
	
	def compile(self, glyfTable):
		if hasattr(self, "data"):
			return self.data
		if self.numberOfContours == 0:
			return ""
		self.recalcBounds(glyfTable)
		data = sstruct.pack(glyphHeaderFormat, self)
		if self.numberOfContours == -1:
			data = data + self.compileComponents(glyfTable)
		else:
			data = data + self.compileCoordinates()
		# from the spec: "Note that the local offsets should be word-aligned"
		if len(data) % 2:
			# ...so if the length of the data is odd, append a null byte
			data = data + "\0"
		return data
	
	def toXML(self, writer, ttFont):
		if self.numberOfContours == -1:
			for compo in self.components:
				compo.toXML(writer, ttFont)
			if hasattr(self, "instructions"):
				writer.begintag("instructions")
				writer.newline()
				writer.dumphex(self.instructions)
				writer.endtag("instructions")
				writer.newline()
		else:
			last = 0
			for i in range(self.numberOfContours):
				writer.begintag("contour")
				writer.newline()
				for j in range(last, self.endPtsOfContours[i] + 1):
					writer.simpletag("pt", [
							("x", self.coordinates[j][0]), 
							("y", self.coordinates[j][1]),
							("on", self.flags[j] & flagOnCurve)])
					writer.newline()
				last = self.endPtsOfContours[i] + 1
				writer.endtag("contour")
				writer.newline()
			if self.numberOfContours:
				writer.begintag("instructions")
				writer.newline()
				writer.dumphex(self.instructions)
				writer.endtag("instructions")
				writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		if name == "contour":
			self.numberOfContours = self.numberOfContours + 1
			if self.numberOfContours < 0:
				raise ttLib.TTLibError, "can't mix composites and contours in glyph"
			coordinates = []
			flags = []
			for element in content:
				if type(element) == types.StringType:
					continue
				name, attrs, content = element
				if name <> "pt":
					continue  # ignore anything but "pt"
				coordinates.append([safeEval(attrs["x"]), safeEval(attrs["y"])])
				flags.append(not not safeEval(attrs["on"]))
			coordinates = Numeric.array(coordinates, Numeric.Int16)
			flags = Numeric.array(flags, Numeric.Int8)
			if not hasattr(self, "coordinates"):
				self.coordinates = coordinates
				self.flags = flags
				self.endPtsOfContours = [len(coordinates)-1]
			else:
				self.coordinates = Numeric.concatenate((self.coordinates, coordinates))
				self.flags = Numeric.concatenate((self.flags, flags))
				self.endPtsOfContours.append(len(self.coordinates)-1)
		elif name == "component":
			if self.numberOfContours > 0:
				raise ttLib.TTLibError, "can't mix composites and contours in glyph"
			self.numberOfContours = -1
			if not hasattr(self, "components"):
				self.components = []
			component = GlyphComponent()
			self.components.append(component)
			component.fromXML((name, attrs, content), ttFont)
		elif name == "instructions":
			self.instructions = readHex(content)
	
	def getCompositeMaxpValues(self, glyfTable, maxComponentDepth=1):
		assert self.numberOfContours == -1
		nContours = 0
		nPoints = 0
		for compo in self.components:
			baseGlyph = glyfTable[compo.glyphName]
			if baseGlyph.numberOfContours == 0:
				continue
			elif baseGlyph.numberOfContours > 0:
				nP, nC = baseGlyph.getMaxpValues()
			else:
				nP, nC, maxComponentDepth = baseGlyph.getCompositeMaxpValues(
						glyfTable, maxComponentDepth + 1)
			nPoints = nPoints + nP
			nContours = nContours + nC
		return nPoints, nContours, maxComponentDepth
	
	def getMaxpValues(self):
		assert self.numberOfContours > 0
		return len(self.coordinates), len(self.endPtsOfContours)
	
	def decompileComponents(self, data, glyfTable):
		self.components = []
		more = 1
		haveInstructions = 0
		while more:
			component = GlyphComponent()
			more, haveInstr, data = component.decompile(data, glyfTable)
			haveInstructions = haveInstructions | haveInstr
			self.components.append(component)
		if haveInstructions:
			numInstructions, = struct.unpack(">h", data[:2])
			data = data[2:]
			self.instructions = data[:numInstructions]
			data = data[numInstructions:]
			assert len(data) in (0, 1), "bad composite data"
	
	def decompileCoordinates(self, data):
		endPtsOfContours = array.array("h")
		endPtsOfContours.fromstring(data[:2*self.numberOfContours])
		if ttLib.endian <> "big":
			endPtsOfContours.byteswap()
		self.endPtsOfContours = endPtsOfContours.tolist()
		
		data = data[2*self.numberOfContours:]
		
		instructionLength, = struct.unpack(">h", data[:2])
		data = data[2:]
		self.instructions = data[:instructionLength]
		data = data[instructionLength:]
		nCoordinates = self.endPtsOfContours[-1] + 1
		flags, xCoordinates, yCoordinates = \
				self.decompileCoordinatesRaw(nCoordinates, data)
		
		# fill in repetitions and apply signs
		coordinates = Numeric.zeros((nCoordinates, 2), Numeric.Int16)
		xIndex = 0
		yIndex = 0
		for i in range(nCoordinates):
			flag = flags[i]
			# x coordinate
			if flag & flagXShort:
				if flag & flagXsame:
					x = xCoordinates[xIndex]
				else:
					x = -xCoordinates[xIndex]
				xIndex = xIndex + 1
			elif flag & flagXsame:
				x = 0
			else:
				x = xCoordinates[xIndex]
				xIndex = xIndex + 1
			# y coordinate
			if flag & flagYShort:
				if flag & flagYsame:
					y = yCoordinates[yIndex]
				else:
					y = -yCoordinates[yIndex]
				yIndex = yIndex + 1
			elif flag & flagYsame:
				y = 0
			else:
				y = yCoordinates[yIndex]
				yIndex = yIndex + 1
			coordinates[i] = (x, y)
		assert xIndex == len(xCoordinates)
		assert yIndex == len(yCoordinates)
		# convert relative to absolute coordinates
		self.coordinates = Numeric.add.accumulate(coordinates)
		# discard all flags but for "flagOnCurve"
		if hasattr(Numeric, "__version__"):
			self.flags = Numeric.bitwise_and(flags, flagOnCurve).astype(Numeric.Int8)
		else:
			self.flags = Numeric.boolean_and(flags, flagOnCurve).astype(Numeric.Int8)
	
	def decompileCoordinatesRaw(self, nCoordinates, data):
		# unpack flags and prepare unpacking of coordinates
		flags = Numeric.array([0] * nCoordinates, Numeric.Int8)
		# Warning: deep Python trickery going on. We use the struct module to unpack
		# the coordinates. We build a format string based on the flags, so we can
		# unpack the coordinates in one struct.unpack() call.
		xFormat = ">" # big endian
		yFormat = ">" # big endian
		i = j = 0
		while 1:
			flag = ord(data[i])
			i = i + 1
			repeat = 1
			if flag & flagRepeat:
				repeat = ord(data[i]) + 1
				i = i + 1
			for k in range(repeat):
				if flag & flagXShort:
					xFormat = xFormat + 'B'
				elif not (flag & flagXsame):
					xFormat = xFormat + 'h'
				if flag & flagYShort:
					yFormat = yFormat + 'B'
				elif not (flag & flagYsame):
					yFormat = yFormat + 'h'
				flags[j] = flag
				j = j + 1
			if j >= nCoordinates:
				break
		assert j == nCoordinates, "bad glyph flags"
		data = data[i:]
		# unpack raw coordinates, krrrrrr-tching!
		xDataLen = struct.calcsize(xFormat)
		yDataLen = struct.calcsize(yFormat)
		if (len(data) - (xDataLen + yDataLen)) not in (0, 1):
			raise ttLib.TTLibError, "bad glyph record"
		xCoordinates = struct.unpack(xFormat, data[:xDataLen])
		yCoordinates = struct.unpack(yFormat, data[xDataLen:xDataLen+yDataLen])
		return flags, xCoordinates, yCoordinates
	
	def compileComponents(self, glyfTable):
		data = ""
		lastcomponent = len(self.components) - 1
		more = 1
		haveInstructions = 0
		for i in range(len(self.components)):
			if i == lastcomponent:
				haveInstructions = hasattr(self, "instructions")
				more = 0
			compo = self.components[i]
			data = data + compo.compile(more, haveInstructions, glyfTable)
		if haveInstructions:
			data = data + struct.pack(">h", len(self.instructions)) + self.instructions
		return data
			
	
	def compileCoordinates(self):
		assert len(self.coordinates) == len(self.flags)
		data = ""
		endPtsOfContours = array.array("h", self.endPtsOfContours)
		if ttLib.endian <> "big":
			endPtsOfContours.byteswap()
		data = data + endPtsOfContours.tostring()
		data = data + struct.pack(">h", len(self.instructions))
		data = data + self.instructions
		nCoordinates = len(self.coordinates)
		
		# make a copy
		coordinates = self.coordinates.astype(self.coordinates.typecode())
		# absolute to relative coordinates
		coordinates[1:] = Numeric.subtract(coordinates[1:], coordinates[:-1])
		flags = self.flags
		compressedflags = []
		xPoints = []
		yPoints = []
		xFormat = ">"
		yFormat = ">"
		lastflag = None
		repeat = 0
		for i in range(len(coordinates)):
			# Oh, the horrors of TrueType
			flag = self.flags[i]
			x, y = coordinates[i]
			# do x
			if x == 0:
				flag = flag | flagXsame
			elif -255 <= x <= 255:
				flag = flag | flagXShort
				if x > 0:
					flag = flag | flagXsame
				else:
					x = -x
				xPoints.append(x)
				xFormat = xFormat + 'B'
			else:
				xPoints.append(x)
				xFormat = xFormat + 'h'
			# do y
			if y == 0:
				flag = flag | flagYsame
			elif -255 <= y <= 255:
				flag = flag | flagYShort
				if y > 0:
					flag = flag | flagYsame
				else:
					y = -y
				yPoints.append(y)
				yFormat = yFormat + 'B'
			else:
				yPoints.append(y)
				yFormat = yFormat + 'h'
			# handle repeating flags
			if flag == lastflag:
				repeat = repeat + 1
				if repeat == 1:
					compressedflags.append(flag)
				elif repeat > 1:
					compressedflags[-2] = flag | flagRepeat
					compressedflags[-1] = repeat
				else:
					compressedflags[-1] = repeat
			else:
				repeat = 0
				compressedflags.append(flag)
			lastflag = flag
		data = data + array.array("B", compressedflags).tostring()
		data = data + apply(struct.pack, (xFormat,)+tuple(xPoints))
		data = data + apply(struct.pack, (yFormat,)+tuple(yPoints))
		return data
	
	def recalcBounds(self, glyfTable):
		coordinates, endPts, flags = self.getCoordinates(glyfTable)
		self.xMin, self.yMin = Numeric.minimum.reduce(coordinates)
		self.xMax, self.yMax = Numeric.maximum.reduce(coordinates)
	
	def getCoordinates(self, glyfTable):
		if self.numberOfContours > 0:
			return self.coordinates, self.endPtsOfContours, self.flags
		elif self.numberOfContours == -1:
			# it's a composite
			allCoords = None
			allFlags = None
			allEndPts = None
			for compo in self.components:
				g = glyfTable[compo.glyphName]
				coordinates, endPts, flags = g.getCoordinates(glyfTable)
				if hasattr(compo, "firstpt"):
					# move according to two reference points
					move = allCoords[compo.firstpt] - coordinates[compo.secondpt]
				else:
					move = compo.x, compo.y
				
				if not hasattr(compo, "transform"):
					coordinates = coordinates + move  # I love NumPy!
				else:
					apple_way = compo.flags & SCALED_COMPONENT_OFFSET
					ms_way = compo.flags & UNSCALED_COMPONENT_OFFSET
					assert not (apple_way and ms_way)
					if not (apple_way or ms_way):
						scale_component_offset = SCALE_COMPONENT_OFFSET_DEFAULT  # see top of this file
					else:
						scale_component_offset = apple_way
					if scale_component_offset:
						# the Apple way: first move, then scale (ie. scale the component offset)
						coordinates = coordinates + move
						coordinates = Numeric.dot(coordinates, compo.transform)
					else:
						# the MS way: first scale, then move
						coordinates = Numeric.dot(coordinates, compo.transform)
						coordinates = coordinates + move
					# due to the transformation the coords. are now floats;
					# round them off nicely, and cast to short
					coordinates = Numeric.floor(coordinates + 0.5).astype(Numeric.Int16)
				if allCoords is None:
					allCoords = coordinates
					allEndPts = endPts
					allFlags = flags
				else:
					allEndPts = allEndPts + (Numeric.array(endPts) + len(allCoords)).tolist()
					allCoords = Numeric.concatenate((allCoords, coordinates))
					allFlags = Numeric.concatenate((allFlags, flags))
			return allCoords, allEndPts, allFlags
		else:
			return Numeric.array([], Numeric.Int16), [], Numeric.array([], Numeric.Int8)
	
	def __cmp__(self, other):
		if self.numberOfContours <= 0:
			return cmp(self.__dict__, other.__dict__)
		else:
			if cmp(len(self.coordinates), len(other.coordinates)):
				return 1
			ctest = Numeric.alltrue(Numeric.alltrue(Numeric.equal(self.coordinates, other.coordinates)))
			ftest = Numeric.alltrue(Numeric.equal(self.flags, other.flags))
			if not ctest or not ftest:
				return 1
			return (
					cmp(self.endPtsOfContours, other.endPtsOfContours) or
					cmp(self.instructions, other.instructions)
				)


class GlyphComponent:
	
	def __init__(self):
		pass
	
	def decompile(self, data, glyfTable):
		flags, glyphID = struct.unpack(">HH", data[:4])
		self.flags = int(flags)
		glyphID = int(glyphID)
		self.glyphName = glyfTable.getGlyphName(int(glyphID))
		#print ">>", reprflag(self.flags)
		data = data[4:]
		
		if self.flags & ARG_1_AND_2_ARE_WORDS:
			if self.flags & ARGS_ARE_XY_VALUES:
				self.x, self.y = struct.unpack(">hh", data[:4])
			else:
				x, y = struct.unpack(">HH", data[:4])
				self.firstpt, self.secondpt = int(x), int(y)
			data = data[4:]
		else:
			if self.flags & ARGS_ARE_XY_VALUES:
				self.x, self.y = struct.unpack(">bb", data[:2])
			else:
				x, y = struct.unpack(">BB", data[:4])
				self.firstpt, self.secondpt = int(x), int(y)
			data = data[2:]
		
		if self.flags & WE_HAVE_A_SCALE:
			scale, = struct.unpack(">h", data[:2])
			self.transform = Numeric.array(
					[[scale, 0], [0, scale]]) / float(0x4000)  # fixed 2.14
			data = data[2:]
		elif self.flags & WE_HAVE_AN_X_AND_Y_SCALE:
			xscale, yscale = struct.unpack(">hh", data[:4])
			self.transform = Numeric.array(
					[[xscale, 0], [0, yscale]]) / float(0x4000)  # fixed 2.14
			data = data[4:]
		elif self.flags & WE_HAVE_A_TWO_BY_TWO:
			(xscale, scale01, 
					scale10, yscale) = struct.unpack(">hhhh", data[:8])
			self.transform = Numeric.array(
					[[xscale, scale01], [scale10, yscale]]) / float(0x4000)  # fixed 2.14
			data = data[8:]
		more = self.flags & MORE_COMPONENTS
		haveInstructions = self.flags & WE_HAVE_INSTRUCTIONS
		self.flags = self.flags & (ROUND_XY_TO_GRID | USE_MY_METRICS | 
				SCALED_COMPONENT_OFFSET | UNSCALED_COMPONENT_OFFSET |
				NON_OVERLAPPING)
		return more, haveInstructions, data
	
	def compile(self, more, haveInstructions, glyfTable):
		data = ""
		
		# reset all flags we will calculate ourselves
		flags = self.flags & (ROUND_XY_TO_GRID | USE_MY_METRICS | 
				SCALED_COMPONENT_OFFSET | UNSCALED_COMPONENT_OFFSET |
				NON_OVERLAPPING)
		if more:
			flags = flags | MORE_COMPONENTS
		if haveInstructions:
			flags = flags | WE_HAVE_INSTRUCTIONS
		
		if hasattr(self, "firstpt"):
			if (0 <= self.firstpt <= 255) and (0 <= self.secondpt <= 255):
				data = data + struct.pack(">BB", self.firstpt, self.secondpt)
			else:
				data = data + struct.pack(">HH", self.firstpt, self.secondpt)
				flags = flags | ARG_1_AND_2_ARE_WORDS
		else:
			flags = flags | ARGS_ARE_XY_VALUES
			if (-128 <= self.x <= 127) and (-128 <= self.y <= 127):
				data = data + struct.pack(">bb", self.x, self.y)
			else:
				data = data + struct.pack(">hh", self.x, self.y)
				flags = flags | ARG_1_AND_2_ARE_WORDS
		
		if hasattr(self, "transform"):
			# XXX needs more testing
			transform = Numeric.floor(self.transform * 0x4000 + 0.5)
			if transform[0][1] or transform[1][0]:
				flags = flags | WE_HAVE_A_TWO_BY_TWO
				data = data + struct.pack(">hhhh", 
						transform[0][0], transform[0][1],
						transform[1][0], transform[1][1])
			elif transform[0][0] <> transform[1][1]:
				flags = flags | WE_HAVE_AN_X_AND_Y_SCALE
				data = data + struct.pack(">hh", 
						transform[0][0], transform[1][1])
			else:
				flags = flags | WE_HAVE_A_SCALE
				data = data + struct.pack(">h", 
						transform[0][0])
		
		glyphID = glyfTable.getGlyphID(self.glyphName)
		return struct.pack(">HH", flags, glyphID) + data
	
	def toXML(self, writer, ttFont):
		attrs = [("glyphName", self.glyphName)]
		if not hasattr(self, "firstpt"):
			attrs = attrs + [("x", self.x), ("y", self.y)]
		else:
			attrs = attrs + [("firstpt", self.firstpt), ("secondpt", self.secondpt)]
		
		if hasattr(self, "transform"):
			# XXX needs more testing
			transform = self.transform
			if transform[0][1] or transform[1][0]:
				attrs = attrs + [
						("scalex", transform[0][0]), ("scale01", transform[0][1]),
						("scale10", transform[1][0]), ("scaley", transform[1][1]),
						]
			elif transform[0][0] <> transform[1][1]:
				attrs = attrs + [
						("scalex", transform[0][0]), ("scaley", transform[1][1]),
						]
			else:
				attrs = attrs + [("scale", transform[0][0])]
		attrs = attrs + [("flags", hex(self.flags))]
		writer.simpletag("component", attrs)
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		self.glyphName = attrs["glyphName"]
		if attrs.has_key("firstpt"):
			self.firstpt = safeEval(attrs["firstpt"])
			self.secondpt = safeEval(attrs["secondpt"])
		else:
			self.x = safeEval(attrs["x"])
			self.y = safeEval(attrs["y"])
		if attrs.has_key("scale01"):
			scalex = safeEval(attrs["scalex"])
			scale01 = safeEval(attrs["scale01"])
			scale10 = safeEval(attrs["scale10"])
			scaley = safeEval(attrs["scaley"])
			self.transform = Numeric.array([[scalex, scale01], [scale10, scaley]])
		elif attrs.has_key("scalex"):
			scalex = safeEval(attrs["scalex"])
			scaley = safeEval(attrs["scaley"])
			self.transform = Numeric.array([[scalex, 0], [0, scaley]])
		elif attrs.has_key("scale"):
			scale = safeEval(attrs["scale"])
			self.transform = Numeric.array([[scale, 0], [0, scale]])
		self.flags = safeEval(attrs["flags"])
	
	def __cmp__(self, other):
		if hasattr(self, "transform"):
			if Numeric.alltrue(Numeric.equal(self.transform, other.transform)):
				selfdict = self.__dict__.copy()
				otherdict = other.__dict__.copy()
				del selfdict["transform"]
				del otherdict["transform"]
				return cmp(selfdict, otherdict)
			else:
				return 1
		else:
			return cmp(self.__dict__, other.__dict__)


def reprflag(flag):
	bin = ""
	if type(flag) == types.StringType:
		flag = ord(flag)
	while flag:
		if flag & 0x01:
			bin = "1" + bin
		else:
			bin = "0" + bin
		flag = flag >> 1
	bin = (14 - len(bin)) * "0" + bin
	return bin

