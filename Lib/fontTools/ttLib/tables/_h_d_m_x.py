import DefaultTable
import sstruct
import string

hdmxHeaderFormat = """
	>   # big endian!
	version:	H
	numRecords:	H
	recordSize:	l
"""

class table__h_d_m_x(DefaultTable.DefaultTable):
	
	def decompile(self, data, ttFont):
		numGlyphs = ttFont['maxp'].numGlyphs
		glyphOrder = ttFont.getGlyphOrder()
		dummy, data = sstruct.unpack2(hdmxHeaderFormat, data, self)
		self.hdmx = {}
		for i in range(self.numRecords):
			ppem = ord(data[0])
			maxSize = ord(data[1])
			widths = {}
			for glyphID in range(numGlyphs):
				widths[glyphOrder[glyphID]] = ord(data[glyphID+2])
			self.hdmx[ppem] = widths
			data = data[self.recordSize:]
		assert len(data) == 0, "too much hdmx data"
	
	def compile(self, ttFont):
		self.version = 0
		numGlyphs = ttFont['maxp'].numGlyphs
		glyphOrder = ttFont.getGlyphOrder()
		self.recordSize = 4 * ((2 + numGlyphs + 3) / 4)
		pad = (self.recordSize - 2 - numGlyphs) * "\0"
		self.numRecords = len(self.hdmx)
		data = sstruct.pack(hdmxHeaderFormat, self)
		items = self.hdmx.items()
		items.sort()
		for ppem, widths in items:
			data = data + chr(ppem) + chr(max(widths.values()))
			for glyphID in range(len(glyphOrder)):
				width = widths[glyphOrder[glyphID]]
				data = data + chr(width)
			data = data + pad
		return data
	
	def toXML(self, writer, ttFont):
		writer.begintag("hdmxData")
		writer.newline()
		ppems = self.hdmx.keys()
		ppems.sort()
		records = []
		format = ""
		for ppem in ppems:
			widths = self.hdmx[ppem]
			records.append(widths)
			format = format + "%4d"
		glyphNames = ttFont.getGlyphOrder()[:]
		glyphNames.sort()
		maxNameLen = max(map(len, glyphNames))
		format = "%" + `maxNameLen` + 's:' + format + ' ;'
		writer.write(format % (("ppem",) + tuple(ppems)))
		writer.newline()
		writer.newline()
		for glyphName in glyphNames:
			row = []
			for ppem in ppems:
				widths = self.hdmx[ppem]
				row.append(widths[glyphName])
			if ";" in glyphName:
				glyphName = "\\x3b".join(glyphName.split(";"))
			writer.write(format % ((glyphName,) + tuple(row)))
			writer.newline()
		writer.endtag("hdmxData")
		writer.newline()
	
	def fromXML(self, (name, attrs, content), ttFont):
		if name <> "hdmxData":
			return
		content = string.join(content, "")
		lines = string.split(content, ";")
		topRow = string.split(lines[0])
		assert topRow[0] == "ppem:", "illegal hdmx format"
		ppems = map(int, topRow[1:])
		self.hdmx = hdmx = {}
		for ppem in ppems:
			hdmx[ppem] = {}
		lines = map(string.split, lines[1:])
		for line in lines:
			if not line:
				continue
			assert line[0][-1] == ":", "illegal hdmx format"
			glyphName = line[0][:-1]
			if "\\" in glyphName:
				from fontTools.misc.textTools import safeEval
				glyphName = safeEval('"""' + glyphName + '"""')
			line = map(int, line[1:])
			assert len(line) == len(ppems), "illegal hdmx format"
			for i in range(len(ppems)):
				hdmx[ppems[i]][glyphName] = line[i]

