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

In addition to font-wide data, :mod:`.ttLib.ttFont` provides access to
individual glyphs through the :class:`.TTFont` object's
``glyphSet[]``. This is a dict-like object that is indexed by glyph
names. Users can use the glyphSet to interact with each glyph's
contours, components, points, and glyph metrics.

These glyph objects also implement the :doc:`Pen Protocol
</pens/index>` by providing ``.draw()`` and ``.drawPoints()``
methods. See the :doc:`pens </pens/index>` package documenation
for more.


.. rubric:: Package contents:
   :heading-level: 2
 

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
