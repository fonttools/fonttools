from __future__ import print_function, division, absolute_import

import random
import timeit

MAX_ERR = 5
MAX_N = 10

SETUP_CODE = '''
from cu2qu import %s
from __main__ import setup_%s
args = setup_%s()
'''


def generate_curve():
    return [
        tuple(float(random.randint(0, 2048)) for coord in range(2))
        for point in range(4)]


def setup_curve_to_quadratic():
    return generate_curve(), MAX_ERR, MAX_N


def setup_curves_to_quadratic():
    num_curves = 3
    return (
        [generate_curve() for curve in range(num_curves)],
        [MAX_ERR] * num_curves, MAX_N)


def run_test(name):
    print('%s:' % name)
    results = timeit.repeat(
        '%s(*args)' % name,
        setup=(SETUP_CODE % (name, name, name)),
        repeat=1000, number=1)
    print('min: %s s' % min(results))
    print('avg: %s s' % (sum(results) / len(results)))
    print()


def main():
    random.seed(1)
    run_test('curve_to_quadratic')
    run_test('curves_to_quadratic')


if __name__ == '__main__':
    main()
