#################################################
ttLib: Read and write OpenType and TrueType fonts
#################################################

.. contents:: On this page:
    :local:

.. rubric:: Overview:
   :heading-level: 2

Most users of the :mod:`fontTools` library will be using it to generate or manipulate
OpenType and TrueType fonts. (FontTools initially only supported TrueType fonts,
gaining OpenType support in version 2.0, and so uses the ``tt`` prefix to refer to
both kinds of font. Because of this we will refer to both as "TrueType fonts"
unless we need to make a distinction.)

The main entry point for such operations is the :py:mod:`fontTools.ttLib.ttFont`
module, but other modules also provide useful functionality for handling OpenType
fonts:

.. toctree::
   :maxdepth: 1

   ttFont

:mod:`.ttLib` supports fonts with TrueType-flavored glyphs (i.e., with
a ``glyf`` table), with PostScript-flavored glyphs (i.e., ``CFF`` or
``CFF2`` tables), and with all of the glyph formats used for color fonts
(``CBDT``, ``COLR``, ``sbix``, and ``SVG``). Static and variable fonts
are both supported.


Command-line utilities
----------------------

:mod:`.ttLib` includes two modules that provide command-line operations:
     
.. toctree::
   :maxdepth: 1
   
   removeOverlaps
   scaleUpem


Supporting modules
------------------

It also contains helper modules that enable lower-level
functionality. In most cases, users will not need to access these
modules directly:

.. toctree::
   :maxdepth: 1
   
   ttCollection
   ttGlyphSet
   macUtils
   reorderGlyphs
   sfnt
   standardGlyphOrder
   tables
   woff2
