############################################################
encodings: Support for OpenType-specific character encodings
############################################################

.. currentmodule:: fontTools.encodings

.. contents:: On this page:
    :local:

       
.. rubric:: Overview:
   :heading-level: 2

fontTools includes support for some character encodings found in legacy Mac
TrueType fonts. Many of these legacy encodings have found their way into the
standard Python :mod:`encodings` library, but others still remain unimplemented.
Importing :mod:`fontTools.encodings.codecs` will therefore add string :func:`encode`
and :func:`decode` support for the following encodings:

* ``x_mac_japanese_ttx``
* ``x_mac_trad_chinese_ttx``
* ``x_mac_korean_ttx``
* ``x_mac_simp_chinese_ttx``

fontTools also includes a module (:mod:`fontTools.encodings.MacRoman`) that
consists of a mapping of glyph IDs to glyph names in the MacRoman character set::

		>>> from fontTools.encodings.MacRoman import MacRoman
		>>> MacRoman[26]
		'twosuperior'

and a module (:mod:`fontTools.encodings.StandardEncoding`) that provides
a similar mapping of glyph IDs to glyph names in the PostScript Standard
Encoding.
		


fontTools.encodings.codecs
--------------------------

.. currentmodule:: fontTools.encodings.codecs

.. automodule:: fontTools.encodings.codecs
   :members:
   :undoc-members:
      

fontTools.encodings.MacRoman
----------------------------

.. currentmodule:: fontTools.encodings.MacRoman

.. automodule:: fontTools.encodings.MacRoman
   :members:
   :undoc-members:
      
fontTools.encodings.StandardEncoding
------------------------------------

.. currentmodule:: fontTools.encodings.StandardEncoding

.. automodule:: fontTools.encodings.StandardEncoding
   :members:
   :undoc-members:
      
