from fontTools.ttLib.ttGlyphSet import LerpGlyphSet
from fontTools.pens.basePen import AbstractPen, BasePen, DecomposingPen
from fontTools.pens.pointPen import AbstractPointPen, SegmentToPointPen
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.misc.transform import Transform
from fontTools.misc.fixedTools import floatToFixedToStr, nearestMultipleShortestRepr
from fontTools.misc.treeTools import minimum_spanning_tree
from fontTools.varLib.models import piecewiseLinearMap
from collections import defaultdict, deque
from math import sqrt, copysign, atan2, pi
import itertools

import logging

log = logging.getLogger("fontTools.varLib.interpolatable")


class LocationLabeler:
    """Describe tested locations without changing their coordinate space."""

    def __init__(self, axis_mapping, *, font=None, discrete_axes=()):
        self.axis_mapping = axis_mapping
        self.font = font
        self.discrete_axes = set(discrete_axes)
        self.cache = {}
        self.reverse_unavailable = False
        self._reverse_mapper = None
        self._forward_mapper = None
        avar = font.get("avar") if font is not None else None
        self.avar2 = (
            avar is not None
            and getattr(avar, "majorVersion", 1) >= 2
            and getattr(avar.table, "VarStore", None) is not None
        )

    @staticmethod
    def _coordinates(location):
        return (
            " ".join(f"{tag}={value}" for tag, value in location.items()) or "default"
        )

    def __call__(self, location, *, include_input=True):
        # Include every nonzero coordinate, including hidden axes. These are
        # the actual tested masters, regardless of whether public inputs can
        # reach them. Discrete zero values are meaningful, not defaults.
        key = tuple(
            sorted(
                (tag, value)
                for tag, value in location.items()
                if value != 0 or tag in self.discrete_axes
            )
        )
        if include_input and key in self.cache:
            return self.cache[key]
        # Midpoints of F2Dot14 peaks can contain a half-unit; retain that
        # extra bit instead of rounding the nominal location to another point.
        coordinates = {tag: floatToFixedToStr(value, 15) for tag, value in key}
        normalized = self._coordinates(coordinates) if coordinates else "all zero"
        labels = [f"normalized: {normalized}"]
        if not include_input:
            return tuple(labels)
        if not self.avar2:
            mapped = {
                tag: floatToFixedToStr(
                    piecewiseLinearMap(value, self.axis_mapping.get(tag, {})), 14
                )
                for tag, value in key
            }
            space = "input" if self.font is not None else "design"
            labels.append(f"{space}: {self._coordinates(mapped)}")
        elif not self.reverse_unavailable:
            try:
                self._add_input_label(labels, dict(key))
            except ImportError:
                # Matching and plotting can work without scipy. Do not make
                # optional avar2 annotations a new hard dependency.
                self.reverse_unavailable = True
        self.cache[key] = tuple(labels)
        return self.cache[key]

    def _add_input_label(self, labels, location):
        from .avar.reverse import ReverseMapper
        from .avar.map import ForwardMapper

        if self._reverse_mapper is None:
            # Build only when a report needs an input label. The formatted
            # label cache already memoizes both matches and failed inversions.
            self._reverse_mapper = ReverseMapper(self.font, cache_size=0)
            self._forward_mapper = ForwardMapper(self.font)

        # A gvar peak is a complete post-avar location: omitted hidden outputs
        # must target zero too. reverse() otherwise leaves those unconstrained.
        target = {a.axisTag: location.get(a.axisTag, 0) for a in self.font["fvar"].axes}
        inputs, error = self._reverse_mapper.reverse(
            target, inputNormalized=True, dropZeroes=True
        )
        tolerance = 1 / 16384
        if error > tolerance:
            return  # Retain the actual internal coordinates, not an approximation.
        formatted = {}
        for axis in self.font["fvar"].axes:
            tag = axis.axisTag
            if tag not in inputs:
                continue
            value = inputs[tag]
            extent = (
                axis.maxValue - axis.defaultValue
                if value >= axis.defaultValue
                else axis.defaultValue - axis.minValue
            )
            formatted[tag] = (
                nearestMultipleShortestRepr(value, extent / 16384)
                if extent
                else str(value)
            )
        # Pretty decimals can move an input across a steep avar segment.
        # Verify the displayed inputs, falling back to full precision when
        # shortening them would turn a good inverse into a misleading label.
        actual = self._forward_mapper.map(
            {tag: float(value) for tag, value in formatted.items()},
            outputNormalized=True,
        )
        display_error = sqrt(
            sum((actual[tag] - value) ** 2 for tag, value in target.items())
        )
        if display_error > tolerance:
            formatted = {tag: str(value) for tag, value in inputs.items()}
        labels.append(f"input: {self._coordinates(formatted)}")


class InterpolatableProblem:
    NOTHING = "nothing"
    MISSING = "missing"
    OPEN_PATH = "open_path"
    PATH_COUNT = "path_count"
    NODE_COUNT = "node_count"
    NODE_INCOMPATIBILITY = "node_incompatibility"
    CONTOUR_ORDER = "contour_order"
    WRONG_START_POINT = "wrong_start_point"
    KINK = "kink"
    UNDERWEIGHT = "underweight"
    OVERWEIGHT = "overweight"

    severity = {
        MISSING: 1,
        OPEN_PATH: 2,
        PATH_COUNT: 3,
        NODE_COUNT: 4,
        NODE_INCOMPATIBILITY: 5,
        CONTOUR_ORDER: 6,
        WRONG_START_POINT: 7,
        KINK: 8,
        UNDERWEIGHT: 9,
        OVERWEIGHT: 10,
        NOTHING: 11,
    }


def sort_problems(problems):
    """Sort problem groups by their most severe problem type."""
    return dict(
        sorted(
            problems.items(),
            key=lambda _: -min(
                (
                    (InterpolatableProblem.severity[p["type"]] + p.get("tolerance", 0))
                    for p in _[1]
                ),
            ),
            reverse=True,
        )
    )


def rot_list(l, k):
    """Rotate list by k items forward.  Ie. item at position 0 will be
    at position k in returned list.  Negative k is allowed."""
    return l[-k:] + l[:-k]


class PerContourPen(BasePen):
    def __init__(self, Pen, glyphset=None):
        BasePen.__init__(self, glyphset)
        self._Pen = Pen
        self._pen = None
        self.value = []

    def _moveTo(self, p0):
        self._newItem()
        self._pen.moveTo(p0)

    def _lineTo(self, p1):
        self._pen.lineTo(p1)

    def _qCurveToOne(self, p1, p2):
        self._pen.qCurveTo(p1, p2)

    def _curveToOne(self, p1, p2, p3):
        self._pen.curveTo(p1, p2, p3)

    def _closePath(self):
        self._pen.closePath()
        self._pen = None

    def _endPath(self):
        self._pen.endPath()
        self._pen = None

    def _newItem(self):
        self._pen = pen = self._Pen()
        self.value.append(pen)


class PerContourOrComponentPen(PerContourPen):
    def addComponent(self, glyphName, transformation):
        self._newItem()
        self.value[-1].addComponent(glyphName, transformation)


class SimpleRecordingPointPen(AbstractPointPen):
    def __init__(self):
        self.value = []

    def beginPath(self, identifier=None, **kwargs):
        pass

    def endPath(self) -> None:
        pass

    def addPoint(self, pt, segmentType=None):
        self.value.append((pt, False if segmentType is None else True))


def vdiff_hypot2(v0, v1):
    s = 0
    for x0, x1 in zip(v0, v1):
        d = x1 - x0
        s += d * d
    return s


def vdiff_hypot2_complex(v0, v1):
    s = 0
    for x0, x1 in zip(v0, v1):
        d = x1 - x0
        s += d.real * d.real + d.imag * d.imag
        # This does the same but seems to be slower:
        # s += (d * d.conjugate()).real
    return s


def matching_cost(G, matching):
    return sum(G[i][j] for i, j in enumerate(matching))


def min_cost_perfect_bipartite_matching_scipy(G):
    n = len(G)
    rows, cols = linear_sum_assignment(G)
    assert (rows == list(range(n))).all()
    # Convert numpy array and integer to Python types,
    # to ensure that this is JSON-serializable.
    cols = list(int(e) for e in cols)
    return list(cols), matching_cost(G, cols)


def min_cost_perfect_bipartite_matching_munkres(G):
    n = len(G)
    cols = [None] * n
    for row, col in Munkres().compute(G):
        cols[row] = col
    return cols, matching_cost(G, cols)


def min_cost_perfect_bipartite_matching_bruteforce(G):
    n = len(G)

    if n > 6:
        raise Exception("Install Python module 'munkres' or 'scipy >= 0.17.0'")

    # Otherwise just brute-force
    permutations = itertools.permutations(range(n))
    best = list(next(permutations))
    best_cost = matching_cost(G, best)
    for p in permutations:
        cost = matching_cost(G, p)
        if cost < best_cost:
            best, best_cost = list(p), cost
    return best, best_cost


# Prefer `scipy.optimize.linear_sum_assignment` for performance.
# `Munkres` is also supported as a fallback for minimalistic systems
# where installing SciPy is not feasible.
try:
    from scipy.optimize import linear_sum_assignment

    min_cost_perfect_bipartite_matching = min_cost_perfect_bipartite_matching_scipy
except ImportError:
    try:
        from munkres import Munkres

        min_cost_perfect_bipartite_matching = (
            min_cost_perfect_bipartite_matching_munkres
        )
    except ImportError:
        min_cost_perfect_bipartite_matching = (
            min_cost_perfect_bipartite_matching_bruteforce
        )


def contour_vector_from_stats(stats):
    # Don't change the order of items here.
    # It's okay to add to the end, but otherwise, other
    # code depends on it. Search for "covariance".
    size = sqrt(abs(stats.area))
    return (
        copysign((size), stats.area),
        stats.meanX,
        stats.meanY,
        stats.stddevX * 2,
        stats.stddevY * 2,
        stats.correlation * size,
    )


def matching_for_vectors(m0, m1):
    n = len(m0)

    costs = [[vdiff_hypot2(v0, v1) for v1 in m1] for v0 in m0]
    (
        matching,
        matching_cost,
    ) = min_cost_perfect_bipartite_matching(costs)
    identity_cost = sum(costs[i][i] for i in range(n))
    return matching, matching_cost, identity_cost


def points_characteristic_bits(points):
    bits = 0
    for pt, b in reversed(points):
        bits = (bits << 1) | b
    return bits


_NUM_ITEMS_PER_POINTS_COMPLEX_VECTOR = 4


def points_complex_vector(points):
    vector = []
    if not points:
        return vector
    points = [complex(*pt) for pt, _ in points]
    n = len(points)
    assert _NUM_ITEMS_PER_POINTS_COMPLEX_VECTOR == 4
    points.extend(points[: _NUM_ITEMS_PER_POINTS_COMPLEX_VECTOR - 1])
    while len(points) < _NUM_ITEMS_PER_POINTS_COMPLEX_VECTOR:
        points.extend(points[: _NUM_ITEMS_PER_POINTS_COMPLEX_VECTOR - 1])
    for i in range(n):
        # The weights are magic numbers.

        # The point itself
        p0 = points[i]
        vector.append(p0)

        # The vector to the next point
        p1 = points[i + 1]
        d0 = p1 - p0
        vector.append(d0 * 3)

        # The turn vector
        p2 = points[i + 2]
        d1 = p2 - p1
        vector.append(d1 - d0)

        # The angle to the next point, as a cross product;
        # Square root of, to match dimentionality of distance.
        cross = d0.real * d1.imag - d0.imag * d1.real
        cross = copysign(sqrt(abs(cross)), cross)
        vector.append(cross * 4)

    return vector


def add_isomorphisms(points, isomorphisms, reverse):
    reference_bits = points_characteristic_bits(points)
    n = len(points)

    # if points[0][0] == points[-1][0]:
    #   abort

    if reverse:
        points = points[::-1]
        bits = points_characteristic_bits(points)
    else:
        bits = reference_bits

    vector = points_complex_vector(points)

    assert len(vector) % n == 0
    mult = len(vector) // n
    mask = (1 << n) - 1

    for i in range(n):
        b = ((bits << (n - i)) & mask) | (bits >> i)
        if b == reference_bits:
            isomorphisms.append(
                (rot_list(vector, -i * mult), n - 1 - i if reverse else i, reverse)
            )


def find_parents_and_order(glyphsets, locations, *, discrete_axes=set()):
    parents = [None] + list(range(len(glyphsets) - 1))
    order = list(range(len(glyphsets)))
    if locations:
        # Order base master first
        bases = [
            i
            for i, l in enumerate(locations)
            if all(v == 0 for k, v in l.items() if k not in discrete_axes)
        ]
        if bases:
            log.info("Found %s base masters: %s", len(bases), bases)
        else:
            log.warning("No base master location found")

        # Form a minimum spanning tree of the locations.
        axes = sorted({k for l in locations for k in l if k not in discrete_axes})
        vectors = [tuple(l.get(k, 0) for k in axes) for l in locations]
        active_axes = [
            {k for k, v in zip(axes, vector) if v != 0} for vector in vectors
        ]
        discrete_locations = [
            {k: l.get(k, 0) for k in discrete_axes} for l in locations
        ]
        edges = []
        for i, j in itertools.combinations(range(len(locations)), 2):
            if discrete_locations[i] != discrete_locations[j]:
                continue
            # Compare masters within the same axis subspace or one of its
            # lower-dimensional subspaces.
            if not (
                active_axes[i] <= active_axes[j] or active_axes[j] <= active_axes[i]
            ):
                continue
            # First change fewer coordinates, then minimize distance.
            changed = sum(v0 != v1 for v0, v1 in zip(vectors[i], vectors[j]))
            distance = vdiff_hypot2(vectors[i], vectors[j])
            edges.append(((changed, distance), i, j))

        graph = defaultdict(set)
        for _, i, j in minimum_spanning_tree(edges):
            graph[i].add(j)
            graph[j].add(i)

        # Traverse graph from the bases and assign parents.
        parents = [None] * len(locations)
        order = []
        visited = set(bases)
        queue = deque(bases)
        while queue:
            i = queue.popleft()
            order.append(i)
            for j in sorted(graph[i]):
                if j not in visited:
                    visited.add(j)
                    parents[j] = i
                    queue.append(j)
        assert len(order) == len(
            parents
        ), "Not all masters are reachable; report an issue"

        log.info("Parents: %s", parents)
        log.info("Order: %s", order)
    return parents, order
