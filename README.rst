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

.. |Build Status| image:: https://travis-ci.org/googlei18n/cu2qu.svg
   :target: https://travis-ci.org/googlei18n/cu2qu
.. |PyPI Version| image:: https://img.shields.io/pypi/v/cu2qu.svg
   :target: https://pypi.org/project/cu2qu/
.. |Coverage| image:: https://codecov.io/gh/googlei18n/cu2qu/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/googlei18n/cu2qu
