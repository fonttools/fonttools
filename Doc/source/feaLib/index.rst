#########################################
feaLib: Read/write OpenType feature files
#########################################

fontTools' ``feaLib`` allows for the creation and parsing of Adobe
Font Development Kit for OpenType feature (``.fea``) files. The syntax
of these files is described `here <https://adobe-type-tools.github.io/afdko/OpenTypeFeatureFileSpecification.html>`_.

The :class:`fontTools.feaLib.parser.Parser` class can be used to parse files
into an abstract syntax tree, and from there the
:class:`fontTools.feaLib.builder.Builder` class can add features to an existing
font file. You can inspect the parsed syntax tree, walk the tree and do clever
things with it, and also generate your own feature files programmatically, by
using the classes in the :mod:`fontTools.feaLib.ast` module.

Parsing
-------

.. autoclass:: fontTools.feaLib.parser.Parser
   :members: parse
   :member-order: bysource

Building
---------

.. automodule:: fontTools.feaLib.builder
   :members: addOpenTypeFeatures, addOpenTypeFeaturesFromString

Generation/Interrogation
------------------------

.. _`glyph-containing object`:
.. _`glyph-containing objects`:

In the below, a **glyph-containing object** is an object of one of the following
classes: :class:`GlyphName`, :class:`GlyphClass`, :class:`GlyphClassName`.

.. automodule:: fontTools.feaLib.ast
   :member-order: bysource
   :members:
