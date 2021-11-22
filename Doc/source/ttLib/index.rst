#############################################
ttLib: Read/write OpenType and TrueType fonts
#############################################

Most users of the fontTools library will be using it to generate or manipulate
OpenType and TrueType fonts. (FontTools initially only supported TrueType fonts,
gaining OpenType support in version 2.0, and so uses the ``tt`` prefix to refer to
both kinds of font. Because of this we will refer to both as "TrueType fonts"
unless we need to make a distinction.)

The main entry point for such operations is the :py:mod:`fontTools.ttLib.ttFont`
module, but other modules also provide useful functionality for handling OpenType
fonts.

.. toctree::
   :maxdepth: 2

   ttFont
   ttCollection
   macUtils
   sfnt
   standardGlyphOrder
   tables
   woff2
