from .interpolatableHelpers import *


def test_starting_point(glyph0, glyph1, ix, tolerance, matching):
    if matching is None:
        matching = list(range(len(glyph0.isomorphisms)))
    contour0 = glyph0.isomorphisms[ix]
    contour1 = glyph1.isomorphisms[matching[ix]]
    m0Vectors = glyph0.greenVectors
    m1Vectors = [glyph1.greenVectors[i] for i in matching]

    proposed_point = 0
    reverse = False
    min_cost = first_cost = 1

    c0 = contour0[0]
    # Next few lines duplicated below.
    costs = [vdiff_hypot2_complex(c0[0], c1[0]) for c1 in contour1]
    min_cost_idx, min_cost = min(enumerate(costs), key=lambda x: x[1])
    first_cost = costs[0]
    proposed_point = contour1[min_cost_idx][1]

    return proposed_point, reverse, min_cost, first_cost
