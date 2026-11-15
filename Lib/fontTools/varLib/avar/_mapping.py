# cython: boundscheck=False, wraparound=False
"""Numerical avar evaluator, optionally compiled with Cython."""

try:
    import cython
except (AttributeError, ImportError):
    from fontTools.misc import cython
COMPILED = cython.compiled

import math


@cython.locals(
    z="double[:]",
    slopes="double[:]",
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
    nudge=cython.double,
)
def evaluate(z, slopes, deltas, offsets, axes, starts, peaks, ends, supports):
    import numpy as np

    if not COMPILED:
        return _evaluatePython(z, slopes, deltas, supports)

    n = z.shape[0]
    nr = offsets.shape[0] - 1
    values_array = np.array(z, dtype=float, copy=True)
    jac_array = np.eye(n)
    factors_array = np.empty(axes.shape[0])
    derivatives_array = np.empty(axes.shape[0])
    values = values_array
    jac = jac_array
    factors = factors_array
    derivatives = derivatives_array
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
                # Do not divide by a factor: its value may be zero while
                # its derivative and the other factors are nonzero.
                product = 1.0
                for g in range(offsets[r], offsets[r + 1]):
                    if f != g:
                        product *= factors[g]
                gradient = derivatives[f] * product
                a = axes[f]
                nudge = delta * gradient
                jac[out, a] = jac[out, a] + nudge
    for out in range(n):
        for column in range(n):
            jac[out, column] *= slopes[column]
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


def _evaluatePython(z, slopes, deltas, supports):
    import numpy as np

    values = z.copy()
    jac = np.eye(len(z))
    for delta, support in zip(deltas.T, supports):
        factors = [_tent(z[i], a, p, b) for i, a, p, b in support]
        scalar = math.prod(v for v, _ in factors)
        gradient = np.zeros(len(z))
        for j, (i, _, _, _) in enumerate(support):
            gradient[i] = factors[j][1] * math.prod(
                v for k, (v, _) in enumerate(factors) if k != j
            )
        jac += np.outer(delta, gradient)
        values = values + delta * scalar
    return values, jac * slopes
