|Build Status| |PyPI Version| |Coverage|

cu2qu
=====

This library provides functions which take in UFO objects (Defcon Fonts
or Robofab RFonts) and converts any cubic curves to quadratic. The most
useful function is probably ``fonts_to_quadratic``:

.. code:: python

    from defcon import Font
    from cu2qu.ufo import fonts_to_quadratic
    thin_font = Font('MyFont-Thin.ufo')
    bold_font = Font('MyFont-Bold.ufo')
    fonts_to_quadratic([thin_font, bold_font])

Interpolation compatibility is guaranteed during conversion. If it's not
needed, converting one font at a time may yield more optimized results:

.. code:: python

    for font in [thin_font, bold_font]:
        fonts_to_quadratic([font])

Some fonts may need a different error threshold than the default (0.001
em). This can also be provided by the caller:

.. code:: python

    fonts_to_quadratic([thin_font, bold_font], max_err_em=0.005)

.. code:: python

    for font in [thin_font, bold_font]:
        fonts_to_quadratic([font], max_err_em=0.001)

``fonts_to_quadratic`` can print a string reporting the number of curves
of each length. For example
``fonts_to_quadratic([font], dump_stats=True)`` may print something
like:

::

    3: 1000
    4: 2000
    5: 100

meaning that the font now contains 1000 curves with three points, 2000
with four points, and 100 with five. Given multiple fonts, the function
will report the total counts across all fonts. You can also accumulate
statistics between calls by providing your own report dictionary:

.. code:: python

    stats = {}
    for font in [thin_font, bold_font]:
        fonts_to_quadratic([font], stats=stats)
    # "stats" will report combined statistics for both fonts

The library also provides a command-line script also named ``cu2qu``.
Check its ``--help`` to see all the options.

Installation
------------

You can install/upgrade cu2qu using pip, like any other Python package.

.. code:: sh

    $ pip install --upgrade cu2qu

This will download the latest stable version available from the Python
Package Index (PyPI).

If you wish to modify the sources in-place, you can clone the git repository
from Github and install in ``--editable`` (or ``-e``) mode:

.. code:: sh

    $ git clone https://github.com/googlefonts/cu2qu
    $ cd cu2qu
    $ pip install --editable .

Optionally, you can build an optimized version of cu2qu which uses Cython_
to compile Python to C. The extension module thus created is *more than
twice as fast* than its pure-Python equivalent.

When installing cu2qu from PyPI using pip, as long as you have a C compiler
available, the cu2qu setup script will automatically attempt to build a
C/Python extension module. If the compilation fails for any reasons, an error
is printed and cu2qu will be installed as pure-Python, without the optimized
extension.

If you have cloned the git repository, the C source files are not present and
need to be regenerated. To do that, you need to install the latest Cython
(as usual, ``pip install -U cython``), and then use the global option
``--with-cython`` when invoking the ``setup.py`` script. You can also export
a ``CU2QU_WITH_CYTHON=1`` environment variable if you prefer.

For example, to build the cu2qu extension module in-place (i.e. in the same
source directory):

.. code:: sh

    $ python setup.py --with-cython build_ext --inplace

You can also pass ``--global-option`` when installing with pip from a local
source checkout, like so:

.. code:: sh

    $ pip install --global-option="--with-cython" -e .


.. _Cython: https://github.com/cython/cython
.. |Build Status| image:: https://travis-ci.org/googlefonts/cu2qu.svg
   :target: https://travis-ci.org/googlefonts/cu2qu
.. |PyPI Version| image:: https://img.shields.io/pypi/v/cu2qu.svg
   :target: https://pypi.org/project/cu2qu/
.. |Coverage| image:: https://codecov.io/gh/googlefonts/cu2qu/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/googlefonts/cu2qu
