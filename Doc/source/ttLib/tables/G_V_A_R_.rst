``GVAR``: 24-bit Glyph Variation table
--------------------------------------

The ``GVAR`` table is an Apple-extended variant of the ``gvar`` table that
uses 24-bit glyph IDs instead of 16-bit ones, allowing it to support fonts
with more than 65,535 glyphs.

It is implemented as a thin subclass of :mod:`fontTools.ttLib.tables._g_v_a_r`.

.. automodule:: fontTools.ttLib.tables.G_V_A_R_
   :members:
   :undoc-members:
