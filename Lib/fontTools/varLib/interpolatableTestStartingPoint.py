from .interpolatableHelpers import *

import cmath


def polyline_orientation_angle_sum(points):
    """
    Determine the orientation of a closed polyline using the angle sum method,
    handling coincident consecutive points by skipping them.

    Note: Does not handle cusp points (i.e. points where the polyline reverses direction).

    :param points: List of complex numbers representing vertices of the polyline.
    :return: +1, 0, or -1 depending on the orientation of the polyline.
    """
    # Remove consecutive duplicate points
    filtered_points = []
    for p in points:
        if not filtered_points or filtered_points[-1] != p:
            filtered_points.append(p)

    n = len(filtered_points)
    total_angle = 0
    for i in range(n):
        p1 = filtered_points[i]
        p2 = filtered_points[(i + 1) % n]
        p3 = filtered_points[(i + 2) % n]

        v1 = p2 - p1
        v2 = p3 - p2

        angle = cmath.phase(v2 / v1)
        total_angle += angle

    # We expect total_angle to be roughly a multiple of 2*pi for a closed polyline.
    # So, very relaxed check for near-zero:
    if abs(total_angle) < 1:
        return 0

    return +1 if total_angle > 0 else -1


def test_starting_point(glyph0, glyph1, ix, tolerance, matching):
    if matching is None:
        matching = list(range(len(glyph0.isomorphisms)))
    contour0 = glyph0.isomorphisms[ix]
    contour1 = glyph1.isomorphisms[matching[ix]]
    points0 = glyph0.points[ix]
    points1 = glyph1.points[matching[ix]]
    m0Vectors = glyph0.greenVectors
    m1Vectors = [glyph1.greenVectors[i] for i in matching]

    orientation0 = polyline_orientation_angle_sum([complex(*pt) for pt, _ in points0])
    orientation1 = polyline_orientation_angle_sum([complex(*pt) for pt, _ in points1])
    orientation_mismatch = orientation0 != orientation1

    c0 = contour0[0]
    # Next few lines duplicated below.
    costs = [
        (
            vdiff_hypot2_complex(c0.vector, c1.vector)
            if orientation_mismatch == c1.reverse
            else inf
        )
        for c1 in contour1
    ]
    min_cost_idx, min_cost = min(enumerate(costs), key=lambda x: x[1])
    first_cost = costs[0]
    proposed_point = contour1[min_cost_idx].start
    reverse = contour1[min_cost_idx].reverse

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
        leeway = 3
        if not reverse and (
            proposed_point <= leeway or proposed_point >= num_points - leeway
        ):
            # Try harder

            # Recover the covariance matrix from the GreenVectors.
            # This is a 2x2 matrix.
            transforms = []
            for vector in (m0Vectors[ix], m1Vectors[ix]):
                meanX = vector[1]
                meanY = vector[2]
                stddevX = vector[3] * 0.5
                stddevY = vector[4] * 0.5
                correlation = vector[5]
                if correlation:
                    correlation /= abs(vector[0])

                # https://cookierobotics.com/007/
                a = stddevX * stddevX  # VarianceX
                c = stddevY * stddevY  # VarianceY
                b = correlation * stddevX * stddevY  # Covariance

                delta = (((a - c) * 0.5) ** 2 + b * b) ** 0.5
                lambda1 = (a + c) * 0.5 + delta  # Major eigenvalue
                lambda2 = (a + c) * 0.5 - delta  # Minor eigenvalue
                theta = atan2(lambda1 - a, b) if b != 0 else (pi * 0.5 if a < c else 0)
                trans = Transform()
                # Don't translate here. We are working on the complex-vector
                # that includes more than just the points. It's horrible what
                # we are doing anyway...
                # trans = trans.translate(meanX, meanY)
                trans = trans.rotate(theta)
                trans = trans.scale(sqrt(lambda1), sqrt(lambda2))
                transforms.append(trans)

            trans = transforms[0]
            new_c0 = Isomorphism(
                [
                    complex(*trans.transformPoint((pt.real, pt.imag)))
                    for pt in c0.vector
                ],
                c0.start,
                c0.reverse,
            )
            trans = transforms[1]
            new_contour1 = []
            for c1 in contour1:
                new_c1 = Isomorphism(
                    [
                        complex(*trans.transformPoint((pt.real, pt.imag)))
                        for pt in c1.vector
                    ],
                    c1.start,
                    c1.reverse,
                )
                new_contour1.append(new_c1)

            # Next few lines duplicate from above.
            costs = [
                (
                    vdiff_hypot2_complex(new_c0.vector, new_c1.vector)
                    if orientation_mismatch == new_c1.reverse
                    else inf
                )
                for new_c1 in new_contour1
            ]
            min_cost_idx, min_cost = min(enumerate(costs), key=lambda x: x[1])
            first_cost = costs[0]
            if min_cost < first_cost * tolerance:
                # Don't report this
                # min_cost = first_cost
                # reverse = False
                # proposed_point = 0  # new_contour1[min_cost_idx][1]
                pass

    this_tolerance = min_cost / first_cost if first_cost else 1
    log.debug(
        "test-starting-point: tolerance %g",
        this_tolerance,
    )
    return this_tolerance, proposed_point, reverse
