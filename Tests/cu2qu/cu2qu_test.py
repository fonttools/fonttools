# Copyright 2016 Google Inc. All Rights Reserved.
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

import collections
import math
import unittest
import os
import json

from fontTools.cu2qu import curve_to_quadratic, curves_to_quadratic


DATADIR = os.path.join(os.path.dirname(__file__), 'data')

MAX_ERR = 5


class CurveToQuadraticTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Do the curve conversion ahead of time, and run tests on results."""
        with open(os.path.join(DATADIR, "curves.json"), "r") as fp:
            curves = json.load(fp)

        cls.single_splines = [
            curve_to_quadratic(c, MAX_ERR) for c in curves]
        cls.single_errors = [
            cls.curve_spline_dist(c, s)
            for c, s in zip(curves, cls.single_splines)]

        curve_groups = [curves[i:i + 3] for i in range(0, 300, 3)]
        cls.compat_splines = [
            curves_to_quadratic(c, [MAX_ERR] * 3) for c in curve_groups]
        cls.compat_errors = [
            [cls.curve_spline_dist(c, s) for c, s in zip(curve_group, splines)]
            for curve_group, splines in zip(curve_groups, cls.compat_splines)]

        cls.results = []

    @classmethod
    def tearDownClass(cls):
        """Print stats from conversion, as determined during tests."""

        for tag, results in cls.results:
            print('\n%s\n%s' % (
                tag, '\n'.join(
                    '%s: %s (%d)' % (k, '#' * (v // 10 + 1), v)
                    for k, v in sorted(results.items()))))

    def test_results_unchanged(self):
        """Tests that the results of conversion haven't changed since the time
        of this test's writing. Useful as a quick check whenever one modifies
        the conversion algorithm.
        """

        expected = {
            2: 6,
            3: 26,
            4: 82,
            5: 232,
            6: 360,
            7: 266,
            8: 28}

        results = collections.defaultdict(int)
        for spline in self.single_splines:
            n = len(spline) - 2
            results[n] += 1
        self.assertEqual(results, expected)
        self.results.append(('single spline lengths', results))

    def test_results_unchanged_multiple(self):
        """Test that conversion results are unchanged for multiple curves."""

        expected = {
            5: 11,
            6: 35,
            7: 49,
            8: 5}

        results = collections.defaultdict(int)
        for splines in self.compat_splines:
            n = len(splines[0]) - 2
            for spline in splines[1:]:
                self.assertEqual(len(spline) - 2, n,
                    'Got incompatible conversion results')
            results[n] += 1
        self.assertEqual(results, expected)
        self.results.append(('compatible spline lengths', results))

    def test_does_not_exceed_tolerance(self):
        """Test that conversion results do not exceed given error tolerance."""

        results = collections.defaultdict(int)
        for error in self.single_errors:
            results[round(error, 1)] += 1
            self.assertLessEqual(error, MAX_ERR)
        self.results.append(('single errors', results))

    def test_does_not_exceed_tolerance_multiple(self):
        """Test that error tolerance isn't exceeded for multiple curves."""

        results = collections.defaultdict(int)
        for errors in self.compat_errors:
            for error in errors:
                results[round(error, 1)] += 1
                self.assertLessEqual(error, MAX_ERR)
        self.results.append(('compatible errors', results))

    @classmethod
    def curve_spline_dist(cls, bezier, spline, total_steps=20):
        """Max distance between a bezier and quadratic spline at sampled points."""

        error = 0
        n = len(spline) - 2
        steps = total_steps // n
        for i in range(0, n - 1):
            p1 = spline[0] if i == 0 else p3
            p2 = spline[i + 1]
            if i < n - 1:
                p3 = cls.lerp(spline[i + 1], spline[i + 2], 0.5)
            else:
                p3 = spline[n + 2]
            segment = p1, p2, p3
            for j in range(steps):
                error = max(error, cls.dist(
                    cls.cubic_bezier_at(bezier, (j / steps + i) / n),
                    cls.quadratic_bezier_at(segment, j / steps)))
        return error

    @classmethod
    def lerp(cls, p1, p2, t):
        (x1, y1), (x2, y2) = p1, p2
        return x1 + (x2 - x1) * t, y1 + (y2 - y1) * t

    @classmethod
    def dist(cls, p1, p2):
        (x1, y1), (x2, y2) = p1, p2
        return math.hypot(x1 - x2, y1 - y2)

    @classmethod
    def quadratic_bezier_at(cls, b, t):
        (x1, y1), (x2, y2), (x3, y3) = b
        _t = 1 - t
        t2 = t * t
        _t2 = _t * _t
        _2_t_t = 2 * t * _t
        return (_t2 * x1 + _2_t_t * x2 + t2 * x3,
                _t2 * y1 + _2_t_t * y2 + t2 * y3)

    @classmethod
    def cubic_bezier_at(cls, b, t):
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = b
        _t = 1 - t
        t2 = t * t
        _t2 = _t * _t
        t3 = t * t2
        _t3 = _t * _t2
        _3_t2_t = 3 * t2 * _t
        _3_t_t2 = 3 * t * _t2
        return (_t3 * x1 + _3_t_t2 * x2 + _3_t2_t * x3 + t3 * x4,
                _t3 * y1 + _3_t_t2 * y2 + _3_t2_t * y3 + t3 * y4)


if __name__ == '__main__':
    unittest.main()
