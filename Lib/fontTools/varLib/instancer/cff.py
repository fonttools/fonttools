"""Helpers for instancing CFF2 charstrings."""

from fontTools.misc.roundTools import otRound

# Generalized operators with relative x, y coordinates (flex's 13th is fd).
_PATH_OPERATORS = {"rmoveto", "rlineto", "rrcurveto", "flex"}
_STEM_OPERATORS = {"hstem", "hstemhm", "vstem", "vstemhm"}


def _isStemCommand(commands, i):
    op, args = commands[i]
    if op in _STEM_OPERATORS:
        return True
    # Implicit vstems before hintmask/cntrmask.
    return (
        op == ""
        and i + 1 < len(commands)
        and commands[i + 1][0] in {"hintmask", "cntrmask"}
        and not any(isinstance(arg, bytes) for arg in args)
    )


def _blendArgValues(arg, numValues):
    # A generalized blend arg is [default, *deltas, 1]; a number has no deltas.
    values = arg[:-1] if isinstance(arg, list) else [arg]
    if any(isinstance(value, list) for value in values):
        raise NotImplementedError("Nested blend lists not supported (yet)")
    assert len(values) <= numValues
    return values + [0] * (numValues - len(values))


def _numBlendArgValues(arg):
    return len(arg) - 1 if isinstance(arg, list) else 1


def convertToAbsoluteCoordinates(commands, vsIndex, getNumRegions):
    """Convert generalized CFF2 outline and stem coordinates in place.

    Return ``None`` on success, or the reason the commands cannot safely be
    converted. All flex operators must already have been generalized to
    ``flex``; an ambiguous variable ``flex1`` cannot be made absolute.
    """
    seenBlend = False
    for op, args in commands:
        if op == "vsindex":
            if seenBlend:
                return "vsindex after a blend"
        elif op == "flex1":
            return "flex1 changes direction across the design space"
        assert op not in {"hflex", "hflex1"}
        seenBlend = seenBlend or any(isinstance(arg, list) for arg in args)

    numValues = getNumRegions(vsIndex) + 1
    outline = [[0] * numValues, [0] * numValues]
    for i, (op, args) in enumerate(commands):
        if op == "vsindex":
            # Before any blend, so no deltas to carry over.
            vsIndex = args[0]
            numValues = getNumRegions(vsIndex) + 1
            outline = [axis[:1] + [0] * (numValues - 1) for axis in outline]
            continue
        if op in _PATH_OPERATORS:
            positions = outline
            numCoordinates = 12 if op == "flex" else len(args)
        elif _isStemCommand(commands, i):
            positions = [[0] * numValues]
            numCoordinates = len(args)
        else:
            continue
        for j in range(numCoordinates):
            k = j % len(positions)
            values = _blendArgValues(args[j], numValues)
            position = positions[k] = [p + v for p, v in zip(positions[k], values)]
            args[j] = position + [1] if any(position[1:]) else position[0]
    return None


def convertToRelativeCoordinates(commands, round=otRound):
    """Round absolute CFF2 coordinates and make them relative again in place."""

    def roundArg(arg):
        if isinstance(arg, list):
            return [round(arg[0])] + arg[1:]
        return round(arg)

    outline = [[0], [0]]
    for i, (op, args) in enumerate(commands):
        if op in _PATH_OPERATORS:
            positions = outline
            numCoordinates = 12 if op == "flex" else len(args)
        elif _isStemCommand(commands, i):
            positions = [[0]]
            numCoordinates = len(args)
        else:
            continue
        for j in range(numCoordinates):
            k = j % len(positions)
            arg = roundArg(args[j])
            numValues = max(len(positions[k]), _numBlendArgValues(arg))
            values = _blendArgValues(arg, numValues)
            previous = positions[k] + [0] * (numValues - len(positions[k]))
            diff = [v - p for v, p in zip(values, previous)]
            positions[k] = values
            args[j] = diff + [1] if any(diff[1:]) else diff[0]
        if op == "flex":
            args[12] = roundArg(args[12])
