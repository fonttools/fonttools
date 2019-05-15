|Travis Build Status| |Appveyor Build status| |Coverage Status| |PyPI| |Gitter Chat|

What is this?
~~~~~~~~~~~~~

| fontTools is a library for manipulating fonts, written in Python. The
  project includes the TTX tool, that can convert TrueType and OpenType
  fonts to and from an XML text format, which is also called TTX. It
  supports TrueType, OpenType, AFM and to an extent Type 1 and some
  Mac-specific formats. The project has an `MIT open-source
  licence <LICENSE>`__.
| Among other things this means you can use it free of charge.

Installation
~~~~~~~~~~~~

FontTools requires `Python <http://www.python.org/download/>`__ 2.7, 3.4
or later.

**NOTE** After January 1 2019, until no later than June 30 2019, the support
for *Python 2.7* will be limited to only bug fixes, and no new features will
be added to the ``py27`` branch. The upcoming FontTools 4.x series will require
*Python 3.5* or above. You can read more `here <https://python3statement.org>`__
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

TTX – From OpenType and TrueType to XML and Back
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once installed you can use the ``ttx`` command to convert binary font
files (``.otf``, ``.ttf``, etc) to the TTX XML format, edit them, and
convert them back to binary format. TTX files have a .ttx file
extension.

.. code:: sh

    ttx /path/to/font.otf
    ttx /path/to/font.ttx

The TTX application can be used in two ways, depending on what
platform you run it on:

-  As a command line tool (Windows/DOS, Unix, macOS)
-  By dropping files onto the application (Windows, macOS)

TTX detects what kind of files it is fed: it will output a ``.ttx`` file
when it sees a ``.ttf`` or ``.otf``, and it will compile a ``.ttf`` or
``.otf`` when the input file is a ``.ttx`` file. By default, the output
file is created in the same folder as the input file, and will have the
same name as the input file but with a different extension. TTX will
*never* overwrite existing files, but if necessary will append a unique
number to the output filename (before the extension) such as
``Arial#1.ttf``

When using TTX from the command line there are a bunch of extra options.
These are explained in the help text, as displayed when typing
``ttx -h`` at the command prompt. These additional options include:

-  specifying the folder where the output files are created
-  specifying which tables to dump or which tables to exclude
-  merging partial ``.ttx`` files with existing ``.ttf`` or ``.otf``
   files
-  listing brief table info instead of dumping to ``.ttx``
-  splitting tables to separate ``.ttx`` files
-  disabling TrueType instruction disassembly

The TTX file format
-------------------

The following tables are currently supported:

.. begin table list
.. code::

    BASE, CBDT, CBLC, CFF, CFF2, COLR, CPAL, DSIG, EBDT, EBLC, FFTM,
    Feat, GDEF, GMAP, GPKG, GPOS, GSUB, Glat, Gloc, HVAR, JSTF, LTSH,
    MATH, META, MVAR, OS/2, SING, STAT, SVG, Silf, Sill, TSI0, TSI1,
    TSI2, TSI3, TSI5, TSIB, TSID, TSIJ, TSIP, TSIS, TSIV, TTFA, VDMX,
    VORG, VVAR, ankr, avar, bsln, cidg, cmap, cvar, cvt, feat, fpgm,
    fvar, gasp, gcid, glyf, gvar, hdmx, head, hhea, hmtx, kern, lcar,
    loca, ltag, maxp, meta, mort, morx, name, opbd, post, prep, prop,
    sbix, trak, vhea and vmtx
.. end table list

Other tables are dumped as hexadecimal data.

TrueType fonts use glyph indices (GlyphIDs) to refer to glyphs in most
places. While this is fine in binary form, it is really hard to work
with for humans. Therefore we use names instead.

The glyph names are either extracted from the ``CFF`` table or the
``post`` table, or are derived from a Unicode ``cmap`` table. In the
latter case the Adobe Glyph List is used to calculate names based on
Unicode values. If all of these methods fail, names are invented based
on GlyphID (eg ``glyph00142``)

It is possible that different glyphs use the same name. If this happens,
we force the names to be unique by appending ``#n`` to the name (``n``
being an integer number.) The original names are being kept, so this has
no influence on a "round tripped" font.

Because the order in which glyphs are stored inside the binary font is
important, we maintain an ordered list of glyph names in the font.

Other Tools
~~~~~~~~~~~

Commands for merging and subsetting fonts are also available:

.. code:: sh

    pyftmerge
    pyftsubset

fontTools Python Module
~~~~~~~~~~~~~~~~~~~~~~~

The fontTools Python module provides a convenient way to
programmatically edit font files.

.. code:: py

    >>> from fontTools.ttLib import TTFont
    >>> font = TTFont('/path/to/font.ttf')
    >>> font
    <fontTools.ttLib.TTFont object at 0x10c34ed50>
    >>>

A selection of sample Python programs is in the
`Snippets <https://github.com/fonttools/fonttools/blob/master/Snippets/>`__
directory.

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
  `lxml <https://http://lxml.de>`__. The latter is preferred whenever present,
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
    ``unicodedata`` backport for Python 2.7 and 3.5 updated to the latest
    Unicode version 9.0. Note this is not necessary if you use Python 3.6
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

- ``Lib/fontTools/pens/cocoaPen.py``

  Pen for drawing glyphs with Cocoa ``NSBezierPath``, requires:

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

Testing
~~~~~~~

To run the test suite, you need to install `pytest <http://docs.pytest.org/en/latest/>`__.
When you run the ``pytest`` command, the tests will run against the
installed ``fontTools`` package, or the first one found in the
``PYTHONPATH``.

You can also use `tox <https://tox.readthedocs.io/en/latest/>`__ to
automatically run tests on different Python versions in isolated virtual
environments.

.. code:: sh

    pip install tox
    tox

Note that when you run ``tox`` without arguments, the tests are executed
for all the environments listed in tox.ini's ``envlist``. In our case,
this includes Python 2.7 and 3.7, so for this to work the ``python2.7``
and ``python3.7`` executables must be available in your ``PATH``.

You can specify an alternative environment list via the ``-e`` option,
or the ``TOXENV`` environment variable:

.. code:: sh

    tox -e py27
    TOXENV="py36-cov,htmlcov" tox

Development Community
~~~~~~~~~~~~~~~~~~~~~

TTX/FontTools development is ongoing in an active community of
developers, that includes professional developers employed at major
software corporations and type foundries as well as hobbyists.

Feature requests and bug reports are always welcome at
https://github.com/fonttools/fonttools/issues/

The best place for discussions about TTX from an end-user perspective as
well as TTX/FontTools development is the
https://groups.google.com/d/forum/fonttools mailing list. There is also
a development https://groups.google.com/d/forum/fonttools-dev mailing
list for continuous integration notifications. You can also email Behdad
privately at behdad@behdad.org

History
~~~~~~~

The fontTools project was started by Just van Rossum in 1999, and was
maintained as an open source project at
http://sourceforge.net/projects/fonttools/. In 2008, Paul Wise (pabs3)
began helping Just with stability maintenance. In 2013 Behdad Esfahbod
began a friendly fork, thoroughly reviewing the codebase and making
changes at https://github.com/behdad/fonttools to add new features and
support for new font formats.

Acknowledgements
~~~~~~~~~~~~~~~~

In alphabetical order:

Olivier Berten, Samyak Bhuta, Erik van Blokland, Petr van Blokland,
Jelle Bosma, Sascha Brawer, Tom Byrer, Frédéric Coiffier, Vincent
Connare, Dave Crossland, Simon Daniels, Peter Dekkers, Behdad Esfahbod,
Behnam Esfahbod, Hannes Famira, Sam Fishman, Matt Fontaine, Yannis
Haralambous, Greg Hitchcock, Jeremie Hornus, Khaled Hosny, John Hudson,
Denis Moyogo Jacquerye, Jack Jansen, Tom Kacvinsky, Jens Kutilek,
Antoine Leca, Werner Lemberg, Tal Leming, Peter Lofting, Cosimo Lupo,
Masaya Nakamura, Dave Opstad, Laurence Penney, Roozbeh Pournader, Garret
Rieger, Read Roberts, Guido van Rossum, Just van Rossum, Andreas Seidel,
Georg Seifert, Miguel Sousa, Adam Twardoch, Adrien Tétar, Vitaly Volkov,
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
