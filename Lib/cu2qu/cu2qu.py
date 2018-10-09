#cython: language_level=3
#distutils: define_macros=CYTHON_TRACE_NOGIL=1

# Copyright 2015 Google Inc. All Rights Reserved.
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


from __future__ import print_function, division, absolute_import

try:
    import cython
except ImportError:
    # if not installed, use the embedded (no-op) copy of Cython.Shadow
    from . import cython

import math


__all__ = ['curve_to_quadratic', 'curves_to_quadratic']

MAX_N = 100

NAN = float("NaN")


if cython.compiled:
    # Yep, I'm compiled.
    COMPILED = True
else:
    # Just a lowly interpreted script.
    COMPILED = False


class Cu2QuError(Exception):
    pass


class ApproxNotFoundError(Cu2QuError):
    def __init__(self, curve):
        message = "no approximation found: %s" % curve
        super(Cu2QuError, self).__init__(message)
        self.curve = curve

@cython.cfunc
@cython.inline
@cython.returns(cython.double)
@cython.locals(v1=cython.complex, v2=cython.complex)
def dot(v1, v2):
    """Return the dot product of two vectors."""
    return (v1 * v2.conjugate()).real


@cython.cfunc
@cython.inline
@cython.locals(a=cython.complex, b=cython.complex, c=cython.complex, d=cython.complex)
@cython.locals(_1=cython.complex, _2=cython.complex, _3=cython.complex, _4=cython.complex)
def calc_cubic_points(a, b, c, d):
    _1 = d
    _2 = (c / 3.0) + d
    _3 = (b + c) / 3.0 + _2
    _4 = a + d + c + b
    return _1, _2, _3, _4


@cython.cfunc
@cython.inline
@cython.locals(p0=cython.complex, p1=cython.complex, p2=cython.complex, p3=cython.complex)
@cython.locals(a=cython.complex, b=cython.complex, c=cython.complex, d=cython.complex)
def calc_cubic_parameters(p0, p1, p2, p3):
    c = (p1 - p0) * 3.0
    b = (p2 - p1) * 3.0 - c
    d = p0
    a = p3 - d - c - b
    return a, b, c, d


@cython.cfunc
@cython.locals(p0=cython.complex, p1=cython.complex, p2=cython.complex, p3=cython.complex)
def split_cubic_into_n_iter(p0, p1, p2, p3, n):
    # Hand-coded special-cases
    if n == 2:
        return iter(split_cubic_into_two(p0, p1, p2, p3))
    if n == 3:
        return iter(split_cubic_into_three(p0, p1, p2, p3))
    if n == 4:
        a, b = split_cubic_into_two(p0, p1, p2, p3)
        return iter(split_cubic_into_two(*a) + split_cubic_into_two(*b))
    if n == 6:
        a, b = split_cubic_into_two(p0, p1, p2, p3)
        return iter(split_cubic_into_three(*a) + split_cubic_into_three(*b))

    return _split_cubic_into_n_gen(p0,p1,p2,p3,n)


@cython.locals(p0=cython.complex, p1=cython.complex, p2=cython.complex, p3=cython.complex, n=cython.int)
@cython.locals(a=cython.complex, b=cython.complex, c=cython.complex, d=cython.complex)
@cython.locals(dt=cython.double, delta_2=cython.double, delta_3=cython.double, i=cython.int)
@cython.locals(a1=cython.complex, b1=cython.complex, c1=cython.complex, d1=cython.complex)
def _split_cubic_into_n_gen(p0, p1, p2, p3, n):
    a, b, c, d = calc_cubic_parameters(p0, p1, p2, p3)
    dt = 1 / n
    delta_2 = dt * dt
    delta_3 = dt * delta_2
    for i in range(n):
        t1 = i * dt
        t1_2 = t1 * t1
        # calc new a, b, c and d
        a1 = a * delta_3
        b1 = (3*a*t1 + b) * delta_2
        c1 = (2*b*t1 + c + 3*a*t1_2) * dt
        d1 = a*t1*t1_2 + b*t1_2 + c*t1 + d
        yield calc_cubic_points(a1, b1, c1, d1)


@cython.locals(p0=cython.complex, p1=cython.complex, p2=cython.complex, p3=cython.complex)
@cython.locals(mid=cython.complex, deriv3=cython.complex)
def split_cubic_into_two(p0, p1, p2, p3):
    mid = (p0 + 3 * (p1 + p2) + p3) * .125
    deriv3 = (p3 + p2 - p1 - p0) * .125
    return ((p0, (p0 + p1) * .5, mid - deriv3, mid),
            (mid, mid + deriv3, (p2 + p3) * .5, p3))


@cython.locals(p0=cython.complex, p1=cython.complex, p2=cython.complex, p3=cython.complex, _27=cython.double)
@cython.locals(mid1=cython.complex, deriv1=cython.complex, mid2=cython.complex, deriv2=cython.complex)
def split_cubic_into_three(p0, p1, p2, p3, _27=1/27):
    # we define 1/27 as a keyword argument so that it will be evaluated only
    # once but still in the scope of this function
    mid1 = (8*p0 + 12*p1 + 6*p2 + p3) * _27
    deriv1 = (p3 + 3*p2 - 4*p0) * _27
    mid2 = (p0 + 6*p1 + 12*p2 + 8*p3) * _27
    deriv2 = (4*p3 - 3*p1 - p0) * _27
    return ((p0, (2*p0 + p1) / 3.0, mid1 - deriv1, mid1),
            (mid1, mid1 + deriv1, mid2 - deriv2, mid2),
            (mid2, mid2 + deriv2, (p2 + 2*p3) / 3.0, p3))


@cython.returns(cython.complex)
@cython.locals(t=cython.double, p0=cython.complex, p1=cython.complex, p2=cython.complex, p3=cython.complex)
@cython.locals(_p1=cython.complex, _p2=cython.complex)
def cubic_approx_control(t, p0, p1, p2, p3):
    """Approximate a cubic bezier curve with a quadratic one.
       Returns the candidate control point."""
    _p1 = p0 + (p1 - p0) * 1.5
    _p2 = p3 + (p2 - p3) * 1.5
    return _p1 + (_p2 - _p1) * t


@cython.returns(cython.complex)
@cython.locals(a=cython.complex, b=cython.complex, c=cython.complex, d=cython.complex)
@cython.locals(ab=cython.complex, cd=cython.complex, p=cython.complex, h=cython.double)
def calc_intersect(a, b, c, d):
    """Calculate the intersection of ab and cd, given a, b, c, d."""

    ab = b - a
    cd = d - c
    p = ab * 1j
    try:
        h = dot(p, a - c) / dot(p, cd)
    except ZeroDivisionError:
        return complex(NAN, NAN)
    return c + cd * h


@cython.cfunc
@cython.returns(cython.int)
@cython.locals(tolerance=cython.double, p0=cython.complex, p1=cython.complex, p2=cython.complex, p3=cython.complex)
@cython.locals(mid=cython.complex, deriv3=cython.complex)
def cubic_farthest_fit_inside(p0, p1, p2, p3, tolerance):
    """Returns True if the cubic Bezier p entirely lies within a distance
    tolerance of origin, False otherwise.  Assumes that p0 and p3 do fit
    within tolerance of origin, and just checks the inside of the curve."""

    # First check p2 then p1, as p2 has higher error early on.
    if abs(p2) <= tolerance and abs(p1) <= tolerance:
        return True

    # Split.
    mid = (p0 + 3 * (p1 + p2) + p3) * .125
    if abs(mid) > tolerance:
        return False
    deriv3 = (p3 + p2 - p1 - p0) * .125
    return (cubic_farthest_fit_inside(p0, (p0+p1)*.5, mid-deriv3, mid, tolerance) and
            cubic_farthest_fit_inside(mid, mid+deriv3, (p2+p3)*.5, p3, tolerance))


@cython.cfunc
@cython.locals(tolerance=cython.double, _2_3=cython.double)
@cython.locals(q1=cython.complex, c0=cython.complex, c1=cython.complex, c2=cython.complex, c3=cython.complex)
def cubic_approx_quadratic(cubic, tolerance, _2_3=2/3):
    """Return the uniq quadratic approximating cubic that maintains
    endpoint tangents if that is within tolerance, None otherwise."""
    # we define 2/3 as a keyword argument so that it will be evaluated only
    # once but still in the scope of this function

    q1 = calc_intersect(*cubic)
    if math.isnan(q1.imag):
        return None
    c0 = cubic[0]
    c3 = cubic[3]
    c1 = c0 + (q1 - c0) * _2_3
    c2 = c3 + (q1 - c3) * _2_3
    if not cubic_farthest_fit_inside(0,
                                     c1 - cubic[1],
                                     c2 - cubic[2],
                                     0, tolerance):
        return None
    return c0, q1, c3


@cython.cfunc
@cython.locals(n=cython.int, tolerance=cython.double, _2_3=cython.double)
@cython.locals(i=cython.int)
@cython.locals(c0=cython.complex, c1=cython.complex, c2=cython.complex, c3=cython.complex)
@cython.locals(q0=cython.complex, q1=cython.complex, next_q1=cython.complex, q2=cython.complex, d1=cython.complex)
def cubic_approx_spline(cubic, n, tolerance, _2_3=2/3):
    """Approximate a cubic bezier curve with a spline of n quadratics.

    Returns None if no quadratic approximation is found which lies entirely
    within a distance `tolerance` from the original curve.
    """
    # we define 2/3 as a keyword argument so that it will be evaluated only
    # once but still in the scope of this function

    if n == 1:
        return cubic_approx_quadratic(cubic, tolerance)

    cubics = split_cubic_into_n_iter(cubic[0], cubic[1], cubic[2], cubic[3], n)

    # calculate the spline of quadratics and check errors at the same time.
    next_cubic = next(cubics)
    next_q1 = cubic_approx_control(0, *next_cubic)
    q2 = cubic[0]
    d1 = 0j
    spline = [cubic[0], next_q1]
    for i in range(1, n+1):

        # Current cubic to convert
        c0, c1, c2, c3 = next_cubic

        # Current quadratic approximation of current cubic
        q0 = q2
        q1 = next_q1
        if i < n:
            next_cubic = next(cubics)
            next_q1 = cubic_approx_control(i / (n-1), *next_cubic)
            spline.append(next_q1)
            q2 = (q1 + next_q1) * .5
        else:
            q2 = c3

        # End-point deltas
        d0 = d1
        d1 = q2 - c3

        if (abs(d1) > tolerance or
            not cubic_farthest_fit_inside(d0,
                                          q0 + (q1 - q0) * _2_3 - c1,
                                          q2 + (q1 - q2) * _2_3 - c2,
                                          d1,
                                          tolerance)):
            return None
    spline.append(cubic[3])

    return spline


@cython.locals(max_err=cython.double)
@cython.locals(n=cython.int)
def curve_to_quadratic(curve, max_err):
    """Return a quadratic spline approximating this cubic bezier.
    Raise 'ApproxNotFoundError' if no suitable approximation can be found
    with the given parameters.
    """

    curve = [complex(*p) for p in curve]

    for n in range(1, MAX_N + 1):
        spline = cubic_approx_spline(curve, n, max_err)
        if spline is not None:
            # done. go home
            return [(s.real, s.imag) for s in spline]

    raise ApproxNotFoundError(curve)



@cython.locals(l=cython.int, last_i=cython.int, i=cython.int)
def curves_to_quadratic(curves, max_errors):
    """Return quadratic splines approximating these cubic beziers.
    Raise 'ApproxNotFoundError' if no suitable approximation can be found
    for all curves with the given parameters.
    """

    curves = [[complex(*p) for p in curve] for curve in curves]
    assert len(max_errors) == len(curves)

    l = len(curves)
    splines = [None] * l
    last_i = i = 0
    n = 1
    while True:
        spline = cubic_approx_spline(curves[i], n, max_errors[i])
        if spline is None:
            if n == MAX_N:
                break
            n += 1
            last_i = i
            continue
        splines[i] = spline
        i = (i + 1) % l
        if i == last_i:
            # done. go home
            return [[(s.real, s.imag) for s in spline] for spline in splines]

    raise ApproxNotFoundError(curves)


if __name__ == '__main__':
    import random
    import timeit

    MAX_ERR = 5

    def generate_curve():
        return [
            tuple(float(random.randint(0, 2048)) for coord in range(2))
            for point in range(4)]

    def setup_curve_to_quadratic():
        return generate_curve(), MAX_ERR

    def setup_curves_to_quadratic():
        num_curves = 3
        return (
            [generate_curve() for curve in range(num_curves)],
            [MAX_ERR] * num_curves)

    def run_benchmark(
            benchmark_module, module, function, setup_suffix='', repeat=5, number=1000):
        setup_func = 'setup_' + function
        if setup_suffix:
            print('%s with %s:' % (function, setup_suffix), end='')
            setup_func += '_' + setup_suffix
        else:
            print('%s:' % function, end='')

        def wrapper(function, setup_func):
            function = globals()[function]
            setup_func = globals()[setup_func]
            def wrapped():
                return function(*setup_func())
            return wrapped
        results = timeit.repeat(wrapper(function, setup_func), repeat=repeat, number=number)
        print('\t%5.1fus' % (min(results) * 1000000. / number))

    def main():
        run_benchmark('cu2qu.benchmark', 'cu2qu', 'curve_to_quadratic')
        run_benchmark('cu2qu.benchmark', 'cu2qu', 'curves_to_quadratic')

    random.seed(1)
    main()
