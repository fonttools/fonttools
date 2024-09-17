###########################################
pens: Inspect and manipulate glyph outlines
###########################################

.. rubric:: Overview:
   :heading-level: 3

The fontTools **pens** are a collection of classes that can operate
on a font glyph via the points and the contours of the glyph's outlines.

Some pens trace through the outlines and generate graphical output,
such as a new glyph outline or a formatted image, but other
pens analyze the outlines and return information about the glyph.

Pens that alter or produce a pen-compatile ``ttGlyph`` object can
be chained together.

New pens can be written by subclassing the ``AbstractPen`` or,
somewhat more practically, ``BasePen`` classes. The Pen Protocol is
documented on the ``BasePen`` page.

.. rubric:: Pens:
   :heading-level: 3

.. toctree::
   :maxdepth: 1

   areaPen
   basePen
   boundsPen
   cocoaPen
   cu2quPen
   filterPen
   freetypePen
   momentsPen
   perimeterPen
   pointInsidePen
   pointPen
   qtPen
   recordingPen
   reportLabPen
   reverseContourPen
   roundingPen
   statisticsPen
   svgPathPen
   t2CharStringPen
   teePen
   transformPen
   ttGlyphPen
   wxPen

