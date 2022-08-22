from fontTools.varLib.models import supportScalar

def changeTupleVariationAxisLimit(var, axisTag, axisLimit):

    axisMin, axisDef, axisMax = axisLimit
    assert -1 <= axisMin <= axisDef <= axisMax <= +1

    # if axis is fully pinned down, get it out of the way
    if axisLimit.minimum == axisLimit.maximum:
        support = {axisTag: var.axes.pop(axisTag, (-1, 0, 1))}
        scalar = supportScalar({axisTag: axisLimit.default}, support)
        if scalar == 0.0:
            return []
        if scalar != 1.0:
            var.scaleDeltas(scalar)
        return [var]

    # skip when current axis is missing (i.e. doesn't participate), or when the
    # 'tent' isn't fully on either the negative or positive side
    lower, peak, upper = var.axes.get(axisTag, (-1, 0, 1))

    if peak == 0 or lower > peak or peak > upper or (lower < 0 and upper > 0):
        return [var]

    negative = lower < 0
    if negative:
        if axisLimit.minimum == -1.0:
            return [var]
        elif axisLimit.minimum == 0.0:
            return []
    else:
        if axisLimit.maximum == 1.0:
            return [var]
        elif axisLimit.maximum == 0.0:
            return []

    limit = axisLimit.minimum if negative else axisLimit.maximum

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
        var.axes[axisTag] = (-1.0, -1.0, -1.0) if negative else (1.0, 1.0, 1.0)
        return [var]

    # case 1: the whole deltaset falls outside the new limit; we can drop it
    elif newLower >= 1.0:
        return []

    # case 2: only the peak and outermost bound fall outside the new limit;
    # we keep the deltaset, update peak and outermost bound and and scale deltas
    # by the scalar value for the restricted axis at the new limit.
    elif newPeak >= 1.0:
        scalar = supportScalar({axisTag: limit}, {axisTag: (lower, peak, upper)})
        var.scaleDeltas(scalar)
        newPeak = 1.0
        newUpper = 1.0
        if negative:
            newLower, newPeak, newUpper = _negate(newUpper, newPeak, newLower)
        var.axes[axisTag] = (newLower, newPeak, newUpper)
        return [var]

    # case 3: peak falls inside but outermost limit still fits within F2Dot14 bounds;
    # we keep deltas as is and only scale the axes bounds. Deltas beyond -1.0
    # or +1.0 will never be applied as implementations must clamp to that range.
    elif newUpper <= 2.0:
        if negative:
            newLower, newPeak, newUpper = _negate(newUpper, newPeak, newLower)
        elif MAX_F2DOT14 < newUpper <= 2.0:
            # we clamp +2.0 to the max F2Dot14 (~1.99994) for convenience
            newUpper = MAX_F2DOT14
        var.axes[axisTag] = (newLower, newPeak, newUpper)
        return [var]

    # case 4: new limit doesn't fit; we need to chop the deltaset into two 'tents',
    # because the shape of a triangle with part of one side cut off cannot be
    # represented as a triangle itself. It can be represented as sum of two triangles.
    # NOTE: This increases the file size!
    else:
        # duplicate the tent, then adjust lower/peak/upper so that the outermost limit
        # of the original tent is +/-2.0, whereas the new tent's starts as the old
        # one peaks and maxes out at +/-1.0.
        newVar = TupleVariation(var.axes, var.coordinates)
        if negative:
            var.axes[axisTag] = (-2.0, -1 * newPeak, -1 * newLower)
            newVar.axes[axisTag] = (-1.0, -1.0, -1 * newPeak)
        else:
            var.axes[axisTag] = (newLower, newPeak, MAX_F2DOT14)
            newVar.axes[axisTag] = (newPeak, 1.0, 1.0)
        # the new tent's deltas are scaled by the difference between the scalar value
        # for the old tent at the desired limit...
        scalar1 = supportScalar({axisTag: limit}, {axisTag: (lower, peak, upper)})
        # ... and the scalar value for the clamped tent (with outer limit +/-2.0),
        # which can be simplified like this:
        scalar2 = 1 / (2 - newPeak)
        newVar.scaleDeltas(scalar1 - scalar2)

        return [var, newVar]

