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

	def info(self):
		return codecs.CodecInfo(name=self.name, encode=self.encode, decode=self.decode)


_mac_croatian_mapping = {
	b"\x80":	unichr(0x00C4),	# LATIN CAPITAL LETTER A WITH DIAERESIS
	b"\x81":	unichr(0x00C5),	# LATIN CAPITAL LETTER A WITH RING ABOVE
	b"\x82":	unichr(0x00C7),	# LATIN CAPITAL LETTER C WITH CEDILLA
	b"\x83":	unichr(0x00C9),	# LATIN CAPITAL LETTER E WITH ACUTE
	b"\x84":	unichr(0x00D1),	# LATIN CAPITAL LETTER N WITH TILDE
	b"\x85":	unichr(0x00D6),	# LATIN CAPITAL LETTER O WITH DIAERESIS
	b"\x86":	unichr(0x00DC),	# LATIN CAPITAL LETTER U WITH DIAERESIS
	b"\x87":	unichr(0x00E1),	# LATIN SMALL LETTER A WITH ACUTE
	b"\x88":	unichr(0x00E0),	# LATIN SMALL LETTER A WITH GRAVE
	b"\x89":	unichr(0x00E2),	# LATIN SMALL LETTER A WITH CIRCUMFLEX
	b"\x8A":	unichr(0x00E4),	# LATIN SMALL LETTER A WITH DIAERESIS
	b"\x8B":	unichr(0x00E3),	# LATIN SMALL LETTER A WITH TILDE
	b"\x8C":	unichr(0x00E5),	# LATIN SMALL LETTER A WITH RING ABOVE
	b"\x8D":	unichr(0x00E7),	# LATIN SMALL LETTER C WITH CEDILLA
	b"\x8E":	unichr(0x00E9),	# LATIN SMALL LETTER E WITH ACUTE
	b"\x8F":	unichr(0x00E8),	# LATIN SMALL LETTER E WITH GRAVE
	b"\x90":	unichr(0x00EA),	# LATIN SMALL LETTER E WITH CIRCUMFLEX
	b"\x91":	unichr(0x00EB),	# LATIN SMALL LETTER E WITH DIAERESIS
	b"\x92":	unichr(0x00ED),	# LATIN SMALL LETTER I WITH ACUTE
	b"\x93":	unichr(0x00EC),	# LATIN SMALL LETTER I WITH GRAVE
	b"\x94":	unichr(0x00EE),	# LATIN SMALL LETTER I WITH CIRCUMFLEX
	b"\x95":	unichr(0x00EF),	# LATIN SMALL LETTER I WITH DIAERESIS
	b"\x96":	unichr(0x00F1),	# LATIN SMALL LETTER N WITH TILDE
	b"\x97":	unichr(0x00F3),	# LATIN SMALL LETTER O WITH ACUTE
	b"\x98":	unichr(0x00F2),	# LATIN SMALL LETTER O WITH GRAVE
	b"\x99":	unichr(0x00F4),	# LATIN SMALL LETTER O WITH CIRCUMFLEX
	b"\x9A":	unichr(0x00F6),	# LATIN SMALL LETTER O WITH DIAERESIS
	b"\x9B":	unichr(0x00F5),	# LATIN SMALL LETTER O WITH TILDE
	b"\x9C":	unichr(0x00FA),	# LATIN SMALL LETTER U WITH ACUTE
	b"\x9D":	unichr(0x00F9),	# LATIN SMALL LETTER U WITH GRAVE
	b"\x9E":	unichr(0x00FB),	# LATIN SMALL LETTER U WITH CIRCUMFLEX
	b"\x9F":	unichr(0x00FC),	# LATIN SMALL LETTER U WITH DIAERESIS
	b"\xA0":	unichr(0x2020),	# DAGGER
	b"\xA1":	unichr(0x00B0),	# DEGREE SIGN
	b"\xA2":	unichr(0x00A2),	# CENT SIGN
	b"\xA3":	unichr(0x00A3),	# POUND SIGN
	b"\xA4":	unichr(0x00A7),	# SECTION SIGN
	b"\xA5":	unichr(0x2022),	# BULLET
	b"\xA6":	unichr(0x00B6),	# PILCROW SIGN
	b"\xA7":	unichr(0x00DF),	# LATIN SMALL LETTER SHARP S
	b"\xA8":	unichr(0x00AE),	# REGISTERED SIGN
	b"\xA9":	unichr(0x0160),	# LATIN CAPITAL LETTER S WITH CARON
	b"\xAA":	unichr(0x2122),	# TRADE MARK SIGN
	b"\xAB":	unichr(0x00B4),	# ACUTE ACCENT
	b"\xAC":	unichr(0x00A8),	# DIAERESIS
	b"\xAD":	unichr(0x2260),	# NOT EQUAL TO
	b"\xAE":	unichr(0x017D),	# LATIN CAPITAL LETTER Z WITH CARON
	b"\xAF":	unichr(0x00D8),	# LATIN CAPITAL LETTER O WITH STROKE
	b"\xB0":	unichr(0x221E),	# INFINITY
	b"\xB1":	unichr(0x00B1),	# PLUS-MINUS SIGN
	b"\xB2":	unichr(0x2264),	# LESS-THAN OR EQUAL TO
	b"\xB3":	unichr(0x2265),	# GREATER-THAN OR EQUAL TO
	b"\xB4":	unichr(0x2206),	# INCREMENT
	b"\xB5":	unichr(0x00B5),	# MICRO SIGN
	b"\xB6":	unichr(0x2202),	# PARTIAL DIFFERENTIAL
	b"\xB7":	unichr(0x2211),	# N-ARY SUMMATION
	b"\xB8":	unichr(0x220F),	# N-ARY PRODUCT
	b"\xB9":	unichr(0x0161),	# LATIN SMALL LETTER S WITH CARON
	b"\xBA":	unichr(0x222B),	# INTEGRAL
	b"\xBB":	unichr(0x00AA),	# FEMININE ORDINAL INDICATOR
	b"\xBC":	unichr(0x00BA),	# MASCULINE ORDINAL INDICATOR
	b"\xBD":	unichr(0x03A9),	# GREEK CAPITAL LETTER OMEGA
	b"\xBE":	unichr(0x017E),	# LATIN SMALL LETTER Z WITH CARON
	b"\xBF":	unichr(0x00F8),	# LATIN SMALL LETTER O WITH STROKE
	b"\xC0":	unichr(0x00BF),	# INVERTED QUESTION MARK
	b"\xC1":	unichr(0x00A1),	# INVERTED EXCLAMATION MARK
	b"\xC2":	unichr(0x00AC),	# NOT SIGN
	b"\xC3":	unichr(0x221A),	# SQUARE ROOT
	b"\xC4":	unichr(0x0192),	# LATIN SMALL LETTER F WITH HOOK
	b"\xC5":	unichr(0x2248),	# ALMOST EQUAL TO
	b"\xC6":	unichr(0x0106),	# LATIN CAPITAL LETTER C WITH ACUTE
	b"\xC7":	unichr(0x00AB),	# LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
	b"\xC8":	unichr(0x010C),	# LATIN CAPITAL LETTER C WITH CARON
	b"\xC9":	unichr(0x2026),	# HORIZONTAL ELLIPSIS
	b"\xCA":	unichr(0x00A0),	# NO-BREAK SPACE
	b"\xCB":	unichr(0x00C0),	# LATIN CAPITAL LETTER A WITH GRAVE
	b"\xCC":	unichr(0x00C3),	# LATIN CAPITAL LETTER A WITH TILDE
	b"\xCD":	unichr(0x00D5),	# LATIN CAPITAL LETTER O WITH TILDE
	b"\xCE":	unichr(0x0152),	# LATIN CAPITAL LIGATURE OE
	b"\xCF":	unichr(0x0153),	# LATIN SMALL LIGATURE OE
	b"\xD0":	unichr(0x0110),	# LATIN CAPITAL LETTER D WITH STROKE
	b"\xD1":	unichr(0x2014),	# EM DASH
	b"\xD2":	unichr(0x201C),	# LEFT DOUBLE QUOTATION MARK
	b"\xD3":	unichr(0x201D),	# RIGHT DOUBLE QUOTATION MARK
	b"\xD4":	unichr(0x2018),	# LEFT SINGLE QUOTATION MARK
	b"\xD5":	unichr(0x2019),	# RIGHT SINGLE QUOTATION MARK
	b"\xD6":	unichr(0x00F7),	# DIVISION SIGN
	b"\xD7":	unichr(0x25CA),	# LOZENGE
	b"\xD8":	unichr(0xF8FF),	# Apple logo
	b"\xD9":	unichr(0x00A9),	# COPYRIGHT SIGN
	b"\xDA":	unichr(0x2044),	# FRACTION SLASH
	b"\xDB":	unichr(0x20AC),	# EURO SIGN
	b"\xDC":	unichr(0x2039),	# SINGLE LEFT-POINTING ANGLE QUOTATION MARK
	b"\xDD":	unichr(0x203A),	# SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
	b"\xDE":	unichr(0x00C6),	# LATIN CAPITAL LETTER AE
	b"\xDF":	unichr(0x00BB),	# RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
	b"\xE0":	unichr(0x2013),	# EN DASH
	b"\xE1":	unichr(0x00B7),	# MIDDLE DOT
	b"\xE2":	unichr(0x201A),	# SINGLE LOW-9 QUOTATION MARK
	b"\xE3":	unichr(0x201E),	# DOUBLE LOW-9 QUOTATION MARK
	b"\xE4":	unichr(0x2030),	# PER MILLE SIGN
	b"\xE5":	unichr(0x00C2),	# LATIN CAPITAL LETTER A WITH CIRCUMFLEX
	b"\xE6":	unichr(0x0107),	# LATIN SMALL LETTER C WITH ACUTE
	b"\xE7":	unichr(0x00C1),	# LATIN CAPITAL LETTER A WITH ACUTE
	b"\xE8":	unichr(0x010D),	# LATIN SMALL LETTER C WITH CARON
	b"\xE9":	unichr(0x00C8),	# LATIN CAPITAL LETTER E WITH GRAVE
	b"\xEA":	unichr(0x00CD),	# LATIN CAPITAL LETTER I WITH ACUTE
	b"\xEB":	unichr(0x00CE),	# LATIN CAPITAL LETTER I WITH CIRCUMFLEX
	b"\xEC":	unichr(0x00CF),	# LATIN CAPITAL LETTER I WITH DIAERESIS
	b"\xED":	unichr(0x00CC),	# LATIN CAPITAL LETTER I WITH GRAVE
	b"\xEE":	unichr(0x00D3),	# LATIN CAPITAL LETTER O WITH ACUTE
	b"\xEF":	unichr(0x00D4),	# LATIN CAPITAL LETTER O WITH CIRCUMFLEX
	b"\xF0":	unichr(0x0111),	# LATIN SMALL LETTER D WITH STROKE
	b"\xF1":	unichr(0x00D2),	# LATIN CAPITAL LETTER O WITH GRAVE
	b"\xF2":	unichr(0x00DA),	# LATIN CAPITAL LETTER U WITH ACUTE
	b"\xF3":	unichr(0x00DB),	# LATIN CAPITAL LETTER U WITH CIRCUMFLEX
	b"\xF4":	unichr(0x00D9),	# LATIN CAPITAL LETTER U WITH GRAVE
	b"\xF5":	unichr(0x0131),	# LATIN SMALL LETTER DOTLESS I
	b"\xF6":	unichr(0x02C6),	# MODIFIER LETTER CIRCUMFLEX ACCENT
	b"\xF7":	unichr(0x02DC),	# SMALL TILDE
	b"\xF8":	unichr(0x00AF),	# MACRON
	b"\xF9":	unichr(0x03C0),	# GREEK SMALL LETTER PI
	b"\xFA":	unichr(0x00CB),	# LATIN CAPITAL LETTER E WITH DIAERESIS
	b"\xFB":	unichr(0x02DA),	# RING ABOVE
	b"\xFC":	unichr(0x00B8),	# CEDILLA
	b"\xFD":	unichr(0x00CA),	# LATIN CAPITAL LETTER E WITH CIRCUMFLEX
	b"\xFE":	unichr(0x00E6),	# LATIN SMALL LETTER AE
	b"\xFF":	unichr(0x02C7),	# CARON
}

_mac_romanian_mapping = {
	b"\x80":	unichr(0x00C4),	# LATIN CAPITAL LETTER A WITH DIAERESIS
	b"\x81":	unichr(0x00C5),	# LATIN CAPITAL LETTER A WITH RING ABOVE
	b"\x82":	unichr(0x00C7),	# LATIN CAPITAL LETTER C WITH CEDILLA
	b"\x83":	unichr(0x00C9),	# LATIN CAPITAL LETTER E WITH ACUTE
	b"\x84":	unichr(0x00D1),	# LATIN CAPITAL LETTER N WITH TILDE
	b"\x85":	unichr(0x00D6),	# LATIN CAPITAL LETTER O WITH DIAERESIS
	b"\x86":	unichr(0x00DC),	# LATIN CAPITAL LETTER U WITH DIAERESIS
	b"\x87":	unichr(0x00E1),	# LATIN SMALL LETTER A WITH ACUTE
	b"\x88":	unichr(0x00E0),	# LATIN SMALL LETTER A WITH GRAVE
	b"\x89":	unichr(0x00E2),	# LATIN SMALL LETTER A WITH CIRCUMFLEX
	b"\x8A":	unichr(0x00E4),	# LATIN SMALL LETTER A WITH DIAERESIS
	b"\x8B":	unichr(0x00E3),	# LATIN SMALL LETTER A WITH TILDE
	b"\x8C":	unichr(0x00E5),	# LATIN SMALL LETTER A WITH RING ABOVE
	b"\x8D":	unichr(0x00E7),	# LATIN SMALL LETTER C WITH CEDILLA
	b"\x8E":	unichr(0x00E9),	# LATIN SMALL LETTER E WITH ACUTE
	b"\x8F":	unichr(0x00E8),	# LATIN SMALL LETTER E WITH GRAVE
	b"\x90":	unichr(0x00EA),	# LATIN SMALL LETTER E WITH CIRCUMFLEX
	b"\x91":	unichr(0x00EB),	# LATIN SMALL LETTER E WITH DIAERESIS
	b"\x92":	unichr(0x00ED),	# LATIN SMALL LETTER I WITH ACUTE
	b"\x93":	unichr(0x00EC),	# LATIN SMALL LETTER I WITH GRAVE
	b"\x94":	unichr(0x00EE),	# LATIN SMALL LETTER I WITH CIRCUMFLEX
	b"\x95":	unichr(0x00EF),	# LATIN SMALL LETTER I WITH DIAERESIS
	b"\x96":	unichr(0x00F1),	# LATIN SMALL LETTER N WITH TILDE
	b"\x97":	unichr(0x00F3),	# LATIN SMALL LETTER O WITH ACUTE
	b"\x98":	unichr(0x00F2),	# LATIN SMALL LETTER O WITH GRAVE
	b"\x99":	unichr(0x00F4),	# LATIN SMALL LETTER O WITH CIRCUMFLEX
	b"\x9A":	unichr(0x00F6),	# LATIN SMALL LETTER O WITH DIAERESIS
	b"\x9B":	unichr(0x00F5),	# LATIN SMALL LETTER O WITH TILDE
	b"\x9C":	unichr(0x00FA),	# LATIN SMALL LETTER U WITH ACUTE
	b"\x9D":	unichr(0x00F9),	# LATIN SMALL LETTER U WITH GRAVE
	b"\x9E":	unichr(0x00FB),	# LATIN SMALL LETTER U WITH CIRCUMFLEX
	b"\x9F":	unichr(0x00FC),	# LATIN SMALL LETTER U WITH DIAERESIS
	b"\xA0":	unichr(0x2020),	# DAGGER
	b"\xA1":	unichr(0x00B0),	# DEGREE SIGN
	b"\xA2":	unichr(0x00A2),	# CENT SIGN
	b"\xA3":	unichr(0x00A3),	# POUND SIGN
	b"\xA4":	unichr(0x00A7),	# SECTION SIGN
	b"\xA5":	unichr(0x2022),	# BULLET
	b"\xA6":	unichr(0x00B6),	# PILCROW SIGN
	b"\xA7":	unichr(0x00DF),	# LATIN SMALL LETTER SHARP S
	b"\xA8":	unichr(0x00AE),	# REGISTERED SIGN
	b"\xA9":	unichr(0x00A9),	# COPYRIGHT SIGN
	b"\xAA":	unichr(0x2122),	# TRADE MARK SIGN
	b"\xAB":	unichr(0x00B4),	# ACUTE ACCENT
	b"\xAC":	unichr(0x00A8),	# DIAERESIS
	b"\xAD":	unichr(0x2260),	# NOT EQUAL TO
	b"\xAE":	unichr(0x0102),	# LATIN CAPITAL LETTER A WITH BREVE
	b"\xAF":	unichr(0x0218),	# LATIN CAPITAL LETTER S WITH COMMA BELOW # for Unicode 3.0 and later
	b"\xB0":	unichr(0x221E),	# INFINITY
	b"\xB1":	unichr(0x00B1),	# PLUS-MINUS SIGN
	b"\xB2":	unichr(0x2264),	# LESS-THAN OR EQUAL TO
	b"\xB3":	unichr(0x2265),	# GREATER-THAN OR EQUAL TO
	b"\xB4":	unichr(0x00A5),	# YEN SIGN
	b"\xB5":	unichr(0x00B5),	# MICRO SIGN
	b"\xB6":	unichr(0x2202),	# PARTIAL DIFFERENTIAL
	b"\xB7":	unichr(0x2211),	# N-ARY SUMMATION
	b"\xB8":	unichr(0x220F),	# N-ARY PRODUCT
	b"\xB9":	unichr(0x03C0),	# GREEK SMALL LETTER PI
	b"\xBA":	unichr(0x222B),	# INTEGRAL
	b"\xBB":	unichr(0x00AA),	# FEMININE ORDINAL INDICATOR
	b"\xBC":	unichr(0x00BA),	# MASCULINE ORDINAL INDICATOR
	b"\xBD":	unichr(0x03A9),	# GREEK CAPITAL LETTER OMEGA
	b"\xBE":	unichr(0x0103),	# LATIN SMALL LETTER A WITH BREVE
	b"\xBF":	unichr(0x0219),	# LATIN SMALL LETTER S WITH COMMA BELOW # for Unicode 3.0 and later
	b"\xC0":	unichr(0x00BF),	# INVERTED QUESTION MARK
	b"\xC1":	unichr(0x00A1),	# INVERTED EXCLAMATION MARK
	b"\xC2":	unichr(0x00AC),	# NOT SIGN
	b"\xC3":	unichr(0x221A),	# SQUARE ROOT
	b"\xC4":	unichr(0x0192),	# LATIN SMALL LETTER F WITH HOOK
	b"\xC5":	unichr(0x2248),	# ALMOST EQUAL TO
	b"\xC6":	unichr(0x2206),	# INCREMENT
	b"\xC7":	unichr(0x00AB),	# LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
	b"\xC8":	unichr(0x00BB),	# RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
	b"\xC9":	unichr(0x2026),	# HORIZONTAL ELLIPSIS
	b"\xCA":	unichr(0x00A0),	# NO-BREAK SPACE
	b"\xCB":	unichr(0x00C0),	# LATIN CAPITAL LETTER A WITH GRAVE
	b"\xCC":	unichr(0x00C3),	# LATIN CAPITAL LETTER A WITH TILDE
	b"\xCD":	unichr(0x00D5),	# LATIN CAPITAL LETTER O WITH TILDE
	b"\xCE":	unichr(0x0152),	# LATIN CAPITAL LIGATURE OE
	b"\xCF":	unichr(0x0153),	# LATIN SMALL LIGATURE OE
	b"\xD0":	unichr(0x2013),	# EN DASH
	b"\xD1":	unichr(0x2014),	# EM DASH
	b"\xD2":	unichr(0x201C),	# LEFT DOUBLE QUOTATION MARK
	b"\xD3":	unichr(0x201D),	# RIGHT DOUBLE QUOTATION MARK
	b"\xD4":	unichr(0x2018),	# LEFT SINGLE QUOTATION MARK
	b"\xD5":	unichr(0x2019),	# RIGHT SINGLE QUOTATION MARK
	b"\xD6":	unichr(0x00F7),	# DIVISION SIGN
	b"\xD7":	unichr(0x25CA),	# LOZENGE
	b"\xD8":	unichr(0x00FF),	# LATIN SMALL LETTER Y WITH DIAERESIS
	b"\xD9":	unichr(0x0178),	# LATIN CAPITAL LETTER Y WITH DIAERESIS
	b"\xDA":	unichr(0x2044),	# FRACTION SLASH
	b"\xDB":	unichr(0x20AC),	# EURO SIGN
	b"\xDC":	unichr(0x2039),	# SINGLE LEFT-POINTING ANGLE QUOTATION MARK
	b"\xDD":	unichr(0x203A),	# SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
	b"\xDE":	unichr(0x021A),	# LATIN CAPITAL LETTER T WITH COMMA BELOW # for Unicode 3.0 and later
	b"\xDF":	unichr(0x021B),	# LATIN SMALL LETTER T WITH COMMA BELOW # for Unicode 3.0 and later
	b"\xE0":	unichr(0x2021),	# DOUBLE DAGGER
	b"\xE1":	unichr(0x00B7),	# MIDDLE DOT
	b"\xE2":	unichr(0x201A),	# SINGLE LOW-9 QUOTATION MARK
	b"\xE3":	unichr(0x201E),	# DOUBLE LOW-9 QUOTATION MARK
	b"\xE4":	unichr(0x2030),	# PER MILLE SIGN
	b"\xE5":	unichr(0x00C2),	# LATIN CAPITAL LETTER A WITH CIRCUMFLEX
	b"\xE6":	unichr(0x00CA),	# LATIN CAPITAL LETTER E WITH CIRCUMFLEX
	b"\xE7":	unichr(0x00C1),	# LATIN CAPITAL LETTER A WITH ACUTE
	b"\xE8":	unichr(0x00CB),	# LATIN CAPITAL LETTER E WITH DIAERESIS
	b"\xE9":	unichr(0x00C8),	# LATIN CAPITAL LETTER E WITH GRAVE
	b"\xEA":	unichr(0x00CD),	# LATIN CAPITAL LETTER I WITH ACUTE
	b"\xEB":	unichr(0x00CE),	# LATIN CAPITAL LETTER I WITH CIRCUMFLEX
	b"\xEC":	unichr(0x00CF),	# LATIN CAPITAL LETTER I WITH DIAERESIS
	b"\xED":	unichr(0x00CC),	# LATIN CAPITAL LETTER I WITH GRAVE
	b"\xEE":	unichr(0x00D3),	# LATIN CAPITAL LETTER O WITH ACUTE
	b"\xEF":	unichr(0x00D4),	# LATIN CAPITAL LETTER O WITH CIRCUMFLEX
	b"\xF0":	unichr(0xF8FF),	# Apple logo
	b"\xF1":	unichr(0x00D2),	# LATIN CAPITAL LETTER O WITH GRAVE
	b"\xF2":	unichr(0x00DA),	# LATIN CAPITAL LETTER U WITH ACUTE
	b"\xF3":	unichr(0x00DB),	# LATIN CAPITAL LETTER U WITH CIRCUMFLEX
	b"\xF4":	unichr(0x00D9),	# LATIN CAPITAL LETTER U WITH GRAVE
	b"\xF5":	unichr(0x0131),	# LATIN SMALL LETTER DOTLESS I
	b"\xF6":	unichr(0x02C6),	# MODIFIER LETTER CIRCUMFLEX ACCENT
	b"\xF7":	unichr(0x02DC),	# SMALL TILDE
	b"\xF8":	unichr(0x00AF),	# MACRON
	b"\xF9":	unichr(0x02D8),	# BREVE
	b"\xFA":	unichr(0x02D9),	# DOT ABOVE
	b"\xFB":	unichr(0x02DA),	# RING ABOVE
	b"\xFC":	unichr(0x00B8),	# CEDILLA
	b"\xFD":	unichr(0x02DD),	# DOUBLE ACUTE ACCENT
	b"\xFE":	unichr(0x02DB),	# OGONEK
	b"\xFF":	unichr(0x02C7),	# CARON
}

_extended_encodings = {
	"x_mac_croatian_ttx": ("ascii", _mac_croatian_mapping),
	"x_mac_romanian_ttx": ("ascii", _mac_romanian_mapping),
	"x_mac_japanese_ttx": ("shift_jis", {
					b"\xFC":	unichr(0x007C),
					b"\x7E":	unichr(0x007E),
					b"\x80":	unichr(0x005C),
					b"\xA0":	unichr(0x00A0),
					b"\xFD":	unichr(0x00A9),
					b"\xFE":	unichr(0x2122),
					b"\xFF":	unichr(0x2026),
				}),
	"x_mac_trad_ttx": ("big5", {
					b"\x80 ":	unichr(0x005C),
					b"\xA0 ":	unichr(0x00A0),
					b"\xFD ":	unichr(0x00A9),
					b"\xFE ":	unichr(0x2122),
					b"\xFF ":	unichr(0x2026),
				}),
	"x_mac_korean_ttx": ("euc_kr", {
					b"\x80 ":	unichr(0x00A0),
					b"\x81 ":	unichr(0x20A9),
					b"\x82 ":	unichr(0x2014),
					b"\x83 ":	unichr(0x00A9),
					b"\xFE ":	unichr(0x2122),
					b"\xFF ":	unichr(0x2026),
				}),
	"x_mac_simp_ttx": ("gb2312", {
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
