#################################################
otlLib: Routines for working with OpenType Layout
#################################################

The ``fontTools.otlLib`` library provides routines to help you create the
subtables and other data structures you need when you are editing a font's
``GSUB`` and ``GPOS`` tables: substitution and positioning rules, anchors,
lookups, coverage tables and so on.

------------------------------------------
High-level OpenType Layout Lookup Builders
------------------------------------------

.. currentmodule:: fontTools.otlLib.builder

.. autoclass:: AlternateSubstBuilder
.. autoclass:: ChainContextPosBuilder
.. autoclass:: ChainContextSubstBuilder
.. autoclass:: LigatureSubstBuilder
.. autoclass:: MultipleSubstBuilder
.. autoclass:: CursivePosBuilder
.. autoclass:: MarkBasePosBuilder
.. autoclass:: MarkLigPosBuilder
.. autoclass:: MarkMarkPosBuilder
.. autoclass:: ReverseChainSingleSubstBuilder
.. autoclass:: SingleSubstBuilder
.. autoclass:: ClassPairPosSubtableBuilder
.. autoclass:: PairPosBuilder
.. autoclass:: SinglePosBuilder

--------------------------------------
Common OpenType Layout Data Structures
--------------------------------------

.. currentmodule:: fontTools.otlLib.builder

.. autofunction:: buildCoverage
.. autofunction:: buildLookup

------------------------------------
Low-level GSUB Table Lookup Builders
------------------------------------

These functions deal with the "simple" lookup types. See above for classes to
help build more complex lookups (contextual and chaining lookups).

.. currentmodule:: fontTools.otlLib.builder

.. autofunction:: buildSingleSubstSubtable
.. autofunction:: buildMultipleSubstSubtable
.. autofunction:: buildAlternateSubstSubtable
.. autofunction:: buildLigatureSubstSubtable

--------------------------
GPOS Shared Table Builders
--------------------------

The functions help build the `GPOS shared tables <https://docs.microsoft.com/en-us/typography/opentype/spec/gpos#shared-tables-value-record-anchor-table-and-mark-array-table>`_
as defined in the OpenType spec: value records, anchors, mark arrays and
mark record tables.

.. currentmodule:: fontTools.otlLib.builder
.. autofunction:: buildValue
.. autofunction:: buildAnchor
.. autofunction:: buildMarkArray
.. autofunction:: buildDevice
.. autofunction:: buildBaseArray
.. autofunction:: buildComponentRecord

------------------------------------
Low-level GPOS Table Lookup Builders
------------------------------------

These functions deal with the "simple" lookup types. See above for classes to
help build more complex lookups (contextual and chaining lookups).

.. currentmodule:: fontTools.otlLib.builder

.. autofunction:: buildCursivePosSubtable
.. autofunction:: buildLigatureArray
.. autofunction:: buildMarkBasePos
.. autofunction:: buildMarkBasePosSubtable
.. autofunction:: buildMarkLigPos
.. autofunction:: buildMarkLigPosSubtable
.. autofunction:: buildPairPosClassesSubtable
.. autofunction:: buildPairPosGlyphs
.. autofunction:: buildPairPosGlyphsSubtable
.. autofunction:: buildSinglePos
.. autofunction:: buildSinglePosSubtable

----------------------------
GDEF Table Subtable Builders
----------------------------

These functions build subtables for elements of the ``GDEF`` table.

.. currentmodule:: fontTools.otlLib.builder

.. autofunction:: buildAttachList
.. autofunction:: buildLigCaretList
.. autofunction:: buildMarkGlyphSetsDef

------------------
STAT Table Builder
------------------

.. currentmodule:: fontTools.otlLib.builder

.. autofunction:: buildStatTable
