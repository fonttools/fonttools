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


import sys
import struct, sstruct
import DefaultTable
from fontTools import ttLib
from fontTools.misc.textTools import safeEval, readHex
import ttProgram
import array
import numpy
from types import StringType, TupleType


class table__g_l_y_f(DefaultTable.DefaultTable):
	
	def decompile(self, data, ttFont):
		loca = ttFont['loca']
		last = int(loca[0])
		self.glyphs = {}
		self.glyphOrder = glyphOrder = ttFont.getGlyphOrder()
		for i in range(0, len(loca)-1):
			glyphName = glyphOrder[i]
			next = int(loca[i+1])
			glyphdata = data[last:next]
			if len(glyphdata) <> (next - last):
				raise ttLib.TTLibError, "not enough 'glyf' table data"
			glyph = Glyph(glyphdata)
			self.glyphs[glyphName] = glyph
			last = next
		# this should become a warning:
		#if len(data) > next:
		#	raise ttLib.TTLibError, "too much 'glyf' table data"
	
	def compile(self, ttFont):
		if not hasattr(self, "glyphOrder"):
			self.glyphOrder = ttFont.getGlyphOrder()
		import string
		locations = []
		currentLocation = 0
		dataList = []
		recalcBBoxes = ttFont.recalcBBoxes
		for glyphName in self.glyphOrder:
			glyph = self.glyphs[glyphName]
			glyphData = glyph.compile(self, recalcBBoxes)
			locations.append(currentLocation)
			currentLocation = currentLocation + len(glyphData)
			dataList.append(glyphData)
		locations.append(currentLocation)
		data = string.join(dataList, "")
		ttFont['loca'].set(locations)
		ttFont['maxp'].numGlyphs = len(self.glyphs)
		return data
	
	def toXML(self, writer, ttFont, progress=None):
		writer.newline()
		glyphNames = ttFont.getGlyphNames()
		writer.comment("The xMin, yMin, xMax and yMax values\nwill be recalculated by the compiler.")
		writer.newline()
		writer.newline()
		counter = 0
		progressStep = 10
		numGlyphs = len(glyphNames)
		for glyphName in glyphNames:
			if not counter % progressStep and progress is not None:
				progress.setLabel("Dumping 'glyf' table... (%s)" % glyphName)
				progress.increment(progressStep / float(numGlyphs))
			counter = counter + 1
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
				writer.endtag('TTGlyph')
				writer.newline()
			else:
				writer.simpletag('TTGlyph', name=glyphName)
				writer.comment("contains no outline data")
				writer.newline()
			writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		if name <> "TTGlyph":
			return
		if not hasattr(self, "glyphs"):
			self.glyphs = {}
		if not hasattr(self, "glyphOrder"):
			self.glyphOrder = ttFont.getGlyphOrder()
		glyphName = attrs["name"]
		if ttFont.verbose:
			ttLib.debugmsg("unpacking glyph '%s'" % glyphName)
		glyph = Glyph()
		for attr in ['xMin', 'yMin', 'xMax', 'yMax']:
			setattr(glyph, attr, safeEval(attrs.get(attr, '0')))
		self.glyphs[glyphName] = glyph
		for element in content:
			if type(element) <> TupleType:
				continue
			glyph.fromXML(element, ttFont)
		if not ttFont.recalcBBoxes:
			glyph.compact(self, 0)
	
	def setGlyphOrder(self, glyphOrder):
		self.glyphOrder = glyphOrder
	
	def getGlyphName(self, glyphID):
		return self.glyphOrder[glyphID]
	
	def getGlyphID(self, glyphName):
		# XXX optimize with reverse dict!!!
		return self.glyphOrder.index(glyphName)
	
	def keys(self):
		return self.glyphs.keys()
	
	def has_key(self, glyphName):
		return self.glyphs.has_key(glyphName)
	
	__contains__ = has_key
	
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
	
	def compact(self, glyfTable, recalcBBoxes=1):
		data = self.compile(glyfTable, recalcBBoxes)
		self.__dict__.clear()
		self.data = data
	
	def expand(self, glyfTable):
		if not hasattr(self, "data"):
			# already unpacked
			return
		if not self.data:
			# empty char
			self.numberOfContours = 0
			return
		dummy, data = sstruct.unpack2(glyphHeaderFormat, self.data, self)
		del self.data
		if self.isComposite():
			self.decompileComponents(data, glyfTable)
		else:
			self.decompileCoordinates(data)
	
	def compile(self, glyfTable, recalcBBoxes=1):
		if hasattr(self, "data"):
			return self.data
		if self.numberOfContours == 0:
			return ""
		if recalcBBoxes:
			self.recalcBounds(glyfTable)
		data = sstruct.pack(glyphHeaderFormat, self)
		if self.isComposite():
			data = data + self.compileComponents(glyfTable)
		else:
			data = data + self.compileCoordinates()
		# From the spec: "Note that the local offsets should be word-aligned"
		# From a later MS spec: "Note that the local offsets should be long-aligned"
		# Let's be modern and align on 4-byte boundaries.
		if len(data) % 4:
			# add pad bytes
			nPadBytes = 4 - (len(data) % 4)
			data = data + "\0" * nPadBytes
		return data
	
	def toXML(self, writer, ttFont):
		if self.isComposite():
			for compo in self.components:
				compo.toXML(writer, ttFont)
			if hasattr(self, "program"):
				writer.begintag("instructions")
				self.program.toXML(writer, ttFont)
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
				self.program.toXML(writer, ttFont)
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
				if type(element) <> TupleType:
					continue
				name, attrs, content = element
				if name <> "pt":
					continue  # ignore anything but "pt"
				coordinates.append([safeEval(attrs["x"]), safeEval(attrs["y"])])
				flags.append(not not safeEval(attrs["on"]))
			coordinates = numpy.array(coordinates, numpy.int16)
			flags = numpy.array(flags, numpy.int8)
			if not hasattr(self, "coordinates"):
				self.coordinates = coordinates
				self.flags = flags
				self.endPtsOfContours = [len(coordinates)-1]
			else:
				self.coordinates = numpy.concatenate((self.coordinates, coordinates))
				self.flags = numpy.concatenate((self.flags, flags))
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
			self.program = ttProgram.Program()
			for element in content:
				if type(element) <> TupleType:
					continue
				self.program.fromXML(element, ttFont)
	
	def getCompositeMaxpValues(self, glyfTable, maxComponentDepth=1):
		assert self.isComposite()
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
			self.program = ttProgram.Program()
			self.program.fromBytecode(data[:numInstructions])
			data = data[numInstructions:]
			assert len(data) < 4, "bad composite data"
	
	def decompileCoordinates(self, data):
		endPtsOfContours = array.array("h")
		endPtsOfContours.fromstring(data[:2*self.numberOfContours])
		if sys.byteorder <> "big":
			endPtsOfContours.byteswap()
		self.endPtsOfContours = endPtsOfContours.tolist()
		
		data = data[2*self.numberOfContours:]
		
		instructionLength, = struct.unpack(">h", data[:2])
		data = data[2:]
		self.program = ttProgram.Program()
		self.program.fromBytecode(data[:instructionLength])
		data = data[instructionLength:]
		nCoordinates = self.endPtsOfContours[-1] + 1
		flags, xCoordinates, yCoordinates = \
				self.decompileCoordinatesRaw(nCoordinates, data)
		
		# fill in repetitions and apply signs
		coordinates = numpy.zeros((nCoordinates, 2), numpy.int16)
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
		self.coordinates = numpy.add.accumulate(coordinates)
		# discard all flags but for "flagOnCurve"
		self.flags = numpy.bitwise_and(flags, flagOnCurve).astype(numpy.int8)

	def decompileCoordinatesRaw(self, nCoordinates, data):
		# unpack flags and prepare unpacking of coordinates
		flags = numpy.array([0] * nCoordinates, numpy.int8)
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
		if not (0 <= (len(data) - (xDataLen + yDataLen)) < 4):
			raise ttLib.TTLibError, "bad glyph record (leftover bytes: %s)" % (len(data) - (xDataLen + yDataLen))
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
				haveInstructions = hasattr(self, "program")
				more = 0
			compo = self.components[i]
			data = data + compo.compile(more, haveInstructions, glyfTable)
		if haveInstructions:
			instructions = self.program.getBytecode()
			data = data + struct.pack(">h", len(instructions)) + instructions
		return data
			
	
	def compileCoordinates(self):
		assert len(self.coordinates) == len(self.flags)
		data = ""
		endPtsOfContours = array.array("h", self.endPtsOfContours)
		if sys.byteorder <> "big":
			endPtsOfContours.byteswap()
		data = data + endPtsOfContours.tostring()
		instructions = self.program.getBytecode()
		data = data + struct.pack(">h", len(instructions)) + instructions
		nCoordinates = len(self.coordinates)
		
		# make a copy
		coordinates = numpy.array(self.coordinates)
		# absolute to relative coordinates
		coordinates[1:] = numpy.subtract(coordinates[1:], coordinates[:-1])
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
		xPoints = map(int, xPoints)  # work around numpy vs. struct >= 2.5 bug
		yPoints = map(int, yPoints)
		data = data + apply(struct.pack, (xFormat,)+tuple(xPoints))
		data = data + apply(struct.pack, (yFormat,)+tuple(yPoints))
		return data
	
	def recalcBounds(self, glyfTable):
		coordinates, endPts, flags = self.getCoordinates(glyfTable)
		if len(coordinates) > 0:
			self.xMin, self.yMin = numpy.minimum.reduce(coordinates)
			self.xMax, self.yMax = numpy.maximum.reduce(coordinates)
		else:
			self.xMin, self.yMin, self.xMax, self.yMax = (0, 0, 0, 0)
	
	def isComposite(self):
		return self.numberOfContours == -1
	
	def __getitem__(self, componentIndex):
		if not self.isComposite():
			raise ttLib.TTLibError, "can't use glyph as sequence"
		return self.components[componentIndex]
	
	def getCoordinates(self, glyfTable):
		if self.numberOfContours > 0:
			return self.coordinates, self.endPtsOfContours, self.flags
		elif self.isComposite():
			# it's a composite
			allCoords = None
			allFlags = None
			allEndPts = None
			for compo in self.components:
				g = glyfTable[compo.glyphName]
				coordinates, endPts, flags = g.getCoordinates(glyfTable)
				if hasattr(compo, "firstPt"):
					# move according to two reference points
					move = allCoords[compo.firstPt] - coordinates[compo.secondPt]
				else:
					move = compo.x, compo.y
				
				if not hasattr(compo, "transform"):
					if len(coordinates) > 0:
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
						coordinates = numpy.dot(coordinates, compo.transform)
					else:
						# the MS way: first scale, then move
						coordinates = numpy.dot(coordinates, compo.transform)
						coordinates = coordinates + move
					# due to the transformation the coords. are now floats;
					# round them off nicely, and cast to short
					coordinates = numpy.floor(coordinates + 0.5).astype(numpy.int16)
				if allCoords is None or len(allCoords) == 0:
					allCoords = coordinates
					allEndPts = endPts
					allFlags = flags
				else:
					allEndPts = allEndPts + (numpy.array(endPts) + len(allCoords)).tolist()
					if len(coordinates) > 0:
						allCoords = numpy.concatenate((allCoords, coordinates))
						allFlags = numpy.concatenate((allFlags, flags))
			return allCoords, allEndPts, allFlags
		else:
			return numpy.array([], numpy.int16), [], numpy.array([], numpy.int8)
	
	def __cmp__(self, other):
		if self.numberOfContours <= 0:
			return cmp(self.__dict__, other.__dict__)
		else:
			if cmp(len(self.coordinates), len(other.coordinates)):
				return 1
			ctest = numpy.alltrue(numpy.alltrue(numpy.equal(self.coordinates, other.coordinates)))
			ftest = numpy.alltrue(numpy.equal(self.flags, other.flags))
			if not ctest or not ftest:
				return 1
			return (
					cmp(self.endPtsOfContours, other.endPtsOfContours) or
					cmp(self.program, other.instructions)
				)


class GlyphComponent:
	
	def __init__(self):
		pass
	
	def getComponentInfo(self):
		"""Return the base glyph name and a transform."""
		# XXX Ignoring self.firstPt & self.lastpt for now: I need to implement
		# something equivalent in fontTools.objects.glyph (I'd rather not 
		# convert it to an absolute offset, since it is valuable information).
		# This method will now raise "AttributeError: x" on glyphs that use
		# this TT feature.
		if hasattr(self, "transform"):
			[[xx, xy], [yx, yy]] = self.transform
			trans = (xx, xy, yx, yy, self.x, self.y)
		else:
			trans = (1, 0, 0, 1, self.x, self.y)
		return self.glyphName, trans
	
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
				self.firstPt, self.secondPt = int(x), int(y)
			data = data[4:]
		else:
			if self.flags & ARGS_ARE_XY_VALUES:
				self.x, self.y = struct.unpack(">bb", data[:2])
			else:
				x, y = struct.unpack(">BB", data[:2])
				self.firstPt, self.secondPt = int(x), int(y)
			data = data[2:]
		
		if self.flags & WE_HAVE_A_SCALE:
			scale, = struct.unpack(">h", data[:2])
			self.transform = numpy.array(
					[[scale, 0], [0, scale]]) / float(0x4000)  # fixed 2.14
			data = data[2:]
		elif self.flags & WE_HAVE_AN_X_AND_Y_SCALE:
			xscale, yscale = struct.unpack(">hh", data[:4])
			self.transform = numpy.array(
					[[xscale, 0], [0, yscale]]) / float(0x4000)  # fixed 2.14
			data = data[4:]
		elif self.flags & WE_HAVE_A_TWO_BY_TWO:
			(xscale, scale01, 
					scale10, yscale) = struct.unpack(">hhhh", data[:8])
			self.transform = numpy.array(
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
		
		if hasattr(self, "firstPt"):
			if (0 <= self.firstPt <= 255) and (0 <= self.secondPt <= 255):
				data = data + struct.pack(">BB", self.firstPt, self.secondPt)
			else:
				data = data + struct.pack(">HH", self.firstPt, self.secondPt)
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
			transform = numpy.floor(self.transform * 0x4000 + 0.5)
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
		if not hasattr(self, "firstPt"):
			attrs = attrs + [("x", self.x), ("y", self.y)]
		else:
			attrs = attrs + [("firstPt", self.firstPt), ("secondPt", self.secondPt)]
		
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
		if attrs.has_key("firstPt"):
			self.firstPt = safeEval(attrs["firstPt"])
			self.secondPt = safeEval(attrs["secondPt"])
		else:
			self.x = safeEval(attrs["x"])
			self.y = safeEval(attrs["y"])
		if attrs.has_key("scale01"):
			scalex = safeEval(attrs["scalex"])
			scale01 = safeEval(attrs["scale01"])
			scale10 = safeEval(attrs["scale10"])
			scaley = safeEval(attrs["scaley"])
			self.transform = numpy.array([[scalex, scale01], [scale10, scaley]])
		elif attrs.has_key("scalex"):
			scalex = safeEval(attrs["scalex"])
			scaley = safeEval(attrs["scaley"])
			self.transform = numpy.array([[scalex, 0], [0, scaley]])
		elif attrs.has_key("scale"):
			scale = safeEval(attrs["scale"])
			self.transform = numpy.array([[scale, 0], [0, scale]])
		self.flags = safeEval(attrs["flags"])
	
	def __cmp__(self, other):
		if hasattr(self, "transform"):
			if numpy.alltrue(numpy.equal(self.transform, other.transform)):
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
	if type(flag) == StringType:
		flag = ord(flag)
	while flag:
		if flag & 0x01:
			bin = "1" + bin
		else:
			bin = "0" + bin
		flag = flag >> 1
	bin = (14 - len(bin)) * "0" + bin
	return bin

