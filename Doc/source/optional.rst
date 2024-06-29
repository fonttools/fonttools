Optional Dependencies
=====================

The FontTools PyPI distribution supports "extras", which are groups of additional dependencies that can be installed alongside FontTools via pip to enable specific features. For example:

.. code:: sh

    pip install fonttools[ufo,lxml,woff,unicode]

This command installs FontTools along with the optional dependencies required for features like "ufo", "lxml", "woff", and "unicode".

.. note:: sh

    Optional dependencies are listed by module below, along with the `Extra` setting that automates `pip` dependency installation when supported.

:py:mod:`fontTools.misc.etree`
--------------------

This module provides an ElementTree-like API for reading and writing XML files. It supports two backend options:

- Built-in `xml.etree` module
- `lxml` preferred for improved speed and security.

*Extra:* `lxml`

:py:mod:`fontTools.ufoLib`
----------------

Package for reading and writing UFO source files. Dependencies include:

- `fs <https://pypi.org/pypi/fs>`__: (aka ``pyfilesystem2``) filesystem abstraction layer
- `enum34 <https://pypi.org/pypi/enum34>`__ backport for the built-in ``enum`` module (module for Python versions < 3.4)

*Extra:* `ufo`

:py:mod:`fontTools.ttLib.woff2`
---------------------

Module for compressing and decompressing WOFF 2.0 web fonts. Requires:

- `brotli <https://pypi.python.org/pypi/Brotli>`__: Python bindings for the Brotli compression library.

*Extra:* `woff`

:py:mod:`fontTools.unicode`
-----------------

Displays Unicode character names when working with the `cmap` table dumps,with `ttx` we use the `unicodedata` module in the Standard Library. 
The version included in there varies between different Python versions.
To use the latest Unicode version, install:

- `unicodedata2 <https://pypi.python.org/pypi/unicodedata2>`__: backport of `unicodedata` for Python 3.x, updated to unicode 14.0. Not necessary with Python 3.11.

*Extra:* `unicode`

:py:mod:`fontTools.varLib.interpolatable`
-------------------------------

Module for resolving contour or component order between different masters. Requires following packages to solve 'minimum weight perfect matching problem in bipartite graphs':

- `scipy <https://pypi.python.org/pypi/scipy>`__: Scientific Library for Python, uses `NumPy <https://pypi.python.org/pypi/numpy>`__ arrays for performance;
- `munkres <https://pypi.python.org/pypi/munkres>`__: implementation of the Hungarian or Kuhn-Munkres algorithm.

*Extra:* `interpolatable`

:py:mod:`fontTools.varLib.plot`
----------------------

Module for visualizing DesignSpaceDocument and resulting VariationModel. Requires:

- `matplotlib <https://pypi.org/pypi/matplotlib>`__: 2D plotting library.

*Extra:* `plot`

:py:mod:`fontTools.misc.symfont`
----------------------

Advanced module for symbolic font statistics analysis. Requires:

- `sympy <https://pypi.python.org/pypi/sympy>`__: Python library for symbolic mathematics.

*Extra:* `symfont`

:py:mod:`fontTools.t1Lib`
---------------

Retrieves information about Macintosh PostScript Type 1 fonts on Python 3. Requires:

- `xattr <https://pypi.python.org/pypi/xattr>`__: Python wrapper for extended filesystem attributes, macOS only.

*Extra:* `type1`

:py:mod:`fontTools.pens.cocoaPen`
------------------------

Pen for drawing glyphs with Cocoa `NSBezierPath`. Requires:

- `PyObjC <https://pypi.python.org/pypi/pyobjc>`__: Python - Objective-C bridge, macOS only.

:py:mod:`fontTools.pens.qtPen`
---------------------

Pen for drawing glyphs with Qt's `QPainterPath`. Requires:

- `PyQt5 <https://pypi.python.org/pypi/PyQt5>`__: Python bindings for the Qt cross-platform UI and application toolkit.

:py:mod:`fontTools.pens.reportLabPen`
---------------------------

Pen for drawing glyphs as PNG images. Requires:

- `<https://pypi.python.org/pypi/reportlab>`__: Python toolkit for generating PDFs and graphics.
