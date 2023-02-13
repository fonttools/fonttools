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

from fontTools.misc.bezierTools import splitCubicIntoTwoAtTC
from fontTools.cu2qu.cu2qu import cubic_farthest_fit_inside


__all__ = ["quadratic_to_curves"]


NAN = float("NaN")


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


@cython.locals(k=cython.double, k_1=cython.double, t=cython.double)
@cython.locals(
    p1=cython.complex,
    p2=cython.complex,
    p3=cython.complex,
    p4=cython.complex,
    p5=cython.complex,
    p6=cython.complex,
    p7=cython.complex,
    off1=cython.complex,
    off2=cython.complex,
)
def merge_two_curves(p1, p2, p3, p4, p5, p6, p7):
    """Return the initial cubic bezier curve subdivided in two segments.
    Input must be a sequence of 7 points, i.e. two consecutive cubic curve
    segments sharing the middle point.
    Inspired by:
    https://math.stackexchange.com/questions/877725/retrieve-the-initial-cubic-b%C3%A9zier-curve-subdivided-in-two-b%C3%A9zier-curves/879213#879213
    """
    k = abs(p5 - p4) / abs(p4 - p3)
    k_1 = k + 1
    off1 = k_1 * p2 - k * p1
    off2 = (k_1 * p6 - p7) / k
    t = 1 / k_1
    return (p1, off1, off2, p7), t


def quadratic_to_curves(p, tolerance=0.5):
    assert len(p) >= 3, "quadratic spline requires at least 3 points"
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

    # elevate quadratic segments to cubic, and join them together
    curves = []

    curve = elevate_quadratic(*q[:3])
    err = 0
    for i in range(4, len(q), 2):
        cubic_segment = elevate_quadratic(q[i - 2], q[i - 1], q[i])
        new_curve, t = merge_two_curves(*(curve + cubic_segment[1:]))

        seg1, seg2 = splitCubicIntoTwoAtTC(*new_curve, t)
        t_point = seg2[0]

        t_err = abs(t_point - cubic_segment[0])
        if (
            t_err > tolerance
            or not cubic_farthest_fit_inside(
                *(v - u for v, u in zip(seg1, curve)), tolerance - err
            )
            or not cubic_farthest_fit_inside(
                *(v - u for v, u in zip(seg2, cubic_segment)), tolerance
            )
        ):
            # Error too high. Start a new segment.
            curves.append(curve)
            new_curve = cubic_segment
            err = 0
            pass

        curve = new_curve
        err += t_err

    curves.append(curve)

    return [tuple((c.real, c.imag) for c in curve) for curve in curves]


def main():
    from fontTools.cu2qu.benchmark import generate_curve
    from fontTools.cu2qu import curve_to_quadratic

    curve = generate_curve()
    quadratics = curve_to_quadratic(curve, 0.05)
    print(len(quadratics))
    print(len(quadratic_to_curves(quadratics, 0.05 * 2)))
