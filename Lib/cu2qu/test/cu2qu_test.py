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


from __future__ import print_function, division, absolute_import

import collections
import unittest
import random

from cu2qu import curve_to_quadratic, curves_to_quadratic
from cu2qu.benchmark import generate_curve

MAX_ERR = 5


class CurveToQuadraticTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Do the curve conversion ahead of time, and run tests on results."""

        random.seed(1)
        curves = [generate_curve() for i in range(1000)]

        cls.single_splines, cls.single_errors = zip(*[
            curve_to_quadratic(c, MAX_ERR) for c in curves])

        cls.compat_splines, cls.compat_errors = zip(*[
            curves_to_quadratic(curves[i:i + 3], [MAX_ERR] * 3)
            for i in range(0, 300, 3)])

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
            3: 5,
            4: 31,
            5: 74,
            6: 228,
            7: 416,
            8: 242,
            9: 4}

        results = collections.defaultdict(int)
        for spline in self.single_splines:
            n = len(spline) - 1
            results[n] += 1
        self.assertEqual(results, expected)
        self.results.append(('single spline lengths', results))

    def test_results_unchanged_multiple(self):
        """Test that conversion results are unchanged for multiple curves."""

        expected = {
            6: 3,
            7: 34,
            8: 62,
            9: 1}

        results = collections.defaultdict(int)
        for splines in self.compat_splines:
            n = len(splines[0]) - 1
            for spline in splines[1:]:
                self.assertEqual(len(spline) - 1, n,
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


if __name__ == '__main__':
    unittest.main()
