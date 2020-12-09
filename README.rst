|CI Build Status| |Coverage Status| |PyPI| |Gitter Chat|

What is this?
~~~~~~~~~~~~~

| fontTools is a library for manipulating fonts, written in Python. The
  project includes the TTX tool, that can convert TrueType and OpenType
  fonts to and from an XML text format, which is also called TTX. It
  supports TrueType, OpenType, AFM and to an extent Type 1 and some
  Mac-specific formats. The project has an `MIT open-source
  licence <LICENSE>`__.
| Among other things this means you can use it free of charge.

`User documentation <https://fonttools.readthedocs.io/en/latest/>`_ and
`developer documentation <https://fonttools.readthedocs.io/en/latest/developer.html>`_
are available at `Read the Docs <https://fonttools.readthedocs.io/>`_.

Installation
~~~~~~~~~~~~

FontTools 4.x requires `Python <http://www.python.org/download/>`__ 3.6
or later. FontTools 3.x requires Python 2.7 or later.

**NOTE** From August 2019, until no later than January 1 2020, the support
for *Python 2.7* will be limited to only critical bug fixes, and no new features
will be added to the ``py27`` branch. You can read more `here <https://python3statement.org>`__
and `here <https://github.com/fonttools/fonttools/issues/765>`__ for the
reasons behind this decision.

The package is listed in the Python Package Index (PyPI), so you can
install it with `pip <https://pip.pypa.io>`__:

.. code:: sh

    pip install fonttools

If you would like to contribute to its development, you can clone the
repository from GitHub, install the package in 'editable' mode and
modify the source code in place. We recommend creating a virtual
environment, using `virtualenv <https://virtualenv.pypa.io>`__ or
Python 3 `venv <https://docs.python.org/3/library/venv.html>`__ module.

.. code:: sh

    # download the source code to 'fonttools' folder
    git clone https://github.com/fonttools/fonttools.git
    cd fonttools

    # create new virtual environment called e.g. 'fonttools-venv', or anything you like
    python -m virtualenv fonttools-venv

    # source the `activate` shell script to enter the environment (Un*x); to exit, just type `deactivate`
    . fonttools-venv/bin/activate

    # to activate the virtual environment in Windows `cmd.exe`, do
    fonttools-venv\Scripts\activate.bat

    # install in 'editable' mode
    pip install -e .

Optional Requirements
---------------------

The ``fontTools`` package currently has no (required) external dependencies
besides the modules included in the Python Standard Library.
However, a few extra dependencies are required by some of its modules, which
are needed to unlock optional features.
The ``fonttools`` PyPI distribution also supports so-called "extras", i.e. a
set of keywords that describe a group of additional dependencies, which can be
used when installing via pip, or when specifying a requirement.
For example:

.. code:: sh

    pip install fonttools[ufo,lxml,woff,unicode]

This command will install fonttools, as well as the optional dependencies that
are required to unlock the extra features named "ufo", etc.

- ``Lib/fontTools/misc/etree.py``

  The module exports a ElementTree-like API for reading/writing XML files, and
  allows to use as the backend either the built-in ``xml.etree`` module or
  `lxml <https://lxml.de>`__. The latter is preferred whenever present,
  as it is generally faster and more secure.

  *Extra:* ``lxml``

- ``Lib/fontTools/ufoLib``

  Package for reading and writing UFO source files; it requires:

  * `fs <https://pypi.org/pypi/fs>`__: (aka ``pyfilesystem2``) filesystem
    abstraction layer.

  * `enum34 <https://pypi.org/pypi/enum34>`__: backport for the built-in ``enum``
    module (only required on Python < 3.4).

  *Extra:* ``ufo``

- ``Lib/fontTools/ttLib/woff2.py``

  Module to compress/decompress WOFF 2.0 web fonts; it requires:

  * `brotli <https://pypi.python.org/pypi/Brotli>`__: Python bindings of
    the Brotli compression library.

  *Extra:* ``woff``

- ``Lib/fontTools/ttLib/sfnt.py``

  To better compress WOFF 1.0 web fonts, the following module can be used
  instead of the built-in ``zlib`` library:

  * `zopfli <https://pypi.python.org/pypi/zopfli>`__: Python bindings of
    the Zopfli compression library.

  *Extra:* ``woff``

- ``Lib/fontTools/unicode.py``

  To display the Unicode character names when dumping the ``cmap`` table
  with ``ttx`` we use the ``unicodedata`` module in the Standard Library.
  The version included in there varies between different Python versions.
  To use the latest available data, you can install:

  * `unicodedata2 <https://pypi.python.org/pypi/unicodedata2>`__:
    ``unicodedata`` backport for Python 2.7 and 3.x updated to the latest
    Unicode version 12.0. Note this is not necessary if you use Python 3.8
    as the latter already comes with an up-to-date ``unicodedata``.

  *Extra:* ``unicode``

- ``Lib/fontTools/varLib/interpolatable.py``

  Module for finding wrong contour/component order between different masters.
  It requires one of the following packages in order to solve the so-called
  "minimum weight perfect matching problem in bipartite graphs", or
  the Assignment problem:

  * `scipy <https://pypi.python.org/pypi/scipy>`__: the Scientific Library
    for Python, which internally uses `NumPy <https://pypi.python.org/pypi/numpy>`__
    arrays and hence is very fast;
  * `munkres <https://pypi.python.org/pypi/munkres>`__: a pure-Python
    module that implements the Hungarian or Kuhn-Munkres algorithm.

  *Extra:* ``interpolatable``

- ``Lib/fontTools/varLib/plot.py``

  Module for visualizing DesignSpaceDocument and resulting VariationModel.

  * `matplotlib <https://pypi.org/pypi/matplotlib>`__: 2D plotting library.

  *Extra:* ``plot``

- ``Lib/fontTools/misc/symfont.py``

  Advanced module for symbolic font statistics analysis; it requires:

  * `sympy <https://pypi.python.org/pypi/sympy>`__: the Python library for
    symbolic mathematics.

  *Extra:* ``symfont``

- ``Lib/fontTools/t1Lib.py``

  To get the file creator and type of Macintosh PostScript Type 1 fonts
  on Python 3 you need to install the following module, as the old ``MacOS``
  module is no longer included in Mac Python:

  * `xattr <https://pypi.python.org/pypi/xattr>`__: Python wrapper for
    extended filesystem attributes (macOS platform only).

  *Extra:* ``type1``

- ``Lib/fontTools/ttLib/removeOverlaps.py``

  Simplify TrueType glyphs by merging overlapping contours and components.

  * `skia-pathops <https://pypi.python.org/pypy/skia-pathops>`__: Python
    bindings for the Skia library's PathOps module, performing boolean
    operations on paths (union, intersection, etc.).

  *Extra:* ``pathops``

- ``Lib/fontTools/pens/cocoaPen.py`` and ``Lib/fontTools/pens/quartzPen.py``

  Pens for drawing glyphs with Cocoa ``NSBezierPath`` or ``CGPath`` require:

  * `PyObjC <https://pypi.python.org/pypi/pyobjc>`__: the bridge between
    Python and the Objective-C runtime (macOS platform only).

- ``Lib/fontTools/pens/qtPen.py``

  Pen for drawing glyphs with Qt's ``QPainterPath``, requires:

  * `PyQt5 <https://pypi.python.org/pypi/PyQt5>`__: Python bindings for
    the Qt cross platform UI and application toolkit.

- ``Lib/fontTools/pens/reportLabPen.py``

  Pen to drawing glyphs as PNG images, requires:

  * `reportlab <https://pypi.python.org/pypi/reportlab>`__: Python toolkit
    for generating PDFs and graphics.

Acknowledgements
~~~~~~~~~~~~~~~~

In alphabetical order:

Olivier Berten, Samyak Bhuta, Erik van Blokland, Petr van Blokland,
Jelle Bosma, Sascha Brawer, Tom Byrer, Antonio Cavedoni, Frédéric 
Coiffier, Vincent Connare, David Corbett, Simon Cozens, Dave Crossland, 
Simon Daniels, Peter Dekkers, Behdad Esfahbod, Behnam Esfahbod, Hannes 
Famira, Sam Fishman, Matt Fontaine, Yannis Haralambous, Greg Hitchcock, 
Jeremie Hornus, Khaled Hosny, John Hudson, Denis Moyogo Jacquerye, Jack 
Jansen, Tom Kacvinsky, Jens Kutilek, Antoine Leca, Werner Lemberg, Tal 
Leming, Peter Lofting, Cosimo Lupo, Masaya Nakamura, Dave Opstad, 
Laurence Penney, Roozbeh Pournader, Garret Rieger, Read Roberts, Guido 
van Rossum, Just van Rossum, Andreas Seidel, Georg Seifert, Chris 
Simpkins, Miguel Sousa, Adam Twardoch, Adrien Tétar, Vitaly Volkov, 
Paul Wise.

Copyrights
~~~~~~~~~~

| Copyright (c) 1999-2004 Just van Rossum, LettError
  (just@letterror.com)
| See `LICENSE <LICENSE>`__ for the full license.

Copyright (c) 2000 BeOpen.com. All Rights Reserved.

Copyright (c) 1995-2001 Corporation for National Research Initiatives.
All Rights Reserved.

Copyright (c) 1991-1995 Stichting Mathematisch Centrum, Amsterdam. All
Rights Reserved.

Have fun!

.. |CI Build Status| image:: https://github.com/fonttools/fonttools/workflows/Test/badge.svg
   :target: https://github.com/fonttools/fonttools/actions?query=workflow%3ATest
.. |Coverage Status| image:: https://codecov.io/gh/fonttools/fonttools/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/fonttools/fonttools
.. |PyPI| image:: https://img.shields.io/pypi/v/fonttools.svg
   :target: https://pypi.org/project/FontTools
.. |Gitter Chat| image:: https://badges.gitter.im/fonttools-dev/Lobby.svg
   :alt: Join the chat at https://gitter.im/fonttools-dev/Lobby
   :target: https://gitter.im/fonttools-dev/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
