"""Extend the Python codecs module with a few encodings that are used in OpenType (name table)
but missing from Python.  See https://github.com/behdad/fonttools/issues/236 for details."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *

import codecs

class ExtendCodec(codecs.Codec):

	def __init__(self, name, base_encoding, mapping):
		self.name = name
		self.base_encoding = base_encoding
		self.mapping = mapping
		self.reverse = dict((v,k) for k,v in mapping.items())
		self.max_len = max(len(v) for v in mapping.values())
		codecs.register_error(name, self.error)

	def encode(self, input, errors='strict'):
		assert errors == 'strict'
		#return codecs.encode(input, self.base_encoding, self.name), len(input)

		# The above line could totally be all we needed, relying on the error
		# handling to replace the unencodable Unicode characters with our extended
		# byte sequences.
		#
		# However, there seems to be a design bug in Python (probably intentional):
		# the error handler for encoding is supposed to return a **Unicode** character,
		# that then needs to be encodable itself...  Ugh.
		#
		# So we implement what codecs.encode() should have been doing: which is expect
		# error handler to return bytes() to be added to the output.

		length = len(input)
		out = b''
		while input:
			try:
				part = codecs.encode(input, self.base_encoding)
				out += part
				input = '' # All converted
			except UnicodeEncodeError as e:
				# Convert the correct part
				out += codecs.encode(input[:e.start], self.base_encoding)
				replacement, pos = self.error(e)
				out += replacement
				input = input[pos:]
		return out, length

	def decode(self, input, errors='strict'):
		assert errors == 'strict'
		return codecs.decode(input, self.base_encoding, self.name), len(input)

	def error(self, e):
		if isinstance(e, UnicodeDecodeError):
			for end in range(e.start + 1, e.end):
				s = e.object[e.start:end]
				if s in self.mapping:
					return self.mapping[s], end
		elif isinstance(e, UnicodeEncodeError):
			for end in range(e.start + 1, e.start + self.max_len + 1):
				s = e.object[e.start:end]
				if s in self.reverse:
					return self.reverse[s], end
		e.encoding = self.name
		raise e

	def info(self):
		return codecs.CodecInfo(name=self.name, encode=self.encode, decode=self.decode)

_extended_encodings = {
	"x-mac-japanese-ttx": ("shift_jis", {
					b"\xFC":	unichr(0x007C),
					b"\x7E":	unichr(0x007E),
					b"\x80":	unichr(0x005C),
					b"\xA0":	unichr(0x00A0),
					b"\xFD":	unichr(0x00A9),
					b"\xFE":	unichr(0x2122),
					b"\xFF":	unichr(0x2026),
				}),
	"x-mac-chinesetrad-ttx": ("big5", {
					b"\x80 ":	unichr(0x005C),
					b"\xA0 ":	unichr(0x00A0),
					b"\xFD ":	unichr(0x00A9),
					b"\xFE ":	unichr(0x2122),
					b"\xFF ":	unichr(0x2026),
				}),
	"x-mac-korean-ttx": ("euc_kr", {
					b"\x80 ":	unichr(0x00A0),
					b"\x81 ":	unichr(0x20A9),
					b"\x82 ":	unichr(0x2014),
					b"\x83 ":	unichr(0x00A9),
					b"\xFE ":	unichr(0x2122),
					b"\xFF ":	unichr(0x2026),
				}),
	"x-mac-chinesesimp-ttx": ("gb2312", {
					b"\x80 ":	unichr(0x00FC),
					b"\xA0 ":	unichr(0x00A0),
					b"\xFD ":	unichr(0x00A9),
					b"\xFE ":	unichr(0x2122),
					b"\xFF ":	unichr(0x2026),
				}),
}

_codecs = {}

def search_function(name):
	if name in _extended_encodings:
		global _codecs
		if name not in _codecs:
			base_encoding, mapping = _extended_encodings[name]
			_codecs[name] = ExtendCodec(name, base_encoding, mapping)
		return _codecs[name].info()

	return None

codecs.register(search_function)
