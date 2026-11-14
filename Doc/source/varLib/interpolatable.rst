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

The midway panel remains a 50/50 blend of the two displayed masters. Its
location label gives their nominal coordinate midpoint, with input coordinates
when recoverable. Other masters can affect the font's actual outline at that
location, so the displayed blend need not be an actual font instance.

.. automodule:: fontTools.varLib.interpolatable
   :members:
   :undoc-members:
