from fontTools.varLib.models import supportScalar, normalizeValue
from fontTools.misc.fixedTools import MAX_F2DOT14

def _negate(*values):
    yield from (-1 * v for v in values)

def _revnegate(v):
    return (-v[2], -v[1], -v[0])

def _solvePinned(tent, axisLimit):

    axisMin, axisDef, axisMax = axisLimit
    assert axisMin == axisDef == axisMax

    support = {'tag': tent}
    scalar = supportScalar({'tag': axisDef}, support)
    if scalar == 0.0:
        return []
    return [(scalar, (-1, 0, +1))]


def _solveDefaultUnmoved(tent, axisLimit):

    axisMin, axisDef, axisMax = axisLimit
    lower, peak, upper = tent

    negative = lower < 0
    if negative:
        if axisMin == -1.0:
            return [(1, tent)]
        elif axisMin == 0.0:
            return []
    else:
        if axisMax == 1.0:
            return [(1, tent)]
        elif axisMax == 0.0:
            return []

    limit = axisMin if negative else axisMax

    # Rebase axis bounds onto the new limit, which then becomes the new -1.0 or +1.0.
    # The results are always positive, because both dividend and divisor are either
    # all positive or all negative.
    newLower = lower / limit
    newPeak = peak / limit
    newUpper = upper / limit
    # for negative TupleVariation, swap lower and upper to simplify procedure
    if negative:
        newLower, newUpper = newUpper, newLower

    # special case when innermost bound == peak == limit
    if newLower == newPeak == 1.0:
        loc = (-1.0, -1.0, -1.0) if negative else (1.0, 1.0, 1.0)
        return [(1, loc)]

    # case 1: the whole deltaset falls outside the new limit; we can drop it
    elif newLower >= 1.0:
        return []

    # case 2: only the peak and outermost bound fall outside the new limit;
    # we keep the deltaset, update peak and outermost bound and and scale deltas
    # by the scalar value for the restricted axis at the new limit.
    elif newPeak >= 1.0:
        scalar = supportScalar({'tag': limit}, {'tag': (lower, peak, upper)})
        newPeak = 1.0
        newUpper = 1.0
        if negative:
            newLower, newPeak, newUpper = _negate(newUpper, newPeak, newLower)
        loc = (newLower, newPeak, newUpper)
        return [(scalar, loc)]

    # case 3: peak falls inside but outermost limit still fits within F2Dot14 bounds;
    # we keep deltas as is and only scale the axes bounds. Deltas beyond -1.0
    # or +1.0 will never be applied as implementations must clamp to that range.
    elif newUpper <= 2.0:
        if negative:
            newLower, newPeak, newUpper = _negate(newUpper, newPeak, newLower)
        elif MAX_F2DOT14 < newUpper <= 2.0:
            # we clamp +2.0 to the max F2Dot14 (~1.99994) for convenience
            newUpper = MAX_F2DOT14
        loc = (newLower, newPeak, newUpper)
        return [(1, loc)]

    # case 4: new limit doesn't fit; we need to chop the deltaset into two 'tents',
    # because the shape of a triangle with part of one side cut off cannot be
    # represented as a triangle itself. It can be represented as sum of two triangles.
    # NOTE: This increases the file size!
    else:
        # duplicate the tent, then adjust lower/peak/upper so that the outermost limit
        # of the original tent is +/-2.0, whereas the new tent's starts as the old
        # one peaks and maxes out at +/-1.0.
        if negative:
            loc = (-2.0, -1 * newPeak, -1 * newLower)
            newloc = (-1.0, -1.0, -1 * newPeak)
        else:
            loc = (newLower, newPeak, MAX_F2DOT14)
            newloc = (newPeak, 1.0, 1.0)
        # the new tent's deltas are scaled by the difference between the scalar value
        # for the old tent at the desired limit...
        scalar1 = supportScalar({tag: limit}, {tag: (lower, peak, upper)})
        # ... and the scalar value for the clamped tent (with outer limit +/-2.0),
        # which can be simplified like this:
        scalar2 = 1 / (2 - newPeak)

        return [(scalar1, loc), (scalar2, newloc)]



def _solveWithoutGain(tent, axisLimit):
    axisMin, axisDef, axisMax = axisLimit
    lower, peak, upper = tent

    # axisMin <= axisDef <= lower < peak <= axisMax

    # case 3: outermost limit still fits within F2Dot14 bounds;
    # we keep deltas as is and only scale the axes bounds. Deltas beyond -1.0
    # or +1.0 will never be applied as implementations must clamp to that range.
    if axisDef + (axisMax - axisDef) * 2 >= upper:

        if axisDef + (axisMax - axisDef) * MAX_F2DOT14 < upper:
            # we clamp +2.0 to the max F2Dot14 (~1.99994) for convenience
            upper = axisDef + (axisMax - axisDef) * MAX_F2DOT14

        return [(1, (lower, peak, upper))]

    # case 4: new limit doesn't fit; we need to chop the deltaset into two 'tents',
    # because the shape of a triangle with part of one side cut off cannot be
    # represented as a triangle itself. It can be represented as sum of two triangles.
    # NOTE: This increases the file size!
    else:

        loc1 = (lower, peak, axisMax)
        scalar1 = 1

        loc2 = (peak, axisMax, axisMax)
        scalar2 = supportScalar({tag: axisMax}, {tag: tent})

        return [(scalar1, loc1), (scalar2, loc2)]


def _solveWithGain(tent, axisLimit):
    axisMin, axisDef, axisMax = axisLimit
    lower, peak, upper = tent

    # lower <= axisDef <= peak <= axisMax

    gain = supportScalar({tag: axisDef}, {tag: tent})
    out = [(gain, axisLimit)]


    # First, the positive side

    # case 3: outermost limit still fits within F2Dot14 bounds;
    # we keep deltas as is and only scale the axes bounds. Deltas beyond -1.0
    # or +1.0 will never be applied as implementations must clamp to that range.
    if axisDef + (axisMax - axisDef) * 2 >= upper:

        if axisDef + (axisMax - axisDef) * MAX_F2DOT14 < upper:
            # we clamp +2.0 to the max F2Dot14 (~1.99994) for convenience
            upper = axisDef + (axisMax - axisDef) * MAX_F2DOT14

        out.append((1 - gain, (axisDef, peak, upper)))

    # case 4: new limit doesn't fit; we need to chop the deltaset into two 'tents',
    # because the shape of a triangle with part of one side cut off cannot be
    # represented as a triangle itself. It can be represented as sum of two triangles.
    # NOTE: This increases the file size!
    else:

        loc1 = (axisDef, peak, axisMax)
        scalar1 = 1

        loc2 = (peak, axisMax, axisMax)
        scalar2 = supportScalar({tag: axisMax}, {tag: tent})

        out.append((scalar1 - gain, loc1))
        out.append((scalar2 - gain, loc2))


    # Now, the negative side

    # case 1neg: lower extends beyond axisMin: we chop.
    if lower <= axisMin:
        loc = (axisMin, axisMin, axisDef)
        scalar = supportScalar({tag: axisMin}, {tag: tent})

        out.append((scalar - gain, loc))

    # case 2neg: lower is betwen axisMin and axisDef: we add two deltasets to
    # keep it "up" all the way to end.
    else:
        loc1 = (axisMin, lower, axisDef)
        scalar1 = 0

        loc2 = (axisMin, axisMin, lower)
        scalar2 = 0

        out.append((scalar1 - gain, loc1))
        out.append((scalar2 - gain, loc2))

    return out


def _solveGeneral(tent, axisLimit):
    axisMin, axisDef, axisMax = axisLimit
    lower, peak, upper = tent

    # Mirror the problem such that axisDef is always <= peak
    if axisDef > peak:
        return [(scalar, _revnegate(t))
                for scalar,t
                in _solveGeneral(_revnegate(tent),
                                 _revnegate(axisLimit))]
    # axisDef <= peak

    # case 1: the whole deltaset falls outside the new limit; we can drop it
    if axisMax <= lower and axisMax < peak:
        return [] # No overlap

    # case 2: only the peak and outermost bound fall outside the new limit;
    # we keep the deltaset, update peak and outermost bound and and scale deltas
    # by the scalar value for the restricted axis at the new limit.
    if axisMax < peak:
        mult = supportScalar({'tag': axisMax}, {'tag': tent})
        tent = (lower, axisMax, axisMax)
        return [(scalar*mult, t) for scalar,t in _solveGeneral(tent, axisLimit)]

    # axisDef <= peak <= axisMax

    if axisDef <= lower and axisDef < peak:
        # No gain to carry
        return _solveWithoutGain(tent, axisLimit)
    else:
        return _solveWithGain(tent, axisLimit)

    raise NotImplementedError


def rebaseTent(tent, axisLimit):

    axisMin, axisDef, axisMax = axisLimit
    assert -1 <= axisMin <= axisDef <= axisMax <= +1

    lower, peak, upper = tent
    assert -2 <= lower <= peak <= upper <= +2

    assert peak != 0

    # Get the pinned case out of the way
    if axisMin == axisMax:
        return _solvePinned(tent, axisLimit)

    # If default isn't moving, get that out of the way as well
    if False and axisDef == 0:
        return _solveDefaultUnmoved(tent, axisLimit)

    sols = _solveGeneral(tent, axisLimit)
    n = lambda v: normalizeValue(v, axisLimit, extrapolate=True)
    sols = [(scalar, (n(v[0]), n(v[1]), n(v[2]))) for scalar,v in sols if scalar != 0]
    return sols
