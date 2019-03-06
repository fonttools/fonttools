"""Extend the Python codecs module with a few encodings that are used in OpenType (name table)
but missing from Python.  See https://github.com/fonttools/fonttools/issues/236 for details."""

from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
import codecs
import encodings

class ExtendCodec(codecs.Codec):

	def __init__(self, name, base_encoding, mapping):
		self.name = name
		self.base_encoding = base_encoding
		self.mapping = mapping
		self.reverse = {v:k for k,v in mapping.items()}
		self.max_len = max(len(v) for v in mapping.values())
		self.info = codecs.CodecInfo(name=self.name, encode=self.encode, decode=self.decode)
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
		#
		# This seems to have been fixed in Python 3.3.  We should try using that and
		# use fallback only if that failed.
		# https://docs.python.org/3.3/library/codecs.html#codecs.register_error

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
			for end in range(e.start + 1, e.end + 1):
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


_extended_encodings = {
	"x_mac_japanese_ttx": ("shift_jis", {
					b"\xFC": unichr(0x007C),
					b"\x7E": unichr(0x007E),
					b"\x80": unichr(0x005C),
					b"\xA0": unichr(0x00A0),
					b"\xFD": unichr(0x00A9),
					b"\xFE": unichr(0x2122),
					b"\xFF": unichr(0x2026),
				}),
	"x_mac_trad_chinese_ttx": ("big5", {
					b"\x80": unichr(0x005C),
					b"\xA0": unichr(0x00A0),
					b"\xFD": unichr(0x00A9),
					b"\xFE": unichr(0x2122),
					b"\xFF": unichr(0x2026),
				}),
	"x_mac_korean_ttx": ("euc_kr", {
					b"\x80": unichr(0x00A0),
					b"\x81": unichr(0x20A9),
					b"\x82": unichr(0x2014),
					b"\x83": unichr(0x00A9),
					b"\xFE": unichr(0x2122),
					b"\xFF": unichr(0x2026),
				}),
	"x_mac_simp_chinese_ttx": ("gb2312", {
					b"\x80": unichr(0x00FC),
					b"\xA0": unichr(0x00A0),
					b"\xFD": unichr(0x00A9),
					b"\xFE": unichr(0x2122),
					b"\xFF": unichr(0x2026),
				}),
}

_cache = {}

def search_function(name):
	name = encodings.normalize_encoding(name) # Rather undocumented...
	if name in _extended_encodings:
		if name not in _cache:
			base_encoding, mapping = _extended_encodings[name]
			assert(name[-4:] == "_ttx")
			# Python 2 didn't have any of the encodings that we are implementing
			# in this file.  Python 3 added aliases for the East Asian ones, mapping
			# them "temporarily" to the same base encoding as us, with a comment
			# suggesting that full implementation will appear some time later.
			# As such, try the Python version of the x_mac_... first, if that is found,
			# use *that* as our base encoding.  This would make our encoding upgrade
			# to the full encoding when and if Python finally implements that.
			# http://bugs.python.org/issue24041
			base_encodings = [name[:-4], base_encoding]
			for base_encoding in base_encodings:
				try:
					codecs.lookup(base_encoding)
				except LookupError:
					continue
				_cache[name] = ExtendCodec(name, base_encoding, mapping)
				break
		return _cache[name].info

	return None

codecs.register(search_function)
