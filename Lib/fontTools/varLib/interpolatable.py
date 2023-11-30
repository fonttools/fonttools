"""
Tool to find wrong contour order between different masters, and
other interpolatability (or lack thereof) issues.

Call as:
$ fonttools varLib.interpolatable font1 font2 ...
"""

from fontTools.pens.basePen import AbstractPen, BasePen, DecomposingPen
from fontTools.pens.pointPen import AbstractPointPen, SegmentToPointPen
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import ControlBoundsPen
from fontTools.pens.statisticsPen import StatisticsPen, StatisticsControlPen
from fontTools.pens.momentsPen import OpenContourError
from fontTools.varLib.models import piecewiseLinearMap, normalizeLocation
from fontTools.misc.fixedTools import floatToFixedToStr
from fontTools.misc.transform import Transform
from collections import defaultdict, deque
from types import SimpleNamespace
from functools import wraps
from pprint import pformat
from math import sqrt, copysign, atan2, pi
import itertools
import logging

log = logging.getLogger("fontTools.varLib.interpolatable")

DEFAULT_TOLERANCE = 0.95
DEFAULT_KINKINESS = 0.5
DEFAULT_KINKINESS_LENGTH = 0.002  # ratio of UPEM
DEFAULT_UPEM = 1000


def _rot_list(l, k):
    """Rotate list by k items forward.  Ie. item at position 0 will be
    at position k in returned list.  Negative k is allowed."""
    return l[-k:] + l[:-k]


class PerContourPen(BasePen):
    def __init__(self, Pen, glyphset=None):
        BasePen.__init__(self, glyphset)
        self._glyphset = glyphset
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


def _vdiff_hypot2(v0, v1):
    s = 0
    for x0, x1 in zip(v0, v1):
        d = x1 - x0
        s += d * d
    return s


def _vdiff_hypot2_complex(v0, v1):
    s = 0
    for x0, x1 in zip(v0, v1):
        d = x1 - x0
        s += d.real * d.real + d.imag * d.imag
        # This does the same but seems to be slower:
        # s += (d * d.conjugate()).real
    return s


def _hypot2_complex(d):
    return d.real * d.real + d.imag * d.imag


def _matching_cost(G, matching):
    return sum(G[i][j] for i, j in enumerate(matching))


def min_cost_perfect_bipartite_matching_scipy(G):
    n = len(G)
    rows, cols = linear_sum_assignment(G)
    assert (rows == list(range(n))).all()
    return list(cols), _matching_cost(G, cols)


def min_cost_perfect_bipartite_matching_munkres(G):
    n = len(G)
    cols = [None] * n
    for row, col in Munkres().compute(G):
        cols[row] = col
    return cols, _matching_cost(G, cols)


def min_cost_perfect_bipartite_matching_bruteforce(G):
    n = len(G)

    if n > 6:
        raise Exception("Install Python module 'munkres' or 'scipy >= 0.17.0'")

    # Otherwise just brute-force
    permutations = itertools.permutations(range(n))
    best = list(next(permutations))
    best_cost = _matching_cost(G, best)
    for p in permutations:
        cost = _matching_cost(G, p)
        if cost < best_cost:
            best, best_cost = list(p), cost
    return best, best_cost


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


def _contour_vector_from_stats(stats):
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


def _matching_for_vectors(m0, m1):
    n = len(m0)

    identity_matching = list(range(n))

    costs = [[_vdiff_hypot2(v0, v1) for v1 in m1] for v0 in m0]
    (
        matching,
        matching_cost,
    ) = min_cost_perfect_bipartite_matching(costs)
    identity_cost = sum(costs[i][i] for i in range(n))
    return matching, matching_cost, identity_cost


def _points_characteristic_bits(points):
    bits = 0
    for pt, b in reversed(points):
        bits = (bits << 1) | b
    return bits


_NUM_ITEMS_PER_POINTS_COMPLEX_VECTOR = 4


def _points_complex_vector(points):
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


def _add_isomorphisms(points, isomorphisms, reverse):
    reference_bits = _points_characteristic_bits(points)
    n = len(points)

    # if points[0][0] == points[-1][0]:
    #   abort

    if reverse:
        points = points[::-1]
        bits = _points_characteristic_bits(points)
    else:
        bits = reference_bits

    vector = _points_complex_vector(points)

    assert len(vector) % n == 0
    mult = len(vector) // n
    mask = (1 << n) - 1

    for i in range(n):
        b = ((bits << (n - i)) & mask) | (bits >> i)
        if b == reference_bits:
            isomorphisms.append(
                (_rot_list(vector, -i * mult), n - 1 - i if reverse else i, reverse)
            )


def _find_parents_and_order(glyphsets, locations):
    parents = [None] + list(range(len(glyphsets) - 1))
    order = list(range(len(glyphsets)))
    if locations:
        # Order base master first
        bases = (i for i, l in enumerate(locations) if all(v == 0 for v in l.values()))
        if bases:
            base = next(bases)
            logging.info("Base master index %s, location %s", base, locations[base])
        else:
            base = 0
            logging.warning("No base master location found")

        # Form a minimum spanning tree of the locations
        try:
            from scipy.sparse.csgraph import minimum_spanning_tree

            graph = [[0] * len(locations) for _ in range(len(locations))]
            axes = set()
            for l in locations:
                axes.update(l.keys())
            axes = sorted(axes)
            vectors = [tuple(l.get(k, 0) for k in axes) for l in locations]
            for i, j in itertools.combinations(range(len(locations)), 2):
                graph[i][j] = _vdiff_hypot2(vectors[i], vectors[j])

            tree = minimum_spanning_tree(graph)
            rows, cols = tree.nonzero()
            graph = defaultdict(set)
            for row, col in zip(rows, cols):
                graph[row].add(col)
                graph[col].add(row)

            # Traverse graph from the base and assign parents
            parents = [None] * len(locations)
            order = []
            visited = set()
            queue = deque([base])
            while queue:
                i = queue.popleft()
                visited.add(i)
                order.append(i)
                for j in sorted(graph[i]):
                    if j not in visited:
                        parents[j] = i
                        queue.append(j)

        except ImportError:
            pass

        log.info("Parents: %s", parents)
        log.info("Order: %s", order)
    return parents, order


def transform_from_stats(stats, inverse=False):

    # https://cookierobotics.com/007/
    a = stats.varianceX
    b = stats.covariance
    c = stats.varianceY

    delta = (((a - c) * 0.5) ** 2 + b * b) ** 0.5
    lambda1 = (a + c) * 0.5 + delta  # Major eigenvalue
    lambda2 = (a + c) * 0.5 - delta  # Minor eigenvalue
    theta = (
        atan2(lambda1 - a, b)
        if b != 0
        else (pi * 0.5 if a < c else 0)
    )
    trans = Transform()

    if lambda2 < 0:
        # XXX This is a hack.
        # The problem is that the covariance matrix is singular.
        # This happens when the contour is a line, or a circle.
        # In that case, the covariance matrix is not a good
        # representation of the contour.
        # We should probably detect this earlier and avoid
        # computing the covariance matrix in the first place.
        # But for now, we just avoid the division by zero.
        lambda2 = 0

    if inverse:
        trans = trans.translate(-stats.meanX, -stats.meanY)
        trans = trans.rotate(-theta)
        trans = trans.scale(1 / sqrt(lambda1), 1 / sqrt(lambda2))
    else:
        trans = trans.scale(sqrt(lambda1), sqrt(lambda2))
        trans = trans.rotate(theta)
        trans = trans.translate(stats.meanX, stats.meanY)

    return trans


def lerp_recordings(recording1, recording2, factor=0.5):
    pen = RecordingPen()
    value = pen.value
    for (op1, args1), (op2, args2) in zip(recording1.value, recording2.value):
        if op1 != op2:
            raise ValueError("Mismatched operations: %s, %s" % (op1, op2))
        if op1 == "addComponent":
            mid_args = args1  # XXX Interpolate transformation?
        else:
            mid_args = [
                (x1 + (x2 - x1) * factor, y1 + (y2 - y1) * factor)
                for (x1, y1), (x2, y2) in zip(args1, args2)
            ]
        value.append((op1, mid_args))
    return pen


def test_gen(
    glyphsets,
    glyphs=None,
    names=None,
    ignore_missing=False,
    *,
    locations=None,
    tolerance=DEFAULT_TOLERANCE,
    kinkiness=DEFAULT_KINKINESS,
    upem=DEFAULT_UPEM,
    show_all=False,
):
    if tolerance >= 10:
        tolerance *= 0.01
    assert 0 <= tolerance <= 1
    if kinkiness >= 10:
        kinkiness *= 0.01
    assert 0 <= kinkiness

    if names is None:
        names = glyphsets

    if glyphs is None:
        # `glyphs = glyphsets[0].keys()` is faster, certainly, but doesn't allow for sparse TTFs/OTFs given out of order
        # ... risks the sparse master being the first one, and only processing a subset of the glyphs
        glyphs = {g for glyphset in glyphsets for g in glyphset.keys()}

    parents, order = _find_parents_and_order(glyphsets, locations)

    def grand_parent(i, glyphname):
        if i is None:
            return None
        i = parents[i]
        if i is None:
            return None
        while parents[i] is not None and glyphsets[i][glyphname] is None:
            i = parents[i]
        return i

    for glyph_name in glyphs:
        log.info("Testing glyph %s", glyph_name)
        allGreenVectors = []
        allGreenVectorsNormalized = []
        allControlVectors = []
        allNodeTypes = []
        allContourIsomorphisms = []
        allContourPoints = []
        allContourPens = []
        allContourPensNormalized = []
        allGlyphs = [glyphset[glyph_name] for glyphset in glyphsets]
        if len([1 for glyph in allGlyphs if glyph is not None]) <= 1:
            continue
        for master_idx, (glyph, glyphset, name) in enumerate(
            zip(allGlyphs, glyphsets, names)
        ):
            if glyph is None:
                if not ignore_missing:
                    yield (
                        glyph_name,
                        {"type": "missing", "master": name, "master_idx": master_idx},
                    )
                allNodeTypes.append(None)
                allControlVectors.append(None)
                allGreenVectors.append(None)
                allGreenVectorsNormalized.append(None)
                allContourIsomorphisms.append(None)
                allContourPoints.append(None)
                allContourPens.append(None)
                allContourPensNormalized.append(None)
                continue

            perContourPen = PerContourOrComponentPen(RecordingPen, glyphset=glyphset)
            try:
                glyph.draw(perContourPen, outputImpliedClosingLine=True)
            except TypeError:
                glyph.draw(perContourPen)
            contourPens = perContourPen.value
            del perContourPen
            contourPensNormalized = []

            contourControlVectors = []
            contourGreenVectors = []
            contourGreenVectorsNormalized = []
            contourIsomorphisms = []
            contourPoints = []
            nodeTypes = []
            allNodeTypes.append(nodeTypes)
            allControlVectors.append(contourControlVectors)
            allGreenVectors.append(contourGreenVectors)
            allGreenVectorsNormalized.append(contourGreenVectorsNormalized)
            allContourIsomorphisms.append(contourIsomorphisms)
            allContourPoints.append(contourPoints)
            allContourPens.append(contourPens)
            allContourPensNormalized.append(contourPensNormalized)
            for ix, contour in enumerate(contourPens):
                contourOps = tuple(op for op, arg in contour.value)
                nodeTypes.append(contourOps)

                greenStats = StatisticsPen(glyphset=glyphset)
                controlStats = StatisticsControlPen(glyphset=glyphset)
                try:
                    contour.replay(greenStats)
                    contour.replay(controlStats)
                except OpenContourError as e:
                    yield (
                        glyph_name,
                        {
                            "master": name,
                            "master_idx": master_idx,
                            "contour": ix,
                            "type": "open_path",
                        },
                    )
                    continue
                contourGreenVectors.append(_contour_vector_from_stats(greenStats))
                contourControlVectors.append(_contour_vector_from_stats(controlStats))


                # Save a "normalized" version of the outlines

                try:
                    rpen = DecomposingRecordingPen(glyphset)
                    tpen = TransformPen(rpen, transform_from_stats(greenStats, inverse=True))
                    contour.replay(tpen)
                    contourPensNormalized.append(rpen)
                except ZeroDivisionError:
                    contourPensNormalized.append(None)

                greenStats = StatisticsPen(glyphset=glyphset)
                rpen.replay(greenStats)
                contourGreenVectorsNormalized.append(_contour_vector_from_stats(greenStats))

                # Check starting point
                if contourOps[0] == "addComponent":
                    continue
                assert contourOps[0] == "moveTo"
                assert contourOps[-1] in ("closePath", "endPath")
                points = SimpleRecordingPointPen()
                converter = SegmentToPointPen(points, False)
                contour.replay(converter)
                # points.value is a list of pt,bool where bool is true if on-curve and false if off-curve;
                # now check all rotations and mirror-rotations of the contour and build list of isomorphic
                # possible starting points.

                isomorphisms = []
                contourIsomorphisms.append(isomorphisms)

                # Add rotations
                _add_isomorphisms(points.value, isomorphisms, False)
                # Add mirrored rotations
                _add_isomorphisms(points.value, isomorphisms, True)

                contourPoints.append(points.value)

        matchings = [None] * len(allControlVectors)

        for m1idx in order:
            if allNodeTypes[m1idx] is None:
                continue
            m0idx = grand_parent(m1idx, glyph_name)
            if m0idx is None:
                continue
            if allNodeTypes[m0idx] is None:
                continue

            #
            # Basic compatibility checks
            #

            m1 = allNodeTypes[m1idx]
            m0 = allNodeTypes[m0idx]
            if len(m0) != len(m1):
                yield (
                    glyph_name,
                    {
                        "type": "path_count",
                        "master_1": names[m0idx],
                        "master_2": names[m1idx],
                        "master_1_idx": m0idx,
                        "master_2_idx": m1idx,
                        "value_1": len(m0),
                        "value_2": len(m1),
                    },
                )
                continue

            if m0 != m1:
                for pathIx, (nodes1, nodes2) in enumerate(zip(m0, m1)):
                    if nodes1 == nodes2:
                        continue
                    if len(nodes1) != len(nodes2):
                        yield (
                            glyph_name,
                            {
                                "type": "node_count",
                                "path": pathIx,
                                "master_1": names[m0idx],
                                "master_2": names[m1idx],
                                "master_1_idx": m0idx,
                                "master_2_idx": m1idx,
                                "value_1": len(nodes1),
                                "value_2": len(nodes2),
                            },
                        )
                        continue
                    for nodeIx, (n1, n2) in enumerate(zip(nodes1, nodes2)):
                        if n1 != n2:
                            yield (
                                glyph_name,
                                {
                                    "type": "node_incompatibility",
                                    "path": pathIx,
                                    "node": nodeIx,
                                    "master_1": names[m0idx],
                                    "master_2": names[m1idx],
                                    "master_1_idx": m0idx,
                                    "master_2_idx": m1idx,
                                    "value_1": n1,
                                    "value_2": n2,
                                },
                            )
                            continue

            #
            # "contour_order" check
            #

            # We try matching both the StatisticsControlPen vector
            # and the StatisticsPen vector.
            #
            # If either method found a identity matching, accept it.
            # This is crucial for fonts like Kablammo[MORF].ttf and
            # Nabla[EDPT,EHLT].ttf, since they really confuse the
            # StatisticsPen vector because of their area=0 contours.
            #
            # TODO: Optimize by only computing the StatisticsPen vector
            # and then checking if it is the identity vector. Only if
            # not, compute the StatisticsControlPen vector and check both.

            n = len(allControlVectors[m0idx])
            done = n <= 1
            if not done:
                m1Control = allControlVectors[m1idx]
                m0Control = allControlVectors[m0idx]
                (
                    matching_control,
                    matching_cost_control,
                    identity_cost_control,
                ) = _matching_for_vectors(m0Control, m1Control)
                done = matching_cost_control == identity_cost_control
            if not done:
                m1Green = allGreenVectors[m1idx]
                m0Green = allGreenVectors[m0idx]
                (
                    matching_green,
                    matching_cost_green,
                    identity_cost_green,
                ) = _matching_for_vectors(m0Green, m1Green)
                done = matching_cost_green == identity_cost_green

            if not done:
                # See if reversing contours in one master helps.
                # That's a common problem.  Then the wrong_start_point
                # test will fix them.
                #
                # Reverse the sign of the area (0); the rest stay the same.
                if not done:
                    m1ControlReversed = [(-m[0],) + m[1:] for m in m1Control]
                    (
                        matching_control_reversed,
                        matching_cost_control_reversed,
                        identity_cost_control_reversed,
                    ) = _matching_for_vectors(m0Control, m1ControlReversed)
                    done = (
                        matching_cost_control_reversed == identity_cost_control_reversed
                    )
                if not done:
                    m1GreenReversed = [(-m[0],) + m[1:] for m in m1Green]
                    (
                        matching_control_reversed,
                        matching_cost_control_reversed,
                        identity_cost_control_reversed,
                    ) = _matching_for_vectors(m0Control, m1ControlReversed)
                    done = (
                        matching_cost_control_reversed == identity_cost_control_reversed
                    )

                if not done:
                    # Otherwise, use the worst of the two matchings.
                    if (
                        matching_cost_control / identity_cost_control
                        < matching_cost_green / identity_cost_green
                    ):
                        matching = matching_control
                        matching_cost = matching_cost_control
                        identity_cost = identity_cost_control
                    else:
                        matching = matching_green
                        matching_cost = matching_cost_green
                        identity_cost = identity_cost_green

                    if matching_cost < identity_cost * tolerance:
                        log.debug(
                            "matching_control_ratio %g; matching_green_ratio %g.",
                            matching_cost_control / identity_cost_control,
                            matching_cost_green / identity_cost_green,
                        )
                        this_tolerance = matching_cost / identity_cost
                        log.debug("tolerance: %g", this_tolerance)
                        yield (
                            glyph_name,
                            {
                                "type": "contour_order",
                                "master_1": names[m0idx],
                                "master_2": names[m1idx],
                                "master_1_idx": m0idx,
                                "master_2_idx": m1idx,
                                "value_1": list(range(n)),
                                "value_2": matching,
                                "tolerance": this_tolerance,
                            },
                        )
                        matchings[m1idx] = matching

            #
            # "wrong_start_point" / weight check
            #

            m1 = allContourIsomorphisms[m1idx]
            m0 = allContourIsomorphisms[m0idx]
            m1Vectors = allGreenVectors[m1idx]
            m0Vectors = allGreenVectors[m0idx]
            m1VectorsNormalized = allGreenVectorsNormalized[m1idx]
            m0VectorsNormalized = allGreenVectorsNormalized[m0idx]
            recording0 = allContourPens[m0idx]
            recording1 = allContourPens[m1idx]
            recording0Normalized = allContourPensNormalized[m0idx]
            recording1Normalized = allContourPensNormalized[m1idx]

            # If contour-order is wrong, adjust it
            if matchings[m1idx] is not None and m1:  # m1 is empty for composite glyphs
                m1 = [m1[i] for i in matchings[m1idx]]
                m1Vectors = [m1Vectors[i] for i in matchings[m1idx]]
                m1VectorsNormalized = [m1VectorsNormalized[i] for i in matchings[m1idx]]
                recording1 = [recording1[i] for i in matchings[m1idx]]
                recording1Normalized = [recording1Normalized[i] for i in matchings[m1idx]]

            midRecording = []
            for c0, c1 in zip(recording0, recording1):
                try:
                    midRecording.append(lerp_recordings(c0, c1))
                except ValueError:
                    # Mismatch because of the reordering above
                    midRecording.append(None)

            for ix, (contour0, contour1) in enumerate(zip(m0, m1)):
                if len(contour0) == 0 or len(contour0) != len(contour1):
                    # We already reported this; or nothing to do; or not compatible
                    # after reordering above.
                    continue

                c0 = contour0[0]
                # Next few lines duplicated below.
                costs = [_vdiff_hypot2_complex(c0[0], c1[0]) for c1 in contour1]
                min_cost_idx, min_cost = min(enumerate(costs), key=lambda x: x[1])
                first_cost = costs[0]

                if min_cost < first_cost * tolerance:
                    this_tolerance = min_cost / first_cost
                    # c0 is the first isomorphism of the m0 master
                    # contour1 is list of all isomorphisms of the m1 master
                    #
                    # If the two shapes are both circle-ish and slightly
                    # rotated, we detect wrong start point. This is for
                    # example the case hundreds of times in
                    # RobotoSerif-Italic[GRAD,opsz,wdth,wght].ttf
                    #
                    # If the proposed point is only one off from the first
                    # point (and not reversed), try harder:
                    #
                    # Find the major eigenvector of the covariance matrix,
                    # and rotate the contours by that angle. Then find the
                    # closest point again.  If it matches this time, let it
                    # pass.

                    proposed_point = contour1[min_cost_idx][1]
                    reverse = contour1[min_cost_idx][2]
                    num_points = len(allContourPoints[m1idx][ix])
                    leeway = 3
                    okay = False
                    if not reverse and (
                        proposed_point <= leeway
                        or proposed_point >= num_points - leeway
                    ):
                        # Try harder

                        # Recover the covariance matrix from the GreenVectors.
                        # This is a 2x2 matrix.
                        transforms = []
                        for vector in (m0Vectors[ix], m1Vectors[ix]):
                            meanX = vector[1]
                            meanY = vector[2]
                            stddevX = vector[3] * 0.5
                            stddevY = vector[4] * 0.5
                            correlation = vector[5] / abs(vector[0])

                            # https://cookierobotics.com/007/
                            a = stddevX * stddevX  # VarianceX
                            c = stddevY * stddevY  # VarianceY
                            b = correlation * stddevX * stddevY  # Covariance

                            delta = (((a - c) * 0.5) ** 2 + b * b) ** 0.5
                            lambda1 = (a + c) * 0.5 + delta  # Major eigenvalue
                            lambda2 = (a + c) * 0.5 - delta  # Minor eigenvalue
                            theta = (
                                atan2(lambda1 - a, b)
                                if b != 0
                                else (pi * 0.5 if a < c else 0)
                            )
                            trans = Transform()
                            # Don't translate here. We are working on the complex-vector
                            # that includes more than just the points. It's horrible what
                            # we are doing anyway...
                            # trans = trans.translate(meanX, meanY)
                            trans = trans.rotate(theta)
                            trans = trans.scale(sqrt(lambda1), sqrt(lambda2))
                            transforms.append(trans)

                        trans = transforms[0]
                        new_c0 = (
                            [
                                complex(*trans.transformPoint((pt.real, pt.imag)))
                                for pt in c0[0]
                            ],
                        ) + c0[1:]
                        trans = transforms[1]
                        new_contour1 = []
                        for c1 in contour1:
                            new_c1 = (
                                [
                                    complex(*trans.transformPoint((pt.real, pt.imag)))
                                    for pt in c1[0]
                                ],
                            ) + c1[1:]
                            new_contour1.append(new_c1)

                        # Next few lines duplicate from above.
                        costs = [
                            _vdiff_hypot2_complex(new_c0[0], new_c1[0])
                            for new_c1 in new_contour1
                        ]
                        min_cost_idx, min_cost = min(
                            enumerate(costs), key=lambda x: x[1]
                        )
                        first_cost = costs[0]
                        if min_cost < first_cost * tolerance:
                            pass
                            # this_tolerance = min_cost / first_cost
                            # proposed_point = new_contour1[min_cost_idx][1]
                        else:
                            okay = True

                    if not okay:
                        yield (
                            glyph_name,
                            {
                                "type": "wrong_start_point",
                                "contour": ix,
                                "master_1": names[m0idx],
                                "master_2": names[m1idx],
                                "master_1_idx": m0idx,
                                "master_2_idx": m1idx,
                                "value_1": 0,
                                "value_2": proposed_point,
                                "reversed": reverse,
                                "tolerance": this_tolerance,
                            },
                        )
                else:
                    # Weight check.
                    #
                    # If contour could be mid-interpolated, and the two
                    # contours have the same area sign, proceeed.
                    #
                    # The sign difference can happen if it's a werido
                    # self-intersecting contour; ignore it.
                    contour = midRecording[ix]
                    from .interpolatablePlot import LerpGlyphSet
                    if contour and (m0VectorsNormalized[ix][0] < 0) == (m1VectorsNormalized[ix][0] < 0):

                        midStats = StatisticsPen(glyphset=None)
                        contour.replay(midStats)

                        midStatsNormalized = StatisticsPen(glyphset=None)
                        tpen = TransformPen(midStatsNormalized, transform_from_stats(midStats, inverse=True))
                        contour.replay(tpen)

                        midVectorNormalized = _contour_vector_from_stats(midStatsNormalized)

                        size0 = m0VectorsNormalized[ix][0] * m0VectorsNormalized[ix][0]
                        size1 = m1VectorsNormalized[ix][0] * m1VectorsNormalized[ix][0]
                        midSize = midVectorNormalized[0] * midVectorNormalized[0]

                        power = 1
                        t = tolerance ** power

                        for overweight, problem_type in enumerate(
                            ("underweight", "overweight")
                        ):
                            if overweight:
                                expectedSize = sqrt(size0 * size1)
                                expectedSize = (size0 + size1) - expectedSize
                                expectedSize = size1 + (midSize - size1) * t + 1e-1

                                #expectedSize = (size0 + size1) * .5
                                continue
                            else:
                                #expectedSize = sqrt(size0 * size1)
                                expectedSize = sqrt(size0 * size1)
                                #expectedSize = size0 + (midSize - size0) * t + 1e-1
                                #expectedSize = sqrt(size0 * size1 * t) + 1e-1

                            log.debug(
                                "%s: actual size %g; threshold size %g, master sizes: %g, %g",
                                problem_type,
                                midSize,
                                expectedSize,
                                size0,
                                size1,
                            )

                            size0, size1 = sorted((size0, size1))

                            if (
                                not overweight and expectedSize < midSize
                            ) or (
                                overweight and 1e-5 + expectedSize < midSize
                            ):
                                try:
                                    if overweight:
                                        this_tolerance = (expectedSize / midSize) ** (1 / power)
                                    else:
                                        this_tolerance = (midSize / expectedSize) ** (1 / power)
                                except ZeroDivisionError:
                                    this_tolerance = 0
                                log.debug("tolerance %g", this_tolerance)
                                yield (
                                    glyph_name,
                                    {
                                        "type": problem_type,
                                        "contour": ix,
                                        "master_1": names[m0idx],
                                        "master_2": names[m1idx],
                                        "master_1_idx": m0idx,
                                        "master_2_idx": m1idx,
                                        "tolerance": this_tolerance,
                                    },
                                )

            #
            # "kink" detector
            #
            m1 = allContourPoints[m1idx]
            m0 = allContourPoints[m0idx]

            # If contour-order is wrong, adjust it
            if matchings[m1idx] is not None and m1:  # m1 is empty for composite glyphs
                m1 = [m1[i] for i in matchings[m1idx]]

            t = 0.1  # ~sin(radian(6)) for tolerance 0.95
            deviation_threshold = (
                upem * DEFAULT_KINKINESS_LENGTH * DEFAULT_KINKINESS / kinkiness
            )

            for ix, (contour0, contour1) in enumerate(zip(m0, m1)):
                if len(contour0) == 0 or len(contour0) != len(contour1):
                    # We already reported this; or nothing to do; or not compatible
                    # after reordering above.
                    continue

                # Walk the contour, keeping track of three consecutive points, with
                # middle one being an on-curve. If the three are co-linear then
                # check for kinky-ness.
                for i in range(len(contour0)):
                    pt0 = contour0[i]
                    pt1 = contour1[i]
                    if not pt0[1] or not pt1[1]:
                        # Skip off-curves
                        continue
                    pt0_prev = contour0[i - 1]
                    pt1_prev = contour1[i - 1]
                    pt0_next = contour0[(i + 1) % len(contour0)]
                    pt1_next = contour1[(i + 1) % len(contour1)]

                    if pt0_prev[1] and pt1_prev[1]:
                        # At least one off-curve is required
                        continue
                    if pt0_prev[1] and pt1_prev[1]:
                        # At least one off-curve is required
                        continue

                    pt0 = complex(*pt0[0])
                    pt1 = complex(*pt1[0])
                    pt0_prev = complex(*pt0_prev[0])
                    pt1_prev = complex(*pt1_prev[0])
                    pt0_next = complex(*pt0_next[0])
                    pt1_next = complex(*pt1_next[0])

                    # We have three consecutive points. Check whether
                    # they are colinear.
                    d0_prev = pt0 - pt0_prev
                    d0_next = pt0_next - pt0
                    d1_prev = pt1 - pt1_prev
                    d1_next = pt1_next - pt1

                    sin0 = d0_prev.real * d0_next.imag - d0_prev.imag * d0_next.real
                    sin1 = d1_prev.real * d1_next.imag - d1_prev.imag * d1_next.real
                    try:
                        sin0 /= abs(d0_prev) * abs(d0_next)
                        sin1 /= abs(d1_prev) * abs(d1_next)
                    except ZeroDivisionError:
                        continue

                    if abs(sin0) > t or abs(sin1) > t:
                        # Not colinear / not smooth.
                        continue

                    # Check the mid-point is actually, well, in the middle.
                    dot0 = d0_prev.real * d0_next.real + d0_prev.imag * d0_next.imag
                    dot1 = d1_prev.real * d1_next.real + d1_prev.imag * d1_next.imag
                    if dot0 < 0 or dot1 < 0:
                        # Sharp corner.
                        continue

                    # Fine, if handle ratios are similar...
                    r0 = abs(d0_prev) / (abs(d0_prev) + abs(d0_next))
                    r1 = abs(d1_prev) / (abs(d1_prev) + abs(d1_next))
                    r_diff = abs(r0 - r1)
                    if abs(r_diff) < t:
                        # Smooth enough.
                        continue

                    mid = (pt0 + pt1) / 2
                    mid_prev = (pt0_prev + pt1_prev) / 2
                    mid_next = (pt0_next + pt1_next) / 2

                    mid_d0 = mid - mid_prev
                    mid_d1 = mid_next - mid

                    sin_mid = mid_d0.real * mid_d1.imag - mid_d0.imag * mid_d1.real
                    try:
                        sin_mid /= abs(mid_d0) * abs(mid_d1)
                    except ZeroDivisionError:
                        continue

                    # ...or if the angles are similar.
                    if abs(sin_mid) * (tolerance * kinkiness) <= t:
                        # Smooth enough.
                        continue

                    # How visible is the kink?

                    cross = sin_mid * abs(mid_d0) * abs(mid_d1)
                    arc_len = abs(mid_d0 + mid_d1)
                    deviation = abs(cross / arc_len)
                    if deviation < deviation_threshold:
                        continue
                    deviation_ratio = deviation / arc_len
                    if deviation_ratio > t:
                        continue

                    this_tolerance = t / (abs(sin_mid) * kinkiness)

                    log.debug(
                        "deviation %g; deviation_ratio %g; sin_mid %g; r_diff %g",
                        deviation,
                        deviation_ratio,
                        sin_mid,
                        r_diff,
                    )
                    log.debug("tolerance %g", this_tolerance)
                    yield (
                        glyph_name,
                        {
                            "type": "kink",
                            "contour": ix,
                            "master_1": names[m0idx],
                            "master_2": names[m1idx],
                            "master_1_idx": m0idx,
                            "master_2_idx": m1idx,
                            "value": i,
                            "tolerance": this_tolerance,
                        },
                    )

            #
            # --show-all
            #

            if show_all:
                yield (
                    glyph_name,
                    {
                        "type": "nothing",
                        "master_1": names[m0idx],
                        "master_2": names[m1idx],
                        "master_1_idx": m0idx,
                        "master_2_idx": m1idx,
                    },
                )


@wraps(test_gen)
def test(*args, **kwargs):
    problems = defaultdict(list)
    for glyphname, problem in test_gen(*args, **kwargs):
        problems[glyphname].append(problem)
    return problems


def recursivelyAddGlyph(glyphname, glyphset, ttGlyphSet, glyf):
    if glyphname in glyphset:
        return
    glyphset[glyphname] = ttGlyphSet[glyphname]

    for component in getattr(glyf[glyphname], "components", []):
        recursivelyAddGlyph(component.glyphName, glyphset, ttGlyphSet, glyf)


def main(args=None):
    """Test for interpolatability issues between fonts"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        "fonttools varLib.interpolatable",
        description=main.__doc__,
    )
    parser.add_argument(
        "--glyphs",
        action="store",
        help="Space-separate name of glyphs to check",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all glyph pairs, even if no problems are found",
    )
    parser.add_argument(
        "--tolerance",
        action="store",
        type=float,
        help="Error tolerance. Between 0 and 1. Default %s" % DEFAULT_TOLERANCE,
    )
    parser.add_argument(
        "--kinkiness",
        action="store",
        type=float,
        help="How aggressively report kinks. Default %s" % DEFAULT_KINKINESS,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report in JSON format",
    )
    parser.add_argument(
        "--pdf",
        action="store",
        help="Output report in PDF format",
    )
    parser.add_argument(
        "--ps",
        action="store",
        help="Output report in PostScript format",
    )
    parser.add_argument(
        "--html",
        action="store",
        help="Output report in HTML format",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only exit with code 1 or 0, no output",
    )
    parser.add_argument(
        "--output",
        action="store",
        help="Output file for the problem report; Default: stdout",
    )
    parser.add_argument(
        "--ignore-missing",
        action="store_true",
        help="Will not report glyphs missing from sparse masters as errors",
    )
    parser.add_argument(
        "inputs",
        metavar="FILE",
        type=str,
        nargs="+",
        help="Input a single variable font / DesignSpace / Glyphs file, or multiple TTF/UFO files",
    )
    parser.add_argument(
        "--name",
        metavar="NAME",
        type=str,
        action="append",
        help="Name of the master to use in the report. If not provided, all are used.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Run verbosely.")
    parser.add_argument("--debug", action="store_true", help="Run with debug output.")

    args = parser.parse_args(args)

    from fontTools import configLogger

    configLogger(level=("INFO" if args.verbose else "ERROR"))
    if args.debug:
        configLogger(level="DEBUG")

    glyphs = args.glyphs.split() if args.glyphs else None

    from os.path import basename

    fonts = []
    names = []
    locations = []
    upem = DEFAULT_UPEM

    original_args_inputs = tuple(args.inputs)

    if len(args.inputs) == 1:
        designspace = None
        if args.inputs[0].endswith(".designspace"):
            from fontTools.designspaceLib import DesignSpaceDocument

            designspace = DesignSpaceDocument.fromfile(args.inputs[0])
            args.inputs = [master.path for master in designspace.sources]
            locations = [master.location for master in designspace.sources]
            axis_triples = {
                a.name: (a.minimum, a.default, a.maximum) for a in designspace.axes
            }
            axis_mappings = {a.name: a.map for a in designspace.axes}
            axis_triples = {
                k: tuple(piecewiseLinearMap(v, dict(axis_mappings[k])) for v in vv)
                for k, vv in axis_triples.items()
            }

        elif args.inputs[0].endswith(".glyphs"):
            from glyphsLib import GSFont, to_designspace

            gsfont = GSFont(args.inputs[0])
            upem = gsfont.upm
            designspace = to_designspace(gsfont)
            fonts = [source.font for source in designspace.sources]
            names = ["%s-%s" % (f.info.familyName, f.info.styleName) for f in fonts]
            args.inputs = []
            locations = [master.location for master in designspace.sources]
            axis_triples = {
                a.name: (a.minimum, a.default, a.maximum) for a in designspace.axes
            }
            axis_mappings = {a.name: a.map for a in designspace.axes}
            axis_triples = {
                k: tuple(piecewiseLinearMap(v, dict(axis_mappings[k])) for v in vv)
                for k, vv in axis_triples.items()
            }

        elif args.inputs[0].endswith(".ttf"):
            from fontTools.ttLib import TTFont

            font = TTFont(args.inputs[0])
            upem = font["head"].unitsPerEm
            if "gvar" in font:
                # Is variable font

                axisMapping = {}
                fvar = font["fvar"]
                for axis in fvar.axes:
                    axisMapping[axis.axisTag] = {
                        -1: axis.minValue,
                        0: axis.defaultValue,
                        1: axis.maxValue,
                    }
                if "avar" in font:
                    avar = font["avar"]
                    for axisTag, segments in avar.segments.items():
                        fvarMapping = axisMapping[axisTag].copy()
                        for location, value in segments.items():
                            axisMapping[axisTag][value] = piecewiseLinearMap(
                                location, fvarMapping
                            )

                gvar = font["gvar"]
                glyf = font["glyf"]
                # Gather all glyphs at their "master" locations
                ttGlyphSets = {}
                glyphsets = defaultdict(dict)

                if glyphs is None:
                    glyphs = sorted(gvar.variations.keys())
                for glyphname in glyphs:
                    for var in gvar.variations[glyphname]:
                        locDict = {}
                        loc = []
                        for tag, val in sorted(var.axes.items()):
                            locDict[tag] = val[1]
                            loc.append((tag, val[1]))

                        locTuple = tuple(loc)
                        if locTuple not in ttGlyphSets:
                            ttGlyphSets[locTuple] = font.getGlyphSet(
                                location=locDict, normalized=True, recalcBounds=False
                            )

                        recursivelyAddGlyph(
                            glyphname, glyphsets[locTuple], ttGlyphSets[locTuple], glyf
                        )

                names = ["''"]
                fonts = [font.getGlyphSet()]
                locations = [{}]
                axis_triples = {a: (-1, 0, +1) for a in sorted(axisMapping.keys())}
                for locTuple in sorted(glyphsets.keys(), key=lambda v: (len(v), v)):
                    name = (
                        "'"
                        + " ".join(
                            "%s=%s"
                            % (
                                k,
                                floatToFixedToStr(
                                    piecewiseLinearMap(v, axisMapping[k]), 14
                                ),
                            )
                            for k, v in locTuple
                        )
                        + "'"
                    )
                    names.append(name)
                    fonts.append(glyphsets[locTuple])
                    locations.append(dict(locTuple))
                args.ignore_missing = True
                args.inputs = []

    if not locations:
        locations = [{} for _ in fonts]

    for filename in args.inputs:
        if filename.endswith(".ufo"):
            from fontTools.ufoLib import UFOReader

            font = UFOReader(filename)
            info = SimpleNamespace()
            font.readInfo(info)
            upem = info.unitsPerEm
            fonts.append(font)
        else:
            from fontTools.ttLib import TTFont

            font = TTFont(filename)
            upem = font["head"].unitsPerEm
            fonts.append(font)

        names.append(basename(filename).rsplit(".", 1)[0])

    glyphsets = []
    for font in fonts:
        if hasattr(font, "getGlyphSet"):
            glyphset = font.getGlyphSet()
        else:
            glyphset = font
        glyphsets.append({k: glyphset[k] for k in glyphset.keys()})

    if args.name:
        accepted_names = set(args.name)
        glyphsets = [
            glyphset
            for name, glyphset in zip(names, glyphsets)
            if name in accepted_names
        ]
        locations = [
            location
            for name, location in zip(names, locations)
            if name in accepted_names
        ]
        names = [name for name in names if name in accepted_names]

    if not glyphs:
        glyphs = sorted(set([gn for glyphset in glyphsets for gn in glyphset.keys()]))

    glyphsSet = set(glyphs)
    for glyphset in glyphsets:
        glyphSetGlyphNames = set(glyphset.keys())
        diff = glyphsSet - glyphSetGlyphNames
        if diff:
            for gn in diff:
                glyphset[gn] = None

    # Normalize locations
    locations = [normalizeLocation(loc, axis_triples) for loc in locations]
    tolerance = args.tolerance or DEFAULT_TOLERANCE
    kinkiness = args.kinkiness if args.kinkiness is not None else DEFAULT_KINKINESS

    try:
        log.info("Running on %d glyphsets", len(glyphsets))
        log.info("Locations: %s", pformat(locations))
        problems_gen = test_gen(
            glyphsets,
            glyphs=glyphs,
            names=names,
            locations=locations,
            upem=upem,
            ignore_missing=args.ignore_missing,
            tolerance=tolerance,
            kinkiness=kinkiness,
            show_all=args.show_all,
        )
        problems = defaultdict(list)

        f = sys.stdout if args.output is None else open(args.output, "w")

        if not args.quiet:
            if args.json:
                import json

                for glyphname, problem in problems_gen:
                    problems[glyphname].append(problem)

                print(json.dumps(problems), file=f)
            else:
                last_glyphname = None
                for glyphname, p in problems_gen:
                    problems[glyphname].append(p)

                    if glyphname != last_glyphname:
                        print(f"Glyph {glyphname} was not compatible:", file=f)
                        last_glyphname = glyphname
                        last_master_idxs = None

                    master_idxs = (
                        (p["master_idx"])
                        if "master_idx" in p
                        else (p["master_1_idx"], p["master_2_idx"])
                    )
                    if master_idxs != last_master_idxs:
                        master_names = (
                            (p["master"])
                            if "master" in p
                            else (p["master_1"], p["master_2"])
                        )
                        print(f"  Masters: %s:" % ", ".join(master_names), file=f)
                        last_master_idxs = master_idxs

                    if p["type"] == "missing":
                        print(
                            "    Glyph was missing in master %s" % p["master"], file=f
                        )
                    elif p["type"] == "open_path":
                        print(
                            "    Glyph has an open path in master %s" % p["master"],
                            file=f,
                        )
                    elif p["type"] == "path_count":
                        print(
                            "    Path count differs: %i in %s, %i in %s"
                            % (
                                p["value_1"],
                                p["master_1"],
                                p["value_2"],
                                p["master_2"],
                            ),
                            file=f,
                        )
                    elif p["type"] == "node_count":
                        print(
                            "    Node count differs in path %i: %i in %s, %i in %s"
                            % (
                                p["path"],
                                p["value_1"],
                                p["master_1"],
                                p["value_2"],
                                p["master_2"],
                            ),
                            file=f,
                        )
                    elif p["type"] == "node_incompatibility":
                        print(
                            "    Node %o incompatible in path %i: %s in %s, %s in %s"
                            % (
                                p["node"],
                                p["path"],
                                p["value_1"],
                                p["master_1"],
                                p["value_2"],
                                p["master_2"],
                            ),
                            file=f,
                        )
                    elif p["type"] == "contour_order":
                        print(
                            "    Contour order differs: %s in %s, %s in %s"
                            % (
                                p["value_1"],
                                p["master_1"],
                                p["value_2"],
                                p["master_2"],
                            ),
                            file=f,
                        )
                    elif p["type"] == "wrong_start_point":
                        print(
                            "    Contour %d start point differs: %s in %s, %s in %s; reversed: %s"
                            % (
                                p["contour"],
                                p["value_1"],
                                p["master_1"],
                                p["value_2"],
                                p["master_2"],
                                p["reversed"],
                            ),
                            file=f,
                        )
                    elif p["type"] == "underweight":
                        print(
                            "    Contour %d interpolation is underweight: %s, %s"
                            % (
                                p["contour"],
                                p["master_1"],
                                p["master_2"],
                            ),
                            file=f,
                        )
                    elif p["type"] == "overweight":
                        print(
                            "    Contour %d interpolation is overweight: %s, %s"
                            % (
                                p["contour"],
                                p["master_1"],
                                p["master_2"],
                            ),
                            file=f,
                        )
                    elif p["type"] == "kink":
                        print(
                            "    Contour %d has a kink at %s: %s, %s"
                            % (
                                p["contour"],
                                p["value"],
                                p["master_1"],
                                p["master_2"],
                            ),
                            file=f,
                        )
                    elif p["type"] == "nothing":
                        print(
                            "    Showing %s and %s"
                            % (
                                p["master_1"],
                                p["master_2"],
                            ),
                            file=f,
                        )
        else:
            for glyphname, problem in problems_gen:
                problems[glyphname].append(problem)

        if args.pdf:
            log.info("Writing PDF to %s", args.pdf)
            from .interpolatablePlot import InterpolatablePDF

            with InterpolatablePDF(args.pdf, glyphsets=glyphsets, names=names) as pdf:
                pdf.add_title_page(
                    original_args_inputs, tolerance=tolerance, kinkiness=kinkiness
                )
                pdf.add_problems(problems)
                if not problems and not args.quiet:
                    pdf.draw_cupcake()

        if args.ps:
            log.info("Writing PS to %s", args.pdf)
            from .interpolatablePlot import InterpolatablePS

            with InterpolatablePS(args.ps, glyphsets=glyphsets, names=names) as ps:
                ps.add_title_page(
                    original_args_inputs, tolerance=tolerance, kinkiness=kinkiness
                )
                ps.add_problems(problems)
                if not problems and not args.quiet:
                    ps.draw_cupcake()

        if args.html:
            log.info("Writing HTML to %s", args.html)
            from .interpolatablePlot import InterpolatableSVG

            svgs = []
            glyph_starts = {}
            with InterpolatableSVG(svgs, glyphsets=glyphsets, names=names) as svg:
                svg.add_title_page(
                    original_args_inputs,
                    show_tolerance=False,
                    tolerance=tolerance,
                    kinkiness=kinkiness,
                )
                for glyph, glyph_problems in problems.items():
                    glyph_starts[len(svgs)] = glyph
                    svg.add_problems(
                        {glyph: glyph_problems},
                        show_tolerance=False,
                        show_page_number=False,
                    )
                if not problems and not args.quiet:
                    svg.draw_cupcake()

            import base64

            with open(args.html, "wb") as f:
                f.write(b"<!DOCTYPE html>\n")
                f.write(
                    b'<html><body align="center" style="font-family: sans-serif; text-color: #222">\n'
                )
                f.write(b"<title>fonttools varLib.interpolatable report</title>\n")
                for i, svg in enumerate(svgs):
                    if i in glyph_starts:
                        f.write(f"<h1>Glyph {glyph_starts[i]}</h1>\n".encode("utf-8"))
                    f.write("<img src='data:image/svg+xml;base64,".encode("utf-8"))
                    f.write(base64.b64encode(svg))
                    f.write(b"' />\n")
                    f.write(b"<hr>\n")
                f.write(b"</body></html>\n")

    except Exception as e:
        e.args += original_args_inputs
        log.error(e)
        raise

    if problems:
        return problems


if __name__ == "__main__":
    import sys

    problems = main()
    sys.exit(int(bool(problems)))
