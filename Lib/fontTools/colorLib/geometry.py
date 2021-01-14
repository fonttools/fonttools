"""Helpers for manipulating 2D points and vectors in COLR table."""

from math import copysign, cos, hypot, pi
from fontTools.misc.fixedTools import otRound


def _vector_between_points(a, b):
    return (b[0] - a[0], b[1] - a[1])


def _distance_between_points(a, b):
    return hypot(*_vector_between_points(a, b))


def _round_point(pt):
    return (otRound(pt[0]), otRound(pt[1]))


def _round_circle(centre, radius):
    return _round_point(centre), otRound(radius)


def _unit_vector(vec):
    length = hypot(*vec)
    if length == 0:
        return None
    return (vec[0] / length, vec[1] / length)


# This is the same tolerance used by Skia's SkTwoPointConicalGradient.cpp to detect
# when a radial gradient's focal point lies on the end circle.
_NEARLY_ZERO = 1 / (1 << 12)  # 0.000244140625


def _is_circle_inside_circle(c0, r0, c1, r1):
    dist = r0 + _distance_between_points(c0, c1)
    return abs(r1 - dist) <= _NEARLY_ZERO or r1 > dist


# The unit vector's X and Y components are respectively
#   U = (cos(α), sin(α))
# where α is the angle between the unit vector and the positive x axis.
_UNIT_VECTOR_THRESHOLD = cos(3 / 8 * pi)  # == sin(1/8 * pi) == 0.38268343236508984


def _nudge_point(pt, direction):
    # Nudge point coordinates -/+ 1.0 approximately based on the direction vector.
    # We divide the unit circle in 8 equal slices oriented towards the cardinal
    # (N, E, S, W) and intermediate (NE, SE, SW, NW) directions. To each slice we
    # map one of the possible cases: -1, 0, +1 for either X and Y coordinate.
    # E.g. Return (x + 1.0, y - 1.0) if unit vector is oriented towards SE, or
    # (x - 1.0, y) if it's pointing West, etc.
    uv = _unit_vector(direction)
    if not uv:
        return pt

    result = []
    for coord, uv_component in zip(pt, uv):
        if -_UNIT_VECTOR_THRESHOLD <= uv_component < _UNIT_VECTOR_THRESHOLD:
            # unit vector component near 0: direction almost orthogonal to the
            # direction of the current axis, thus keep coordinate unchanged
            result.append(coord)
        else:
            # nudge coord by +/- 1.0 in direction of unit vector
            result.append(coord + copysign(1.0, uv_component))
    return tuple(result)


def nudge_start_circle_almost_inside(c0, r0, c1, r1):
    """ Nudge c0 so it continues to be inside/outside c1 after rounding.

    The rounding of circle coordinates to integers may cause an abrupt change
    if the start circle c0 is so close to the end circle c1's perimiter that
    it ends up falling outside (or inside) as a result of the rounding.
    To keep the gradient unchanged, we nudge it in the right direction.

    See:
    https://github.com/googlefonts/colr-gradients-spec/issues/204
    https://github.com/googlefonts/picosvg/issues/158
    """
    inside_before_round = _is_circle_inside_circle(c0, r0, c1, r1)
    rc0, rr0 = _round_circle(c0, r0)
    rc1, rr1 = _round_circle(c1, r1)
    inside_after_round = _is_circle_inside_circle(rc0, rr0, rc1, rr1)

    if inside_before_round != inside_after_round:
        # at most 2 iterations ought to be enough to converge
        for _ in range(2):
            if rc0 == rc1:  # nowhere to nudge along a zero vector, bail out
                break
            if inside_after_round:
                direction = _vector_between_points(rc1, rc0)
            else:
                direction = _vector_between_points(rc0, rc1)
            rc0 = _nudge_point(rc0, direction)
            inside_after_round = _is_circle_inside_circle(rc0, rr0, rc1, rr1)
            if inside_before_round == inside_after_round:
                break
        else:  # ... or it's a bug
            raise AssertionError(
                f"Nudging circle <c0={c0}, r0={r0}> "
                f"{'inside' if inside_before_round else 'outside'} "
                f"<c1={c1}, r1={r1}> failed after two attempts!"
            )

    return rc0
