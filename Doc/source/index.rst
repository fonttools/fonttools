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

Commands for merging and subsetting fonts are also available::

    pyftmerge
    pyftsubset

Please see the :py:mod:`fontTools.merge` and :py:mod:`fontTools.subset` documentation for additional information about these tools.

Libraries
---------

XXX

A selection of sample Python programs using these libaries can be found in the `Snippets directory <https://github.com/fonttools/fonttools/blob/master/Snippets/>`_ of the fontTools repository.

Optional Requirements
---------------------

The fontTools package currently has no (required) external dependencies
besides the modules included in the Python Standard Library.
However, a few extra dependencies are required to unlock optional features
in some of the library modules.

The fonttools PyPI distribution also supports so-called "extras", i.e. a
set of keywords that describe a group of additional dependencies, which can be
used when installing via pip, or when specifying a requirement.
For example:

.. code:: sh

    pip install fonttools[ufo,lxml,woff,unicode]

This command will install fonttools, as well as the optional dependencies that
are required to unlock the extra features named "ufo", etc.

.. note::

    Optional dependencies are detailed by module in the list below with the ``Extra`` setting that automates ``pip`` dependency installation when this is supported.



:py:mod:`fontTools.misc.etree`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The module exports a ElementTree-like API for reading/writing XML files, and allows to use as the backend either the built-in ``xml.etree`` module or `lxml <https://lxml.de>`__. The latter is preferred whenever present, as it is generally faster and more secure.

*Extra:* ``lxml``


:py:mod:`fontTools.ufoLib`
^^^^^^^^^^^^^^^^^^^^^^^^^^

Package for reading and writing UFO source files; it requires:

* `fs <https://pypi.org/pypi/fs>`__: (aka ``pyfilesystem2``) filesystem abstraction layer.

* `enum34 <https://pypi.org/pypi/enum34>`__: backport for the built-in ``enum`` module (only required on Python < 3.4).

*Extra:* ``ufo``


:py:mod:`fontTools.ttLib.woff2`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Module to compress/decompress WOFF 2.0 web fonts; it requires:

* `brotli <https://pypi.python.org/pypi/Brotli>`__: Python bindings of the Brotli compression library.

*Extra:* ``woff``


:py:mod:`fontTools.unicode`
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To display the Unicode character names when dumping the ``cmap`` table
with ``ttx`` we use the ``unicodedata`` module in the Standard Library.
The version included in there varies between different Python versions.
To use the latest available data, you can install:

* `unicodedata2 <https://pypi.python.org/pypi/unicodedata2>`__: ``unicodedata`` backport for Python 2.7
  and 3.x updated to the latest Unicode version 12.0. Note this is not necessary if you use Python 3.8
  as the latter already comes with an up-to-date ``unicodedata``.

*Extra:* ``unicode``


:py:mod:`fontTools.varLib.interpolatable`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Module for finding wrong contour/component order between different masters.
It requires one of the following packages in order to solve the so-called
"minimum weight perfect matching problem in bipartite graphs", or
the Assignment problem:

* `scipy <https://pypi.python.org/pypi/scipy>`__: the Scientific Library for Python, which internally
  uses `NumPy <https://pypi.python.org/pypi/numpy>`__ arrays and hence is very fast;
* `munkres <https://pypi.python.org/pypi/munkres>`__: a pure-Python module that implements the Hungarian
  or Kuhn-Munkres algorithm.

*Extra:* ``interpolatable``


:py:mod:`fontTools.varLib.plot`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Module for visualizing DesignSpaceDocument and resulting VariationModel.

* `matplotlib <https://pypi.org/pypi/matplotlib>`__: 2D plotting library.

*Extra:* ``plot``


:py:mod:`fontTools.misc.symfont`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Advanced module for symbolic font statistics analysis; it requires:

* `sympy <https://pypi.python.org/pypi/sympy>`__: the Python library for symbolic mathematics.

*Extra:* ``symfont``


:py:mod:`fontTools.t1Lib`
^^^^^^^^^^^^^^^^^^^^^^^^^

To get the file creator and type of Macintosh PostScript Type 1 fonts
on Python 3 you need to install the following module, as the old ``MacOS``
module is no longer included in Mac Python:

* `xattr <https://pypi.python.org/pypi/xattr>`__: Python wrapper for extended filesystem attributes
  (macOS platform only).

*Extra:* ``type1``


:py:mod:`fontTools.pens.cocoaPen`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pen for drawing glyphs with Cocoa ``NSBezierPath``, requires:

* `PyObjC <https://pypi.python.org/pypi/pyobjc>`__: the bridge between Python and the Objective-C
  runtime (macOS platform only).


:py:mod:`fontTools.pens.qtPen`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pen for drawing glyphs with Qt's ``QPainterPath``, requires:

* `PyQt5 <https://pypi.python.org/pypi/PyQt5>`__: Python bindings for the Qt cross platform UI and
  application toolkit.


:py:mod:`fontTools.pens.reportLabPen`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pen to drawing glyphs as PNG images, requires:

* `reportlab <https://pypi.python.org/pypi/reportlab>`__: Python toolkit for generating PDFs and
  graphics.

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