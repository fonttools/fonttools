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

The solver retains its continuous mapping, Jacobian data, starting points,
and exact forward evaluator. It memoizes up to 128 target solutions by default;
``cache_size=0`` disables memoization, and ``clear_cache()`` discards cached
solutions. Unit and output-filtering options share cached solutions, but
explicitly specified fixed-axis targets and sparsity tolerances remain distinct.
Each call returns a fresh location dictionary. Pins and ``vary`` are fixed at
construction, and changing the font's fvar or avar tables requires a new mapper.
The module-level ``reverse()`` function remains available for individual calls.

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
