from fontTools.varLib.models import supportScalar, normalizeValue
from fontTools.misc.fixedTools import MAX_F2DOT14
from functools import cache

def _revnegate(v):
    return (-v[2], -v[1], -v[0])


def _solve(tent, axisLimit):
    axisMin, axisDef, axisMax = axisLimit
    lower, peak, upper = tent

    # Mirror the problem such that axisDef is always <= peak
    if axisDef > peak:
        return [(scalar, _revnegate(t) if t is not None else None)
                for scalar,t
                in _solve(_revnegate(tent), _revnegate(axisLimit))]
    # axisDef <= peak

    # case 1: the whole deltaset falls outside the new limit; we can drop it
    if axisMax <= lower and axisMax < peak:
        return [] # No overlap

    # case 2: only the peak and outermost bound fall outside the new limit;
    # we keep the deltaset, update peak and outermost bound and and scale deltas
    # by the scalar value for the restricted axis at the new limit, and solve
    # recursively.
    if axisMax < peak:
        mult = supportScalar({'tag': axisMax}, {'tag': tent})
        tent = (lower, axisMax, axisMax)
        return [(scalar*mult, t) for scalar,t in _solve(tent, axisLimit)]

    # lower <= axisDef <= peak <= axisMax

    gain = supportScalar({'tag': axisDef}, {'tag': tent})
    out = [(gain, None)]

    # First, the positive side

    # outGain is the scalar of axisMax at the tent.
    outGain = supportScalar({'tag': axisMax}, {'tag': tent})

    # case 3a: gain is more than outGain. The tent down-slope crosses
    # the axis into negative. We have to split it into multiples.
    if gain > outGain:

        # Crossing point on the axis.
        crossing = peak + ((1 - gain) * (upper - peak) / (1 - outGain))

        loc = (peak, peak, crossing)
        scalar = 1

        # The part before the crossing point.
        out.append((scalar - gain, loc))

        # The part after the crossing point may use one or two tents,
        # depending on whether upper is before axisMax or not, in one
        # case we need to keep it down to eternity.

        # case 3a1, similar to case 1neg; just one tent needed.
        if upper >= axisMax:
            loc = (crossing, axisMax, axisMax)
            scalar = supportScalar({'tag': axisMax}, {'tag': tent})

            out.append((scalar - gain, loc))

        # case 3a2, similar to case 2neg; two tents needed, to keep
        # down to eternity.
        else:
            # Downslope.
            loc1 = (crossing, upper, axisMax)
            scalar1 = 0

            # Eternity justify.
            loc2 = (upper, axisMax, axisMax)
            scalar2 = supportScalar({'tag': axisMax}, {'tag': tent})

            out.append((scalar1 - gain, loc1))
            out.append((scalar2 - gain, loc2))

    # case 3: outermost limit still fits within F2Dot14 bounds;
    # we keep deltas as is and only scale the axes bounds. Deltas beyond -1.0
    # or +1.0 will never be applied as implementations must clamp to that range.
    elif axisDef + (axisMax - axisDef) * 2 >= upper:

        if axisDef + (axisMax - axisDef) * MAX_F2DOT14 < upper:
            # we clamp +2.0 to the max F2Dot14 (~1.99994) for convenience
            upper = axisDef + (axisMax - axisDef) * MAX_F2DOT14

        loc = (max(axisDef, lower), peak, upper)

        # Don't add a dirac delta!
        if upper > axisDef:
            out.append((1 - gain, loc))

    # case 4: new limit doesn't fit; we need to chop into two tents,
    # because the shape of a triangle with part of one side cut off
    # cannot be represented as a triangle itself.
    else:

        loc1 = (max(axisDef, lower), peak, axisMax)
        scalar1 = 1

        loc2 = (peak, axisMax, axisMax)
        scalar2 = supportScalar({'tag': axisMax}, {'tag': tent})

        out.append((scalar1 - gain, loc1))
        # Don't add a dirac delta!
        if (peak < axisMax):
            out.append((scalar2 - gain, loc2))


    # Now, the negative side

    # case 1neg: lower extends beyond axisMin: we chop. Simple.
    if lower <= axisMin:
        loc = (axisMin, axisMin, axisDef)
        scalar = supportScalar({'tag': axisMin}, {'tag': tent})

        out.append((scalar - gain, loc))

    # case 2neg: lower is betwen axisMin and axisDef: we add two
    # deltasets to # keep it down all the way to eternity.
    else:
        # Downslope.
        loc1 = (axisMin, lower, axisDef)
        scalar1 = 0

        # Eternity justify.
        loc2 = (axisMin, axisMin, lower)
        scalar2 = 0

        out.append((scalar1 - gain, loc1))
        out.append((scalar2 - gain, loc2))

    return out


@cache
def rebaseTent(tent, axisLimit):

    axisMin, axisDef, axisMax = axisLimit
    assert -1 <= axisMin <= axisDef <= axisMax <= +1

    lower, peak, upper = tent
    assert -2 <= lower <= peak <= upper <= +2

    assert peak != 0

    sols = _solve(tent, axisLimit)

    n = lambda v: normalizeValue(v, axisLimit, extrapolate=True)
    sols = [(scalar, (n(v[0]), n(v[1]), n(v[2])) if v is not None else None) for scalar,v in sols if scalar != 0]

    return sols
