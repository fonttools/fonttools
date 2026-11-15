"""Find pre-fvar coordinates that approximate a post-avar location.

The numerical solver uses an unrounded forward map and its local Jacobian.
Candidates are ranked using the actual forward map, including avar2 rounding
and clipping. SciPy is optional and is imported when a solver is constructed.
"""

from bisect import bisect_left, bisect_right
from collections import OrderedDict
import math

from fontTools.misc.fixedTools import floatToFixedToStr, nearestMultipleShortestRepr
from fontTools.varLib.models import normalizeValue, piecewiseLinearMap
from fontTools.varLib.varStore import NO_VARIATION_INDEX
from .map import ForwardMapper, _denormalize, _load_font, _parse_coordinates


def _segment(value, items):
    """Piecewise-linear segment value and a one-sided derivative."""
    if not items:
        return value, 1.0
    keys = [k for k, _ in items]
    i = bisect_right(keys, value)
    if value < keys[0] or value > keys[-1] or len(items) == 1:
        k, v = items[0 if value < keys[0] else -1]
        return value + v - k, 1.0
    i = min(max(i, 1), len(items) - 1)
    a, va = items[i - 1]
    b, vb = items[i]
    slope = (vb - va) / (b - a)
    return va + (value - a) * slope, slope


def _tent(value, start, peak, end):
    """Tent value and right derivative (inward at a one-sided peak)."""
    if value < start or value > end:
        return 0.0, 0.0
    if value == peak:
        if peak < end:
            return 1.0, -1 / (end - peak)
        return 1.0, 1 / (peak - start) if start < peak else 0.0
    if value == end and end < 1:
        return 0.0, 0.0
    if value < peak:
        slope = 1 / (peak - start)
        return (value - start) * slope, slope
    slope = -1 / (end - peak)
    return (value - end) * slope, slope


def _segmentPreimages(value, items, lo, hi):
    """Find all isolated preimages and representatives of flat intervals."""
    mapping = dict(items)
    points = sorted({lo, hi, *[k for k in mapping if lo <= k <= hi]})
    preimages = []
    for a, b in zip(points, points[1:]):
        va, vb = piecewiseLinearMap(a, mapping), piecewiseLinearMap(b, mapping)
        if min(va, vb) <= value <= max(va, vb):
            preimages.append(
                min(max(0, a), b)
                if va == vb
                else a + (value - va) * (b - a) / (vb - va)
            )
            if va == vb:
                # A whole interval maps to this value. Its ends are needed
                # when a jump occurs on entering or leaving the plateau.
                preimages.extend((a, b))
    return sorted(set(preimages))


def _inverseSegment(value, items, lo, hi):
    """Choose a segment preimage nearest default, including flat intervals."""
    preimages = _segmentPreimages(value, items, lo, hi)
    if preimages:
        return min(preimages, key=abs)
    mapping = dict(items)
    points = sorted({lo, hi, *[k for k in mapping if lo <= k <= hi]})
    return min(points, key=lambda v: abs(piecewiseLinearMap(v, mapping) - value))


def _jumpPreimages(peak, at_start, at_end, items, lo, hi):
    # A collapsed tent edge jumps from zero to one at its peak. Pull that
    # plane back through every avar1 branch, including plateau endpoints.
    roots = _segmentPreimages(peak, items, lo, hi)
    segments = dict(items)
    points = sorted({lo, hi, *[k for k, _ in items if lo <= k <= hi], *roots})
    jumps = []
    for root in roots:
        index = bisect_left(points, root)
        neighbors = []
        if index:
            neighbors.append((points[index - 1] + root) / 2)
        if index + 1 < len(points):
            neighbors.append((root + points[index + 1]) / 2)
        values = (piecewiseLinearMap(v, segments) for v in neighbors)
        if any(
            (at_start and value < peak) or (at_end and value > peak) for value in values
        ):
            jumps.append(root)
    return jumps


class _AvarMapping:
    """Unrounded, piecewise-smooth forward mapping and analytic Jacobian."""

    def __init__(self, font):
        import numpy as np

        self.np = np
        self.axes = font["fvar"].axes
        self.tags = [a.axisTag for a in self.axes]
        avar = font.get("avar")
        version = getattr(avar, "majorVersion", 1)
        if version not in (1, 2):
            raise NotImplementedError("Unknown avar table version")
        self.segments = [
            sorted(avar.segments.get(tag, {}).items()) if avar else []
            for tag in self.tags
        ]
        store = avar.table.VarStore if avar and version == 2 else None
        self.supports = []
        self.deltas = np.zeros((len(self.axes), 0))
        if store is not None:
            indexMap = avar.table.VarIdxMap
            # Assemble D[output axis, region] in normalized-coordinate units.
            # Resolving VarIdxMap here also handles axes that share delta rows.
            # Missing/out-of-range rows contribute zero, as in VarStoreInstancer.
            deltas = np.zeros((len(self.axes), len(store.VarRegionList.Region)))
            for i in range(len(self.axes)):
                index = indexMap[i] if indexMap is not None else i
                outer, inner = index >> 16, index & 0xFFFF
                if index == NO_VARIATION_INDEX or outer >= len(store.VarData):
                    continue
                data = store.VarData[outer]
                if inner >= len(data.Item):
                    continue
                for region, delta in zip(data.VarRegionIndex, data.Item[inner]):
                    deltas[i, region] += delta / 16384
            # Ignore unused regions and axes ignored by OpenType supportScalar.
            used = np.any(deltas, axis=0)
            for r in np.flatnonzero(used):
                self.supports.append(
                    [
                        (i, a.StartCoord, a.PeakCoord, a.EndCoord)
                        for i, a in enumerate(
                            store.VarRegionList.Region[r].VarRegionAxis
                        )
                        if a.PeakCoord != 0
                        and a.StartCoord <= a.PeakCoord <= a.EndCoord
                        and not (a.StartCoord < 0 < a.EndCoord)
                    ]
                )
            self.deltas = deltas[:, used]

    def __call__(self, x):
        np = self.np
        # x is normalized BEFORE avar1; z = A(x) is the intermediate location.
        # Before clipping/rounding, the full map is H(x) = z + D * s(z), where
        # s contains the products of per-axis tents for each region. Within a
        # region cell this is multilinear, not generally one affine transform.
        values, slopes = zip(*(_segment(v, s) for v, s in zip(x, self.segments)))
        z = np.array(values)
        jac = np.eye(len(x))
        for deltas, support in zip(self.deltas.T, self.supports):
            factors = [_tent(z[i], a, p, b) for i, a, p, b in support]
            scalar = math.prod(v for v, _ in factors)
            gradient = np.zeros(len(x))
            for j, (i, _, _, _) in enumerate(support):
                # Do not divide by a factor: zero factors can have nonzero
                # derivatives at a region boundary.
                gradient[i] = factors[j][1] * math.prod(
                    v for k, (v, _) in enumerate(factors) if k != j
                )
            jac += np.outer(deltas, gradient)
            # All regions see the same intermediate coordinates.
            values = np.asarray(values) + deltas * scalar
        # Chain rule: J_H = (I + D * J_s) * diag(A'). Multiplying columns by
        # the avar1 slopes differentiates with respect to our input x, not z.
        return np.asarray(values), jac * slopes


def reverse(
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
    """Approximately invert an avar (version 1 or 2) mapping.

    Returns ``(location, error)``, where ``error`` is the residual output error
    in normalized coordinates (Euclidean distance over the scored axes). It is
    about one F2Dot14 unit or less when the search reaches the target, and
    larger when the target is unreachable. Returns None for a font without
    fvar.

    ``location`` specifies post-avar targets. An omitted axis targets
    normalized zero while its input is free; when its input is pinned or hidden
    it is left unconstrained, since the caller cannot move it. Input and output
    units follow avar.map: by default both are in pre-fvar units, with
    ``inputNormalized`` and ``outputNormalized`` selecting normalized target and
    result coordinates, respectively.

    Hidden axes are held at their fvar defaults. ``pinned`` optionally maps
    other axis tags to fixed PRE-FVAR values, regardless of the unit flags.
    A pinned value of None means the axis's fvar default.
    ``vary`` optionally restricts the inputs that may move to a set of axis
    tags, pinning every other axis to its default and overriding hidden flags;
    by default all non-hidden axes may vary.
    Returned coordinates stay within the fvar ranges.

    Output error is Euclidean distance in normalized coordinates. Among
    candidates within ``tolerance`` of the smallest error found, prefer fewer
    non-default input axes, then smaller error and normalized distance from
    default. ``tolerance`` is only this sparsity budget, not an accuracy
    threshold. Sparsity is sought by greedy elimination, not exhaustive subset
    search. Multiple starts reduce local-minimum sensitivity but do not
    guarantee a global optimum. Requires SciPy. For repeated targets with the
    same font and input constraints, use ReverseMapper.
    """
    if "fvar" not in font:
        return None
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and non-negative")
    return ReverseMapper(font, pinned=pinned, vary=vary, cache_size=0).reverse(
        location,
        inputNormalized=inputNormalized,
        outputNormalized=outputNormalized,
        dropZeroes=dropZeroes,
        tolerance=tolerance,
    )


class ReverseMapper:
    """Prepare an avar inverse solver for multiple targets.

    Pin and vary constraints are fixed at construction. reverse() takes the
    target, unit flags, output filtering, and sparsity tolerance, returning the
    same (location, error) pair as the module-level reverse() function.

    The unrounded mapping/Jacobian, exact forward evaluator, axis bounds,
    and target-independent starting points are reused. Up to cache_size target
    solutions are memoized per instance; zero disables this cache. Output
    dictionaries are fresh, so callers may modify them safely.

    The font must contain fvar. Do not change its fvar or avar tables while
    using a mapper; build a new mapper after such changes.
    """

    def __init__(self, font, *, pinned=None, vary=None, cache_size=128):
        if "fvar" not in font:
            raise ValueError("Font does not contain an 'fvar' table")
        if not isinstance(cache_size, int) or cache_size < 0:
            raise ValueError("cache_size must be a non-negative integer")
        self._axes = tuple(font["fvar"].axes)
        self._triples = {
            a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in self._axes
        }
        pinned = dict(pinned or {})
        vary_tags = None if vary is None else set(vary)
        unknown = sorted((pinned.keys() | (vary_tags or set())) - self._triples.keys())
        if unknown:
            raise ValueError(f"Unknown axis tag(s): {', '.join(unknown)}")
        if vary_tags is not None:
            conflict = sorted(vary_tags & pinned.keys())
            if conflict:
                raise ValueError(
                    f"Axis(es) cannot be both varied and pinned: {', '.join(conflict)}"
                )
        pinned = {
            tag: self._triples[tag][1] if value is None else value
            for tag, value in pinned.items()
        }
        for axis in self._axes:
            tag = axis.axisTag
            # An explicit vary list overrides hidden flags and fixes every
            # unlisted input; otherwise hidden inputs stay at their defaults.
            if vary_tags is None:
                if axis.flags & 1:
                    if tag in pinned and pinned[tag] != axis.defaultValue:
                        raise ValueError(f"Hidden axis {tag} must stay at its default")
                    pinned[tag] = axis.defaultValue
            elif tag not in vary_tags and tag not in pinned:
                pinned[tag] = axis.defaultValue
        for tag, value in pinned.items():
            lo, _, hi = self._triples[tag]
            if not math.isfinite(value) or not lo <= value <= hi:
                raise ValueError(f"Pinned coordinate for {tag} must be in [{lo}, {hi}]")
        self._pinned = pinned
        self._cache_size = cache_size
        self._cache = OrderedDict()
        if not self._axes:
            return
        try:
            import numpy as np
            from scipy.optimize import least_squares
        except ImportError as e:
            raise ImportError(
                "Reverse avar mapping requires scipy; install fonttools[avar]"
            ) from e
        self._np = np
        self._least_squares = least_squares
        self._mapping = _AvarMapping(font)
        self._forward = ForwardMapper(font)
        # Normalize inputs so weight, optical size, etc. have comparable
        # scales. An endpoint default makes the domain one-sided. Hidden,
        # pinned, and collapsed inputs are excluded from optimization.
        self._lower = np.array(
            [-1.0 if a.minValue < a.defaultValue else 0.0 for a in self._axes]
        )
        self._upper = np.array(
            [1.0 if a.defaultValue < a.maxValue else 0.0 for a in self._axes]
        )
        self._fixed = np.array(
            [
                normalizeValue(
                    pinned.get(a.axisTag, a.defaultValue), self._triples[a.axisTag]
                )
                for a in self._axes
            ]
        )
        self._free = [
            i
            for i, a in enumerate(self._axes)
            if a.axisTag not in pinned and self._lower[i] < self._upper[i]
        ]
        self._free_set = set(self._free)
        # Cache each region-peak seed and its unrounded forward value. Only
        # ranking these seeds against the new target must happen per call.
        self._peak_seeds = []
        self._jumps = {}
        self._jump_contexts = []
        jump_preimages = {}
        for support in self._mapping.supports:
            x = self._fixed.copy()
            for i, _, peak, _ in support:
                if i in self._free_set:
                    x[i] = _inverseSegment(
                        peak, self._mapping.segments[i], self._lower[i], self._upper[i]
                    )
            self._peak_seeds.append((x, np.clip(self._mapping(x)[0], -1, 1)))
            boundaries = {}
            for i, start, peak, end in support:
                if i not in self._free_set or (start != peak and peak != end):
                    continue
                key = (i, peak, start == peak, end == peak)
                if key not in jump_preimages:
                    jump_preimages[key] = _jumpPreimages(
                        peak,
                        start == peak,
                        end == peak,
                        self._mapping.segments[i],
                        self._lower[i],
                        self._upper[i],
                    )
                roots = jump_preimages[key]
                if roots:
                    boundaries[i] = roots
                    self._jumps.setdefault(i, set()).update(roots)
            if boundaries:
                # Keep a region-peak context so product tents are active even
                # when the current best solution has zero gradient elsewhere.
                # Hold all its jump coordinates together to test intersections
                # that would disappear if any one coordinate moved off-plane.
                context = x.copy()
                for i, roots in boundaries.items():
                    context[i] = min(roots, key=lambda value: abs(value - x[i]))
                locked = tuple(boundaries)
                self._jump_contexts.append((context, locked))
                # Cover alternate avar1 preimages without forming an
                # exponential Cartesian product across every affected axis.
                for i, roots in boundaries.items():
                    for value in roots:
                        alternate = context.copy()
                        alternate[i] = value
                        self._jump_contexts.append((alternate, locked))
        self._jumps = {i: sorted(values) for i, values in self._jumps.items()}
        self._jump_contexts = [
            (np.array(coordinates), locked)
            for coordinates, locked in dict.fromkeys(
                (tuple(seed), locked) for seed, locked in self._jump_contexts
            )
        ]
        rng = np.random.default_rng(0)
        self._random_seeds = tuple(
            rng.uniform(self._lower, self._upper) for _ in range(4)
        )

    def clear_cache(self):
        """Discard memoized targets; retain the prepared font and constraints."""
        self._cache.clear()

    def reverse(
        self,
        location,
        *,
        inputNormalized=False,
        outputNormalized=False,
        dropZeroes=False,
        tolerance=1 / 16384,
    ):
        """Solve one target using the same options as module-level reverse()."""
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("tolerance must be finite and non-negative")
        unknown = sorted(location.keys() - self._triples.keys())
        if unknown:
            raise ValueError(f"Unknown axis tag(s): {', '.join(unknown)}")
        for tag, value in location.items():
            if not math.isfinite(value) or (inputNormalized and not -1 <= value <= 1):
                raise ValueError(f"Invalid target coordinate for {tag}: {value}")
        if not self._axes:
            return {}, 0.0
        np = self._np
        target = np.array(
            [
                (
                    location.get(a.axisTag, 0)
                    if inputNormalized
                    else normalizeValue(
                        location.get(a.axisTag, a.defaultValue),
                        self._triples[a.axisTag],
                    )
                )
                for a in self._axes
            ]
        )
        # Equal numeric targets can constrain different outputs: an omitted
        # hidden/pinned axis is unconstrained, while an explicit zero is not.
        scored = np.array(
            [
                a.axisTag in location or i in self._free_set
                for i, a in enumerate(self._axes)
            ]
        )
        key = (tuple(target), tuple(scored), tolerance)
        if self._cache_size and key in self._cache:
            coordinates, error = self._cache[key]
            self._cache.move_to_end(key)
        else:
            coordinates, error = self._solve(target, scored, tolerance)
            if self._cache_size:
                self._cache[key] = (coordinates, error)
                if len(self._cache) > self._cache_size:
                    self._cache.popitem(last=False)
        result = {}
        for axis, value in zip(self._axes, coordinates):
            if dropZeroes and value == 0:
                continue
            tag = axis.axisTag
            result[tag] = (
                value
                if outputNormalized
                else self._pinned.get(
                    tag, float(_denormalize(value, self._triples[tag]))
                )
            )
        return result, error

    def _solve(self, target, scored, tolerance):
        np = self._np
        least_squares = self._least_squares
        axes = self._axes
        triples = self._triples
        pinned = self._pinned
        mapping = self._mapping
        lower, upper, fixed, free = self._lower, self._upper, self._fixed, self._free
        candidates = {}

        def add(x):
            x = x.copy()
            x[free] = np.where(abs(x[free]) < 1e-10, 0, x[free])
            key = tuple(x)
            if key not in candidates:
                # Score through the public forward path, including the round trip
                # through pre-fvar coordinates that the caller will actually use.
                user = {
                    a.axisTag: _denormalize(v, triples[a.axisTag])
                    for a, v in zip(axes, x)
                }
                user.update(pinned)
                actual = self._forward.map(
                    user, outputNormalized=True, dropZeroes=False
                )
                deviation = np.array([actual[tag] for tag in mapping.tags]) - target
                error = np.linalg.norm(deviation[scored])
                candidates[key] = (error, x)

        def best():
            # Output accuracy comes first, up to the requested tolerance. Use the
            # smallest residual seen across ALL candidates as the error budget's
            # anchor, so successive axis removals cannot accumulate tolerance loss.
            # Within that budget prefer fewer non-default inputs, then accuracy,
            # then proximity to default. This is a preference, not an L0 penalty
            # added to the residual, which could trade away an otherwise good fit.
            error = min(e for e, _ in candidates.values())
            return min(
                (c for c in candidates.values() if c[0] <= error + tolerance),
                key=lambda c: (np.count_nonzero(c[1]), c[0], np.dot(c[1], c[1])),
            )

        def solve(seed, varying, bounds=None):
            x = seed.copy()
            box_lower, box_upper = (lower, upper) if bounds is None else bounds
            if bounds is not None:
                x[varying] = np.clip(x[varying], box_lower[varying], box_upper[varying])
            add(x)
            if not varying:
                return
            # First seek an exact inverse without the flat plateaus introduced by
            # clipping. At +/-1 the target is an inequality on the unclipped map.
            # Then minimize the true clipped output error, also for unreachable
            # targets (the two objectives need not have the same nearest point).
            for clipped in (False, True):
                cached = None

                def evaluate(v):
                    nonlocal cached
                    if cached is not None and np.array_equal(v, cached[0]):
                        return cached[1:]
                    x[varying] = v
                    raw, jac = mapping(x)
                    if clipped:
                        residual = np.clip(raw, -1, 1) - target
                        active = (raw >= -1) & (raw <= 1) & scored
                        residual = np.where(scored, residual, 0)
                    else:
                        residual = raw - target
                        active = scored & ~(
                            ((target == 1) & (raw > 1)) | ((target == -1) & (raw < -1))
                        )
                        residual = np.where(active, residual, 0)
                    jac = jac[:, varying] * active[:, None]
                    cached = (v.copy(), residual, jac)
                    return residual, jac

                # Trust-region least squares repeatedly solves a bounded local
                # linear problem using this Jacobian, then checks the nonlinear
                # residual before accepting a step. Rank deficiency is expected:
                # multiple inputs can produce the same output, especially after
                # saturation. Avoid explicitly inverting J or forming J.T @ J.
                result = least_squares(
                    lambda v: evaluate(v)[0],
                    x[varying],
                    jac=lambda v: evaluate(v)[1],
                    bounds=(box_lower[varying], box_upper[varying]),
                    ftol=1e-11,
                    xtol=1e-11,
                    gtol=1e-11,
                    max_nfev=200,
                )
                x[varying] = result.x
                add(x)

        # The default promotes sparse solutions; inverting avar1 alone gives a
        # better guess when its segment maps depart substantially from identity.
        # Keep the target-as-input guess too, since avar2 can undo that remapping.
        seeds = [
            fixed.copy(),
            np.array(
                [
                    _inverseSegment(t, s, lo, hi)
                    for t, s, lo, hi in zip(target, mapping.segments, lower, upper)
                ]
            ),
            np.clip(target, lower, upper),
        ]
        # Rank the prepared seeds for this target, preserving their original
        # order on ties. Each solve works on copies of the stored coordinates.
        peaks = sorted(
            self._peak_seeds,
            key=lambda item: np.linalg.norm((item[1] - target)[scored]),
        )
        seeds.extend(x for x, _ in peaks[:8])
        seeds.extend(self._random_seeds)
        seen = set()
        for seed in seeds:
            seed = np.asarray(seed).copy()
            for i in range(len(axes)):
                if i not in free:
                    seed[i] = fixed[i]
            if tuple(seed) in seen:
                continue
            seen.add(tuple(seed))
            solve(seed, free)

        if self._jumps:
            # A gradient cannot guide a solve onto a zero-width support.
            # Fit its exact boundary with the jump axes held fixed, including
            # intersections of several jump planes in the same product tent.
            for seed, locked in self._jump_contexts:
                solve(seed, [i for i in free if i not in locked])

            def adjacent(value, i, direction):
                # Work in user units so denormalizing and normalizing again
                # cannot round an ostensibly open endpoint back onto the jump.
                user = _denormalize(value, triples[axes[i].axisTag])
                while True:
                    user = math.nextafter(user, math.inf * direction)
                    normalized = normalizeValue(user, triples[axes[i].axisTag])
                    if (normalized - value) * direction > 0:
                        return normalized

            for i, boundaries in self._jumps.items():
                for index, boundary in enumerate(boundaries):
                    # Project the current best fit onto each plane as well:
                    # other axes may need values far from the region peak.
                    seed = best()[1].copy()
                    seed[i] = boundary
                    solve(seed, [j for j in free if j != i])
                    contexts = [
                        x
                        for x, locked in self._jump_contexts
                        if i in locked and x[i] == boundary
                    ]
                    anchors = [best()[1]]
                    if contexts:
                        anchors.append(
                            min(
                                contexts,
                                key=lambda x: np.linalg.norm(
                                    (np.clip(mapping(x)[0], -1, 1) - target)[scored]
                                ),
                            )
                        )
                    # Search the two adjacent intervals independently. Bounds
                    # prevent trust-region steps from crossing this axis's
                    # jumps and invalidating the local linear approximation.
                    # Other axes remain free: this is not an exhaustive product
                    # of all cells across all axes.
                    intervals = []
                    if lower[i] < boundary:
                        left = boundaries[index - 1] if index else lower[i]
                        intervals.append(
                            (
                                adjacent(left, i, 1) if index else left,
                                adjacent(boundary, i, -1),
                            )
                        )
                    if boundary < upper[i]:
                        right = (
                            boundaries[index + 1]
                            if index + 1 < len(boundaries)
                            else upper[i]
                        )
                        intervals.append(
                            (
                                adjacent(boundary, i, 1),
                                (
                                    adjacent(right, i, -1)
                                    if index + 1 < len(boundaries)
                                    else right
                                ),
                            )
                        )
                    for lo, hi in intervals:
                        if lo > hi:
                            continue  # No representable input between these jumps.
                        box_lower, box_upper = lower.copy(), upper.copy()
                        box_lower[i], box_upper[i] = lo, hi
                        varying = free if lo < hi else [j for j in free if j != i]
                        for anchor in anchors:
                            seed = anchor.copy()
                            seed[i] = (
                                max(lo, hi - min((hi - lo) / 2, 1 / 16384))
                                if hi < boundary
                                else min(hi, lo + min((hi - lo) / 2, 1 / 16384))
                            )
                            solve(seed, varying, (box_lower, box_upper))

        # Try dropping each non-default axis, refitting the others. Accept only
        # candidates within the output-error budget, then repeat after a removal.
        # Refitting matters: simply zeroing a coordinate misses solutions where
        # another axis can take over its contribution. Backward elimination is
        # greedy; finding the sparsest possible subset would be combinatorial.
        while True:
            _, x = best()
            active = [i for i in free if x[i] != 0]
            for i in active:
                seed = x.copy()
                seed[i] = 0
                solve(seed, [j for j in active if j != i])
            if np.count_nonzero(best()[1]) >= np.count_nonzero(x):
                break

        # Refine against the rounded forward map on a small coordinate stencil.
        # One tick in intermediate space is divided by the local avar1 slope, so
        # the intermediate coordinate moves about one F2Dot14 unit even where the
        # segment compresses (slope < 1). Differentiating the rounded avar2 mapper
        # mostly gives zero derivatives because of quantization. Instead, use its
        # exact residual only to rank nearby candidates once the continuous solver
        # has located a good basin.
        for _ in range(3):
            error, x = best()
            if error == 0:
                break
            for i in free:
                _, slope = _segment(x[i], mapping.segments[i])
                if not slope:
                    continue  # A flat segment cannot move the intermediate value.
                step = 1 / (16384 * abs(slope))
                for offset in (-1, -0.5, 0.5, 1):
                    trial = x.copy()
                    trial[i] = np.clip(x[i] + offset * step, lower[i], upper[i])
                    add(trial)
            if np.array_equal(best()[1], x):
                break

        error, x = best()
        return tuple(float(value) for value in x), float(error)


def _split_items(items):
    """Flatten comma-separated and/or repeated CLI items into a list.

    Empty fields (e.g. from a trailing comma) are dropped.
    """
    return [
        field.strip() for item in items for field in item.split(",") if field.strip()
    ]


def _parse_vary(parser, items):
    """Parse --vary items (comma-separated and/or repeated) into axis tags."""
    tags = _split_items(items)
    for tag in tags:
        if "=" in tag:
            parser.error(
                f"Invalid --vary axis {tag!r}. Expected an axis tag, e.g. wght"
            )
    return tags


def _make_parser(prog, description, *, coords_help, input_help):
    """Build the shared options for reverse and roundtrip commands."""
    import argparse

    parser = argparse.ArgumentParser(prog, description=description)
    parser.add_argument("font", metavar="varfont.ttf", help="Variable-font file.")
    parser.add_argument(
        "coords",
        metavar="[AXIS=value...]",
        help=coords_help,
        nargs="*",
        default=[],
    )
    parser.add_argument(
        "-f", action="store_true", help="Do not omit axes at default location."
    )
    parser.add_argument("-i", action="store_true", help=input_help)
    parser.add_argument(
        "-o", action="store_true", help="Output coordinates as normalized (-1..1)."
    )
    parser.add_argument(
        "--pin",
        action="append",
        default=[],
        metavar="AXIS[=value]",
        help="Fix an input axis in pre-fvar units; omit the value to pin at its "
        "fvar default. Repeat or comma-separate for more axes.",
    )
    parser.add_argument(
        "--vary",
        action="append",
        default=[],
        metavar="AXIS[,AXIS...]",
        help="Vary only these axes, pinning every other axis to its fvar "
        "default (overrides hidden flags). Repeat or comma-separate. Default: "
        "vary all non-hidden axes.",
    )
    parser.add_argument(
        "--show-error",
        action="store_true",
        help="Print the normalized residual error to stderr.",
    )
    return parser


def _run_cli(parser, args, mapper):
    """Load inputs, run a mapping operation, and print its location and error."""
    import sys

    options = parser.parse_args(args)

    font = _load_font(parser, options.font)
    location = _parse_coordinates(parser, options.coords)
    pinned = (
        _parse_coordinates(parser, _split_items(options.pin), allow_default=True)
        if options.pin
        else None
    )
    vary = _parse_vary(parser, options.vary) if options.vary else None

    try:
        result = mapper(
            font,
            location,
            inputNormalized=options.i,
            outputNormalized=options.o,
            dropZeroes=not options.f,
            pinned=pinned,
            vary=vary,
        )
    except ValueError as e:
        parser.error(str(e))
    except ImportError as e:
        sys.exit(str(e))

    assert result is not None
    mapped, error = result
    if options.show_error:
        print(f"normalized residual error: {error:g}", file=sys.stderr)

    # Both commands print at the font's F2Dot14 resolution for readability;
    # the library APIs retain the solver's full-precision coordinates.
    triples = {
        a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in font["fvar"].axes
    }
    for tag, v in mapped.items():
        if options.o:
            s = floatToFixedToStr(v, 14)
        else:
            lo, default, hi = triples[tag]
            step = (hi - default if v >= default else default - lo) / 16384
            s = nearestMultipleShortestRepr(v, step) if step else str(float(v))
        print(f"{tag}={s}")


def main(args=None):
    """Find pre-fvar inputs that produce post-avar targets (invert `avar`)."""
    parser = _make_parser(
        "fonttools varLib.avar.reverse",
        "Find pre-fvar inputs for post-avar targets (requires scipy).",
        coords_help="Post-avar targets, e.g. 'wght=0.6 wdth=-0.2'. Omit for the "
        "default location. An omitted free axis targets normalized zero.",
        input_help="Target coordinates are normalized (-1..1).",
    )
    return _run_cli(parser, args, reverse)


if __name__ == "__main__":
    import sys

    sys.exit(main())
