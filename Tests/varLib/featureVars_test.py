from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.varLib.featureVars import (
    overlayFeatureVariations)


def test_linear(n = 10):
    conds = []
    for i in range(n):
        end = i / n
        start = end - 1.
        region = [{'X': (start, end)}]
        subst = {'g%.2g'%start: 'g%.2g'%end}
        conds.append((region, subst))
    overlaps = overlayFeatureVariations(conds)
    assert len(overlaps) == 2 * n - 1, overlaps
    return conds, overlaps

def test_quadratic(n = 10):
    conds = []
    for i in range(1, n + 1):
        region = [{'X': (0, i / n),
                   'Y': (0, (n + 1 - i) / n)}]
        subst = {str(i): str(n + 1 - i)}
        conds.append((region, subst))
    overlaps = overlayFeatureVariations(conds)
    assert len(overlaps) == n * (n + 1) // 2, overlaps
    return conds, overlaps


def run(test, n, quiet):

    print()
    print("%s:" % test.__name__)
    input, output = test(n)
    if quiet:
        print(len(output))
    else:
        print()
        print("Input:")
        pprint(input)
        print()
        print("Output:")
        pprint(output)
        print()

if __name__ == "__main__":
    import sys
    from pprint import pprint
    quiet = False
    n = 3
    if len(sys.argv) > 1 and sys.argv[1] == '-q':
        quiet = True
        del sys.argv[1]
    if len(sys.argv) > 1:
        n = int(sys.argv[1])

    run(test_linear, n=n, quiet=quiet)
    run(test_quadratic, n=n, quiet=quiet)
