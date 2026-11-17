"""Inspect avar features on the slice with hidden inputs at their defaults.

Structural features are candidates: overlapping regions can cancel them.
Coordinates describing their loci use user units; deltas and output bounds
use normalized coordinates. Quantization steps are not structural features.
"""

import itertools
import json
import math

from fontTools.misc.roundTools import otRound
from fontTools.varLib.models import normalizeValue, piecewiseLinearMap, supportScalar
from fontTools.varLib.varStore import NO_VARIATION_INDEX
from .map import ForwardMapper, _denormalize, _load_font


def _tent(value, triple):
    return supportScalar({"axis": value}, {"axis": triple})


def _preimages(value, mapping, lower, upper):
    points = sorted({lower, upper, *[k for k in mapping if lower < k < upper]})
    roots = set()
    for a, b in zip(points, points[1:]):
        va, vb = (piecewiseLinearMap(x, mapping) for x in (a, b))
        if va == vb == value:
            roots.update((a, b))
        elif va != vb and min(va, vb) <= value <= max(va, vb):
            roots.add(a + (value - va) * (b - a) / (vb - va))
    return roots


def _support_ranges(triple, mapping, lower, upper):
    """Closed support bounds, including isolated peaks and plateau preimages."""
    points = sorted(
        {lower, upper, *[k for k in mapping if lower < k < upper]}
        | set().union(*(_preimages(v, mapping, lower, upper) for v in triple))
    )
    intervals = [
        (p, p) for p in points if _tent(piecewiseLinearMap(p, mapping), triple)
    ]
    intervals.extend(
        (a, b)
        for a, b in zip(points, points[1:])
        if _tent(piecewiseLinearMap((a + b) / 2, mapping), triple)
    )
    return _merge_intervals(intervals)


def _merge_intervals(intervals):
    merged = []
    for a, b in sorted(intervals):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(b, merged[-1][1])
        else:
            merged.append([a, b])
    return merged


class _AxisSpace:
    def __init__(self, font):
        self.forward = ForwardMapper(font)
        self.free = tuple(
            a.axisTag
            for a in self.forward.axes
            if not a.flags & 1 and a.minValue < a.maxValue
        )
        self.fixed = {
            a.axisTag: a.defaultValue
            for a in self.forward.axes
            if a.axisTag not in self.free
        }
        self.domains = {
            tag: (
                -1.0 if lo < default else 0.0,
                1.0 if default < hi else 0.0,
            )
            for tag, (lo, default, hi) in self.forward.triples.items()
        }
        self.knots = {}
        self.zranges = {}
        for tag in self.forward.tags:
            lo, hi = self.domains[tag] if tag in self.free else (0, 0)
            mapping = self.forward.segments.get(tag, {})
            points = {lo, hi, 0.0, *[k for k in mapping if lo < k < hi]}
            self.knots[tag] = points
            mapped = [piecewiseLinearMap(p, mapping) for p in points]
            self.zranges[tag] = min(mapped), max(mapped)

        self.regions = []
        self.rows = {tag: [] for tag in self.forward.tags}
        instancer = self.forward._instancer
        if instancer is None:
            return
        by_region = {}
        for tag, index in zip(self.forward.tags, self.forward._indices):
            outer, inner = index >> 16, index & 0xFFFF
            if index == NO_VARIATION_INDEX or outer >= len(instancer._varData):
                continue
            data = instancer._varData[outer]
            if inner >= len(data.Item):
                continue
            for r, delta in zip(data.VarRegionIndex, data.Item[inner]):
                if not delta:
                    continue
                support = {
                    t: triple
                    for t, triple in instancer._getSupport(r).items()
                    if triple[1] != 0
                    and triple[0] <= triple[1] <= triple[2]
                    and not triple[0] < 0 < triple[2]
                }
                by_region.setdefault(r, {"support": support, "deltas": {}})
                deltas = by_region[r]["deltas"]
                deltas[tag] = deltas.get(tag, 0) + delta
                # Keep original terms for conservative bounds and summation.
                self.rows[tag].append((delta, support))

        for index, region in sorted(by_region.items()):
            support = region["support"]
            fixed_scalar = supportScalar(
                {tag: self.zranges[tag][0] for tag in self.fixed},
                {tag: triple for tag, triple in support.items() if tag in self.fixed},
            )
            if not fixed_scalar:
                continue
            ranges = {}
            for tag, triple in support.items():
                if tag not in self.free:
                    continue
                mapping = self.forward.segments.get(tag, {})
                ranges[tag] = _support_ranges(triple, mapping, *self.domains[tag])
                if not ranges[tag]:
                    break
                for edge in triple:
                    self.knots[tag].update(
                        _preimages(edge, mapping, *self.domains[tag])
                    )
            else:
                deltas = {tag: d / 16384 for tag, d in region["deltas"].items() if d}
                if deltas:
                    self.regions.append(
                        dict(index=index, support=support, deltas=deltas, ranges=ranges)
                    )

    def continuous(self, location):
        z = {
            tag: piecewiseLinearMap(
                normalizeValue(location.get(tag, triple[1]), triple),
                self.forward.segments.get(tag, {}),
            )
            for tag, triple in self.forward.triples.items()
        }
        return {
            tag: z[tag]
            + sum(delta * supportScalar(z, support) / 16384 for delta, support in terms)
            for tag, terms in self.rows.items()
        }

    def bounds(self):
        """Conservative marginal bounds; these do not describe joint reachability."""
        result = {}
        for tag, (lo, hi) in self.zranges.items():
            if self.forward.version == 2:
                lo, hi = otRound(lo * 16384), otRound(hi * 16384)
                delta_lo = delta_hi = 0.0
                for delta, support in self.rows[tag]:
                    if any(
                        t in self.fixed and not _tent(self.zranges[t][0], triple)
                        for t, triple in support.items()
                    ):
                        continue
                    # Each scalar is in [0, 1]. Constant regions are exactly 1.
                    a, b = (
                        (delta, delta)
                        if not support
                        else (min(0, delta), max(0, delta))
                    )
                    delta_lo = math.nextafter(delta_lo + a, -math.inf)
                    delta_hi = math.nextafter(delta_hi + b, math.inf)
                lo = (lo + otRound(delta_lo)) / 16384
                hi = (hi + otRound(delta_hi)) / 16384
                if self.forward._instancer is not None:
                    lo, hi = min(1, max(-1, lo)), min(1, max(-1, hi))
            result[tag] = [lo, hi]
        return result

    def user(self, tag, value):
        return _denormalize(value, self.forward.triples[tag])


def analyze(font):
    """Return JSON-compatible structural features in the public input space.

    Hidden and collapsed input axes stay at default. Hidden *outputs* are
    retained. A boundary fixes one input coordinate, with the other coordinates
    restricted to the listed unions of closed intervals. Those intervals are
    support closures; a tent may be zero at an endpoint. Features are structural
    candidates, not a claim that every boundary survives cancellation or clipping.
    Interaction regions identify products of at least two varying input factors.
    """
    space = _AxisSpace(font)
    boundaries = []
    for tag in space.free:
        mapping = space.forward.segments.get(tag, {})
        lo, hi = space.domains[tag]
        keys = sorted({lo, hi, *[k for k in mapping if lo < k < hi]})
        for a, k, b in zip(keys, keys[1:], keys[2:]):
            va, vk, vb = (piecewiseLinearMap(v, mapping) for v in (a, k, b))
            if (vk - va) / (k - a) != (vb - vk) / (b - k):
                boundaries.append(
                    dict(kind="segment", axis=tag, value=space.user(tag, k))
                )
    regions = []
    for region in space.regions:
        ranges = {
            tag: [[space.user(tag, a), space.user(tag, b)] for a, b in intervals]
            for tag, intervals in region["ranges"].items()
        }
        varying = [
            tag for tag in ranges if space.zranges[tag][0] != space.zranges[tag][1]
        ]
        regions.append(
            dict(
                index=region["index"],
                ranges=ranges,
                outputs=region["deltas"],
                interaction=len(varying) > 1,
            )
        )
        for tag in varying:
            mapping = space.forward.segments.get(tag, {})
            for edge, roles in itertools.groupby(
                sorted(zip(region["support"][tag], ("start", "peak", "end"))),
                key=lambda item: item[0],
            ):
                roles = [role for _, role in roles]
                for value in sorted(_preimages(edge, mapping, *space.domains[tag])):
                    boundaries.append(
                        dict(
                            kind="region",
                            region=region["index"],
                            axis=tag,
                            value=space.user(tag, value),
                            roles=roles,
                            ranges={t: r for t, r in ranges.items() if t != tag},
                            outputs=list(region["deltas"]),
                        )
                    )
    return dict(
        axes={
            tag: dict(
                minimum=space.forward.triples[tag][0],
                default=space.forward.triples[tag][1],
                maximum=space.forward.triples[tag][2],
                knots=[space.user(tag, v) for v in sorted(space.knots[tag])],
            )
            for tag in space.free
        },
        fixed=space.fixed,
        defaultOutput=space.forward.map({}, outputNormalized=True),
        outputBounds=space.bounds(),
        boundaries=boundaries,
        regions=regions,
    )


def contours(font, axes, output, level=0, *, location=None, samples=33):
    """Extract an unrounded output level set on a one- or two-axis slice.

    Input geometry uses user units; ``level`` uses normalized output units.
    Other inputs stay at ``location`` or their defaults; hidden inputs must
    stay at default. One-dimensional roots use SciPy; two-dimensional curves
    use ContourPy. Knots are inserted in the sampling grid. Curves approximate
    the continuous map before avar2 rounding and clipping; levels +/-1 describe
    saturation boundaries. Constant intervals/cells are returned separately.
    Slices with jumps are rejected rather than interpolated across.
    """
    space = _AxisSpace(font)
    axes = tuple(axes)
    if len(axes) not in (1, 2) or len(set(axes)) != len(axes):
        raise ValueError("Choose one or two distinct input axes")
    if any(tag not in space.free for tag in axes):
        raise ValueError("Slice axes must be non-hidden, non-collapsed input axes")
    if output not in space.forward.tags:
        raise ValueError(f"Unknown output axis: {output}")
    if not math.isfinite(level):
        raise ValueError("level must be finite")
    if not isinstance(samples, int) or samples < 2:
        raise ValueError("samples must be an integer >= 2")
    location = dict(location or {})
    for tag, value in location.items():
        if tag not in space.forward.triples:
            raise ValueError(f"Unknown axis: {tag}")
        lo, default, hi = space.forward.triples[tag]
        if not math.isfinite(value) or not lo <= value <= hi:
            raise ValueError(f"Coordinate for {tag} must be in [{lo}, {hi}]")
        if tag in axes:
            raise ValueError(f"Cannot fix slice axis {tag}")
        if tag in space.fixed and value != default:
            raise ValueError(f"Hidden or collapsed input {tag} must stay at default")
    # A contouring grid assumes continuity. The structural report still
    # describes zero-width supports, whose contours need one-sided tracing.
    from .reverse import _jumpPreimages

    for region in space.regions:
        if output not in region["deltas"]:
            continue
        fixed_z = {
            tag: piecewiseLinearMap(
                normalizeValue(location.get(tag, triple[1]), triple),
                space.forward.segments.get(tag, {}),
            )
            for tag, triple in space.forward.triples.items()
            if tag not in axes
        }
        if not supportScalar(
            fixed_z, {tag: t for tag, t in region["support"].items() if tag not in axes}
        ):
            continue
        for tag in axes:
            if tag not in region["support"]:
                continue
            start, peak, end = region["support"][tag]
            roots = (
                _jumpPreimages(
                    peak,
                    start == peak,
                    peak == end,
                    sorted(space.forward.segments.get(tag, {}).items()),
                    *space.domains[tag],
                )
                if start == peak or peak == end
                else []
            )
            if roots:
                raise ValueError("Slice contains a jump; inspect analyze() boundaries")

    if samples ** len(axes) > 65536:
        raise ValueError("Slice grid exceeds 65536 points; reduce samples")
    grids = []
    for tag in axes:
        lo, hi = space.domains[tag]
        grid = sorted(
            space.knots[tag]
            | {lo + (hi - lo) * i / (samples - 1) for i in range(samples)}
        )
        grids.append([space.user(tag, v) for v in grid])
    if math.prod(map(len, grids)) > 65536:
        raise ValueError("Slice grid exceeds 65536 points after adding avar knots")

    def evaluate(*values):
        return space.continuous({**location, **dict(zip(axes, values))})[output] - level

    result = dict(
        axes=list(axes),
        output=output,
        level=level,
        fixed={
            tag: location.get(tag, triple[1])
            for tag, triple in space.forward.triples.items()
            if tag not in axes
        },
        points=[],
        lines=[],
        boxes=[],
        approximate=len(axes) == 2,
    )
    if len(axes) == 1:
        from scipy.optimize import brentq

        grid = grids[0]
        values = [evaluate(x) for x in grid]
        intervals, points = [], set()
        for a, b, va, vb in zip(grid, grid[1:], values, values[1:]):
            if va == vb == 0:
                intervals.append((a, b))
            elif va * vb < 0:
                points.add(brentq(evaluate, a, b))
        points.update(x for x, value in zip(grid, values) if value == 0)
        intervals = _merge_intervals(intervals)
        result["points"] = [
            [p] for p in sorted(points) if not any(a <= p <= b for a, b in intervals)
        ]
        result["lines"] = [[[a], [b]] for a, b in intervals]
    else:
        try:
            import contourpy
        except ImportError as e:
            raise ImportError(
                "Two-axis contours require contourpy; install fonttools[avar]"
            ) from e
        import numpy as np

        x, y = grids
        z = np.array([[evaluate(a, b) for a in x] for b in y])
        generator = contourpy.contour_generator(x=x, y=y, z=z, line_type="Separate")
        result["lines"] = [line.tolist() for line in generator.lines(0)]
        result["boxes"] = [
            [x[i], y[j], x[i + 1], y[j + 1]]
            for j in range(len(y) - 1)
            for i in range(len(x) - 1)
            if np.all(z[j : j + 2, i : i + 2] == 0)
        ]
        # ContourPy traces separating curves. A level attained only at a
        # vertex or along a grid edge need not separate signs, so retain
        # these lower-dimensional level sets explicitly as well.
        covered_points, covered_edges = set(), set()
        for line in result["lines"]:
            covered_points.update(map(tuple, line))
            covered_edges.update(
                tuple(sorted((tuple(a), tuple(b)))) for a, b in zip(line, line[1:])
            )
        flat = set()
        for j in range(len(y) - 1):
            for i in range(len(x) - 1):
                if np.all(z[j : j + 2, i : i + 2] == 0):
                    flat.update((a, b) for a in (i, i + 1) for b in (j, j + 1))
        for j, b in enumerate(y):
            for i, a in enumerate(x):
                if z[j, i] != 0:
                    continue
                for ni, nj in ((i + 1, j), (i, j + 1)):
                    if ni >= len(x) or nj >= len(y) or z[nj, ni] != 0:
                        continue
                    edge = tuple(sorted(((a, b), (x[ni], y[nj]))))
                    if edge in covered_edges or ((i, j) in flat and (ni, nj) in flat):
                        continue
                    result["lines"].append([list(p) for p in edge])
                    covered_points.update(edge)
        result["points"] = [
            [a, b]
            for j, b in enumerate(y)
            for i, a in enumerate(x)
            if z[j, i] == 0 and (a, b) not in covered_points and (i, j) not in flat
        ]
    return result


def main(args=None):
    """Inspect avar structure or extract an output contour as JSON."""
    import argparse

    parser = argparse.ArgumentParser(
        "fonttools varLib.avar.analyze", description=main.__doc__
    )
    parser.add_argument("font")
    parser.add_argument("--axes", help="One or two slice axes, comma-separated")
    parser.add_argument(
        "--contour", metavar="AXIS=value", help="Normalized output level"
    )
    parser.add_argument("--samples", type=int, default=33)
    parser.add_argument(
        "--at",
        action="append",
        default=[],
        metavar="AXIS=value",
        help="Fix another input in user units",
    )
    options = parser.parse_args(args)
    from .map import _parse_coordinates

    font = _load_font(parser, options.font)
    try:
        if options.contour:
            if not options.axes:
                parser.error("--contour requires --axes")
            target = _parse_coordinates(parser, [options.contour])
            output, level = next(iter(target.items()))
            result = contours(
                font,
                options.axes.split(","),
                output,
                level,
                location=_parse_coordinates(parser, options.at),
                samples=options.samples,
            )
        else:
            if options.axes or options.at:
                parser.error("--axes and --at require --contour")
            result = analyze(font)
    except (ValueError, ImportError) as e:
        parser.error(str(e))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
