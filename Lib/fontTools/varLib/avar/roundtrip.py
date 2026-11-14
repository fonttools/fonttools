"""Forward-map a location through avar, then recover equivalent inputs."""

from .map import map as map_forward
from .reverse import reverse, _make_parser, _run_cli


def roundtrip(
    font,
    location,
    *,
    inputNormalized=False,
    outputNormalized=False,
    dropZeroes=False,
    pinned=None,
    vary=None,
    tolerance=1 / 16384,
):
    """Map a pre-fvar source through avar and reverse the resulting location.

    Return ``(location, error)`` as in :func:`fontTools.varLib.avar.reverse.reverse`,
    or None for a font without fvar. ``inputNormalized`` describes the source
    units; ``outputNormalized`` describes the recovered input units.

    All forward-mapped output axes, including hidden and pinned axes, are
    scored during reversal. The error measures post-avar output differences,
    so a non-injective map may recover a different but equivalent input.
    """
    target = map_forward(
        font,
        location,
        inputNormalized=inputNormalized,
        outputNormalized=True,
        dropZeroes=False,
    )
    if target is None:
        return None
    return reverse(
        font,
        target,
        inputNormalized=True,
        outputNormalized=outputNormalized,
        dropZeroes=dropZeroes,
        pinned=pinned,
        vary=vary,
        tolerance=tolerance,
    )


def main(args=None):
    """Map pre-fvar inputs through avar, then recover equivalent inputs."""
    parser = _make_parser(
        "fonttools varLib.avar.roundtrip",
        "Forward-map a source through avar, then recover equivalent pre-fvar "
        "inputs (requires scipy). The residual measures output error; a "
        "non-injective map may recover a different but equivalent input.",
        coords_help="Pre-fvar source coordinates, e.g. 'wght=700 wdth=125'. "
        "Omit for the default location.",
        input_help="Source coordinates are normalized (-1..1).",
    )
    return _run_cli(parser, args, roundtrip)


if __name__ == "__main__":
    import sys

    sys.exit(main())
