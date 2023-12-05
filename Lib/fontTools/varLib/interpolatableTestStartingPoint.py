from .interpolatableHelpers import *


def test_starting_point(glyph0, glyph1, ix, tolerance, matching):
    if matching is None:
        matching = list(range(len(glyph0.isomorphisms)))
    contour0 = glyph0.isomorphisms[ix]
    contour1 = glyph1.isomorphisms[matching[ix]]
    m0Vectors = glyph0.greenVectors
    m1Vectors = [glyph1.greenVectors[i] for i in matching]

    c0 = contour0[0]
    # Next few lines duplicated below.
    costs = [vdiff_hypot2_complex(c0[0], c1[0]) for c1 in contour1]
    min_cost_idx, min_cost = min(enumerate(costs), key=lambda x: x[1])
    first_cost = costs[0]

    proposed_point = contour1[min_cost_idx][1]
    reverse = contour1[min_cost_idx][2]
    this_tolerance = min_cost / first_cost if first_cost else 1

    if min_cost < first_cost * tolerance:
        # c0 is the first isomorphism of the m0 master
        # contour1 is list of all isomorphisms of the m1 master
        #
        # If the two shapes are both circle-ish and slightly
        # rotated, we detect wrong start point. This is for
        # example the case hundreds of times in
        # RobotoSerif-Italic[GRAD,opsz,wdth,wght].ttf
        #
        # If the proposed point is only one off from the first
        # point (and not reversed), try harder:
        #
        # Find the major eigenvector of the covariance matrix,
        # and rotate the contours by that angle. Then find the
        # closest point again.  If it matches this time, let it
        # pass.

        num_points = len(glyph1.points[ix])
        leeway = num_points // 4
        if proposed_point <= leeway or proposed_point >= num_points - leeway:
            # Try harder
            contour0 = glyph0.isomorphismsNormalized[ix]
            contour1 = glyph1.isomorphismsNormalized[matching[ix]]

            c0 = contour0[0]
            costs = [vdiff_hypot2_complex(c0[0], c1[0]) for c1 in contour1]
            new_min_cost_idx, new_min_cost = min(enumerate(costs), key=lambda x: x[1])
            new_first_cost = costs[0]
            new_this_tolerance = new_min_cost / new_first_cost if new_first_cost else 1
            if new_this_tolerance > this_tolerance:
                proposed_point = contour1[new_min_cost_idx][1]
                reverse = contour1[new_min_cost_idx][2]
                this_tolerance = new_this_tolerance

    log.debug(
        "test-starting-point: tolerance %g",
        this_tolerance,
    )
    return this_tolerance, proposed_point, reverse
