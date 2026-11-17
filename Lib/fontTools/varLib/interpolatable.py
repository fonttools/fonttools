"""
Tool to find wrong contour order between different masters, and
other interpolatability (or lack thereof) issues.

Call as:
$ fonttools varLib.interpolatable font1 font2 ...
"""

from .interpolatableHelpers import *
from .interpolatableTestContourOrder import test_contour_order
from .interpolatableTestStartingPoint import test_starting_point
from fontTools.pens.recordingPen import (
    RecordingPen,
    DecomposingRecordingPen,
    lerpRecordings,
    replayRecording,
)
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.statisticsPen import StatisticsPen, StatisticsControlPen
from fontTools.varLib.models import piecewiseLinearMap, normalizeLocation
from fontTools.misc.fixedTools import floatToFixedToStr
from fontTools.misc.lazyTools import LazyList
from fontTools.misc.transform import Transform
from collections import defaultdict
from types import SimpleNamespace
from functools import wraps
from pprint import pformat
from math import sqrt, copysign, atan2, pi
import logging
import os

log = logging.getLogger("fontTools.varLib.interpolatable")

DEFAULT_TOLERANCE = 0.95
DEFAULT_KINKINESS = 0.5
DEFAULT_KINKINESS_LENGTH = 0.002  # ratio of UPEM
DEFAULT_UPEM = 1000


def _with_progress(items, progressFunc):
    for item in items:
        yield item
        if progressFunc is not None:
            progressFunc(item)


def _make_progress(label, total, enabled):
    import sys
    from time import monotonic

    if not enabled or not total or not sys.stderr.isatty():
        return None
    stream = sys.stderr
    done = 0
    last_update = monotonic()

    def draw():
        filled = 20 * done // total
        bar = "#" * filled + "-" * (20 - filled)
        print(
            f"\r{label}: [{bar}] {done}/{total}",
            end="\n" if done == total else "",
            file=stream,
            flush=True,
        )

    def advance(glyph_name):
        nonlocal done, last_update
        done += 1
        now = monotonic()
        if done == total or now - last_update >= 0.1:
            draw()
            last_update = now

    draw()
    return advance


def _record_glyph(glyph, glyphset):
    pen = PerContourOrComponentPen(RecordingPen, glyphset=glyphset)
    try:
        glyph.draw(pen, outputImpliedClosingLine=True)
    except TypeError:
        glyph.draw(pen)
    return pen.value


def _contour_area(recording, glyphset=None):
    pen = AreaPen(glyphset)
    try:
        replayRecording(recording, pen)
    except (ValueError, NotImplementedError):
        return None
    return pen.value


def _contour_isomorphisms(points):
    isomorphisms = []
    add_isomorphisms(points, isomorphisms, False)
    add_isomorphisms(points, isomorphisms, True)
    return isomorphisms


def _underweight_tolerance(area0, area1, mid_area, tolerance):
    if area0 * area1 <= 0:
        return 1
    expected = sqrt(abs(area0) * abs(area1))
    # Preserve the endpoints' winding: a reversed midpoint has crossed zero
    # area, even if its absolute area has grown again.
    mid_area = copysign(1, area0) * mid_area
    log.debug(
        "underweight: midpoint area %g; threshold %g, endpoint areas %g, %g",
        mid_area,
        expected * tolerance,
        area0,
        area1,
    )
    if expected * tolerance <= mid_area + 1e-5:
        return 1
    return max(0, mid_area / expected)


def _kink_tolerance(d0, d1, tolerance, kinkiness, upem):
    if not kinkiness:
        return 1
    t = 0.1
    length0, length1 = abs(d0), abs(d1)
    arc_len = abs(d0 + d1)
    if not length0 or not length1 or not arc_len:
        return 1
    cross = d0.real * d1.imag - d0.imag * d1.real
    sin_mid = cross / (length0 * length1)
    if abs(sin_mid) * tolerance * kinkiness <= t:
        return 1
    deviation = abs(cross) / arc_len
    deviation_threshold = (
        upem * DEFAULT_KINKINESS_LENGTH * DEFAULT_KINKINESS / kinkiness
    )
    if deviation < deviation_threshold or deviation / arc_len > t:
        return 1
    log.debug(
        "kink: deviation %g; deviation_ratio %g; sin_mid %g",
        deviation,
        deviation / arc_len,
        sin_mid,
    )
    return t / (abs(sin_mid) * kinkiness)


class Glyph:
    ITEMS = (
        "recordings",
        "areas",
        "greenStats",
        "controlStats",
        "greenVectors",
        "controlVectors",
        "nodeTypes",
        "isomorphisms",
        "points",
        "openContours",
    )
    LAZY_ITEMS = (
        "greenStats",
        "controlStats",
        "greenVectors",
        "controlVectors",
        "isomorphisms",
    )

    def __init__(self, glyphname, glyphset):
        self.name = glyphname
        for item in self.ITEMS:
            setattr(self, item, LazyList() if item in self.LAZY_ITEMS else [])
        self._populate(glyphset)

    def _fill_in(self, ix):
        for item in self.ITEMS:
            if len(getattr(self, item)) == ix:
                getattr(self, item).append(None)

    def _populate(self, glyphset):
        glyph = glyphset[self.name]
        self.doesnt_exist = glyph is None
        if self.doesnt_exist:
            return

        self.recordings = _record_glyph(glyph, glyphset)

        def statistics(penClass, contour):
            pen = penClass(glyphset=glyphset)
            contour.replay(pen)
            return pen

        for ix, contour in enumerate(self.recordings):
            nodeTypes = [op for op, arg in contour.value]
            self.nodeTypes.append(nodeTypes)

            stats_contour = contour
            try:
                if nodeTypes[0] == "addComponent":
                    # Reuse the expanded outline for area and both statistics pens.
                    stats_contour = DecomposingRecordingPen(
                        glyphset, skipMissingComponents=True
                    )
                    contour.replay(stats_contour)
                area = _contour_area(stats_contour.value, glyphset)
            except (ValueError, NotImplementedError):
                area = None
            if area is None:
                self.openContours.append(True)
                self._fill_in(ix)
                continue
            self.openContours.append(False)
            self.areas.append(area)
            self.greenStats.append(
                lambda _, c=stats_contour: statistics(StatisticsPen, c)
            )
            self.controlStats.append(
                lambda _, c=stats_contour: statistics(StatisticsControlPen, c)
            )
            self.greenVectors.append(
                lambda _, i=ix, stats=self.greenStats: contour_vector_from_stats(
                    stats[i]
                )
            )
            self.controlVectors.append(
                lambda _, i=ix, stats=self.controlStats: contour_vector_from_stats(
                    stats[i]
                )
            )

            # Check starting point
            if nodeTypes[0] == "addComponent":
                self._fill_in(ix)
                continue

            assert nodeTypes[0] == "moveTo"
            assert nodeTypes[-1] in ("closePath", "endPath")
            points = SimpleRecordingPointPen()
            converter = SegmentToPointPen(points, False)
            contour.replay(converter)
            # points.value is a list of pt,bool where bool is true if on-curve and false if off-curve;
            # now check all rotations and mirror-rotations of the contour and build list of isomorphic
            # possible starting points.
            self.points.append(points.value)

            self.isomorphisms.append(
                lambda _, points=points.value: _contour_isomorphisms(points)
            )

    def draw(self, pen, contour_idx=None):
        if contour_idx is None:
            for contour in self.recordings:
                contour.draw(pen)
        else:
            self.recordings[contour_idx].draw(pen)


def test_gen(
    glyphsets,
    glyphs=None,
    names=None,
    ignore_missing=False,
    *,
    locations=None,
    sparse=None,
    tolerance=DEFAULT_TOLERANCE,
    kinkiness=DEFAULT_KINKINESS,
    upem=DEFAULT_UPEM,
    show_all=False,
    discrete_axes=[],
    progressFunc=None,
    midpointFunc=None,
    _parents_and_order=None,
):
    """Yield interpolation problems, calling progressFunc after each glyph.

    The optional callback receives the completed glyph's name.
    midpointFunc, when provided with locations, returns a glyphset at a
    normalized location to confirm candidate kink and underweight findings.
    """
    if tolerance >= 10:
        tolerance *= 0.01
    assert 0 <= tolerance <= 1
    if kinkiness >= 10:
        kinkiness *= 0.01
    assert 0 <= kinkiness
    if midpointFunc is not None and not locations:
        raise ValueError("midpointFunc requires master locations")

    names = names or [repr(g) for g in glyphsets]
    if sparse is None:
        sparse = [False] * len(glyphsets)

    if glyphs is None:
        # `glyphs = glyphsets[0].keys()` is faster, certainly, but doesn't allow for sparse TTFs/OTFs given out of order
        # ... risks the sparse master being the first one, and only processing a subset of the glyphs
        glyphs = {g for glyphset in glyphsets for g in glyphset.keys()}

    parents, order = _parents_and_order or find_parents_and_order(
        glyphsets, locations, discrete_axes=discrete_axes
    )

    def grand_parent(i, allGlyphs):
        if i is None:
            return None
        i = parents[i]
        if i is None:
            return None
        # Missing and empty glyphs are both skipped by the pair comparisons.
        # Walk past either kind of intermediate to reach a usable ancestor.
        while parents[i] is not None and not allGlyphs[i].nodeTypes:
            i = parents[i]
        return i

    for glyph_name in _with_progress(glyphs, progressFunc):
        log.info("Testing glyph %s", glyph_name)
        allGlyphs = [Glyph(glyph_name, glyphset) for glyphset in glyphsets]
        if len([1 for glyph in allGlyphs if not glyph.doesnt_exist]) <= 1:
            continue
        for master_idx, glyph in enumerate(allGlyphs):
            if glyph.doesnt_exist:
                if not ignore_missing and not sparse[master_idx]:
                    yield (
                        glyph_name,
                        {
                            "type": InterpolatableProblem.MISSING,
                            "master": names[master_idx],
                            "master_idx": master_idx,
                        },
                    )
                continue

            has_open = False
            for ix, open in enumerate(glyph.openContours):
                if not open:
                    continue
                has_open = True
                yield (
                    glyph_name,
                    {
                        "type": InterpolatableProblem.OPEN_PATH,
                        "master": names[master_idx],
                        "master_idx": master_idx,
                        "contour": ix,
                    },
                )
            if has_open:
                continue

        matchings = [None] * len(glyphsets)
        midpoints = {}
        midpoint_points = {}

        def actual_midpoint_contour(m0idx, m1idx, ix, node_types):
            if midpointFunc is None:
                return None
            key = (m0idx, m1idx)
            if key not in midpoints:
                loc0, loc1 = locations[m0idx], locations[m1idx]
                location = {
                    k: (loc0.get(k, 0) + loc1.get(k, 0)) / 2
                    for k in loc0.keys() | loc1.keys()
                }
                glyphset = midpointFunc(location)
                glyph = glyphset.get(glyph_name)
                midpoints[key] = (
                    _record_glyph(glyph, glyphset) if glyph is not None else []
                )
            contours = midpoints[key]
            if len(contours) != len(allGlyphs[m0idx].recordings):
                return None
            contour = contours[ix]
            if [op for op, _ in contour.value] != node_types:
                return None
            return contour

        for m1idx in order:
            glyph1 = allGlyphs[m1idx]
            if glyph1 is None or not glyph1.nodeTypes:
                continue
            m0idx = grand_parent(m1idx, allGlyphs)
            if m0idx is None:
                continue
            glyph0 = allGlyphs[m0idx]
            if glyph0 is None or not glyph0.nodeTypes:
                continue

            #
            # Basic compatibility checks
            #

            m0 = glyph0.nodeTypes
            m1 = glyph1.nodeTypes
            if len(m0) != len(m1):
                yield (
                    glyph_name,
                    {
                        "type": InterpolatableProblem.PATH_COUNT,
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
                                "type": InterpolatableProblem.NODE_COUNT,
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
                                    "type": InterpolatableProblem.NODE_INCOMPATIBILITY,
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
            # InterpolatableProblem.CONTOUR_ORDER check
            #

            this_tolerance, matching = test_contour_order(glyph0, glyph1)
            if this_tolerance < tolerance:
                yield (
                    glyph_name,
                    {
                        "type": InterpolatableProblem.CONTOUR_ORDER,
                        "master_1": names[m0idx],
                        "master_2": names[m1idx],
                        "master_1_idx": m0idx,
                        "master_2_idx": m1idx,
                        "value_1": list(range(len(matching))),
                        "value_2": matching,
                        "tolerance": this_tolerance,
                    },
                )
                matchings[m1idx] = matching

            #
            # wrong-start-point / weight check
            #

            m0Isomorphisms = glyph0.isomorphisms
            m1Isomorphisms = glyph1.isomorphisms
            recording0 = glyph0.recordings
            recording1 = glyph1.recordings

            # If contour-order is wrong, adjust it
            matching = matchings[m1idx]
            if (
                matching is not None and m1Isomorphisms
            ):  # m1 is empty for composite glyphs
                m1Isomorphisms = [m1Isomorphisms[i] for i in matching]
                recording1 = [recording1[i] for i in matching]

            for ix, (contour0, contour1) in enumerate(
                zip(m0Isomorphisms, m1Isomorphisms)
            ):
                if (
                    contour0 is None
                    or contour1 is None
                    or len(contour0) == 0
                    or len(contour0) != len(contour1)
                ):
                    # We already reported this; or nothing to do; or not compatible
                    # after reordering above.
                    continue

                this_tolerance, proposed_point, reverse = test_starting_point(
                    glyph0, glyph1, ix, tolerance, matching
                )

                if this_tolerance < tolerance:
                    yield (
                        glyph_name,
                        {
                            "type": InterpolatableProblem.WRONG_START_POINT,
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

                # A geometric-mean area baseline tolerates ordinary scaling.
                # Opposite endpoint windings can be self-intersections; skip.
                area0 = glyph0.areas[ix]
                area1 = glyph1.areas[ix if matching is None else matching[ix]]
                if area0 * area1 <= 0:
                    continue
                mid_area = _contour_area(
                    lerpRecordings(recording0[ix].value, recording1[ix].value)
                )
                if mid_area is None:
                    continue
                this_tolerance = _underweight_tolerance(
                    area0, area1, mid_area, tolerance
                )
                if this_tolerance >= tolerance:
                    continue
                verified = False
                actual = actual_midpoint_contour(m0idx, m1idx, ix, glyph0.nodeTypes[ix])
                if actual is not None:
                    actual_area = _contour_area(actual.value)
                    if actual_area is not None:
                        verified = True
                        this_tolerance = _underweight_tolerance(
                            area0, area1, actual_area, tolerance
                        )
                        if this_tolerance >= tolerance:
                            continue
                yield (
                    glyph_name,
                    {
                        "type": InterpolatableProblem.UNDERWEIGHT,
                        "contour": ix,
                        "master_1": names[m0idx],
                        "master_2": names[m1idx],
                        "master_1_idx": m0idx,
                        "master_2_idx": m1idx,
                        "tolerance": this_tolerance,
                        **({"actual_midpoint": True} if verified else {}),
                    },
                )

            #
            # "kink" detector
            #
            m0 = glyph0.points
            m1 = glyph1.points

            # If contour-order is wrong, adjust it
            if matchings[m1idx] is not None and m1:  # m1 is empty for composite glyphs
                m1 = [m1[i] for i in matchings[m1idx]]

            t = 0.1  # ~sin(radian(6)) for tolerance 0.95

            for ix, (contour0, contour1) in enumerate(zip(m0, m1)):
                if (
                    contour0 is None
                    or contour1 is None
                    or len(contour0) == 0
                    or len(contour0) != len(contour1)
                ):
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
                    if pt0_next[1] and pt1_next[1]:
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

                    this_tolerance = _kink_tolerance(
                        mid_d0, mid_d1, tolerance, kinkiness, upem
                    )
                    if this_tolerance >= tolerance:
                        continue
                    verified = False
                    actual = actual_midpoint_contour(
                        m0idx, m1idx, ix, glyph0.nodeTypes[ix]
                    )
                    if actual is not None:
                        if actual not in midpoint_points:
                            points = SimpleRecordingPointPen()
                            actual.replay(SegmentToPointPen(points, False))
                            same_points = len(points.value) == len(contour0) and all(
                                p[1] == q[1] for p, q in zip(points.value, contour0)
                            )
                            midpoint_points[actual] = (
                                points.value if same_points else None
                            )
                        actual_points = midpoint_points[actual]
                        if actual_points is not None:
                            actual_pt = complex(*actual_points[i][0])
                            actual_prev = complex(*actual_points[i - 1][0])
                            actual_next = complex(
                                *actual_points[(i + 1) % len(actual_points)][0]
                            )
                            verified = True
                            this_tolerance = _kink_tolerance(
                                actual_pt - actual_prev,
                                actual_next - actual_pt,
                                tolerance,
                                kinkiness,
                                upem,
                            )
                            if this_tolerance >= tolerance:
                                continue
                    yield (
                        glyph_name,
                        {
                            "type": InterpolatableProblem.KINK,
                            "contour": ix,
                            "master_1": names[m0idx],
                            "master_2": names[m1idx],
                            "master_1_idx": m0idx,
                            "master_2_idx": m1idx,
                            "value": i,
                            "tolerance": this_tolerance,
                            **({"actual_midpoint": True} if verified else {}),
                        },
                    )

            #
            # --show-all
            #

            if show_all:
                yield (
                    glyph_name,
                    {
                        "type": InterpolatableProblem.NOTHING,
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


_worker_context = None


def _init_worker(context, args, parents_and_order):
    import signal

    global _worker_context
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    glyphsets, options = context if context is not None else main(args, _prepare=True)
    options = dict(options)
    options["names"] = list(range(len(glyphsets)))
    options["progressFunc"] = None
    options["_parents_and_order"] = parents_and_order
    _worker_context = glyphsets, options


def _check_batch(glyphs):
    glyphsets, options = _worker_context
    options = dict(options, glyphs=glyphs)
    return list(test_gen(glyphsets, **options))


def _parallel_test_gen(glyphsets, options, jobs, worker_args):
    from concurrent.futures import ProcessPoolExecutor, as_completed
    import multiprocessing
    import sys
    import threading

    glyphs = list(options["glyphs"])
    if not glyphs:
        return
    jobs = min(jobs, len(glyphs))
    parents_and_order = find_parents_and_order(
        glyphsets, options["locations"], discrete_axes=options["discrete_axes"]
    )
    use_fork = (
        sys.platform == "linux"
        and "fork" in multiprocessing.get_all_start_methods()
        and threading.active_count() == 1
    )
    # Fork shares the prepared glyphsets. Spawned workers load their own copy
    # once, since glyphsets and instance callbacks need not be picklable.
    mp_context = multiprocessing.get_context("fork" if use_fork else "spawn")
    context = (glyphsets, options) if use_fork else None
    batch_size = max(1, min(8, (len(glyphs) + jobs * 8 - 1) // (jobs * 8)))
    batches = [glyphs[i : i + batch_size] for i in range(0, len(glyphs), batch_size)]
    progress = options["progressFunc"]
    names = options["names"]
    with ProcessPoolExecutor(
        max_workers=jobs,
        mp_context=mp_context,
        initializer=_init_worker,
        initargs=(context, worker_args, parents_and_order),
    ) as pool:
        futures = {
            pool.submit(_check_batch, batch): i for i, batch in enumerate(batches)
        }
        pending = {}
        next_batch = 0
        try:
            for future in as_completed(futures):
                index = futures[future]
                pending[index] = future.result()
                if progress is not None:
                    for glyph in batches[index]:
                        progress(glyph)
                while next_batch in pending:
                    for glyph, problem in pending.pop(next_batch):
                        if "master_idx" in problem:
                            problem["master"] = names[problem["master_idx"]]
                        else:
                            problem["master_1"] = names[problem["master_1_idx"]]
                            problem["master_2"] = names[problem["master_2_idx"]]
                        yield glyph, problem
                    next_batch += 1
        except BaseException:
            for future in futures:
                future.cancel()
            if hasattr(pool, "terminate_workers"):
                pool.terminate_workers()
            raise


def recursivelyAddGlyph(glyphname, glyphset, ttGlyphSet, glyf):
    if glyphname in glyphset:
        return
    glyphset[glyphname] = ttGlyphSet[glyphname]

    for component in getattr(glyf[glyphname], "components", []):
        recursivelyAddGlyph(component.glyphName, glyphset, ttGlyphSet, glyf)


def ensure_parent_dir(path):
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    return path


def print_master_tree(parents, order, names, locations, discrete_axes=(), *, file=None):
    """Print the master comparison tree with normalized locations."""
    children = defaultdict(list)
    for i in order:
        children[parents[i]].append(i)
    stack = [(i, "", "") for i in reversed(children[None])]
    while stack:
        i, prefix, branch = stack.pop()
        label = f"[{i}] {names[i]}"
        if locations:
            coordinates = (
                " ".join(
                    f"{k}={v}"
                    for k, v in sorted(locations[i].items())
                    if v != 0 or k in discrete_axes
                )
                or "default"
            )
            location_label = f"normalized: {coordinates}"
            if names[i] != location_label:
                label += f" ({location_label})"
        print(prefix + branch + label, file=file)
        child_prefix = prefix + (
            "    " if branch == "└── " else "│   " if branch else ""
        )
        for j, child in reversed(list(enumerate(children[i]))):
            child_branch = "└── " if j == len(children[i]) - 1 else "├── "
            stack.append((child, child_prefix, child_branch))


def main(args=None, *, _prepare=False):
    """Test for interpolatability issues between fonts"""
    import argparse
    import sys

    argv = list(args) if args is not None else sys.argv[1:]
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
        "--show-graph",
        action="store_true",
        help="Show the resolved master comparison tree and exit",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        help="Show a progress bar when stderr is a terminal",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=1,
        help="Number of worker processes; 0 uses all available CPUs (default: 1)",
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

    args = parser.parse_args(argv)
    if args.jobs < 0:
        parser.error("--jobs must be zero or greater")
    if not args.jobs:
        cpu_count = getattr(os, "process_cpu_count", os.cpu_count)
        args.jobs = cpu_count() or 1
    if _prepare:
        args.quiet = True
        args.jobs = 1

    from fontTools import configLogger

    configLogger(level=("INFO" if args.verbose else "WARNING"))
    if args.debug:
        configLogger(level="DEBUG")

    glyphs = args.glyphs.split() if args.glyphs else None
    show_progress = args.progress and not args.quiet

    from os.path import basename

    fonts = []
    names = []
    locations = []
    location_labeler = None
    midpointFunc = None
    sparse = None
    discrete_axes = set()
    upem = DEFAULT_UPEM

    original_args_inputs = tuple(args.inputs)

    if len(args.inputs) == 1:
        designspace = None
        if args.inputs[0].endswith(".designspace"):
            from fontTools.designspaceLib import DesignSpaceDocument

            designspace = DesignSpaceDocument.fromfile(args.inputs[0])
            args.inputs = [
                (master.path, master.layerName) for master in designspace.sources
            ]
            locations = [master.location for master in designspace.sources]
            discrete_axes = {
                a.name for a in designspace.axes if not hasattr(a, "minimum")
            }
            axis_triples = {
                a.name: (a.minimum, a.default, a.maximum)
                for a in designspace.axes
                if a.name not in discrete_axes
            }
            axis_mappings = {a.name: a.map for a in designspace.axes}
            axis_triples = {
                k: tuple(piecewiseLinearMap(v, dict(axis_mappings[k])) for v in vv)
                for k, vv in axis_triples.items()
            }
            # Any non-default Designspace source can omit glyphs, even when
            # it uses a separate UFO's default layer. Each discrete subspace
            # has its own default at the continuous axes' default location.
            sparse = [
                any(
                    loc.get(k, triple[1]) != triple[1]
                    for k, triple in axis_triples.items()
                )
                for loc in locations
            ]

        elif args.inputs[0].endswith((".glyphs", ".glyphspackage")):
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

        elif args.inputs[0].endswith(".ttf") or args.inputs[0].endswith(".otf"):
            from fontTools.ttLib import TTFont

            # Is variable font?

            font = TTFont(args.inputs[0])
            upem = font["head"].unitsPerEm

            fvar = font["fvar"]
            axisMapping = {}
            for axis in fvar.axes:
                axisMapping[axis.axisTag] = {
                    -1: axis.minValue,
                    0: axis.defaultValue,
                    1: axis.maxValue,
                }
            normalized = False
            if "avar" in font:
                avar = font["avar"]
                if getattr(avar.table, "VarStore", None):
                    axisMapping = {tag: {-1: -1, 0: 0, 1: 1} for tag in axisMapping}
                    normalized = True
                else:
                    for axisTag, segments in avar.segments.items():
                        fvarMapping = axisMapping[axisTag].copy()
                        for location, value in segments.items():
                            axisMapping[axisTag][value] = piecewiseLinearMap(
                                location, fvarMapping
                            )

            location_labeler = LocationLabeler(axisMapping, font=font)

            def midpointFunc(location, font=font):
                return font.getGlyphSet(
                    location=location, normalized=True, recalcBounds=False
                )

            # Gather all glyphs at their "master" locations
            ttGlyphSets = {}
            glyphsets = defaultdict(dict)

            if "gvar" in font or "GVAR" in font:
                gvarTag = "GVAR" if "GVAR" in font else "gvar"
                glyfTag = "GLYF" if gvarTag == "GVAR" else "glyf"
                gvar = font[gvarTag]
                glyf = font[glyfTag]

                if glyphs is None:
                    glyphs = sorted(gvar.variations.keys())
                progress = _make_progress("Finding masters", len(glyphs), show_progress)
                for glyphname in _with_progress(glyphs, progress):
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

            elif "CFF2" in font:
                fvarAxes = font["fvar"].axes
                cff2 = font["CFF2"].cff.topDictIndex[0]
                charstrings = cff2.CharStrings

                if glyphs is None:
                    glyphs = sorted(charstrings.keys())
                progress = _make_progress("Finding masters", len(glyphs), show_progress)
                for glyphname in _with_progress(glyphs, progress):
                    cs = charstrings[glyphname]
                    private = cs.private

                    # Extract vsindex for the glyph
                    vsindices = {getattr(private, "vsindex", 0)}
                    vsindex = getattr(private, "vsindex", 0)
                    last_op = 0
                    # The spec says vsindex can only appear once and must be the first
                    # operator in the charstring, but we support multiple.
                    # https://github.com/harfbuzz/boring-expansion-spec/issues/158
                    for op in cs.program:
                        if op == "blend":
                            vsindices.add(vsindex)
                        elif op == "vsindex":
                            assert isinstance(last_op, int)
                            vsindex = last_op
                        last_op = op

                    if not hasattr(private, "vstore"):
                        continue

                    varStore = private.vstore.otVarStore
                    for vsindex in vsindices:
                        varData = varStore.VarData[vsindex]
                        for regionIndex in varData.VarRegionIndex:
                            region = varStore.VarRegionList.Region[regionIndex]

                            locDict = {}
                            loc = []
                            for axisIndex, axis in enumerate(region.VarRegionAxis):
                                tag = fvarAxes[axisIndex].axisTag
                                val = axis.PeakCoord
                                locDict[tag] = val
                                loc.append((tag, val))

                            locTuple = tuple(loc)
                            if locTuple not in ttGlyphSets:
                                ttGlyphSets[locTuple] = font.getGlyphSet(
                                    location=locDict,
                                    normalized=True,
                                    recalcBounds=False,
                                )

                            glyphset = glyphsets[locTuple]
                            glyphset[glyphname] = ttGlyphSets[locTuple][glyphname]

            def location_name(location):
                # Quiet diagnostics need only normalized names. Graphical
                # panels request input labels separately; --name filtering
                # still matches the complete names used in text/JSON output.
                return " | ".join(
                    location_labeler(
                        location,
                        include_input=(not args.quiet and not args.show_graph)
                        or bool(args.name),
                    )
                )

            names = LazyList([lambda _: location_name({})]) if normalized else ["''"]
            fonts = [font.getGlyphSet()]
            locations = [{}]
            axis_triples = {a: (-1, 0, +1) for a in sorted(axisMapping.keys())}
            for locTuple in sorted(glyphsets.keys(), key=lambda v: (len(v), v)):
                if normalized:
                    # Resolve names only for masters mentioned by a diagnostic,
                    # rather than solving every internal master before testing.
                    name = lambda _, loc=dict(locTuple): location_name(loc)
                else:
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
        layerName = None
        if isinstance(filename, tuple):
            filename, layerName = filename

        if filename.endswith(".ufo"):
            from fontTools.ufoLib import UFOReader

            font = UFOReader(filename)
            info = SimpleNamespace()
            font.readInfo(info)
            upem = info.unitsPerEm
            fonts.append(font.getGlyphSet(layerName=layerName))
        else:
            from fontTools.ttLib import TTFont

            font = TTFont(filename)
            upem = font["head"].unitsPerEm
            fonts.append(font)

        name = basename(filename).rsplit(".", 1)[0]
        if layerName is not None:
            name += " (%s)" % layerName
        names.append(name)

    if sparse is None:
        sparse = [False] * len(fonts)

    if len(fonts) < 2:
        log.warning("Font file does not seem to be variable. Nothing to check.")
        return

    glyphsets = []
    for font in fonts:
        if args.show_graph:
            glyphsets.append(None)
            continue
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
        sparse = [
            is_sparse
            for name, is_sparse in zip(names, sparse)
            if name in accepted_names
        ]
        names = [name for name in names if name in accepted_names]

    # Normalize locations
    locations = [
        {
            **normalizeLocation(loc, axis_triples, allow_decreasing=True),
            **{k: v for k, v in loc.items() if k in discrete_axes},
        }
        for loc in locations
    ]
    if args.show_graph:
        parents, order = find_parents_and_order(
            glyphsets, locations, discrete_axes=discrete_axes
        )
        if args.output is None:
            print_master_tree(parents, order, names, locations, discrete_axes)
        else:
            with open(ensure_parent_dir(args.output), "w", encoding="utf-8") as f:
                print_master_tree(
                    parents, order, names, locations, discrete_axes, file=f
                )
        return

    if not glyphs:
        glyphs = sorted(set([gn for glyphset in glyphsets for gn in glyphset.keys()]))

    glyphsSet = set(glyphs)
    for glyphset in glyphsets:
        glyphSetGlyphNames = set(glyphset.keys())
        diff = glyphsSet - glyphSetGlyphNames
        if diff:
            for gn in diff:
                glyphset[gn] = None

    if locations and location_labeler is None:
        location_labeler = LocationLabeler(
            {
                tag: {-1: triple[0], 0: triple[1], 1: triple[2]}
                for tag, triple in axis_triples.items()
            },
            discrete_axes=discrete_axes,
        )
    tolerance = args.tolerance or DEFAULT_TOLERANCE
    kinkiness = args.kinkiness if args.kinkiness is not None else DEFAULT_KINKINESS
    options = dict(
        glyphs=glyphs,
        names=names,
        locations=locations,
        sparse=sparse,
        upem=upem,
        ignore_missing=args.ignore_missing,
        tolerance=tolerance,
        kinkiness=kinkiness,
        show_all=args.show_all,
        discrete_axes=discrete_axes,
        midpointFunc=midpointFunc,
        progressFunc=None,
    )
    if _prepare:
        return glyphsets, options

    try:
        log.info("Running on %d glyphsets", len(glyphsets))
        log.info("Locations: %s", pformat(locations))
        progress = _make_progress("Checking glyphs", len(glyphs), show_progress)
        options["progressFunc"] = progress
        problems_gen = (
            test_gen(glyphsets, **options)
            if args.jobs == 1
            else _parallel_test_gen(
                glyphsets,
                options,
                args.jobs,
                argv,
            )
        )
        if progress is not None:
            # Finish the bar before writing diagnostics to the same terminal.
            problems_gen = list(problems_gen)
        problems = defaultdict(list)

        f = (
            sys.stdout
            if args.output is None
            else open(ensure_parent_dir(args.output), "w")
        )

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
                        (p["master_idx"],)
                        if "master_idx" in p
                        else (p["master_1_idx"], p["master_2_idx"])
                    )
                    if master_idxs != last_master_idxs:
                        master_names = (
                            (p["master"],)
                            if "master" in p
                            else (p["master_1"], p["master_2"])
                        )
                        print(f"  Masters: %s:" % ", ".join(master_names), file=f)
                        last_master_idxs = master_idxs

                    if p["type"] == InterpolatableProblem.MISSING:
                        print(
                            "    Glyph was missing in master %s" % p["master"], file=f
                        )
                    elif p["type"] == InterpolatableProblem.OPEN_PATH:
                        print(
                            "    Glyph has an open path in master %s" % p["master"],
                            file=f,
                        )
                    elif p["type"] == InterpolatableProblem.PATH_COUNT:
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
                    elif p["type"] == InterpolatableProblem.NODE_COUNT:
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
                    elif p["type"] == InterpolatableProblem.NODE_INCOMPATIBILITY:
                        print(
                            "    Node %d incompatible in path %i: %s in %s, %s in %s"
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
                    elif p["type"] == InterpolatableProblem.CONTOUR_ORDER:
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
                    elif p["type"] == InterpolatableProblem.WRONG_START_POINT:
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
                    elif p["type"] == InterpolatableProblem.UNDERWEIGHT:
                        print(
                            "    Contour %d interpolation is underweight: %s, %s"
                            % (
                                p["contour"],
                                p["master_1"],
                                p["master_2"],
                            ),
                            file=f,
                        )
                    elif p["type"] == InterpolatableProblem.OVERWEIGHT:
                        print(
                            "    Contour %d interpolation is overweight: %s, %s"
                            % (
                                p["contour"],
                                p["master_1"],
                                p["master_2"],
                            ),
                            file=f,
                        )
                    elif p["type"] == InterpolatableProblem.KINK:
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
                    elif p["type"] == InterpolatableProblem.NOTHING:
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

        problems = sort_problems(problems)

        for p in "ps", "pdf":
            arg = getattr(args, p)
            if arg is None:
                continue
            log.info("Writing %s to %s", p.upper(), arg)
            from .interpolatablePlot import InterpolatablePS, InterpolatablePDF

            PlotterClass = InterpolatablePS if p == "ps" else InterpolatablePDF

            with PlotterClass(
                ensure_parent_dir(arg),
                glyphsets=glyphsets,
                names=names,
                locations=locations,
                location_labeler=location_labeler,
                midpointFunc=midpointFunc,
            ) as doc:
                doc.add_title_page(
                    original_args_inputs, tolerance=tolerance, kinkiness=kinkiness
                )
                if problems:
                    doc.add_summary(problems)
                doc.add_problems(problems)
                if not problems and not args.quiet:
                    doc.draw_cupcake()
                if problems:
                    doc.add_index()
                    doc.add_table_of_contents()

        if args.html:
            log.info("Writing HTML to %s", args.html)
            from .interpolatablePlot import InterpolatableSVG

            svgs = []
            glyph_starts = {}
            with InterpolatableSVG(
                svgs,
                glyphsets=glyphsets,
                names=names,
                locations=locations,
                location_labeler=location_labeler,
                midpointFunc=midpointFunc,
            ) as svg:
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
            import html

            with open(ensure_parent_dir(args.html), "wb") as f:
                f.write(b"<!DOCTYPE html>\n")
                f.write(
                    b'<html><body align="center" style="font-family: sans-serif; text-color: #222">\n'
                )
                f.write(b"<title>fonttools varLib.interpolatable report</title>\n")
                for i, svg in enumerate(svgs):
                    if i in glyph_starts:
                        f.write(
                            f"<h1>Glyph {html.escape(glyph_starts[i])}</h1>\n".encode(
                                "utf-8"
                            )
                        )
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
