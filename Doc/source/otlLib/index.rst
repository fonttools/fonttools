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

.. automodule:: fontTools.otlLib.builder
   :members: AlternateSubstBuilder, ChainContextPosBuilder, ChainContextSubstBuilder, LigatureSubstBuilder, MultipleSubstBuilder, CursivePosBuilder, MarkBasePosBuilder, MarkLigPosBuilder, MarkMarkPosBuilder, ReverseChainSingleSubstBuilder, SingleSubstBuilder, ClassPairPosSubtableBuilder, PairPosBuilder, SinglePosBuilder
   :member-order: bysource

--------------------------------------
Common OpenType Layout Data Structures
--------------------------------------

.. automodule:: fontTools.otlLib.builder
   :members: buildCoverage, buildLookup

------------------------------------
Low-level GSUB Table Lookup Builders
------------------------------------

These functions deal with the "simple" lookup types. See above for classes to
help build more complex lookups (contextual and chaining lookups).

.. automodule:: fontTools.otlLib.builder
   :members: buildSingleSubstSubtable, buildMultipleSubstSubtable, buildAlternateSubstSubtable, buildLigatureSubstSubtable

--------------------------
GPOS Shared Table Builders
--------------------------

The functions help build the `GPOS shared tables <https://docs.microsoft.com/en-us/typography/opentype/spec/gpos#shared-tables-value-record-anchor-table-and-mark-array-table>`_
as defined in the OpenType spec: value records, anchors, mark arrays and
mark record tables.

.. automodule:: fontTools.otlLib.builder
   :members: buildValue, buildAnchor, buildMarkArray, buildDevice, buildBaseArray, buildComponentRecord, buildMarkArray, buildValue
   :member-order: bysource

------------------------------------
Low-level GPOS Table Lookup Builders
------------------------------------

These functions deal with the "simple" lookup types. See above for classes to
help build more complex lookups (contextual and chaining lookups).

.. automodule:: fontTools.otlLib.builder
   :members: buildCursivePosSubtable, buildLigatureArray, buildMarkBasePos, buildMarkBasePosSubtable, buildMarkLigPos, buildMarkLigPosSubtable, buildPairPosClassesSubtable, buildPairPosGlyphs, buildPairPosGlyphsSubtable, buildSinglePos, buildSinglePosSubtable
   :member-order: bysource

----------------------------
GDEF Table Subtable Builders
----------------------------

These functions build subtables for elements of the ``GDEF`` table.

.. automodule:: fontTools.otlLib.builder
   :members: buildAttachList, buildLigCaretList, buildMarkGlyphSetsDef
   :member-order: bysource

------------------
STAT Table Builder
------------------

.. automodule:: fontTools.otlLib.builder
   :members: buildStatTable
   :member-order: bysource
