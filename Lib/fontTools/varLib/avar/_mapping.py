# cython: boundscheck=False, wraparound=False
"""Numerical avar evaluator, optionally compiled with Cython."""

try:
    import cython
except (AttributeError, ImportError):
    from fontTools.misc import cython
COMPILED = cython.compiled

import math

if cython.compiled:
    from cython.cimports.libc.math import floor
else:
    from math import floor
from bisect import bisect_right


@cython.locals(
    z="double[:]",
    slopes="double[:]",
    columns="long[:]",
    factor_columns="long[:]",
    deltas="double[:, :]",
    offsets="long[:]",
    axes="long[:]",
    starts="double[:]",
    peaks="double[:]",
    ends="double[:]",
    values="double[:]",
    jac="double[:, :]",
    factors="double[:]",
    derivatives="double[:]",
    n=cython.int,
    nr=cython.int,
    r=cython.int,
    f=cython.int,
    g=cython.int,
    a=cython.int,
    out=cython.int,
    column=cython.int,
    v=cython.double,
    start=cython.double,
    peak=cython.double,
    end=cython.double,
    factor=cython.double,
    derivative=cython.double,
    scalar=cython.double,
    product=cython.double,
    gradient=cython.double,
    delta=cython.double,
    nudge="volatile double",
)
def evaluate(
    z,
    slopes,
    deltas,
    offsets,
    axes,
    starts,
    peaks,
    ends,
    supports,
    columns=None,
    factor_columns=None,
):
    import numpy as np

    if columns is None:
        columns = np.arange(len(z), dtype="l")
        factor_columns = axes
    if not COMPILED:
        return _evaluatePython(z, slopes, deltas, supports, columns)

    n = z.shape[0]
    nr = offsets.shape[0] - 1
    values_array = np.array(z, dtype=float, copy=True)
    jac_array = np.zeros((n, len(columns)))
    factors_array = np.empty(axes.shape[0])
    derivatives_array = np.empty(axes.shape[0])
    values = values_array
    jac = jac_array
    factors = factors_array
    derivatives = derivatives_array
    for column in range(len(columns)):
        jac[columns[column], column] = 1.0
    # Retain region summation order and separate multiplication/addition,
    # matching the Python evaluator at rounding-sensitive boundaries.
    for r in range(nr):
        scalar = 1.0
        for f in range(offsets[r], offsets[r + 1]):
            v = z[axes[f]]
            start = starts[f]
            peak = peaks[f]
            end = ends[f]
            factor = 0.0
            derivative = 0.0
            if v < start or v > end:
                pass
            elif v == peak:
                factor = 1.0
                if peak < end:
                    derivative = -1.0 / (end - peak)
                elif start < peak:
                    derivative = 1.0 / (peak - start)
            elif v == end and end < 1:
                pass
            elif v < peak:
                derivative = 1.0 / (peak - start)
                factor = (v - start) * derivative
            else:
                derivative = -1.0 / (end - peak)
                factor = (v - end) * derivative
            factors[f] = factor
            derivatives[f] = derivative
            scalar *= factor
        for out in range(n):
            delta = deltas[out, r]
            if delta == 0:
                continue
            nudge = delta * scalar
            values[out] = values[out] + nudge
            for f in range(offsets[r], offsets[r + 1]):
                a = factor_columns[f]
                if a < 0:
                    continue
                # Do not divide by a factor: its value may be zero while
                # its derivative and the other factors are nonzero.
                product = 1.0
                for g in range(offsets[r], offsets[r + 1]):
                    if f != g:
                        product *= factors[g]
                gradient = derivatives[f] * product
                nudge = delta * gradient
                jac[out, a] = jac[out, a] + nudge
    for out in range(n):
        for column in range(len(columns)):
            jac[out, column] *= slopes[columns[column]]
    return values_array, jac_array


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


def _evaluatePython(z, slopes, deltas, supports, columns=None):
    import numpy as np

    if columns is None:
        columns = np.arange(len(z), dtype="l")
    positions = {i: j for j, i in enumerate(columns)}
    values = z.copy()
    jac = np.zeros((len(z), len(columns)))
    for j, i in enumerate(columns):
        jac[i, j] = 1.0
    for delta, support in zip(deltas.T, supports):
        factors = [_tent(z[i], a, p, b) for i, a, p, b in support]
        scalar = math.prod(v for v, _ in factors)
        gradient = np.zeros(len(columns))
        for j, (i, _, _, _) in enumerate(support):
            if i not in positions:
                continue
            gradient[positions[i]] = factors[j][1] * math.prod(
                v for k, (v, _) in enumerate(factors) if k != j
            )
        jac += np.outer(delta, gradient)
        values = values + delta * scalar
    return values, jac * slopes[columns]


def _segment(value, items):
    """Piecewise-linear segment value and a one-sided derivative."""
    if not items:
        return value, 1.0
    keys = [k for k, _ in items]
    i = bisect_right(keys, value)
    if value < keys[0] or value > keys[len(keys) - 1] or len(items) == 1:
        k, v = items[0 if value < keys[0] else len(items) - 1]
        return value + v - k, 1.0
    i = min(max(i, 1), len(items) - 1)
    a, va = items[i - 1]
    b, vb = items[i]
    slope = (vb - va) / (b - a)
    return va + (value - a) * slope, slope


def packSegments(segments):
    import numpy as np

    offsets = [0]
    keys, values = [], []
    for segment in segments:
        keys.extend(k for k, _ in segment)
        values.extend(v for _, v in segment)
        offsets.append(len(keys))
    return (
        np.array(offsets, dtype="l"),
        np.array(keys, dtype=float),
        np.array(values, dtype=float),
    )


@cython.locals(
    x="double[:]",
    offsets="long[:]",
    keys="double[:]",
    values="double[:]",
    z="double[:]",
    slopes="double[:]",
    n=cython.int,
    i=cython.int,
    j=cython.int,
    first=cython.int,
    last=cython.int,
    left=cython.int,
    right=cython.int,
    mid=cython.int,
    v=cython.double,
    slope=cython.double,
    nudge="volatile double",
)
def mapSegments(x, offsets, keys, values, segments):
    import numpy as np

    if not COMPILED:
        pairs = [_segment(v, segment) for v, segment in zip(x, segments)]
        return np.array([v for v, _ in pairs]), np.array([s for _, s in pairs])
    n = len(x)
    z_array, slopes_array = np.empty(n), np.empty(n)
    z, slopes = z_array, slopes_array
    # Binary-search packed avar1 knots without constructing Python lists or
    # tuples at every evaluation. Preserve _segment's one-sided derivatives.
    for i in range(n):
        v = x[i]
        first, last = offsets[i], offsets[i + 1]
        slope = 1.0
        if first == last:
            pass
        elif v < keys[first] or v > keys[last - 1] or last - first == 1:
            j = first if v < keys[first] else last - 1
            v = v + values[j] - keys[j]
        else:
            left, right = first, last
            while left < right:
                mid = (left + right) // 2
                if v < keys[mid]:
                    right = mid
                else:
                    left = mid + 1
            j = min(max(left, first + 1), last - 1)
            slope = (values[j] - values[j - 1]) / (keys[j] - keys[j - 1])
            nudge = (v - keys[j - 1]) * slope
            v = values[j - 1] + nudge
        z[i], slopes[i] = v, slope
    return z_array, slopes_array


@cython.cfunc
@cython.returns("void")
@cython.locals(
    user="double[:]",
    triples="double[:, :]",
    seg_offsets="long[:]",
    seg_keys="double[:]",
    seg_values="double[:]",
    offsets="long[:]",
    axes="long[:]",
    starts="double[:]",
    peaks="double[:]",
    ends="double[:]",
    row_offsets="long[:]",
    row_regions="long[:]",
    row_deltas="double[:]",
    z="double[:]",
    scalars="double[:]",
    out="double[:]",
    n=cython.int,
    nr=cython.int,
    i=cython.int,
    j=cython.int,
    k=cython.int,
    lo=cython.int,
    hi=cython.int,
    mid=cython.int,
    first=cython.int,
    last=cython.int,
    r=cython.int,
    f=cython.int,
    quantize=cython.int,
    clamp=cython.int,
    v=cython.double,
    start=cython.double,
    peak=cython.double,
    end=cython.double,
    scalar=cython.double,
    delta=cython.double,
    nudge="volatile double",
)
def _scoreInto(
    user,
    triples,
    seg_offsets,
    seg_keys,
    seg_values,
    offsets,
    axes,
    starts,
    peaks,
    ends,
    row_offsets,
    row_regions,
    row_deltas,
    quantize,
    clamp,
    z,
    scalars,
    out,
):
    n = len(user)
    nr = len(offsets) - 1
    # Volatile products prevent fused multiply-add from changing tie rounding.
    # This follows the exact forward map, not the differentiable surrogate:
    # keep normalization, segment arithmetic, delta order, and rounding intact.
    for i in range(n):
        v = max(triples[i, 0], min(triples[i, 2], user[i]))
        if v == triples[i, 1] or triples[i, 0] == triples[i, 2]:
            v = 0.0
        elif v < triples[i, 1]:
            v = (v - triples[i, 1]) / (triples[i, 1] - triples[i, 0])
        else:
            v = (v - triples[i, 1]) / (triples[i, 2] - triples[i, 1])
        first = seg_offsets[i]
        last = seg_offsets[i + 1]
        if first == last:
            pass
        elif last - first == 1:
            v = v + seg_values[first] - seg_keys[first]
        elif v < seg_keys[first]:
            v = v + seg_values[first] - seg_keys[first]
        elif v > seg_keys[last - 1]:
            v = v + seg_values[last - 1] - seg_keys[last - 1]
        else:
            lo = first
            hi = last
            while lo < hi:
                mid = (lo + hi) // 2
                if v < seg_keys[mid]:
                    hi = mid
                else:
                    lo = mid + 1
            j = max(first + 1, min(lo, last - 1))
            if v == seg_keys[j - 1]:
                v = seg_values[j - 1]
            elif v == seg_keys[j]:
                v = seg_values[j]
            else:
                nudge = (seg_values[j] - seg_values[j - 1]) * (v - seg_keys[j - 1])
                v = seg_values[j - 1] + nudge / (seg_keys[j] - seg_keys[j - 1])
        z[i] = v
    for r in range(nr):
        scalar = 1.0
        for f in range(offsets[r], offsets[r + 1]):
            v = z[axes[f]]
            start = starts[f]
            peak = peaks[f]
            end = ends[f]
            if v == peak:
                continue
            if v <= start or end <= v:
                scalar = 0.0
                break
            if v < peak:
                scalar *= (v - start) / (peak - start)
            else:
                scalar *= (v - end) / (peak - end)
        scalars[r] = scalar
    for i in range(n):
        v = z[i]
        if quantize:
            v = floor(v * 16384.0 + 0.5)
            if clamp:
                delta = 0.0
                for f in range(row_offsets[i], row_offsets[i + 1]):
                    scalar = scalars[row_regions[f]]
                    if scalar:
                        nudge = row_deltas[f] * scalar
                        delta = delta + nudge
                v += floor(delta + 0.5)
                v = max(-16384.0, min(16384.0, v))
            v /= 16384.0
        out[i] = v


@cython.locals(
    user="double[:]",
    triples="double[:, :]",
    seg_offsets="long[:]",
    seg_keys="double[:]",
    seg_values="double[:]",
    offsets="long[:]",
    axes="long[:]",
    starts="double[:]",
    peaks="double[:]",
    ends="double[:]",
    row_offsets="long[:]",
    row_regions="long[:]",
    row_deltas="double[:]",
    z="double[:]",
    scalars="double[:]",
    out="double[:]",
    n=cython.int,
    nr=cython.int,
    i=cython.int,
    j=cython.int,
    k=cython.int,
    lo=cython.int,
    hi=cython.int,
    mid=cython.int,
    first=cython.int,
    last=cython.int,
    r=cython.int,
    f=cython.int,
    quantize=cython.int,
    clamp=cython.int,
    v=cython.double,
    start=cython.double,
    peak=cython.double,
    end=cython.double,
    scalar=cython.double,
    delta=cython.double,
    nudge="volatile double",
)
def score(
    user,
    triples,
    seg_offsets,
    seg_keys,
    seg_values,
    offsets,
    axes,
    starts,
    peaks,
    ends,
    row_offsets,
    row_regions,
    row_deltas,
    quantize,
    clamp,
    tags,
):
    import numpy as np

    n = len(user)
    nr = len(offsets) - 1
    z, scalars, out = np.empty(n), np.empty(nr), np.empty(n)
    _scoreInto(
        user,
        triples,
        seg_offsets,
        seg_keys,
        seg_values,
        offsets,
        axes,
        starts,
        peaks,
        ends,
        row_offsets,
        row_regions,
        row_deltas,
        quantize,
        clamp,
        z,
        scalars,
        out,
    )
    return {tag: out[i] for i, tag in enumerate(tags)}


@cython.locals(
    user="double[:]",
    coordinates="double[:, :]",
    pins="double[:]",
    result="double[:, :]",
    candidate=cython.int,
    triples="double[:, :]",
    seg_offsets="long[:]",
    seg_keys="double[:]",
    seg_values="double[:]",
    offsets="long[:]",
    axes="long[:]",
    starts="double[:]",
    peaks="double[:]",
    ends="double[:]",
    row_offsets="long[:]",
    row_regions="long[:]",
    row_deltas="double[:]",
    z="double[:]",
    scalars="double[:]",
    out="double[:]",
    n=cython.int,
    nr=cython.int,
    i=cython.int,
    j=cython.int,
    k=cython.int,
    lo=cython.int,
    hi=cython.int,
    mid=cython.int,
    first=cython.int,
    last=cython.int,
    r=cython.int,
    f=cython.int,
    quantize=cython.int,
    clamp=cython.int,
    v=cython.double,
    start=cython.double,
    peak=cython.double,
    end=cython.double,
    scalar=cython.double,
    delta=cython.double,
    nudge="volatile double",
)
def scoreBatch(
    coordinates,
    pins,
    triples,
    seg_offsets,
    seg_keys,
    seg_values,
    offsets,
    axes,
    starts,
    peaks,
    ends,
    row_offsets,
    row_regions,
    row_deltas,
    quantize,
    clamp,
    tags,
):
    import numpy as np

    n = len(pins)
    nr = len(offsets) - 1
    user, z, scalars = np.empty(n), np.empty(n), np.empty(nr)
    result_array = np.empty((len(coordinates), n))
    result = result_array
    # Reuse scratch arrays across candidates, preserving the public path's
    # normalized -> user -> normalized round trip and exact pinned values.
    for candidate in range(len(coordinates)):
        for i in range(n):
            if pins[i] == pins[i]:
                user[i] = pins[i]
            else:
                v = coordinates[candidate, i]
                if v >= 0:
                    nudge = v * (triples[i, 2] - triples[i, 1])
                else:
                    nudge = v * (triples[i, 1] - triples[i, 0])
                user[i] = triples[i, 1] + nudge
        out = result[candidate]
        _scoreInto(
            user,
            triples,
            seg_offsets,
            seg_keys,
            seg_values,
            offsets,
            axes,
            starts,
            peaks,
            ends,
            row_offsets,
            row_regions,
            row_deltas,
            quantize,
            clamp,
            z,
            scalars,
            out,
        )
    return result_array
