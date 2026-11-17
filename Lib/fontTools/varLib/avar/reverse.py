"""Find pre-fvar coordinates that approximate a post-avar location.

The numerical solver uses an unrounded forward map and its local Jacobian.
Candidates are ranked using the actual forward map, including avar2 rounding
and clipping. SciPy is optional and is imported when a solver is constructed.
"""

from bisect import bisect_left
from collections import OrderedDict
from functools import partial
import math

from fontTools.misc.fixedTools import floatToFixedToStr, nearestMultipleShortestRepr
from fontTools.varLib.models import normalizeValue, piecewiseLinearMap
from fontTools.varLib.varStore import NO_VARIATION_INDEX
from . import _mapping
from ._mapping import _segment, _tent
from .map import ForwardMapper, _denormalize, _load_font, _parse_coordinates

# Inputs and outputs are normalized. Solve below the output quantization scale;
# candidate ranking and the final stencil still use the exact rounded map.
_SOLVER_TOLERANCE = 1e-8


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


def _adjacentInput(value, triple, direction):
    # Choose an open endpoint in user units, so the normalization round trip
    # cannot round a supposedly one-sided probe back onto a jump plane.
    user = _denormalize(math.nextafter(value, math.inf * direction), triple)
    while True:
        normalized = normalizeValue(user, triple)
        if (normalized - value) * direction > 0:
            return normalized
        user = math.nextafter(user, math.inf * direction)


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
        self.constant_deltas = np.ones(len(self.axes), dtype=bool)
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
                # Inspect the original row, conservatively: do not infer
                # constancy from cancellations in the assembled matrix.
                self.constant_deltas[i] = not any(data.Item[inner])
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

        # Pack region geometry once. The optional Cython evaluator consumes
        # buffers directly, without Python objects or a NumPy C-API dependency.
        offsets = [0]
        factors = []
        for support in self.supports:
            factors.extend(support)
            offsets.append(len(factors))
        self._packed = (
            np.array(offsets, dtype="l"),
            np.array([f[0] for f in factors], dtype="l"),
            *(np.array([f[j] for f in factors], dtype=float) for j in (1, 2, 3)),
        )

        self._segments = _mapping.packSegments(self.segments)
        self._column_cache = OrderedDict()

    def __call__(self, x, columns=None):
        # H(x) = A(x) + D * s(A(x)); the evaluator applies the chain rule
        # through avar1 and differentiates product tents without dividing by
        # their factors, which can vanish at a region boundary.
        values, slopes = _mapping.mapSegments(
            self.np.asarray(x, dtype=float), *self._segments, self.segments
        )
        # A solve may vary only a handful of inputs. Cache their packed
        # column indices, and omit every other derivative from both backends.
        key = tuple(range(len(x))) if columns is None else tuple(columns)
        packed_columns = self._column_cache.get(key)
        if packed_columns is None:
            positions = {i: j for j, i in enumerate(key)}
            packed_columns = (
                self.np.array(key, dtype="l"),
                self.np.array(
                    [positions.get(i, -1) for i in self._packed[1]], dtype="l"
                ),
            )
            self._column_cache[key] = packed_columns
            if len(self._column_cache) > 64:
                self._column_cache.popitem(last=False)
        self._column_cache.move_to_end(key)
        return _mapping.evaluate(
            self.np.asarray(values, dtype=float),
            self.np.asarray(slopes),
            self.deltas,
            *self._packed,
            self.supports,
            *packed_columns,
        )


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
    partial=False,
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

    With ``partial=True``, only explicitly supplied output axes are scored;
    omitted outputs are unconstrained. This is useful for reachability queries.

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
        partial=partial,
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
        self._batch_score = None
        self._score = partial(
            self._forward.map, outputNormalized=True, dropZeroes=False
        )
        if _mapping.COMPILED:
            from ._scorer import _ForwardScorer

            self._score = _ForwardScorer(self._forward, pinned=pinned)
            self._batch_score = self._score.batch
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
        self._separable = not any(self._mapping.supports)
        self._offset = np.sum(self._mapping.deltas, axis=1)
        self._clipped = (
            self._forward.version == 2 and self._forward._instancer is not None
        )
        self._one_dim_knots = {}
        if not self._separable:
            for i in self._free:
                segments = self._mapping.segments[i]
                lo, hi = self._lower[i], self._upper[i]
                knots = {lo, hi, *[k for k, _ in segments if lo <= k <= hi]}
                edges = {
                    v
                    for support in self._mapping.supports
                    for axis, *values in support
                    if axis == i
                    for v in values
                }
                for edge in edges:
                    knots.update(_segmentPreimages(edge, segments, lo, hi))
                self._one_dim_knots[i] = sorted(knots)

        self._constant_outputs = self._mapping.constant_deltas & np.array(
            [i not in self._free_set for i in range(len(self._axes))]
        )
        default_output = self._forward.map(
            {a.axisTag: pinned.get(a.axisTag, a.defaultValue) for a in self._axes},
            outputNormalized=True,
        )
        self._default_output = np.array(
            [default_output[tag] for tag in self._mapping.tags]
        )
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
            self._peak_seeds.append(
                (x, np.clip(self._mapping(x, columns=[])[0], -1, 1))
            )
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
        partial=False,
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
                a.axisTag in location or (not partial and i in self._free_set)
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

    def _linearCandidates(self, seed, i, lo, hi, target, scored):
        # With every other input fixed, product tents and avar1 are affine
        # between their knots. Split again where an output saturates, then
        # minimize ||a*t+b-target||^2 by projecting onto the line segment.
        np = self._np
        points = sorted({lo, hi, *[v for v in self._one_dim_knots[i] if lo <= v <= hi]})
        candidates = set(points)
        if lo <= 0 <= hi:
            candidates.add(0.0)
        triple = self._triples[self._axes[i].axisTag]
        for left, right in zip(points, points[1:]):
            mid = (left + right) / 2
            if not left < mid < right:
                continue
            x = seed.copy()
            x[i] = mid
            raw, jac = self._mapping(x, columns=[i])
            slope = jac[:, 0]
            cuts = {left, right}
            if self._clipped:
                for value, derivative in zip(raw, slope):
                    if derivative:
                        for edge in (-1, 1):
                            root = mid + (edge - value) / derivative
                            if left < root < right:
                                cuts.add(float(root))
            cuts = sorted(cuts)
            for a, b in zip(cuts, cuts[1:]):
                center = (a + b) / 2
                values = raw + slope * (center - mid)
                active = scored.copy()
                if self._clipped:
                    active &= (values > -1) & (values < 1)
                direction = slope[active]
                denominator = np.dot(direction, direction)
                optimum = (
                    center - np.dot(direction, (values - target)[active]) / denominator
                    if denominator
                    else 0.0
                )
                # Evaluate the exact knot separately: its value can differ
                # from either limit when a tent has a collapsed edge.
                lower = _adjacentInput(a, triple, 1)
                upper = _adjacentInput(b, triple, -1)
                if lower <= upper:
                    candidates.add(float(np.clip(optimum, lower, upper)))
                    candidates.add(float(np.clip(0, lower, upper)))
        for value in sorted(candidates):
            x = seed.copy()
            x[i] = value
            yield x

    def _solve(self, target, scored, tolerance):
        np = self._np
        least_squares = self._least_squares
        axes = self._axes
        triples = self._triples
        pinned = self._pinned
        mapping = self._mapping
        lower, upper, fixed, free = self._lower, self._upper, self._fixed, self._free
        # Fixed inputs with zero delta rows produce constant outputs. Their
        # residual is an unavoidable error floor. If the default free inputs
        # fit all remaining outputs exactly, they attain that floor with the
        # smallest possible number of non-default coordinates. No search can
        # improve either the error or sparsity, even for an unreachable target.
        dynamic = scored & ~self._constant_outputs
        nearest = np.array(target, dtype=float)
        if self._forward.version == 2:
            # Every avar2 output lies on the F2Dot14 grid, even with a NULL
            # VarStore. Include both half-tick ties by comparing distances,
            # rather than requiring the particular rounded coordinate.
            nearest = np.floor(target * 16384 + 0.5) / 16384
        nearest[self._constant_outputs] = self._default_output[self._constant_outputs]
        minimum_deviation = abs(nearest - target)
        error_floor = float(np.linalg.norm(minimum_deviation[scored]))
        if np.array_equal(
            abs(self._default_output[dynamic] - target[dynamic]),
            minimum_deviation[dynamic],
        ):
            return tuple(float(v) for v in fixed), float(
                np.linalg.norm((self._default_output - target)[scored])
            )
        candidates = {}
        linear_solved = {}

        def add_many(points):
            pending = {}
            for x in points:
                x = x.copy()
                x[free] = np.where(abs(x[free]) < 1e-10, 0, x[free])
                key = tuple(x)
                if key not in candidates and key not in pending:
                    pending[key] = x
            if not pending:
                return
            if self._batch_score is not None:
                actuals = self._batch_score(np.array(list(pending.values())))
            else:
                actuals = []
                for x in pending.values():
                    user = {
                        a.axisTag: _denormalize(v, triples[a.axisTag])
                        for a, v in zip(axes, x)
                    }
                    user.update(pinned)
                    actual = self._score(user)
                    actuals.append(np.array([actual[tag] for tag in mapping.tags]))
            for (key, x), actual in zip(pending.items(), actuals):
                # Keep the same NumPy norm and candidate insertion order; only
                # the coordinate conversion and forward evaluations are batched.
                error = np.linalg.norm((actual - target)[scored])
                candidates[key] = (error, x)

        def add(x):
            add_many((x,))

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
            if self._separable:
                # No region depends on an input: outputs separate by axis,
                # possibly with a constant avar2 offset. Invert each segment
                # map directly, choosing its preimage nearest the default.
                for i in varying:
                    x[i] = _inverseSegment(
                        target[i] - self._offset[i],
                        mapping.segments[i],
                        box_lower[i],
                        box_upper[i],
                    )
                add(x)
                return
            if len(varying) == 1:
                i = varying[0]
                key = (i, tuple(v for j, v in enumerate(x) if j != i))
                lo, hi = box_lower[i], box_upper[i]
                ranges = linear_solved.setdefault(key, [])
                if any(a <= lo and hi <= b for a, b in ranges):
                    return
                ranges.append((lo, hi))
                for candidate in self._linearCandidates(x, i, lo, hi, target, scored):
                    add(candidate)
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
                    raw, jac = mapping(x, columns=varying)
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
                    jac = jac * active[:, None]
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
                    ftol=_SOLVER_TOLERANCE,
                    xtol=_SOLVER_TOLERANCE,
                    gtol=_SOLVER_TOLERANCE,
                    max_nfev=200,
                )
                x[varying] = result.x
                add(x)
                if (
                    not clipped
                    and result.optimality < _SOLVER_TOLERANCE
                    and np.all(result.x > box_lower[varying] + 1e-9)
                    and np.all(result.x < box_upper[varying] - 1e-9)
                ):
                    # A second solve would immediately satisfy the same gtol
                    # if clipping leaves both residual and Jacobian unchanged.
                    # Stay away from the bounds: SciPy nudges an initial point
                    # inward there, which can change the restarted problem.
                    raw, jac = mapping(x, columns=varying)
                    clipped_residual = np.where(scored, np.clip(raw, -1, 1) - target, 0)
                    active = scored & (raw >= -1) & (raw <= 1)
                    if np.array_equal(result.fun, clipped_residual) and np.array_equal(
                        result.jac, jac * active[:, None]
                    ):
                        break

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
        if self._separable or len(free) == 1:
            seeds = [fixed.copy()]
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

        if self._jumps and len(free) > 1:
            # A gradient cannot guide a solve onto a zero-width support.
            # Fit its exact boundary with the jump axes held fixed, including
            # intersections of several jump planes in the same product tent.
            for seed, locked in self._jump_contexts:
                solve(seed, [i for i in free if i not in locked])

            def adjacent(value, i, direction):
                return _adjacentInput(value, triples[axes[i].axisTag], direction)

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
                                    (
                                        np.clip(mapping(x, columns=[])[0], -1, 1)
                                        - target
                                    )[scored]
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
            # An unattainable zero is not a reason to keep probing: fixed
            # outputs and quantization may impose a strictly positive floor.
            if error <= error_floor:
                break
            trials = []
            for i in free:
                _, slope = _segment(x[i], mapping.segments[i])
                if not slope:
                    continue  # A flat segment cannot move the intermediate value.
                step = 1 / (16384 * abs(slope))
                for offset in (-1, -0.5, 0.5, 1):
                    trial = x.copy()
                    trial[i] = np.clip(x[i] + offset * step, lower[i], upper[i])
                    trials.append(trial)
            add_many(trials)
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
