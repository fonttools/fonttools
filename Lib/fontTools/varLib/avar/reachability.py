"""Check post-avar targets with hidden input axes held at default."""

import json
import math

from fontTools.varLib.models import normalizeValue
from .analyze import _AxisSpace
from .map import _load_font, _parse_coordinates


class ReachabilityMapper:
    """Prepare repeated target checks against a font's public input space.

    Only explicitly supplied outputs are constrained, including any hidden
    outputs in the target. Results contain normalized targets and outputs and
    a witness in user units, omitting inputs at their fvar defaults.
    ``reachable`` means that forward evaluation of
    that witness meets the requested tolerance. ``unreachable`` means marginal
    bounds exclude the target. Otherwise the result is ``undetermined``: a
    numerical search does not establish non-reachability.

    Construct a new mapper after changing fvar or avar.
    """

    def __init__(self, font):
        self._space = _AxisSpace(font)
        self._bounds = self._space.bounds()
        self._font = font
        self._reverse = None

    def check(self, location, *, inputNormalized=False, tolerance=1 / 16384):
        """Check a possibly partial output target; omitted axes are unconstrained.

        Targets use user units unless ``inputNormalized`` is true. ``tolerance``
        is Euclidean output distance in normalized coordinates. A hidden axis
        in ``location`` constrains its output, never its input.
        """
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("tolerance must be finite and non-negative")
        triples = self._space.forward.triples
        unknown = sorted(location.keys() - triples.keys())
        if unknown:
            raise ValueError(f"Unknown axis tag(s): {', '.join(unknown)}")
        target = {}
        for tag, value in location.items():
            if not math.isfinite(value):
                raise ValueError(f"Invalid target coordinate for {tag}: {value}")
            triple = triples[tag]
            if not inputNormalized and triple[0] == triple[2] and value != triple[1]:
                raise ValueError(
                    f"Collapsed output axis {tag} has no user scale beyond its default"
                )
            target[tag] = (
                value
                if inputNormalized
                else normalizeValue(value, triple, extrapolate=True)
            )
        distances = [
            max(self._bounds[tag][0] - value, 0, value - self._bounds[tag][1])
            for tag, value in target.items()
        ]
        lower_bound = math.hypot(*distances)
        result = dict(
            status="unreachable",
            target=target,
            tolerance=tolerance,
            errorLowerBound=lower_bound,
            input=None,
            output=None,
            error=None,
        )
        if lower_bound > tolerance:
            return result
        witness = {tag: triple[1] for tag, triple in triples.items()}
        actual = self._space.forward.map(witness, outputNormalized=True)
        error = math.hypot(*(actual[tag] - value for tag, value in target.items()))
        # Delay SciPy until a target actually needs an inverse search.
        if error > tolerance:
            if self._reverse is None:
                from .reverse import ReverseMapper

                self._reverse = ReverseMapper(self._font)
            # Targets just beyond the output cube can still be reached to a
            # caller's tolerance. Seek its boundary, then verify the original
            # target rather than silently clamping the reported residual.
            witness, _ = self._reverse.reverse(
                {tag: min(1, max(-1, value)) for tag, value in target.items()},
                inputNormalized=True,
                partial=True,
                tolerance=0,
            )
            actual = self._space.forward.map(witness, outputNormalized=True)
            error = math.hypot(*(actual[tag] - value for tag, value in target.items()))
        result.update(
            status="reachable" if error <= tolerance else "undetermined",
            input={
                tag: value for tag, value in witness.items() if value != triples[tag][1]
            },
            output=actual,
            error=error,
        )
        return result


def check(font, location, *, inputNormalized=False, tolerance=1 / 16384):
    """Check one target; use ReachabilityMapper to reuse preparation and caching."""
    return ReachabilityMapper(font).check(
        location,
        inputNormalized=inputNormalized,
        tolerance=tolerance,
    )


def main(args=None):
    """Check output reachability and print a verified input witness as JSON."""
    import argparse

    parser = argparse.ArgumentParser(
        "fonttools varLib.avar.reachability", description=main.__doc__
    )
    parser.add_argument("font")
    parser.add_argument("coords", nargs="*", metavar="AXIS=value")
    parser.add_argument(
        "-i", action="store_true", help="Targets are normalized output coordinates"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1 / 16384,
        help="Normalized Euclidean output error",
    )
    options = parser.parse_args(args)
    font = _load_font(parser, options.font)
    location = _parse_coordinates(parser, options.coords)
    try:
        result = check(
            font, location, inputNormalized=options.i, tolerance=options.tolerance
        )
    except (ValueError, ImportError) as e:
        parser.error(str(e))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
