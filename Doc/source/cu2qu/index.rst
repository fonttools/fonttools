##########################################
cu2qu: Cubic to quadratic curve conversion
##########################################

Routines for converting cubic curves to quadratic splines, suitable for use
in OpenType to TrueType outline conversion.

Conversion is carried out to a degree of tolerance provided by the user. While
it is relatively easy to find the best *single* quadratic curve to represent a
given cubic (see for example `this method from CAGD <https://www.sirver.net/blog/2011/08/23/degree-reduction-of-bezier-curves/>`_),
the best-fit method may not be sufficiently accurate for type design.

Instead, this method chops the cubic curve into multiple segments before
converting each cubic segment to a quadratic, in order to ensure that the
resulting spline fits within the given tolerance.

The basic curve conversion routines are implemented in the
:mod:`fontTools.cu2qu.cu2qu` module; the :mod:`fontTools.cu2qu.ufo` module
applies these routines to all of the curves in a UFO file or files; while the
:mod:`fontTools.cu2qu.cli` module implements the ``fonttools cu2qu`` command
for converting a UFO format font with cubic curves into one with quadratic
curves.

fontTools.cu2qu.cu2qu
---------------------

.. automodule:: fontTools.cu2qu.cu2qu
   :inherited-members:
   :members:
   :undoc-members:

fontTools.cu2qu.ufo
-------------------

.. automodule:: fontTools.cu2qu.ufo
   :inherited-members:
   :members:
   :undoc-members:
