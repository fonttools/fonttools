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

import random
import timeit

MAX_ERR = 5

SETUP_CODE = '''
from %(module)s import %(function)s
from %(benchmark_module)s import %(setup_function)s
args = %(setup_function)s()
'''


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
        benchmark_module, module, function, setup_suffix='', repeat=1000):
    setup_func = 'setup_' + function
    if setup_suffix:
        print('%s with %s:' % (function, setup_suffix), end='')
        setup_func += '_' + setup_suffix
    else:
        print('%s:' % function, end='')
    results = timeit.repeat(
        '%s(*args)' % function,
        setup=(SETUP_CODE % {
            'benchmark_module': benchmark_module, 'setup_function': setup_func,
            'module': module, 'function': function}),
        repeat=repeat, number=1)
    print('\tavg=%dus' % (sum(results) / len(results) * 1000000.),
          '\tmin=%dus' % (min(results) * 1000000.))


def main():
    run_benchmark('benchmark', 'cu2qu', 'curve_to_quadratic')
    run_benchmark('benchmark', 'cu2qu', 'curves_to_quadratic')


if __name__ == '__main__':
    random.seed(1)
    main()
