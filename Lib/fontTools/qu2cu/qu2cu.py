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
from fontTools.cu2qu.cu2qu import cubic_farthest_fit_inside


__all__ = ["quadratic_to_curves"]


if cython.compiled:
    # Yep, I'm compiled.
    COMPILED = True
else:
    # Just a lowly interpreted script.
    COMPILED = False


@cython.locals(_1_3=cython.double, _2_3=cython.double)
@cython.locals(
    p0=cython.complex,
    p1=cython.complex,
    p2=cython.complex,
    p1_2_3=cython.complex,
)
def elevate_quadratic(p0, p1, p2, _1_3=1 / 3, _2_3=2 / 3):
    """Given a quadratic bezier curve, return its degree-elevated cubic."""

    p1_2_3 = p1 * _2_3
    return (
        p0,
        (p0 * _1_3 + p1_2_3),
        (p2 * _1_3 + p1_2_3),
        p2,
    )


@cython.locals(
    n=cython.int,
    prod_ratio=cython.double,
    sum_ratio=cython.double,
    ratio=cython.double,
)
def merge_curves(curves):
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

    p1 = p0 + (p1 - p0) / (ts[0] if ts else 1)
    p2 = p3 + (p2 - p3) / ((1 - ts[-1]) if ts else 1)

    curve = (p0, p1, p2, p3)

    return curve, ts


def quadratic_to_curves(p, tolerance=0.5):
    assert len(p) >= 3, "quadratic spline requires at least 3 points"
    is_complex = type(p[0]) is complex
    if not is_complex:
        p = [complex(x, y) for (x, y) in p]

    # if spline has more than one offcurve, insert interpolated oncurves
    q = list(p)
    count = 0
    num_offcurves = len(p) - 2
    for i in range(1, num_offcurves):
        off1 = p[i]
        off2 = p[i + 1]
        on = off1 + (off2 - off1) * 0.5
        q.insert(i + 1 + count, on)
        count += 1
    del p

    # Elevate quadratic segments to cubic
    elevated_quadratics = [
        elevate_quadratic(*q[i : i + 3]) for i in range(0, len(q) - 2, 2)
    ]

    sols = [(0, 0, 0)]  # (best_num_segments, best_error, start_index)
    for i in range(1, len(elevated_quadratics) + 1):
        best_sol = (len(q) + 1, 0, 1)
        for j in range(0, i):

            # Fit elevated_quadratics[j:i] into one cubic
            curve, ts = merge_curves(elevated_quadratics[j:i])
            reconstructed = splitCubicAtTC(*curve, *ts)
            error = max(
                abs(reconst[3] - orig[3])
                for reconst, orig in zip(reconstructed, elevated_quadratics[j:i])
            )
            if error > tolerance or not all(
                cubic_farthest_fit_inside(
                    *(v - u for v, u in zip(seg1, seg2)), tolerance
                )
                for seg1, seg2 in zip(reconstructed, elevated_quadratics[j:i])
            ):
                continue

            j_sol_count, j_sol_error, _ = sols[j]
            i_sol_count = j_sol_count + 1
            i_sol_error = max(j_sol_error, error)
            i_sol = (i_sol_count, i_sol_error, i - j)
            if i_sol < best_sol:
                best_sol = i_sol

            if i_sol_count == 1:
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
        curves.append(merge_curves(elevated_quadratics[j:i])[0])
        j = i

    if not is_complex:
        curves = [tuple((c.real, c.imag) for c in curve) for curve in curves]
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
