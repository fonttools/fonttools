##############
interpolatable
##############

Note also that :mod:`varLib.interpolatable` supports some :doc:`optional </optional>`
external libraries.

When location data is available, master pairs are chosen using a
minimum spanning tree within each discrete-axis subspace. An edge is allowed
only when one master's set of nonzero continuous axes is a subset of the
other's (including equal sets). Edges that change fewer coordinate values
take priority, with squared Euclidean distance breaking ties. Thus matching
coordinates favor comparisons along grid lines, while one-axis masters are
still compared to their nearest neighbors. Each subspace needs a default
master at zero on all continuous axes. Without location data, masters are
compared along a chain in input order.

``--show-graph`` prints the resolved master comparison tree, including master
names and normalized coordinates, then exits without checking glyphs. The
tree is written to standard output, or to the file given by ``--output``.

For inputs with location data, graphical reports show the normalized
coordinates of every tested master.
For variable fonts these are post-avar coordinates. Input coordinates are
also shown when they can be recovered; avar2 input labels use the optional
SciPy-based inverter and are omitted when it cannot find a match within one
F2Dot14 unit. Internal masters are still tested even when no public input
location reaches them.

Input labels are resolved on demand using reusable forward and reverse
mappers. Formatted labels (including unreachable locations) are cached.
``--quiet`` diagnostics
use normalized names without solving input locations; graphical reports still
recover input labels for the panels they display. ``--name`` filtering matches
complete names, including recoverable input coordinates.

The midway panel remains a 50/50 blend of the two displayed masters. Its
location label gives their nominal coordinate midpoint, with input coordinates
when recoverable. Other masters can affect the font's actual outline at that
location, so the displayed blend need not be an actual font instance.

.. automodule:: fontTools.varLib.interpolatable
   :members:
   :undoc-members:
