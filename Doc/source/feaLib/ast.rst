####################################################
ast: Interrogate and generate OpenType feature files
####################################################

.. currentmodule:: fontTools.feaLib.astt

.. rubric:: Overview:
   :heading-level: 2

feaLib's :mod:`.ast` module provides classes that represent the objects
and structures used to define OpenType feature lookups in the ``fea``
syntax. After your code has parsed a ``.fea`` file into an abstract
syntax tree (AST), you can use these classes to modify existing
lookups or create new lookups and features.

The root of the AST representation of a parsed ``.fea`` file is a
:class:`fontTools.feaLib.ast.FeatureFile` object. You can walk the
tree by examining its :attr:`statements` attribute. Nodes in the
tree have an :meth:`asFea` method that will return a ``.fea``
formated string representation, including correct indentation of block elements.


.. _`glyph-containing object`:
.. _`glyph-containing objects`:

In the below, a **glyph-containing object** is an object of one of the following
classes: :class:`GlyphName`, :class:`GlyphClass`, :class:`GlyphClassName`.

.. automodule:: fontTools.feaLib.ast
   :members:
   :undoc-members:
      
    .. rubric:: Module members
       :heading-level: 2



