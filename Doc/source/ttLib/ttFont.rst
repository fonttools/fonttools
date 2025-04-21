####################################
ttFont: Read and write font contents
####################################

.. contents:: On this page:
    :local:

.. rubric:: Overview
   :heading-level: 2

:mod:`.ttLib.ttFont` is the primary fontTools interface for
inspecting, constructing, or deconstructing TrueType and OpenType
fonts.

The :class:`fontTools.ttLib.ttFont.TTFont` class provides access to
font-level data, including font metrics, substitution and positioning
features, and metadata, through a set of :doc:`table converters
</ttLib/tables>`. A :class:`.TTFont` may be instantiated from a single
font file, or it may be a member of a
:class:`.TTCollection`. :class:`.TTFont` objects can also be
constructed from scratch. 


glyphSets and ttGlyphs
----------------------

In addition to font-wide data, :mod:`.ttLib.ttFont` provides access to
individual glyphs through a :class:`.TTFont` instance's
``.glyphSet[]`` attribute. A ``.glyphSet`` is a dict-like object that is
indexed by glyph names. Users can use the glyphSet to interact with
each glyph's contours, components, points, and glyph metrics.

Informally, some fontTools code or documentation will make reference to
the individual glyphs in a ``.glyphSet`` as a "ttGlyph" or the
like. This is convenient terminology, particularly for
discussion. However, it is important to note that there is not a
"ttGlyph" class. Instead, the ``.glyphSet`` attribute of a
:class:`.TTFont` serves as an abstraction layer that provides a
uniform interface to the glyphs, regardless of whether the
:class:`.TTFont` instance in use comes from a font file with
TrueType-flavored glyphs (and, therefore, has a `glyf` table
containing glyph contours) or a font with PostScript-flavored outlines
(and, therefore, with a ``CFF`` or ``CFF2`` table containing the glyph
contours).

Regardless of the flavor, each "ttGlyph" entry in the ``.glyphSet``
includes the corresponding Bezier outlines and components from the
``glyf`` or ``CFF``/``CFF2`` table and the glyph's metrics. Horizontal
metrics are drawn from the font's ``hmtx`` table, and vertical metrics
(if any) are drawn from the ``vmtx`` table. These attributes are:

    width
        The advance width of the glyph
    
    lsb
        The left sidebearing of the glyph
    
    height
        (For vertical-layout fonts) The advance height of the glyph
    
    tsb
        (for vertical-layout fonts) The top sidebearing of the glyph

Note that these attributes do not describe the bounding box of the
glyph filled shape, because the filled area might include negative
coordinate values or extend beyond the advance width due to overhang.

The bounds of the glyph are accessible as ``xMin``, ``xMax``,
``yMin``, and ``yMax`` attributes.

For implementation details regarding the different flavors of
"ttGlyph", see the :doc:`ttGlyphSet </ttLib/ttGlyphSet>`
documentation.

These glyph objects also implement the :doc:`Pen Protocol
</pens/index>` by providing ``.draw()`` and ``.drawPoints()``
methods. See the :doc:`pens </pens/index>` package documenation
for more.


Package contents
----------------
 

.. autoclass:: fontTools.ttLib.ttFont.TTFont
   :members:
   :undoc-members:


      
.. autoclass:: fontTools.ttLib.ttFont.GlyphOrder
   :members:
   :undoc-members:
   :private-members:


.. automodule:: fontTools.ttLib.ttFont
   :members: getTableModule, registerCustomTableClass, unregisterCustomTableClass, getCustomTableClass, getClassTag, newTable, tagToIdentifier, identifierToTag, tagToXML, xmlToTag, sortedTagList, reorderFontTables
   :exclude-members: TTFont, GlyphOrder
