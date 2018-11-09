from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.varLib.featureVars import (
    overlayFeatureVariations)


def test_explosion(n = 10):
    conds = []
    for i in range(n):
        end = i / n
        start = end - 1.
        region = [{'axis': (start, end)}]
        subst = {'g%.2g'%start: 'g%.2g'%end}
        conds.append((region, subst))
    overlaps = overlayFeatureVariations(conds)
    # XXX Currently fails for n > 2!
    #assert len(overlaps) == 2 * n - 1, overlaps
    return conds, overlaps

if __name__ == "__main__":
    import sys
    from pprint import pprint
    args = {}
    if len(sys.argv) > 1:
        args['n'] = int(sys.argv[1])
    input, output = test_explosion(**args)
    print("Input:")
    pprint(input)
    print()
    print("Output:")
    pprint(output)
