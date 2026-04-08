``bgcl``: Apple Color Emoji Background Color table
--------------------------------------------------

The ``bgcl`` table is an Apple private table used in Apple Color Emoji fonts.
It stores a JSON blob describing background color palettes used when rendering
emoji wallpapers on iOS 16 and later.

The JSON payload contains:

- ``colors``: a list of palette entries, each an ``[R, G, B, A]`` array where
  R/G/B are 0–255 and A is 0–1.
- ``emojicolors``: per-emoji palette assignments referencing entries in
  ``colors``.

.. automodule:: fontTools.ttLib.tables._b_g_c_l
   :members:
   :undoc-members:
