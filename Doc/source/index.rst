.. image:: ../../Icons/FontToolsIconGreenCircle.png
   :width: 200px
   :height: 200px
   :alt: Font Tools
   :align: center


fontTools Docs
==============

|Travis Build Status| |Appveyor Build status| |Coverage Status| |PyPI| |Gitter Chat|

About
-----


fontTools is a library for manipulating fonts, written in Python. The project includes the TTX tool, that can convert TrueType and OpenType fonts to and from an XML text format, which is also called TTX. It supports TrueType, OpenType, AFM and to an extent Type 1 and some Mac-specific formats. The project has an `MIT open-source license <https://github.com/fonttools/fonttools/blob/master/LICENSE>`_. Among other things this means you can use it free of charge.

Installation
------------

.. note::

    fontTools requires `Python <http://www.python.org/download/>`_ 3.6 or later.

The package is listed in the Python Package Index (PyPI), so you can install it with `pip <https://pip.pypa.io/>`_::

    pip install fonttools

If you would like to contribute to its development, you can clone the repository from GitHub, install the package in 'editable' mode and modify the source code in place. We recommend creating a virtual environment, using the Python 3 `venv <https://docs.python.org/3/library/venv.html>`_ module::

    # download the source code to 'fonttools' folder
    git clone https://github.com/fonttools/fonttools.git
    cd fonttools

    # create new virtual environment called e.g. 'fonttools-venv', or anything you like
    python -m venv fonttools-venv

    # source the `activate` shell script to enter the environment (Un*x)
    . fonttools-venv/bin/activate

    # to activate the virtual environment in Windows `cmd.exe`, do
    fonttools-venv\Scripts\activate.bat

    # install in 'editable' mode
    pip install -e .


.. note::

    To exit a Python virtual environment, enter the command ``deactivate``.

See the Optional Requirements section below for details about module-specific dependencies that must be installed in select cases.


TTX – From OpenType and TrueType to XML and Back
------------------------------------------------

Once installed you can use the ttx command to convert binary font files (.otf, .ttf, etc) to the TTX XML format, edit them, and convert them back to binary format. TTX files have a .ttx file extension::

    ttx /path/to/font.otf
    ttx /path/to/font.ttx

The TTX application can be used in two ways, depending on what platform you run it on:

* As a command line tool (Windows/DOS, Unix, macOS)
* By dropping files onto the application (Windows, macOS)

TTX detects what kind of files it is fed: it will output a ``.ttx`` file when it sees a ``.ttf`` or ``.otf``, and it will compile a ``.ttf`` or ``.otf`` when the input file is a ``.ttx`` file. By default, the output file is created in the same folder as the input file, and will have the same name as the input file but with a different extension. TTX will never overwrite existing files, but if necessary will append a unique number to the output filename (before the extension) such as ``Arial#1.ttf``.

When using TTX from the command line there are a bunch of extra options. These are explained in the help text, as displayed when typing ``ttx -h`` at the command prompt. These additional options include:


* specifying the folder where the output files are created
* specifying which tables to dump or which tables to exclude
* merging partial .ttx files with existing .ttf or .otf files
* listing brief table info instead of dumping to .ttx
* splitting tables to separate .ttx files
* disabling TrueType instruction disassembly

The TTX file format
^^^^^^^^^^^^^^^^^^^

The following tables are currently supported::

    BASE, CBDT, CBLC, CFF, CFF2, COLR, CPAL, DSIG, EBDT, EBLC, FFTM,
    Feat, GDEF, GMAP, GPKG, GPOS, GSUB, Glat, Gloc, HVAR, JSTF, LTSH,
    MATH, META, MVAR, OS/2, SING, STAT, SVG, Silf, Sill, TSI0, TSI1,
    TSI2, TSI3, TSI5, TSIB, TSID, TSIJ, TSIP, TSIS, TSIV, TTFA, VDMX,
    VORG, VVAR, ankr, avar, bsln, cidg, cmap, cvar, cvt, feat, fpgm,
    fvar, gasp, gcid, glyf, gvar, hdmx, head, hhea, hmtx, kern, lcar,
    loca, ltag, maxp, meta, mort, morx, name, opbd, post, prep, prop,
    sbix, trak, vhea and vmtx

Other tables are dumped as hexadecimal data.

TrueType fonts use glyph indices (GlyphIDs) to refer to glyphs in most places. While this is fine in binary form, it is really hard to work with for humans. Therefore we use names instead.

The glyph names are either extracted from the ``CFF`` table or the ``post`` table, or are derived from a Unicode ``cmap`` table. In the latter case the Adobe Glyph List is used to calculate names based on Unicode values. If all of these methods fail, names are invented based on GlyphID (eg ``glyph00142``)

It is possible that different glyphs use the same name. If this happens, we force the names to be unique by appending #n to the name (n being an integer number.) The original names are being kept, so this has no influence on a "round tripped" font.

Because the order in which glyphs are stored inside the binary font is important, we maintain an ordered list of glyph names in the font.

Please see the :py:mod:`fontTools.ttx` documentation for additional details.


Other Tools
-----------

Commands for inspecting, merging and subsetting fonts are also available::

    pyftinspect
    pyftmerge
    pyftsubset

Please see the :py:mod:`fontTools.inspect`, :py:mod:`fontTools.merge`, and :py:mod:`fontTools.subset` documentation for additional information about these tools.


fontTools Python Library
------------------------

The fontTools Python library provides a convenient way to programmatically edit font files::

    >>> from fontTools.ttLib import TTFont
    >>> font = TTFont('/path/to/font.ttf')
    >>> font
    <fontTools.ttLib.TTFont object at 0x10c34ed50>
    >>>

A selection of sample Python programs is in the `Snippets directory <https://github.com/fonttools/fonttools/blob/master/Snippets/>`_ of the fontTools repository.

Please navigate to the respective area of the documentation to learn more about the available modules in the fontTools library.


Optional Requirements
---------------------

.. note::

    Additional dependencies are required by some of the fontTools modules to unlock optional features.  The list below details these optional dependencies.


inspect Module
^^^^^^^^^^^^^^

:py:mod:`fontTools.inspect`
^^^^^^^^^^^^^^^^^^^^^^^^^^^

A GUI font inspector, requires one of the following packages:

* `PyGTK <https://pypi.python.org/pypi/PyGTK>`_: Python bindings for GTK  2.x (only works with Python 2)
* `PyGObject <https://wiki.gnome.org/action/show/Projects/PyGObject>`_ : Python bindings for GTK 3.x and gobject-introspection libraries (also compatible with Python 3)



misc Module
^^^^^^^^^^^

:py:mod:`fontTools.misc.symfont`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Advanced module for symbolic font statistics analysis; it requires:

* `sympy <https://pypi.python.org/pypi/sympy>`_: the Python library for symbolic mathematics



pens Modules
^^^^^^^^^^^^

:py:mod:`fontTools.pens.cocoaPen`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pen for drawing glyphs with Cocoa ``NSBezierPath``, requires:

* `PyObjC <https://pypi.python.org/pypi/pyobjc>`_: the bridge between Python and the Objective-C runtime (macOS platform only)


:py:mod:`fontTools.pens.qtPen`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pen for drawing glyphs with Qt's QPainterPath, requires:

* `PyQt5 <https://pypi.python.org/pypi/PyQt5>`_: Python bindings for the Qt cross platform UI and application toolkit


:py:mod:`fontTools.pens.reportLabPen`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pen to drawing glyphs as PNG images, requires:

* `reportlab <https://pypi.python.org/pypi/reportlab>`_: Python toolkit for generating PDFs and graphics



t1Lib Module
^^^^^^^^^^^^

:py:mod:`fontTools.t1Lib`
^^^^^^^^^^^^^^^^^^^^^^^^^

To get the file creator and type of Apple PostScript Type 1 fonts on Python 3 you need to install the following module, as the old macOS module is no longer included in macOS Python:

* `xattr <https://pypi.python.org/pypi/xattr>`_: Python wrapper for extended filesystem attributes (macOS platform only)



ttLib Modules
^^^^^^^^^^^^^

:py:mod:`fontTools.ttLib.woff2`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Module to compress/decompress WOFF 2.0 web fonts; it requires:

* `brotli <https://pypi.python.org/pypi/Brotli>`_: Python bindings of the Brotli compression library.


:py:mod:`fontTools.ttLib.sfnt`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To better compress WOFF 1.0 web fonts, the following module can be used instead of the built-in zlib library:

* `zopfli <https://pypi.python.org/pypi/zopfli>`_: Python bindings of the Zopfli compression library


ufoLib Module
^^^^^^^^^^^^^

:py:mod:`fontTools.ufoLib`
^^^^^^^^^^^^^^^^^^^^^^^^^^

Package for reading and writing UFO source files; it requires:

* `fs <https://pypi.org/pypi/fs>`_: (aka ``pyfilesystem2``) filesystem abstraction layer
* `enum34 <https://pypi.org/pypi/enum34>`_: backport for the built-in enum module (only required on Python < 3.4)


unicode Module
^^^^^^^^^^^^^^

:py:mod:`fontTools.unicode`
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To display the Unicode character names when dumping the cmap table with ttx we use the unicodedata module in the Standard Library. The version included in there varies between different Python versions. To use the latest available data, you can install:

* `unicodedata2 <https://pypi.python.org/pypi/unicodedata2>`_: unicodedata backport for Python 2.7 and 3.5 updated to the latest Unicode version 9.0. Note this is not necessary if you use Python 3.6 as the latter already comes with an up-to-date unicodedata.


varLib Module
^^^^^^^^^^^^^

:py:mod:`fontTools.varLib.interpolatable`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Module for finding wrong contour/component order between different masters. It requires one of the following packages in order to solve the so-called "minimum weight perfect matching problem in bipartite graphs", or the Assignment problem:

* `scipy <https://pypi.python.org/pypi/scipy>`_: the Scientific Library for Python, which internally uses `NumPy <https://pypi.python.org/pypi/numpy>`_ arrays and hence is very fast
* `munkres <https://pypi.python.org/pypi/munkres>`_: a pure-Python module that implements the Hungarian or Kuhn-Munkres algorithm


Testing
-------

To run the test suite, use::

    python setup.py test

If you have `pytest <http://docs.pytest.org/en/latest/>`_, you can run the pytest command directly. The tests will run against the installed fontTools package, or the first one found in the ``PYTHONPATH``.

You can also use `tox <https://testrun.org/tox/latest/>`_ to automatically run tests on different Python versions in isolated virtual environments::

    pip install tox
    tox



.. note::

    When you run ``tox`` without arguments, the tests are executed for all the environments listed in the ``tox.ini`` ``envlist``. The current Python interpreters defined for tox testing must be available on your system ``PATH``.

You can specify a different testing environment list via the ``-e`` option, or the ``TOXENV`` environment variable::

    tox -e py27-nocov
    TOXENV="py36-cov,htmlcov" tox


Development Community
---------------------

fontTools development is ongoing in an active community of developers that includes professional developers employed at major software corporations and type foundries as well as hobbyists.

Feature requests and bug reports are always welcome at https://github.com/fonttools/fonttools/issues/

The best place for end-user and developer discussion about the fontTools project is the https://groups.google.com/d/forum/fonttools mailing list. There is also a development https://groups.google.com/d/forum/fonttools-dev mailing list for continuous integration notifications. You can also email Behdad privately at behdad@behdad.org.


Acknowledgments
---------------

In alphabetical order:

Olivier Berten, Samyak Bhuta, Erik van Blokland, Petr van Blokland, Jelle Bosma, Sascha Brawer, Tom Byrer, Frédéric Coiffier, Vincent Connare, Dave Crossland, Simon Daniels, Behdad Esfahbod, Behnam Esfahbod, Hannes Famira, Sam Fishman, Matt Fontaine, Yannis Haralambous, Greg Hitchcock, Jeremie Hornus, Khaled Hosny, John Hudson, Denis Moyogo Jacquerye, Jack Jansen, Tom Kacvinsky, Jens Kutilek, Antoine Leca, Werner Lemberg, Tal Leming, Peter Lofting, Cosimo Lupo, Masaya Nakamura, Dave Opstad, Laurence Penney, Roozbeh Pournader, Garret Rieger, Read Roberts, Guido van Rossum, Just van Rossum, Andreas Seidel, Georg Seifert, Miguel Sousa, Adam Twardoch, Adrien Tétar, Vitaly Volkov, Paul Wise


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
   subset
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