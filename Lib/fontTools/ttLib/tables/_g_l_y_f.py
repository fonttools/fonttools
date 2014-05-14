"""_g_l_y_f.py -- Converter classes for the 'glyf' table."""


from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools import ttLib
from fontTools.misc.textTools import safeEval
from fontTools.misc.arrayTools import calcBounds, calcIntBounds, pointInRect
from fontTools.misc.bezierTools import calcQuadraticBounds
from fontTools.misc.fixedTools import fixedToFloat as fi2fl, floatToFixed as fl2fi
from . import DefaultTable
from . import ttProgram
import sys
import struct
import array
import warnings

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


class table__g_l_y_f(DefaultTable.DefaultTable):
	
	def decompile(self, data, ttFont):
		loca = ttFont['loca']
		last = int(loca[0])
		noname = 0
		self.glyphs = {}
		self.glyphOrder = glyphOrder = ttFont.getGlyphOrder()
		for i in range(0, len(loca)-1):
			try:
				glyphName = glyphOrder[i]
			except IndexError:
				noname = noname + 1
				glyphName = 'ttxautoglyph%s' % i
			next = int(loca[i+1])
			glyphdata = data[last:next]
			if len(glyphdata) != (next - last):
				raise ttLib.TTLibError("not enough 'glyf' table data")
			glyph = Glyph(glyphdata)
			self.glyphs[glyphName] = glyph
			last = next
		if len(data) > next:
			warnings.warn("too much 'glyf' table data")
		if noname:
			warnings.warn('%s glyphs have no name' % i)
		if not ttFont.lazy:
			for glyph in self.glyphs.values():
				glyph.expand(self)
	
	def compile(self, ttFont):
		if not hasattr(self, "glyphOrder"):
			self.glyphOrder = ttFont.getGlyphOrder()
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
		data = bytesjoin(dataList)
		if 'loca' in ttFont:
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
				progress.increment(progressStep / numGlyphs)
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
	
	def fromXML(self, name, attrs, content, ttFont):
		if name != "TTGlyph":
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
			if not isinstance(element, tuple):
				continue
			name, attrs, content = element
			glyph.fromXML(name, attrs, content, ttFont)
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
		return glyphName in self.glyphs
	
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


class Glyph(object):
	
	def __init__(self, data=""):
		if not data:
			# empty char
			self.numberOfContours = 0
			return
		self.data = data
	
	def compact(self, glyfTable, recalcBBoxes=True):
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
	
	def compile(self, glyfTable, recalcBBoxes=True):
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
			data = data + b"\0" * nPadBytes
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
	
	def fromXML(self, name, attrs, content, ttFont):
		if name == "contour":
			if self.numberOfContours < 0:
				raise ttLib.TTLibError("can't mix composites and contours in glyph")
			self.numberOfContours = self.numberOfContours + 1
			coordinates = GlyphCoordinates()
			flags = []
			for element in content:
				if not isinstance(element, tuple):
					continue
				name, attrs, content = element
				if name != "pt":
					continue  # ignore anything but "pt"
				coordinates.append((safeEval(attrs["x"]), safeEval(attrs["y"])))
				flags.append(not not safeEval(attrs["on"]))
			flags = array.array("B", flags)
			if not hasattr(self, "coordinates"):
				self.coordinates = coordinates
				self.flags = flags
				self.endPtsOfContours = [len(coordinates)-1]
			else:
				self.coordinates.extend (coordinates)
				self.flags.extend(flags)
				self.endPtsOfContours.append(len(self.coordinates)-1)
		elif name == "component":
			if self.numberOfContours > 0:
				raise ttLib.TTLibError("can't mix composites and contours in glyph")
			self.numberOfContours = -1
			if not hasattr(self, "components"):
				self.components = []
			component = GlyphComponent()
			self.components.append(component)
			component.fromXML(name, attrs, content, ttFont)
		elif name == "instructions":
			self.program = ttProgram.Program()
			for element in content:
				if not isinstance(element, tuple):
					continue
				name, attrs, content = element
				self.program.fromXML(name, attrs, content, ttFont)
	
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
		if sys.byteorder != "big":
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
		self.coordinates = coordinates = GlyphCoordinates.zeros(nCoordinates)
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
		coordinates.relativeToAbsolute()
		# discard all flags but for "flagOnCurve"
		self.flags = array.array("B", (f & flagOnCurve for f in flags))

	def decompileCoordinatesRaw(self, nCoordinates, data):
		# unpack flags and prepare unpacking of coordinates
		flags = array.array("B", [0] * nCoordinates)
		# Warning: deep Python trickery going on. We use the struct module to unpack
		# the coordinates. We build a format string based on the flags, so we can
		# unpack the coordinates in one struct.unpack() call.
		xFormat = ">" # big endian
		yFormat = ">" # big endian
		i = j = 0
		while True:
			flag = byteord(data[i])
			i = i + 1
			repeat = 1
			if flag & flagRepeat:
				repeat = byteord(data[i]) + 1
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
		if len(data) - (xDataLen + yDataLen) >= 4:
			warnings.warn("too much glyph data: %d excess bytes" % (len(data) - (xDataLen + yDataLen)))
		xCoordinates = struct.unpack(xFormat, data[:xDataLen])
		yCoordinates = struct.unpack(yFormat, data[xDataLen:xDataLen+yDataLen])
		return flags, xCoordinates, yCoordinates
	
	def compileComponents(self, glyfTable):
		data = b""
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
		data = b""
		endPtsOfContours = array.array("h", self.endPtsOfContours)
		if sys.byteorder != "big":
			endPtsOfContours.byteswap()
		data = data + endPtsOfContours.tostring()
		instructions = self.program.getBytecode()
		data = data + struct.pack(">h", len(instructions)) + instructions
		nCoordinates = len(self.coordinates)
		
		coordinates = self.coordinates.copy()
		coordinates.absoluteToRelative()
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
			flag = flags[i]
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
			if flag == lastflag and repeat != 255:
				repeat = repeat + 1
				if repeat == 1:
					compressedflags.append(flag)
				else:
					compressedflags[-2] = flag | flagRepeat
					compressedflags[-1] = repeat
			else:
				repeat = 0
				compressedflags.append(flag)
			lastflag = flag
		data = data + array.array("B", compressedflags).tostring()
		if coordinates.isFloat():
			# Warn?
			xPoints = [int(round(x)) for x in xPoints]
			yPoints = [int(round(y)) for y in xPoints]
		data = data + struct.pack(*(xFormat,)+tuple(xPoints))
		data = data + struct.pack(*(yFormat,)+tuple(yPoints))
		return data
	
	def recalcBounds(self, glyfTable):
		coords, endPts, flags = self.getCoordinates(glyfTable)
		if len(coords) > 0:
			if 0:
				# This branch calculates exact glyph outline bounds
				# analytically, handling cases without on-curve
				# extremas, etc.  However, the glyf table header
				# simply says that the bounds should be min/max x/y
				# "for coordinate data", so I suppose that means no
				# fancy thing here, just get extremas of all coord
				# points (on and off).  As such, this branch is
				# disabled.

				# Collect on-curve points
				onCurveCoords = [coords[j] for j in range(len(coords))
						 if flags[j] & flagOnCurve]
				# Add implicit on-curve points
				start = 0
				for end in endPts:
					last = end
					for j in range(start, end + 1):
						if not ((flags[j] | flags[last]) & flagOnCurve):
							x = (coords[last][0] + coords[j][0]) / 2
							y = (coords[last][1] + coords[j][1]) / 2
							onCurveCoords.append((x,y))
						last = j
					start = end + 1
				# Add bounds for curves without an explicit extrema
				start = 0
				for end in endPts:
					last = end
					for j in range(start, end + 1):
						if not (flags[j] & flagOnCurve):
							next = j + 1 if j < end else start
							bbox = calcBounds([coords[last], coords[next]])
							if not pointInRect(coords[j], bbox):
								# Ouch!
								warnings.warn("Outline has curve with implicit extrema.")
								# Ouch!  Find analytical curve bounds.
								pthis = coords[j]
								plast = coords[last]
								if not (flags[last] & flagOnCurve):
									plast = ((pthis[0]+plast[0])/2, (pthis[1]+plast[1])/2)
								pnext = coords[next]
								if not (flags[next] & flagOnCurve):
									pnext = ((pthis[0]+pnext[0])/2, (pthis[1]+pnext[1])/2)
								bbox = calcQuadraticBounds(plast, pthis, pnext)
								onCurveCoords.append((bbox[0],bbox[1]))
								onCurveCoords.append((bbox[2],bbox[3]))
						last = j
					start = end + 1

				self.xMin, self.yMin, self.xMax, self.yMax = calcIntBounds(onCurveCoords)
			else:
				self.xMin, self.yMin, self.xMax, self.yMax = calcIntBounds(coords)
		else:
			self.xMin, self.yMin, self.xMax, self.yMax = (0, 0, 0, 0)
	
	def isComposite(self):
		"""Can be called on compact or expanded glyph."""
		if hasattr(self, "data"):
			return struct.unpack(">h", self.data[:2])[0] == -1
		else:
			return self.numberOfContours == -1
	
	def __getitem__(self, componentIndex):
		if not self.isComposite():
			raise ttLib.TTLibError("can't use glyph as sequence")
		return self.components[componentIndex]
	
	def getCoordinates(self, glyfTable):
		if self.numberOfContours > 0:
			return self.coordinates, self.endPtsOfContours, self.flags
		elif self.isComposite():
			# it's a composite
			allCoords = GlyphCoordinates()
			allFlags = array.array("B")
			allEndPts = []
			for compo in self.components:
				g = glyfTable[compo.glyphName]
				coordinates, endPts, flags = g.getCoordinates(glyfTable)
				if hasattr(compo, "firstPt"):
					# move according to two reference points
					x1,y1 = allCoords[compo.firstPt]
					x2,y2 = coordinates[compo.secondPt]
					move = x1-x2, y1-y2
				else:
					move = compo.x, compo.y
				
				coordinates = GlyphCoordinates(coordinates)
				if not hasattr(compo, "transform"):
					coordinates.translate(move)
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
						coordinates.translate(move)
						coordinates.transform(compo.transform)
					else:
						# the MS way: first scale, then move
						coordinates.transform(compo.transform)
						coordinates.translate(move)
				offset = len(allCoords)
				allEndPts.extend(e + offset for e in endPts)
				allCoords.extend(coordinates)
				allFlags.extend(flags)
			return allCoords, allEndPts, allFlags
		else:
			return GlyphCoordinates(), [], array.array("B")

	def getComponentNames(self, glyfTable):
		if not hasattr(self, "data"):
			if self.isComposite():
				return [c.glyphName for c in self.components]
			else:
				return []

		# Extract components without expanding glyph

		if not self.data or struct.unpack(">h", self.data[:2])[0] >= 0:
			return []  # Not composite

		data = self.data
		i = 10
		components = []
		more = 1
		while more:
			flags, glyphID = struct.unpack(">HH", data[i:i+4])
			i += 4
			flags = int(flags)
			components.append(glyfTable.getGlyphName(int(glyphID)))

			if flags & ARG_1_AND_2_ARE_WORDS: i += 4
			else: i += 2
			if flags & WE_HAVE_A_SCALE: i += 2
			elif flags & WE_HAVE_AN_X_AND_Y_SCALE: i += 4
			elif flags & WE_HAVE_A_TWO_BY_TWO: i += 8
			more = flags & MORE_COMPONENTS

		return components

	def removeHinting(self):
		if not hasattr(self, "data"):
			self.program = ttProgram.Program()
			self.program.fromBytecode([])
			return

		# Remove instructions without expanding glyph

		if not self.data:
			return
		numContours = struct.unpack(">h", self.data[:2])[0]
		data = array.array("B", self.data)
		i = 10
		if numContours >= 0:
			i += 2 * numContours # endPtsOfContours
			nCoordinates = ((data[i-2] << 8) | data[i-1]) + 1
			instructionLen = (data[i] << 8) | data[i+1]
			# Zero it
			data[i] = data [i+1] = 0
			i += 2
			if instructionLen:
				# Splice it out
				data = data[:i] + data[i+instructionLen:]
				if instructionLen % 4:
					# We now have to go ahead and drop
					# the old padding.  Otherwise with
					# padding we have to add, we may
					# end up with more than 3 bytes of
					# padding.
					coordBytes = 0
					j = 0
					while True:
						flag = data[i]
						i = i + 1
						repeat = 1
						if flag & flagRepeat:
							repeat = data[i] + 1
							i = i + 1
						xBytes = yBytes = 0
						if flag & flagXShort:
							xBytes = 1
						elif not (flag & flagXsame):
							xBytes = 2
						if flag & flagYShort:
							yBytes = 1
						elif not (flag & flagYsame):
							yBytes = 2
						coordBytes += (xBytes + yBytes) * repeat
						j += repeat
						if j >= nCoordinates:
							break
					assert j == nCoordinates, "bad glyph flags"
					data = data[:i + coordBytes]
		else:
			more = 1
			while more:
				flags =(data[i] << 8) | data[i+1]
				# Turn instruction flag off
				flags &= ~WE_HAVE_INSTRUCTIONS
				data[i+0] = flags >> 8
				data[i+1] = flags & 0xFF
				i += 4
				flags = int(flags)

				if flags & ARG_1_AND_2_ARE_WORDS: i += 4
				else: i += 2
				if flags & WE_HAVE_A_SCALE: i += 2
				elif flags & WE_HAVE_AN_X_AND_Y_SCALE: i += 4
				elif flags & WE_HAVE_A_TWO_BY_TWO: i += 8
				more = flags & MORE_COMPONENTS

			# Cut off
			data = data[:i]

		data = data.tostring()

		if len(data) % 4:
			# add pad bytes
			nPadBytes = 4 - (len(data) % 4)
			data = data + b"\0" * nPadBytes

		self.data = data

	def __ne__(self, other):
		return not self.__eq__(other)
	def __eq__(self, other):
		if type(self) != type(other):
			return NotImplemented
		return self.__dict__ == other.__dict__


class GlyphComponent(object):
	
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
			self.transform = [[fi2fl(scale,14), 0], [0, fi2fl(scale,14)]]  # fixed 2.14
			data = data[2:]
		elif self.flags & WE_HAVE_AN_X_AND_Y_SCALE:
			xscale, yscale = struct.unpack(">hh", data[:4])
			self.transform = [[fi2fl(xscale,14), 0], [0, fi2fl(yscale,14)]]  # fixed 2.14
			data = data[4:]
		elif self.flags & WE_HAVE_A_TWO_BY_TWO:
			(xscale, scale01, 
					scale10, yscale) = struct.unpack(">hhhh", data[:8])
			self.transform = [[fi2fl(xscale,14), fi2fl(scale01,14)],
					  [fi2fl(scale10,14), fi2fl(yscale,14)]] # fixed 2.14
			data = data[8:]
		more = self.flags & MORE_COMPONENTS
		haveInstructions = self.flags & WE_HAVE_INSTRUCTIONS
		self.flags = self.flags & (ROUND_XY_TO_GRID | USE_MY_METRICS | 
				SCALED_COMPONENT_OFFSET | UNSCALED_COMPONENT_OFFSET |
				NON_OVERLAPPING)
		return more, haveInstructions, data
	
	def compile(self, more, haveInstructions, glyfTable):
		data = b""
		
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
			transform = [[fl2fi(x,14) for x in row] for row in self.transform]
			if transform[0][1] or transform[1][0]:
				flags = flags | WE_HAVE_A_TWO_BY_TWO
				data = data + struct.pack(">hhhh", 
						transform[0][0], transform[0][1],
						transform[1][0], transform[1][1])
			elif transform[0][0] != transform[1][1]:
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
			transform = self.transform
			if transform[0][1] or transform[1][0]:
				attrs = attrs + [
						("scalex", transform[0][0]), ("scale01", transform[0][1]),
						("scale10", transform[1][0]), ("scaley", transform[1][1]),
						]
			elif transform[0][0] != transform[1][1]:
				attrs = attrs + [
						("scalex", transform[0][0]), ("scaley", transform[1][1]),
						]
			else:
				attrs = attrs + [("scale", transform[0][0])]
		attrs = attrs + [("flags", hex(self.flags))]
		writer.simpletag("component", attrs)
		writer.newline()
	
	def fromXML(self, name, attrs, content, ttFont):
		self.glyphName = attrs["glyphName"]
		if "firstPt" in attrs:
			self.firstPt = safeEval(attrs["firstPt"])
			self.secondPt = safeEval(attrs["secondPt"])
		else:
			self.x = safeEval(attrs["x"])
			self.y = safeEval(attrs["y"])
		if "scale01" in attrs:
			scalex = safeEval(attrs["scalex"])
			scale01 = safeEval(attrs["scale01"])
			scale10 = safeEval(attrs["scale10"])
			scaley = safeEval(attrs["scaley"])
			self.transform = [[scalex, scale01], [scale10, scaley]]
		elif "scalex" in attrs:
			scalex = safeEval(attrs["scalex"])
			scaley = safeEval(attrs["scaley"])
			self.transform = [[scalex, 0], [0, scaley]]
		elif "scale" in attrs:
			scale = safeEval(attrs["scale"])
			self.transform = [[scale, 0], [0, scale]]
		self.flags = safeEval(attrs["flags"])
	
	def __ne__(self, other):
		return not self.__eq__(other)
	def __eq__(self, other):
		if type(self) != type(other):
			return NotImplemented
		return self.__dict__ == other.__dict__

class GlyphCoordinates(object):

	def __init__(self, iterable=[]):
		self._a = array.array("h")
		self.extend(iterable)

	def isFloat(self):
		return self._a.typecode == 'f'

	def _ensureFloat(self):
		if self.isFloat():
			return
		self._a = array.array("f", self._a)

	def _checkFloat(self, p):
		if any(isinstance(v, float) for v in p):
			p = [int(v) if int(v) == v else v for v in p]
			if any(isinstance(v, float) for v in p):
				self._ensureFloat()
		return p

	@staticmethod
	def zeros(count):
		return GlyphCoordinates([(0,0)] * count)

	def copy(self):
		c = GlyphCoordinates()
		c._a.extend(self._a)
		return c

	def __len__(self):
		return len(self._a) // 2

	def __getitem__(self, k):
		if isinstance(k, slice):
			indices = range(*k.indices(len(self)))
			return [self[i] for i in indices]
		return self._a[2*k],self._a[2*k+1]

	def __setitem__(self, k, v):
		if isinstance(k, slice):
			indices = range(*k.indices(len(self)))
			# XXX This only works if len(v) == len(indices)
			# TODO Implement __delitem__
			for j,i in enumerate(indices):
				self[i] = v[j]
			return
		v = self._checkFloat(v)
		self._a[2*k],self._a[2*k+1] = v

	def __repr__(self):
		return 'GlyphCoordinates(['+','.join(str(c) for c in self)+'])'

	def append(self, p):
		p = self._checkFloat(p)
		self._a.extend(tuple(p))

	def extend(self, iterable):
		for p in iterable:
			p = self._checkFloat(p)
			self._a.extend(p)

	def relativeToAbsolute(self):
		a = self._a
		x,y = 0,0
		for i in range(len(a) // 2):
			a[2*i  ] = x = a[2*i  ] + x
			a[2*i+1] = y = a[2*i+1] + y

	def absoluteToRelative(self):
		a = self._a
		x,y = 0,0
		for i in range(len(a) // 2):
			dx = a[2*i  ] - x
			dy = a[2*i+1] - y
			x = a[2*i  ]
			y = a[2*i+1]
			a[2*i  ] = dx
			a[2*i+1] = dy

	def translate(self, p):
		(x,y) = p
		a = self._a
		for i in range(len(a) // 2):
			a[2*i  ] += x
			a[2*i+1] += y

	def transform(self, t):
		a = self._a
		for i in range(len(a) // 2):
			x = a[2*i  ]
			y = a[2*i+1]
			px = x * t[0][0] + y * t[1][0]
			py = x * t[0][1] + y * t[1][1]
			self[i] = (px, py)

	def __ne__(self, other):
		return not self.__eq__(other)
	def __eq__(self, other):
		if type(self) != type(other):
			return NotImplemented
		return self._a == other._a


def reprflag(flag):
	bin = ""
	if isinstance(flag, str):
		flag = byteord(flag)
	while flag:
		if flag & 0x01:
			bin = "1" + bin
		else:
			bin = "0" + bin
		flag = flag >> 1
	bin = (14 - len(bin)) * "0" + bin
	return bin

