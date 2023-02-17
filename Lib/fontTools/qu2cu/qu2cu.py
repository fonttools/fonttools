# cython: language_level=3
# distutils: define_macros=CYTHON_TRACE_NOGIL=1

# Copyright 2023 Google Inc. All Rights Reserved.
# Copyright 2023 Behdad Esfahbod. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
    import cython
except ImportError:
    # if cython not installed, use mock module with no-op decorators and types
    from fontTools.misc import cython

from fontTools.misc.bezierTools import splitCubicAtTC


__all__ = ["quadratic_to_curves", "quadratics_to_curves"]


if cython.compiled:
    # Yep, I'm compiled.
    COMPILED = True
else:
    # Just a lowly interpreted script.
    COMPILED = False


# Copied from cu2qu
@cython.cfunc
@cython.returns(cython.int)
@cython.locals(
    tolerance=cython.double,
    p0=cython.complex,
    p1=cython.complex,
    p2=cython.complex,
    p3=cython.complex,
)
@cython.locals(mid=cython.complex, deriv3=cython.complex)
def cubic_farthest_fit_inside(p0, p1, p2, p3, tolerance):
    """Check if a cubic Bezier lies within a given distance of the origin.

    "Origin" means *the* origin (0,0), not the start of the curve. Note that no
    checks are made on the start and end positions of the curve; this function
    only checks the inside of the curve.

    Args:
        p0 (complex): Start point of curve.
        p1 (complex): First handle of curve.
        p2 (complex): Second handle of curve.
        p3 (complex): End point of curve.
        tolerance (double): Distance from origin.

    Returns:
        bool: True if the cubic Bezier ``p`` entirely lies within a distance
        ``tolerance`` of the origin, False otherwise.
    """
    # First check p2 then p1, as p2 has higher error early on.
    if abs(p2) <= tolerance and abs(p1) <= tolerance:
        return True

    # Split.
    mid = (p0 + 3 * (p1 + p2) + p3) * 0.125
    if abs(mid) > tolerance:
        return False
    deriv3 = (p3 + p2 - p1 - p0) * 0.125
    return cubic_farthest_fit_inside(
        p0, (p0 + p1) * 0.5, mid - deriv3, mid, tolerance
    ) and cubic_farthest_fit_inside(mid, mid + deriv3, (p2 + p3) * 0.5, p3, tolerance)


@cython.locals(_1_3=cython.double, _2_3=cython.double)
@cython.locals(
    p0=cython.complex,
    p1=cython.complex,
    p2=cython.complex,
    p1_2_3=cython.complex,
)
def elevate_quadratic(p0, p1, p2, _1_3=1 / 3, _2_3=2 / 3):
    """Given a quadratic bezier curve, return its degree-elevated cubic."""

    # https://pomax.github.io/bezierinfo/#reordering
    p1_2_3 = p1 * _2_3
    return (
        p0,
        (p0 * _1_3 + p1_2_3),
        (p2 * _1_3 + p1_2_3),
        p2,
    )


@cython.locals(
    n=cython.int,
    k=cython.int,
    prod_ratio=cython.double,
    sum_ratio=cython.double,
    ratio=cython.double,
    p0=cython.complex,
    p1=cython.complex,
    p2=cython.complex,
    p3=cython.complex,
)
def merge_curves(curves):
    """Give a cubic-Bezier spline, reconstruct one cubic-Bezier
    that has the same endpoints and tangents and approxmates
    the spline."""

    # Reconstruct the t values of the cut segments
    n = len(curves)
    prod_ratio = 1.0
    sum_ratio = 1.0
    ts = [1]
    for k in range(1, n):
        ck = curves[k]
        c_before = curves[k - 1]

        # |t_(k+1) - t_k| / |t_k - t_(k - 1)| = ratio
        assert ck[0] == c_before[3]
        ratio = abs(ck[1] - ck[0]) / abs(c_before[3] - c_before[2])

        prod_ratio *= ratio
        sum_ratio += prod_ratio
        ts.append(sum_ratio)

    # (t(n) - t(n - 1)) / (t_(1) - t(0)) = prod_ratio

    ts = [t / sum_ratio for t in ts[:-1]]

    p0 = curves[0][0]
    p1 = curves[0][1]
    p2 = curves[n - 1][2]
    p3 = curves[n - 1][3]

    # Build the curve by scaling the control-points.
    p1 = p0 + (p1 - p0) / (ts[0] if ts else 1)
    p2 = p3 + (p2 - p3) / ((1 - ts[-1]) if ts else 1)

    curve = (p0, p1, p2, p3)

    return curve, ts


def add_implicit_on_curves(p):
    q = list(p)
    count = 0
    num_offcurves = len(p) - 2
    for i in range(1, num_offcurves):
        off1 = p[i]
        off2 = p[i + 1]
        on = off1 + (off2 - off1) * 0.5
        q.insert(i + 1 + count, on)
        count += 1
    return q


def quadratics_to_curves(pp, tolerance=0.5, all_cubic=False):
    is_complex = type(pp[0][0]) is complex
    if not is_complex:
        pp = [[complex(x, y) for (x, y) in p] for p in pp]

    q = [pp[0][0]]
    for p in pp:
        assert q[-1] == p[0]
        q.extend(add_implicit_on_curves(p)[1:])

    curves = spline_to_curves(q, tolerance, all_cubic)

    if not is_complex:
        curves = [tuple((c.real, c.imag) for c in curve) for curve in curves]
    return curves


def quadratic_to_curves(q, tolerance=0.5, all_cubic=False):
    is_complex = type(q[0]) is complex
    if not is_complex:
        q = [complex(x, y) for (x, y) in q]

    q = add_implicit_on_curves(q)

    curves = spline_to_curves(q, tolerance, all_cubic)

    if not is_complex:
        curves = [tuple((c.real, c.imag) for c in curve) for curve in curves]
    return curves


def spline_to_curves(q, tolerance=0.5, all_cubic=False):
    assert len(q) >= 3, "quadratic spline requires at least 3 points"

    # Elevate quadratic segments to cubic
    elevated_quadratics = [
        elevate_quadratic(*q[i : i + 3]) for i in range(0, len(q) - 2, 2)
    ]

    # Dynamic-Programming to find the solution with fewest number of
    # cubic curves, and within those the one with smallest error.
    sols = [(0, 0, 0)]  # (best_num_segments, best_error, start_index)
    for i in range(1, len(elevated_quadratics) + 1):
        best_sol = (len(q) + 1, 0, 1)
        for j in range(0, i):

            # Fit elevated_quadratics[j:i] into one cubic
            try:
                curve, ts = merge_curves(elevated_quadratics[j:i])
            except ZeroDivisionError:
                continue

            # Now reconstruct the segments from the fitted curve
            reconstructed_iter = splitCubicAtTC(*curve, *ts)
            reconstructed = []

            # Knot errors
            error = 0
            for k, reconst in enumerate(reconstructed_iter):
                orig = elevated_quadratics[j + k]
                err = abs(reconst[3] - orig[3])
                error = max(error, err)
                if error > tolerance:
                    break
                reconstructed.append(reconst)
            if error > tolerance:
                # Not feasible
                continue

            # Interior errors
            for k, reconst in enumerate(reconstructed):
                orig = elevated_quadratics[j + k]
                p0, p1, p2, p3 = tuple(v - u for v, u in zip(reconst, orig))

                if not cubic_farthest_fit_inside(p0, p1, p2, p3, tolerance):
                    error = tolerance + 1
                    break
            if error > tolerance:
                # Not feasible
                continue

            # Save best solution
            j_sol_count, j_sol_error, _ = sols[j]
            i_sol_count = j_sol_count + 1
            i_sol_error = max(j_sol_error, error)
            i_sol = (i_sol_count, i_sol_error, i - j)
            if i_sol < best_sol:
                best_sol = i_sol

            if i_sol_count == 1:
                # Can't get any better than this
                break

        sols.append(best_sol)

    # Reconstruct solution
    splits = []
    i = len(sols) - 1
    while i:
        splits.append(i)
        _, _, count = sols[i]
        i -= count
    curves = []
    j = 0
    for i in reversed(splits):
        if not all_cubic and j + 1 == i:
            curves.append(q[j * 2 : j * 2 + 3])
        else:
            curves.append(merge_curves(elevated_quadratics[j:i])[0])
        j = i

    return curves


def main():
    from fontTools.cu2qu.benchmark import generate_curve
    from fontTools.cu2qu import curve_to_quadratic

    tolerance = 0.05
    reconstruct_tolerance = tolerance * 1
    curve = generate_curve()
    quadratics = curve_to_quadratic(curve, tolerance)
    print(
        "cu2qu tolerance %g. qu2cu tolerance %g." % (tolerance, reconstruct_tolerance)
    )
    print("One random cubic turned into %d quadratics." % len(quadratics))
    curves = quadratic_to_curves(quadratics, reconstruct_tolerance)
    print("Those quadratics turned back into %d cubics. " % len(curves))
    print("Original curve:", curve)
    print("Reconstructed curve(s):", curves)


if __name__ == "__main__":
    main()
