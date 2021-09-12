Optional Dependencies
=====================

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
