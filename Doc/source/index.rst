.. image:: ../../Icons/FontToolsIconGreenCircle.png
   :width: 200px
   :height: 200px
   :alt: Font Tools
   :align: center


fontTools Docs
==============

About
-----

fontTools is a family of libraries and utilities for manipulating fonts in Python.

The project has an `MIT open-source license <https://github.com/fonttools/fonttools/blob/master/LICENSE>`_. Among other things this means you can use it free of charge.

Installation
------------

.. note::

    fontTools requires `Python <http://www.python.org/download/>`_ 3.6 or later.

The package is listed in the Python Package Index (PyPI), so you can install it with `pip <https://pip.pypa.io/>`_::

    pip install fonttools

See the Optional Requirements section below for details about module-specific dependencies that must be installed in select cases.

Utilities
---------

fontTools installs four command-line utilities:

- ``pyftmerge``, a tool for merging fonts; see :py:mod:`fontTools.merge`
- ``pyftsubset``, a tool for subsetting fonts; see :py:mod:`fontTools.subset`
- ``ttx``, a tool for converting between OpenType binary fonts (OTF) and an XML representation (TTX); see :py:mod:`fontTools.ttx`
- ``fonttools``, a "meta-tool" for accessing other components of the fontTools family.

This last utility takes a subcommand, which could be one of:

- ``cffLib.width``: Calculate optimum defaultWidthX/nominalWidthX values
- ``cu2qu``: Convert a UFO font from cubic to quadratic curves
- ``feaLib``: Add features from a feature file (.fea) into a OTF font
- ``help``: Show this help
- ``merge``: Merge multiple fonts into one
- ``mtiLib``: Convert a FontDame OTL file to TTX XML
- ``subset``: OpenType font subsetter and optimizer
- ``ttLib.woff2``: Compress and decompress WOFF2 fonts
- ``ttx``: Convert OpenType fonts to XML and back
- ``varLib``: Build a variable font from a designspace file and masters
- ``varLib.instancer``: Partially instantiate a variable font.
- ``varLib.interpolatable``: Test for interpolatability issues between fonts
- ``varLib.interpolate_layout``: Interpolate GDEF/GPOS/GSUB tables for a point on a designspace
- ``varLib.models``: Normalize locations on a given designspace
- ``varLib.mutator``: Instantiate a variation font
- ``varLib.varStore``: Optimize a font's GDEF variation store

Libraries
---------

The main library you will want to access when using fontTools for font
engineering is likely to be :py:mod:`fontTools.ttLib`, which is the package
for handling TrueType/OpenType fonts. However, there are many other
libraries in the fontTools suite:

- :py:mod:`fontTools.afmLib`: Module for reading and writing AFM files
- :py:mod:`fontTools.agl`: Access to the Adobe Glyph List
- :py:mod:`fontTools.cffLib`: Read/write tools for Adobe CFF fonts
- :py:mod:`fontTools.colorLib`: Module for handling colors in CPAL/COLR fonts
- :py:mod:`fontTools.cu2qu`: Module for cubic to quadratic conversion
- :py:mod:`fontTools.designspaceLib`: Read and write designspace files
- :py:mod:`fontTools.encodings`: Support for font-related character encodings
- :py:mod:`fontTools.feaLib`: Read and read AFDKO feature files
- :py:mod:`fontTools.fontBuilder`: Construct TTF/OTF fonts from scratch
- :py:mod:`fontTools.merge`: Tools for merging font files
- :py:mod:`fontTools.pens`: Various classes for manipulating glyph outlines
- :py:mod:`fontTools.subset`: OpenType font subsetting and optimization
- :py:mod:`fontTools.svgLib.path`: Library for drawing SVG paths onto glyphs
- :py:mod:`fontTools.t1Lib`: Tools for PostScript Type 1 fonts (Python2 only)
- :py:mod:`fontTools.ttx`: Module for converting between OTF and XML representation
- :py:mod:`fontTools.ufoLib`: Module for reading and writing UFO files
- :py:mod:`fontTools.unicodedata`: Convert between Unicode and OpenType script information
- :py:mod:`fontTools.varLib`: Module for dealing with 'gvar'-style font variations
- :py:mod:`fontTools.voltLib`: Module for dealing with Visual OpenType Layout Tool (VOLT) files

A selection of sample Python programs using these libaries can be found in the `Snippets directory <https://github.com/fonttools/fonttools/blob/master/Snippets/>`_ of the fontTools repository.

Optional Dependencies
---------------------

The fontTools package currently has no (required) external dependencies
besides the modules included in the Python Standard Library.
However, a few extra dependencies are required to unlock optional features
in some of the library modules. See the :doc:`optional requirements <./optional>`
page for more information.

Developer information
---------------------

Information for developers can be found :doc:`here <./developer>`.

License
-------

`MIT license <https://github.com/fonttools/fonttools/blob/master/LICENSE>`_.  See the full text of the license for details.


Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Library

   afmLib
   agl
   cffLib/index
   colorLib/index
   cu2qu/index
   designspaceLib/index
   encodings/index
   feaLib/index
   merge
   misc/index
   mtiLib
   otlLib/index
   pens/index
   subset/index
   svgLib/index
   t1Lib
   ttLib/index
   ttx
   ufoLib/index
   unicode
   unicodedata/index
   varLib/index
   voltLib


.. |Travis Build Status| image:: https://travis-ci.org/fonttools/fonttools.svg
   :target: https://travis-ci.org/fonttools/fonttools
.. |Appveyor Build status| image:: https://ci.appveyor.com/api/projects/status/0f7fmee9as744sl7/branch/master?svg=true
   :target: https://ci.appveyor.com/project/fonttools/fonttools/branch/master
.. |Coverage Status| image:: https://codecov.io/gh/fonttools/fonttools/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/fonttools/fonttools
.. |PyPI| image:: https://img.shields.io/pypi/v/fonttools.svg
   :target: https://pypi.org/project/FontTools
.. |Gitter Chat| image:: https://badges.gitter.im/fonttools-dev/Lobby.svg
   :alt: Join the chat at https://gitter.im/fonttools-dev/Lobby
   :target: https://gitter.im/fonttools-dev/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge