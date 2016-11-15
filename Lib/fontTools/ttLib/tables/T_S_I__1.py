from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from . import DefaultTable

class table_T_S_I__1(DefaultTable.DefaultTable):

	extras = {0xfffa: "ppgm", 0xfffb: "cvt", 0xfffc: "reserved", 0xfffd: "fpgm"}

	indextable = "TSI0"

	def decompile(self, data, ttFont):
		indextable = ttFont[self.indextable]
		self.glyphPrograms = {}
		for i in range(len(indextable.indices)):
			glyphID, textLength, textOffset = indextable.indices[i]
			if textLength == 0x8000:
				# Ugh. Hi Beat!
				textLength = indextable.indices[i+1][1]
			if textLength > 0x8000:
				pass  # XXX Hmmm.
			text = data[textOffset:textOffset+textLength]
			assert len(text) == textLength
			if text:
				self.glyphPrograms[ttFont.getGlyphName(glyphID)] = text

		self.extraPrograms = {}
		for i in range(len(indextable.extra_indices)):
			extraCode, textLength, textOffset = indextable.extra_indices[i]
			if textLength == 0x8000:
				if self.extras[extraCode] == "fpgm":	# this is the last one
					textLength = len(data) - textOffset
				else:
					textLength = indextable.extra_indices[i+1][1]
			text = data[textOffset:textOffset+textLength]
			assert len(text) == textLength
			if text:
				self.extraPrograms[self.extras[extraCode]] = text

	def compile(self, ttFont):
		if not hasattr(self, "glyphPrograms"):
			self.glyphPrograms = {}
			self.extraPrograms = {}
		data = b''
		indextable = ttFont[self.indextable]
		glyphNames = ttFont.getGlyphOrder()

		indices = []
		for i in range(len(glyphNames)):
			if len(data) % 2:
				data = data + b"\015"  # align on 2-byte boundaries, fill with return chars. Yum.
			name = glyphNames[i]
			if name in self.glyphPrograms:
				text = tobytes(self.glyphPrograms[name])
			else:
				text = b""
			textLength = len(text)
			if textLength >= 0x8000:
				textLength = 0x8000  # XXX ???
			indices.append((i, textLength, len(data)))
			data = data + text

		extra_indices = []
		codes = sorted(self.extras.items())
		for i in range(len(codes)):
			if len(data) % 2:
				data = data + b"\015"  # align on 2-byte boundaries, fill with return chars.
			code, name = codes[i]
			if name in self.extraPrograms:
				text = tobytes(self.extraPrograms[name], encoding="utf-8")
			else:
				text = b""
			textLength = len(text)
			if textLength >= 0x8000:
				textLength = 0x8000  # XXX ???
			extra_indices.append((code, textLength, len(data)))
			data = data + text
		indextable.set(indices, extra_indices)
		return data

	def toXML(self, writer, ttFont):
		names = sorted(self.glyphPrograms.keys())
		writer.newline()
		for name in names:
			text = self.glyphPrograms[name]
			if not text:
				continue
			writer.begintag("glyphProgram", name=name)
			writer.newline()
			writer.write_noindent(text.replace(b"\r", b"\n"))
			writer.newline()
			writer.endtag("glyphProgram")
			writer.newline()
			writer.newline()
		extra_names = sorted(self.extraPrograms.keys())
		for name in extra_names:
			text = self.extraPrograms[name]
			if not text:
				continue
			writer.begintag("extraProgram", name=name)
			writer.newline()
			writer.write_noindent(text.replace(b"\r", b"\n"))
			writer.newline()
			writer.endtag("extraProgram")
			writer.newline()
			writer.newline()

	def fromXML(self, name, attrs, content, ttFont):
		if not hasattr(self, "glyphPrograms"):
			self.glyphPrograms = {}
			self.extraPrograms = {}
		lines = strjoin(content).replace("\r", "\n").split("\n")
		text = '\r'.join(lines[1:-1])
		if name == "glyphProgram":
			self.glyphPrograms[attrs["name"]] = text
		elif name == "extraProgram":
			self.extraPrograms[attrs["name"]] = text
