##############
interpolatable
##############

Note also that :mod:`varLib.interpolatable` supports some :doc:`optional </optional>`
external libraries.

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
