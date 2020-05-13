##################################################
encodings: Support for OpenType-specific encodings
##################################################

fontTools includes support for some character encodings found in legacy Mac
TrueType fonts. Many of these legacy encodings have found their way into the
standard Python ``encodings`` library, but others still remain unimplemented.
Importing ``fontTools.encodings.codecs`` will therefore add string ``encode``
and ``decode`` support for the following encodings:

* ``x_mac_japanese_ttx``
* ``x_mac_trad_chinese_ttx``
* ``x_mac_korean_ttx``
* ``x_mac_simp_chinese_ttx``

fontTools also includes a package (``fontTools.encodings.MacRoman``) which
contains a mapping of glyph IDs to glyph names in the MacRoman character set::

		>>> from fontTools.encodings.MacRoman import MacRoman
		>>> MacRoman[26]
		'twosuperior'
