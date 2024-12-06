###########################################
pens: Inspect and manipulate glyph outlines
###########################################

.. contents:: On this page:
    :local:
       

.. rubric:: Overview:
   :heading-level: 2

The fontTools **pens** are a collection of classes that can operate
on a font glyph via the points and the contours of the glyph's outlines.

Some pens trace through the outlines and generate graphical output,
such as a new glyph outline or a formatted image, but other
pens analyze the outlines and return information about the glyph.

Pens that alter or produce a pen-compatible :class:`.ttGlyph` object can
be chained together.

The majority of the pens are segment-oriented, meaning that they
operate by processing the Bezier segments of each glyph or glyph
component in order. This model corresponds to the way that glyph data
is stored in both TrueType-flavored and CFF-flavored OpenType
fonts.

There are also several "point-oriented" pens in the collection. These
pens serve to interpret the storage format used in Unified Font Object
(UFO) source files, which records all of the points of each contour in
sequential order, rather than as Bezier-curve segments. UFO's
point-only file format can be deterministically converted to
segment-oriented form and vice-versa; therefore all pens are available
to be used with UFO sources. The generic example can be found on the
:ref:`pointPen` page:

.. toctree::
   :maxdepth: 1

   pointPen

but there are ``pointPen`` variants of several other pens, included
alongside the modules for their segment-oriented version.

New pens can be written by sub-classing the :class:`.AbstractPen` or,
somewhat more practically, :class:`.BasePen` classes. The general Pen
Protocol is documented on the :ref:`basePen` page:

.. toctree::
   :maxdepth: 1

   basePen

Some of the platform-specific pen modules rely on importing external
Python libraries; these cases are noted on the relevant pens' pages.



Pen modules
-----------



.. toctree::
   :maxdepth: 1

   areaPen
   boundsPen
   cu2quPen
   filterPen
   momentsPen
   perimeterPen
   pointInsidePen
   recordingPen
   reverseContourPen
   roundingPen
   statisticsPen
   svgPathPen
   t2CharStringPen
   teePen
   transformPen
   ttGlyphPen

.. toctree::
   :maxdepth: 1

   cairoPen
   cocoaPen
   freetypePen
   qtPen
   quartzPen
   reportLabPen
   wxPen

