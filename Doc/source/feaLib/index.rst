#############################################
feaLib: Read and write OpenType feature files
#############################################

.. currentmodule:: fontTools.feaLib

.. contents:: On this page:
    :local:

       
.. rubric:: Overview
   :heading-level: 2

fontTools' :mod:`.feaLib` allows for the creation and parsing of Adobe
Font Development Kit for OpenType feature (``.fea``) files. The syntax
of these files is described `here <https://adobe-type-tools.github.io/afdko/OpenTypeFeatureFileSpecification.html>`_.

``.fea`` files are primarily used for writing human-readable
definitions for the OpenType features stored in a font's ``GSUB`` and
``GPOS`` tables.

Supporting modules
------------------

feaLib contains modules for parsing and inspecting ``.fea`` files
as well as utilities for converting ``.fea`` rules into ``GSUB`` and
``GPOS`` tables and inserting them into fonts.
		   
 .. toctree::
    :maxdepth: 1

    parser
    ast

The :class:`fontTools.feaLib.parser.Parser` class can be used to parse files
into an abstract syntax tree, and from there the
:class:`fontTools.feaLib.builder.Builder` class can add features to an existing
font file. You can inspect the parsed syntax tree, walk the tree and do clever
things with it, and also generate your own feature files programmatically, by
using the classes in the :mod:`fontTools.feaLib.ast` module.



fontTools.feaLib.builder
------------------------

.. currentmodule:: fontTools.feaLib.builder

.. automodule:: fontTools.feaLib.builder
   :members: addOpenTypeFeatures, addOpenTypeFeaturesFromString, Builder
   :undoc-members:


fontTools.feaLib.lookupDebugInfo
--------------------------------

.. currentmodule:: fontTools.feaLib.lookupDebugInfo

.. automodule:: fontTools.feaLib.lookupDebugInfo
   :members:
   :undoc-members:


fontTools.feaLib.error
----------------------

.. currentmodule:: fontTools.feaLib.error

.. automodule:: fontTools.feaLib.error
   :members:
   :undoc-members:
