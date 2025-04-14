###########################################
pens: Inspect and manipulate glyph outlines
###########################################


.. rubric:: Overview:
   :heading-level: 2

The fontTools **pens** are a collection of classes that can operate
on a font glyph via the points and the contours of the glyph's outlines.

Some pens trace through the outlines and generate graphical output,
such as a new glyph outline or a formatted image, but other
pens analyze the outlines and return information about the glyph.

Pens that alter or produce a pen-compatible :class:`.ttGlyph` object can
be chained together by calling he :meth:`.draw` method of each glyph
object, in turn, with a subsequent pen argument.

The majority of the pens process glyph outlines in a segment-oriented
manner, meaning that they operate by processing the Bezier segments of
each glyph or glyph component in sequential order. This model
corresponds to the way that glyph data is stored in both
TrueType-flavored and CFF-flavored OpenType fonts; the documentation
often refers to pens of this type as *SegmentPens*.

New pens can be written by sub-classing the :class:`.AbstractPen` or,
somewhat more practically, :class:`.BasePen` classes. The general Pen
Protocol is documented on the :doc:`basePen </pens/basePen>` page:

.. toctree::
   :maxdepth: 2

   basePen

There are also several "point-oriented" pens in the collection. These
pens serve to interpret the storage format used in Unified Font Object
(UFO) source files, which records all of the points of each contour in
sequential order, rather than as Bezier-curve segments. Thus, these
*PointPens* operate only on sequences of points.

UFO's point-only file format can be deterministically converted into
segment-oriented form and vice-versa; therefore all pens are available
to be used with UFO sources. General examples can be found on the
:doc:`pointPen </pens/pointPen>` page:

.. toctree::
   :maxdepth: 2

   pointPen

but there are also ``-PointPen`` variants available for several of the
other pens, included alongside the modules for their segment-oriented
version.



Pen modules
-----------


Note:
  Some of the platform-specific pen modules rely on importing external
  Python libraries; these cases are noted on the relevant pen modules'
  pages.



.. toctree::
   :maxdepth: 2

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
   :maxdepth: 2

   cairoPen
   cocoaPen
   freetypePen
   qtPen
   quartzPen
   reportLabPen
   wxPen

