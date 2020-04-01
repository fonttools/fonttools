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

import os
import random

from benchmark import run_benchmark

MAX_ERR_EM = 0.002
DATADIR = os.path.join(
    os.path.dirname(__file__), os.path.pardir, 'tests', 'data')


def setup_fonts_to_quadratic_defcon():
    from defcon import Font
    return [[Font(os.path.join(DATADIR, 'RobotoSubset-Regular.ufo'))],
            MAX_ERR_EM]


def main():
    run_benchmark(
        'ufo_benchmark', 'cu2qu.ufo', 'fonts_to_quadratic',
        setup_suffix='defcon', repeat=10)


if __name__ == '__main__':
    random.seed(1)
    main()
