.. image:: ../../Icons/FontToolsIconGreenCircle.png
   :width: 200px
   :height: 200px
   :alt: Font Tools
   :align: center


---fontTools Documentation---
=============================
About
-----

fontTools is a family of libraries and utilities for manipulating fonts in Python.

The project is licensed under the `MIT open-source license <https://github.com/fonttools/fonttools/blob/main/LICENSE>`_, allowing free usage.

Installation
------------

.. note::

    fontTools requires `Python <http://www.python.org/download/>`_ 3.9 or later.

To install fontTools, use `pip <https://pip.pypa.io/>`_:


    pip install fonttools

Utilities
---------

fontTools includes the following command-line utilities:

- ``pyftmerge``: Tool for merging fonts; see :py:mod:`fontTools.merge`
- ``pyftsubset``: Tool for subsetting fonts; see :py:mod:`fontTools.subset`
- ``ttx``: Tool for converting between OTF and XML representation; see :py:mod:`fontTools.ttx`
- ``fonttools``: Meta-tool for accessing other fontTools components.

For ``fonttools``, you can use subcommands like:

- ``cffLib.width``: Calculate optimum defaultWidthX/nominalWidthX values
- ``cu2qu``: Convert a UFO font from cubic to quadratic curves
- ``feaLib``: Add features from a feature file (.fea) into a OTF font
- ``merge``: Merge multiple fonts into one
- ``subset``: OpenType font subsetter and optimizer
- ``ttx``: Convert OpenType fonts to XML and back
- ``varLib``: Build a variable font from a designspace file and masters
- ``varLib.instancer``: Partially instantiate a variable font
- ``voltLib.voltToFea``: Convert MS VOLT to AFDKO feature files.

Libraries
---------

The main library for font engineering is :py:mod:`fontTools.ttLib.ttFont`, which handles TrueType/OpenType fonts. Other libraries include:

- :py:mod:`fontTools.afmLib`: Read and write AFM files
- :py:mod:`fontTools.agl`: Access the Adobe Glyph List
- :py:mod:`fontTools.cffLib`: Tools for Adobe CFF fonts
- :py:mod:`fontTools.colorLib`: Handle colors in CPAL/COLR fonts
- :py:mod:`fontTools.cu2qu`: Convert cubic to quadratic curves
- :py:mod:`fontTools.designspaceLib`: Read and write designspace files
- :py:mod:`fontTools.encodings`: Support for font-related encodings
- :py:mod:`fontTools.feaLib`: Read and write AFDKO feature files
- :py:mod:`fontTools.fontBuilder`: Construct TTF/OTF fonts from scratch
- :py:mod:`fontTools.merge`: Tools for merging font files
- :py:mod:`fontTools.subset`: OpenType font subsetting and optimization
- :py:mod:`fontTools.svgLib.path`: Draw SVG paths onto glyphs
- :py:mod:`fontTools.ttLib`: Read/write OpenType and TrueType fonts
- :py:mod:`fontTools.ttx`: Convert between OTF and XML representation
- :py:mod:`fontTools.ufoLib`: Read and write UFO files
- :py:mod:`fontTools.unicodedata`: Convert between Unicode and OpenType script info
- :py:mod:`fontTools.varLib`: Deal with 'gvar'-style font variations
- :py:mod:`fontTools.voltLib`: Deal with Visual OpenType Layout Tool (VOLT) files

Optional Dependencies
---------------------

fontTools has no external dependencies besides the Python Standard Library. Some optional features require additional modules; see the :doc:`optional requirements </optional>` page for details.

Developer Information
---------------------

For developer resources, refer to the :doc:`developer information </developer>`.

License
-------

fontTools is licensed under the `MIT license <https://github.com/fonttools/fonttools/blob/main/LICENSE>`_. Refer to the full text of the license for details.


.. toctree::
   :maxdepth: 1
   :hidden:

   afmLib
   agl
   cffLib/index
   colorLib/index
   config
   cu2qu/index
   designspaceLib/index
   encodings/index
   feaLib/index
   merge
   misc/index
   mtiLib
   otlLib/index
   pens/index
   qu2cu/index
   subset/index
   svgLib/index
   t1Lib
   tfmLib
   ttLib/index
   ttx
   ufoLib/index
   unicodedata/index
   varLib/index
   voltLib/index

.. |Travis Build Status| image:: https://travis-ci.org/fonttools/fonttools.svg
   :target: https://travis-ci.org/fonttools/fonttools
.. |Appveyor Build status| image:: https://ci.appveyor.com/api/projects/status/0f7fmee9as744sl7/branch/master?svg=true
   :target: https://ci.appveyor.com/project/fonttools/fonttools/branch/master
.. |Coverage Status| image:: https://codecov.io/gh/fonttools/fonttools/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/fonttools/fonttools
.. |PyPI| image:: https://img.shields.io/pypi/v/fonttools.svg
   :target: https://pypi.org/project/FontTools
.. |Gitter Chat| image:: https://badges.gitter.im/fonttools-dev/Lobby.svg
   :alt: Join the chat at https://gitter.im/fonttools-dev/Lobby
   :target: https://gitter.im/fonttools-dev/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
