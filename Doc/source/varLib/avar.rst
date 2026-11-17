#####################
avar: Axis mappings
#####################

``fonttools varLib.avar.map`` maps variation coordinates through avar version
1 or 2. ``fonttools varLib.avar.reverse`` inverts it, finding pre-fvar
coordinates for a post-avar target::

    fonttools varLib.avar.reverse -i Font.ttf wght=0.6 wdth=-0.2

``-i`` selects normalized targets; by default the result uses pre-fvar units.
Add ``-o`` for normalized input coordinates in the result. An omitted target
axis means normalized zero while its input is free; a pinned or hidden axis is
left unconstrained, since its input cannot move. Hidden *input* axes are
always held at their fvar defaults. To fix another input axis, use ``--pin``
with a pre-fvar value (independent of ``-i`` and ``-o``)::

    fonttools varLib.avar.reverse -i --pin opsz=14 Font.ttf wght=0.6

Omit the value to pin an axis at its fvar default. Repeat ``--pin`` or
comma-separate to fix more axes::

    fonttools varLib.avar.reverse -i --pin opsz,wdth=100 Font.ttf wght=0.6

By default every non-hidden axis may vary. To restrict the result to a chosen
set of input axes, use ``--vary`` (comma-separated or repeated); every other
axis is pinned to its fvar default, overriding hidden flags::

    fonttools varLib.avar.reverse -i --vary wght,wdth,opsz Font.ttf wght=0.6 wdth=-0.2

``fonttools varLib.avar.roundtrip`` takes a pre-fvar source, forward-maps it
through avar, and reverses the result. This checks how well a design location
survives the round trip. ``-i`` selects normalized source coordinates and
``-o`` selects normalized recovered inputs; ``--pin``, ``--vary``, and
``--show-error`` work as in the reverse command::

    fonttools varLib.avar.roundtrip -o Font.ttf wght=700 wdth=125

The residual measures post-avar output differences, including the outputs of
hidden and pinned axes. A non-injective map can recover different but equivalent
inputs.

Inspecting structure and reachability
====================================

``fonttools varLib.avar.analyze`` reports structural features as JSON in the
user-facing input space, with hidden and collapsed input axes fixed at their
fvar defaults::

    fonttools varLib.avar.analyze Font.ttf

The report includes per-axis knots, segment-map slope changes, active avar2
region boundaries pulled back through the segment maps, and regions containing
cross-axis products. Boundary patches are described by a fixed axis coordinate
and unions of intervals on other axes. Intervals describe support closures;
their endpoints may have zero contribution. Hidden outputs are retained.
These are structural candidates: overlapping regions, cancellation, and output
clipping can make some candidates invisible. This is not a complete
classification of critical points or topology.

Extract a normalized output level set on a one- or two-axis input slice::

    fonttools varLib.avar.analyze Font.ttf --axes wght,wdth --contour XOPQ=0.3 --at opsz=14

Unspecified inputs stay at default. Slice coordinates and ``--at`` use user
units. The result contains isolated points, polylines, and constant cells.
One-dimensional roots use SciPy, and two-dimensional polylines use ContourPy.
Curves describe the continuous map before avar2 quantization and clipping;
levels -1 and +1 describe saturation boundaries. Two-dimensional curves are
sampled approximations, with avar knots inserted into the grid. Slices with
jumps are rejected to avoid interpolating across discontinuities. The grid
is limited to 65,536 points.

``fonttools varLib.avar.reachability`` checks output targets and returns JSON::

    fonttools varLib.avar.reachability -i Font.ttf XOPQ=0.3

Only explicitly supplied outputs are constrained; omitted outputs are free.
``-i`` selects normalized targets; otherwise targets use pre-fvar units.
Hidden inputs remain at default even when a hidden output is targeted. A
``reachable`` result contains a user-coordinate witness verified with the
rounded/clipped forward map. Its ``input`` dictionary omits axes at their
fvar defaults; omitted inputs implicitly use those defaults. Conservative
marginal bounds can establish
``unreachable``. Other failed searches return ``undetermined``, with the best
fit found and its normalized Euclidean error. Marginal bounds do not describe
joint reachability. ``--tolerance`` sets the accepted output error (default:
one F2Dot14 unit).

Python callers can reuse a prepared checker::

    from fontTools.varLib.avar.analyze import analyze, contours
    from fontTools.varLib.avar.reachability import ReachabilityMapper

    structure = analyze(font)
    geometry = contours(font, ["wght", "wdth"], "XOPQ", 0.3, location={"opsz": 14})
    checker = ReachabilityMapper(font)
    result = checker.check({"XOPQ": 0.3}, inputNormalized=True)

Plotting slices
===============

``fonttools varLib.avar.plot`` uses the analyzer's structural boundaries and
contour geometry to plot an input slice next to its mapped output grid::

    fonttools varLib.avar.plot Font.ttf wght wdth --output XOPQ --at opsz=14 -o avar.svg

It also supports a single input axis. Omitting ``-o`` opens a Matplotlib
window. Input coordinates use user units; colors and projected output axes
use normalized units. Hidden inputs and other unspecified inputs stay at
default. The mapped view shows the projected image of this particular slice,
not the complete reachable space. Jumps in either projected output are
rejected rather than connected by grid segments. Install
``fonttools[avar,plot]`` for the optional numerical, contour, and plotting
dependencies::

    from fontTools.varLib.avar.plot import plot

    figure = plot(font, ["wght", "wdth"], output="XOPQ", location={"opsz": 14})
    figure.savefig("avar.svg")

Prepared mapping
================

For repeated forward evaluations, prepare a mapper once::

    from fontTools.varLib.avar.map import ForwardMapper

    mapper = ForwardMapper(font)
    first = mapper.map({"wght": 600}, outputNormalized=True)
    second = mapper.map({"wght": 700}, outputNormalized=True)

This retains axis metadata and the VarStore region-support cache. It requires
no NumPy or SciPy. Construct a new mapper after changing the font's fvar or
avar tables. The module-level ``map()`` function remains available for
individual calls.

Prepare a reverse mapper to solve several targets with the same constraints::

    from fontTools.varLib.avar.reverse import ReverseMapper

    mapper = ReverseMapper(font, pinned={"opsz": None})
    first, error = mapper.reverse({"wght": 0.6}, inputNormalized=True)
    second, error = mapper.reverse({"wght": 0.8}, inputNormalized=True)

The solver retains its unrounded mapping, Jacobian data, starting points,
and exact forward evaluator. It memoizes up to 128 target solutions by default;
``cache_size=0`` disables memoization, and ``clear_cache()`` discards cached
solutions. Unit and output-filtering options share cached solutions, but
explicitly specified fixed-axis targets and sparsity tolerances remain distinct.
Each call returns a fresh location dictionary. Pins and ``vary`` are fixed at
construction, and changing the font's fvar or avar tables requires a new mapper.
The module-level ``reverse()`` function remains available for individual calls.
The Python reverse APIs also accept ``partial=True`` to leave every omitted
output unconstrained, as in the reachability checker.

Collapsed region-support edges can introduce jumps even before rounding.
The solver tests their exact boundaries with the affected inputs fixed, then
searches adjacent intervals with bounds that prevent crossing those jumps.
Boundaries are pulled back through the avar1 segment maps, including multiple
preimages and plateau endpoints. Region contexts also test intersections of
jump planes. This does not exhaustively enumerate combinations of intervals
across all axes, so a global optimum is still not guaranteed.

Reverse mapping requires the optional ``fonttools[avar]`` dependencies.
It minimizes normalized output error, then prefers fewer non-default input
axes among solutions within one F2Dot14 unit of the best error found. A greedy
search seeks sparse solutions; neither global optimality nor the minimum
possible number of axes is guaranteed. Unreachable targets return an
approximation; ``--show-error`` prints the residual, and the Python API returns
it as the ``error`` alongside the location. CLI output is rounded to the font's
F2Dot14 resolution for readability. The font is not modified.

.. automodule:: fontTools.varLib.avar.reverse
   :members: reverse, ReverseMapper

.. automodule:: fontTools.varLib.avar.map
   :members: ForwardMapper

.. automodule:: fontTools.varLib.avar.roundtrip
   :members: roundtrip

.. automodule:: fontTools.varLib.avar.analyze
   :members: analyze, contours

.. automodule:: fontTools.varLib.avar.reachability
   :members: check, ReachabilityMapper

.. automodule:: fontTools.varLib.avar.plot
   :members: plot
