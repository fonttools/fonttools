"""_g_l_y_f.py -- Converter classes for the 'glyf' table."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools import ttLib
from fontTools.misc.textTools import safeEval, pad
from fontTools.misc.arrayTools import calcBounds, calcIntBounds, pointInRect
from fontTools.misc.bezierTools import calcQuadraticBounds
from fontTools.misc.fixedTools import fixedToFloat as fi2fl, floatToFixed as fl2fi
from numbers import Number
from . import DefaultTable
from . import ttProgram
import sys
import struct
import array
import logging


log = logging.getLogger(__name__)

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

	# this attribute controls the amount of padding applied to glyph data upon compile.
	# Glyph lenghts are aligned to multiples of the specified value. 
	# Allowed values are (0, 1, 2, 4). '0' means no padding; '1' (default) also means
	# no padding, except for when padding would allow to use short loca offsets.
	padding = 1

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
		if len(data) - next >= 4:
			log.warning(
				"too much 'glyf' table data: expected %d, received %d bytes",
				next, len(data))
		if noname:
			log.warning('%s glyphs have no name', noname)
		if ttFont.lazy is False: # Be lazy for None and True
			for glyph in self.glyphs.values():
				glyph.expand(self)

	def compile(self, ttFont):
		if not hasattr(self, "glyphOrder"):
			self.glyphOrder = ttFont.getGlyphOrder()
		padding = self.padding
		assert padding in (0, 1, 2, 4)
		locations = []
		currentLocation = 0
		dataList = []
		recalcBBoxes = ttFont.recalcBBoxes
		for glyphName in self.glyphOrder:
			glyph = self.glyphs[glyphName]
			glyphData = glyph.compile(self, recalcBBoxes)
			if padding > 1:
				glyphData = pad(glyphData, size=padding)
			locations.append(currentLocation)
			currentLocation = currentLocation + len(glyphData)
			dataList.append(glyphData)
		locations.append(currentLocation)

		if padding == 1 and currentLocation < 0x20000:
			# See if we can pad any odd-lengthed glyphs to allow loca
			# table to use the short offsets.
			indices = [i for i,glyphData in enumerate(dataList) if len(glyphData) % 2 == 1]
			if indices and currentLocation + len(indices) < 0x20000:
				# It fits.  Do it.
				for i in indices:
					dataList[i] += b'\0'
				currentLocation = 0
				for i,glyphData in enumerate(dataList):
					locations[i] = currentLocation
					currentLocation += len(glyphData)
				locations[len(dataList)] = currentLocation

		data = bytesjoin(dataList)
		if 'loca' in ttFont:
			ttFont['loca'].set(locations)
		if 'maxp' in ttFont:
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
		log.debug("unpacking glyph '%s'", glyphName)
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

_flagSignBytes = {
	0: 2,
	flagXsame: 0,
	flagXShort|flagXsame: +1,
	flagXShort: -1,
	flagYsame: 0,
	flagYShort|flagYsame: +1,
	flagYShort: -1,
}

def flagBest(x, y, onCurve):
	"""For a given x,y delta pair, returns the flag that packs this pair
	most efficiently, as well as the number of byte cost of such flag."""

	flag = flagOnCurve if onCurve else 0
	cost = 0
	# do x
	if x == 0:
		flag = flag | flagXsame
	elif -255 <= x <= 255:
		flag = flag | flagXShort
		if x > 0:
			flag = flag | flagXsame
		cost += 1
	else:
		cost += 2
	# do y
	if y == 0:
		flag = flag | flagYsame
	elif -255 <= y <= 255:
		flag = flag | flagYShort
		if y > 0:
			flag = flag | flagYsame
		cost += 1
	else:
		cost += 2
	return flag, cost

def flagFits(newFlag, oldFlag, mask):
	newBytes = _flagSignBytes[newFlag & mask]
	oldBytes = _flagSignBytes[oldFlag & mask]
	return newBytes == oldBytes or abs(newBytes) > abs(oldBytes)

def flagSupports(newFlag, oldFlag):
	return ((oldFlag & flagOnCurve) == (newFlag & flagOnCurve) and
		flagFits(newFlag, oldFlag, flagXsame|flagXShort) and
		flagFits(newFlag, oldFlag, flagYsame|flagYShort))

def flagEncodeCoord(flag, mask, coord, coordBytes):
	byteCount = _flagSignBytes[flag & mask]
	if byteCount == 1:
		coordBytes.append(coord)
	elif byteCount == -1:
		coordBytes.append(-coord)
	elif byteCount == 2:
		coordBytes.append((coord >> 8) & 0xFF)
		coordBytes.append(coord & 0xFF)

def flagEncodeCoords(flag, x, y, xBytes, yBytes):
	flagEncodeCoord(flag, flagXsame|flagXShort, x, xBytes)
	flagEncodeCoord(flag, flagYsame|flagYShort, y, yBytes)


ARG_1_AND_2_ARE_WORDS		= 0x0001  # if set args are words otherwise they are bytes
ARGS_ARE_XY_VALUES		= 0x0002  # if set args are xy values, otherwise they are points
ROUND_XY_TO_GRID		= 0x0004  # for the xy values if above is true
WE_HAVE_A_SCALE			= 0x0008  # Sx = Sy, otherwise scale == 1.0
NON_OVERLAPPING			= 0x0010  # set to same value for all components (obsolete!)
MORE_COMPONENTS			= 0x0020  # indicates at least one more glyph after this one
WE_HAVE_AN_X_AND_Y_SCALE	= 0x0040  # Sx, Sy
WE_HAVE_A_TWO_BY_TWO		= 0x0080  # t00, t01, t10, t11
WE_HAVE_INSTRUCTIONS		= 0x0100  # instructions follow
USE_MY_METRICS			= 0x0200  # apply these metrics to parent glyph
OVERLAP_COMPOUND		= 0x0400  # used by Apple in GX fonts
SCALED_COMPONENT_OFFSET		= 0x0800  # composite designed to have the component offset scaled (designed for Apple)
UNSCALED_COMPONENT_OFFSET	= 0x1000  # composite designed not to have the component offset scaled (designed for MS)


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
			del self.data
			self.numberOfContours = 0
			return
		dummy, data = sstruct.unpack2(glyphHeaderFormat, self.data, self)
		del self.data
		# Some fonts (eg. Neirizi.ttf) have a 0 for numberOfContours in
		# some glyphs; decompileCoordinates assumes that there's at least
		# one, so short-circuit here.
		if self.numberOfContours == 0:
			return
		if self.isComposite():
			self.decompileComponents(data, glyfTable)
		else:
			self.decompileCoordinates(data)

	def compile(self, glyfTable, recalcBBoxes=True):
		if hasattr(self, "data"):
			if recalcBBoxes:
				# must unpack glyph in order to recalculate bounding box
				self.expand(glyfTable)
			else:
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
			if len(data) >= 4:
				log.warning(
					"too much glyph data at the end of composite glyph: %d excess bytes",
					len(data))

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
			log.warning(
				"too much glyph data: %d excess bytes", len(data) - (xDataLen + yDataLen))
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
		data = []
		endPtsOfContours = array.array("h", self.endPtsOfContours)
		if sys.byteorder != "big":
			endPtsOfContours.byteswap()
		data.append(endPtsOfContours.tostring())
		instructions = self.program.getBytecode()
		data.append(struct.pack(">h", len(instructions)))
		data.append(instructions)

		deltas = self.coordinates.copy()
		if deltas.isFloat():
			# Warn?
			deltas.toInt()
		deltas.absoluteToRelative()

		# TODO(behdad): Add a configuration option for this?
		deltas = self.compileDeltasGreedy(self.flags, deltas)
		#deltas = self.compileDeltasOptimal(self.flags, deltas)

		data.extend(deltas)
		return bytesjoin(data)

	def compileDeltasGreedy(self, flags, deltas):
		# Implements greedy algorithm for packing coordinate deltas:
		# uses shortest representation one coordinate at a time.
		compressedflags = []
		xPoints = []
		yPoints = []
		lastflag = None
		repeat = 0
		for flag,(x,y) in zip(flags, deltas):
			# Oh, the horrors of TrueType
			# do x
			if x == 0:
				flag = flag | flagXsame
			elif -255 <= x <= 255:
				flag = flag | flagXShort
				if x > 0:
					flag = flag | flagXsame
				else:
					x = -x
				xPoints.append(bytechr(x))
			else:
				xPoints.append(struct.pack(">h", x))
			# do y
			if y == 0:
				flag = flag | flagYsame
			elif -255 <= y <= 255:
				flag = flag | flagYShort
				if y > 0:
					flag = flag | flagYsame
				else:
					y = -y
				yPoints.append(bytechr(y))
			else:
				yPoints.append(struct.pack(">h", y))
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
		compressedFlags = array.array("B", compressedflags).tostring()
		compressedXs = bytesjoin(xPoints)
		compressedYs = bytesjoin(yPoints)
		return (compressedFlags, compressedXs, compressedYs)

	def compileDeltasOptimal(self, flags, deltas):
		# Implements optimal, dynaic-programming, algorithm for packing coordinate
		# deltas.  The savings are negligible :(.
		candidates = []
		bestTuple = None
		bestCost = 0
		repeat = 0
		for flag,(x,y) in zip(flags, deltas):
			# Oh, the horrors of TrueType
			flag, coordBytes = flagBest(x, y, flag)
			bestCost += 1 + coordBytes
			newCandidates = [(bestCost, bestTuple, flag, coordBytes),
							(bestCost+1, bestTuple, (flag|flagRepeat), coordBytes)]
			for lastCost,lastTuple,lastFlag,coordBytes in candidates:
				if lastCost + coordBytes <= bestCost + 1 and (lastFlag & flagRepeat) and (lastFlag < 0xff00) and flagSupports(lastFlag, flag):
					if (lastFlag & 0xFF) == (flag|flagRepeat) and lastCost == bestCost + 1:
						continue
					newCandidates.append((lastCost + coordBytes, lastTuple, lastFlag+256, coordBytes))
			candidates = newCandidates
			bestTuple = min(candidates, key=lambda t:t[0])
			bestCost = bestTuple[0]

		flags = []
		while bestTuple:
			cost, bestTuple, flag, coordBytes = bestTuple
			flags.append(flag)
		flags.reverse()

		compressedFlags = array.array("B")
		compressedXs = array.array("B")
		compressedYs = array.array("B")
		coords = iter(deltas)
		ff = []
		for flag in flags:
			repeatCount, flag = flag >> 8, flag & 0xFF
			compressedFlags.append(flag)
			if flag & flagRepeat:
				assert(repeatCount > 0)
				compressedFlags.append(repeatCount)
			else:
				assert(repeatCount == 0)
			for i in range(1 + repeatCount):
				x,y = next(coords)
				flagEncodeCoords(flag, x, y, compressedXs, compressedYs)
				ff.append(flag)
		try:
			next(coords)
			raise Exception("internal error")
		except StopIteration:
			pass
		compressedFlags = compressedFlags.tostring()
		compressedXs = compressedXs.tostring()
		compressedYs = compressedYs.tostring()

		return (compressedFlags, compressedXs, compressedYs)

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
								log.warning("Outline has curve with implicit extrema.")
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
		if hasattr(self, "data") and self.data:
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

	def trim(self, remove_hinting=False):
		""" Remove padding and, if requested, hinting, from a glyph.
			This works on both expanded and compacted glyphs, without
			expanding it."""
		if not hasattr(self, "data"):
			if remove_hinting:
				self.program = ttProgram.Program()
				self.program.fromBytecode([])
			# No padding to trim.
			return
		if not self.data:
			return
		numContours = struct.unpack(">h", self.data[:2])[0]
		data = array.array("B", self.data)
		i = 10
		if numContours >= 0:
			i += 2 * numContours # endPtsOfContours
			nCoordinates = ((data[i-2] << 8) | data[i-1]) + 1
			instructionLen = (data[i] << 8) | data[i+1]
			if remove_hinting:
				# Zero instruction length
				data[i] = data [i+1] = 0
				i += 2
				if instructionLen:
					# Splice it out
					data = data[:i] + data[i+instructionLen:]
				instructionLen = 0
			else:
				i += 2 + instructionLen

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
			i += coordBytes
			# Remove padding
			data = data[:i]
		else:
			more = 1
			we_have_instructions = False
			while more:
				flags =(data[i] << 8) | data[i+1]
				if remove_hinting:
					flags &= ~WE_HAVE_INSTRUCTIONS
				if flags & WE_HAVE_INSTRUCTIONS:
					we_have_instructions = True
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
			if we_have_instructions:
				instructionLen = (data[i] << 8) | data[i+1]
				i += 2 + instructionLen
			# Remove padding
			data = data[:i]

		self.data = data.tostring()

	def removeHinting(self):
		self.trim (remove_hinting=True)

	def draw(self, pen, glyfTable, offset=0):

		if self.isComposite():
			for component in self.components:
				glyphName, transform = component.getComponentInfo()
				pen.addComponent(glyphName, transform)
			return

		coordinates, endPts, flags = self.getCoordinates(glyfTable)
		if offset:
			coordinates = coordinates.copy()
			coordinates.translate((offset, 0))
		start = 0
		for end in endPts:
			end = end + 1
			contour = coordinates[start:end]
			cFlags = flags[start:end]
			start = end
			if 1 not in cFlags:
				# There is not a single on-curve point on the curve,
				# use pen.qCurveTo's special case by specifying None
				# as the on-curve point.
				contour.append(None)
				pen.qCurveTo(*contour)
			else:
				# Shuffle the points so that contour the is guaranteed
				# to *end* in an on-curve point, which we'll use for
				# the moveTo.
				firstOnCurve = cFlags.index(1) + 1
				contour = contour[firstOnCurve:] + contour[:firstOnCurve]
				cFlags = cFlags[firstOnCurve:] + cFlags[:firstOnCurve]
				pen.moveTo(contour[-1])
				while contour:
					nextOnCurve = cFlags.index(1) + 1
					if nextOnCurve == 1:
						pen.lineTo(contour[0])
					else:
						pen.qCurveTo(*contour[:nextOnCurve])
					contour = contour[nextOnCurve:]
					cFlags = cFlags[nextOnCurve:]
			pen.closePath()

	def __eq__(self, other):
		if type(self) != type(other):
			return NotImplemented
		return self.__dict__ == other.__dict__

	def __ne__(self, other):
		result = self.__eq__(other)
		return result if result is NotImplemented else not result

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
			x = int(round(self.x))
			y = int(round(self.y))
			flags = flags | ARGS_ARE_XY_VALUES
			if (-128 <= x <= 127) and (-128 <= y <= 127):
				data = data + struct.pack(">bb", x, y)
			else:
				data = data + struct.pack(">hh", x, y)
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

	def __eq__(self, other):
		if type(self) != type(other):
			return NotImplemented
		return self.__dict__ == other.__dict__

	def __ne__(self, other):
		result = self.__eq__(other)
		return result if result is NotImplemented else not result

class GlyphCoordinates(object):

	def __init__(self, iterable=[], typecode="h"):
		self._a = array.array(typecode)
		self.extend(iterable)

	def isFloat(self):
		return self._a.typecode == 'f'

	def _ensureFloat(self):
		if self.isFloat():
			return
		# The conversion to list() is to work around Jython bug
		self._a = array.array("f", list(self._a))

	def _checkFloat(self, p):
		if self.isFloat():
			return p
		if any(isinstance(v, float) for v in p):
			p = [int(v) if int(v) == v else v for v in p]
			if any(isinstance(v, float) for v in p):
				self._ensureFloat()
		return p

	@staticmethod
	def zeros(count):
		return GlyphCoordinates([(0,0)] * count)

	def copy(self):
		c = GlyphCoordinates(typecode=self._a.typecode)
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
			for j,i in enumerate(indices):
				self[i] = v[j]
			return
		v = self._checkFloat(v)
		self._a[2*k],self._a[2*k+1] = v

	def __delitem__(self, i):
		i = (2*i) % len(self._a)
		del self._a[i]
		del self._a[i]


	def __repr__(self):
		return 'GlyphCoordinates(['+','.join(str(c) for c in self)+'])'

	def append(self, p):
		p = self._checkFloat(p)
		self._a.extend(tuple(p))

	def extend(self, iterable):
		for p in iterable:
			p = self._checkFloat(p)
			self._a.extend(p)

	def toInt(self):
		if not self.isFloat():
			return
		a = array.array("h")
		for n in self._a:
			a.append(int(round(n)))
		self._a = a

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
		"""
		>>> GlyphCoordinates([(1,2)]).translate((.5,0))
		"""
		(x,y) = self._checkFloat(p)
		a = self._a
		for i in range(len(a) // 2):
			a[2*i  ] += x
			a[2*i+1] += y

	def scale(self, p):
		"""
		>>> GlyphCoordinates([(1,2)]).scale((.5,0))
		"""
		(x,y) = self._checkFloat(p)
		a = self._a
		for i in range(len(a) // 2):
			a[2*i  ] *= x
			a[2*i+1] *= y

	def transform(self, t):
		"""
		>>> GlyphCoordinates([(1,2)]).transform(((.5,0),(.2,.5)))
		"""
		a = self._a
		for i in range(len(a) // 2):
			x = a[2*i  ]
			y = a[2*i+1]
			px = x * t[0][0] + y * t[1][0]
			py = x * t[0][1] + y * t[1][1]
			self[i] = (px, py)

	def __eq__(self, other):
		"""
		>>> g = GlyphCoordinates([(1,2)])
		>>> g2 = GlyphCoordinates([(1.0,2)])
		>>> g3 = GlyphCoordinates([(1.5,2)])
		>>> g == g2
		True
		>>> g == g3
		False
		>>> g2 == g3
		False
		"""
		if type(self) != type(other):
			return NotImplemented
		return self._a == other._a

	def __ne__(self, other):
		"""
		>>> g = GlyphCoordinates([(1,2)])
		>>> g2 = GlyphCoordinates([(1.0,2)])
		>>> g3 = GlyphCoordinates([(1.5,2)])
		>>> g != g2
		False
		>>> g != g3
		True
		>>> g2 != g3
		True
		"""
		result = self.__eq__(other)
		return result if result is NotImplemented else not result

	# Math operations

	def __pos__(self):
		"""
		>>> g = GlyphCoordinates([(1,2)])
		>>> g
		GlyphCoordinates([(1, 2)])
		>>> g2 = +g
		>>> g2
		GlyphCoordinates([(1, 2)])
		>>> g2.translate((1,0))
		>>> g2
		GlyphCoordinates([(2, 2)])
		>>> g
		GlyphCoordinates([(1, 2)])
		"""
		return self.copy()
	def __neg__(self):
		"""
		>>> g = GlyphCoordinates([(1,2)])
		>>> g
		GlyphCoordinates([(1, 2)])
		>>> g2 = -g
		>>> g2
		GlyphCoordinates([(-1, -2)])
		>>> g
		GlyphCoordinates([(1, 2)])
		"""
		r = self.copy()
		a = r._a
		for i in range(len(a)):
			a[i] = -a[i]
		return r
	def __abs__(self):
		"""
		>>> g = GlyphCoordinates([(-1.5,2)])
		>>> g
		GlyphCoordinates([(-1.5, 2.0)])
		>>> g2 = abs(g)
		>>> g
		GlyphCoordinates([(-1.5, 2.0)])
		>>> g2
		GlyphCoordinates([(1.5, 2.0)])
		"""
		r = self.copy()
		a = r._a
		for i in range(len(a)):
			a[i] = abs(a[i])
		return r
	def __round__(self):
		"""
		Note: This is Python 3 only.  Python 2 does not call __round__.
		As such, we cannot test this method either. :(
		"""
		r = self.copy()
		r.toInt()
		return r

	def __add__(self, other): return self.copy().__iadd__(other)
	def __sub__(self, other): return self.copy().__isub__(other)
	def __mul__(self, other): return self.copy().__imul__(other)
	def __truediv__(self, other): return self.copy().__itruediv__(other)

	__radd__ = __add__
	__rmul__ = __mul__
	def __rsub__(self, other): return other + (-self)

	def __iadd__(self, other):
		"""
		>>> g = GlyphCoordinates([(1,2)])
		>>> g += (.5,0)
		>>> g
		GlyphCoordinates([(1.5, 2.0)])
		>>> g2 = GlyphCoordinates([(3,4)])
		>>> g += g2
		>>> g
		GlyphCoordinates([(4.5, 6.0)])
		"""
		if isinstance(other, tuple):
			assert len(other) ==  2
			self.translate(other)
			return self
		if isinstance(other, GlyphCoordinates):
			if other.isFloat(): self._ensureFloat()
			other = other._a
			a = self._a
			assert len(a) == len(other)
			for i in range(len(a)):
				a[i] += other[i]
			return self
		return NotImplemented

	def __isub__(self, other):
		"""
		>>> g = GlyphCoordinates([(1,2)])
		>>> g -= (.5,0)
		>>> g
		GlyphCoordinates([(0.5, 2.0)])
		>>> g2 = GlyphCoordinates([(3,4)])
		>>> g -= g2
		>>> g
		GlyphCoordinates([(-2.5, -2.0)])
		"""
		if isinstance(other, tuple):
			assert len(other) ==  2
			self.translate((-other[0],-other[1]))
			return self
		if isinstance(other, GlyphCoordinates):
			if other.isFloat(): self._ensureFloat()
			other = other._a
			a = self._a
			assert len(a) == len(other)
			for i in range(len(a)):
				a[i] -= other[i]
			return self
		return NotImplemented

	def __imul__(self, other):
		"""
		>>> g = GlyphCoordinates([(1,2)])
		>>> g *= (2,.5)
		>>> g *= 2
		>>> g
		GlyphCoordinates([(4.0, 2.0)])
		>>> g = GlyphCoordinates([(1,2)])
		>>> g *= 2
		>>> g
		GlyphCoordinates([(2, 4)])
		"""
		if isinstance(other, Number):
			other = (other, other)
		if isinstance(other, tuple):
			if other == (1,1):
				return self
			assert len(other) ==  2
			self.scale(other)
			return self
		return NotImplemented

	def __itruediv__(self, other):
		"""
		>>> g = GlyphCoordinates([(1,3)])
		>>> g /= (.5,1.5)
		>>> g /= 2
		>>> g
		GlyphCoordinates([(1.0, 1.0)])
		"""
		if isinstance(other, Number):
			other = (other, other)
		if isinstance(other, tuple):
			if other == (1,1):
				return self
			assert len(other) ==  2
			self.scale((1./other[0],1./other[1]))
			return self
		return NotImplemented


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


if __name__ == "__main__":
	import doctest, sys
	sys.exit(doctest.testmod().failed)
