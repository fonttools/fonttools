from fontTools.ttLib import newTable
from fontTools.ttLib.tables._f_v_a_r import Axis as fvarAxis
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.basePen import NullPen
from fontTools.pens.statisticsPen import StatisticsPen
from fontTools.varLib.models import piecewiseLinearMap, normalizeValue
from fontTools.misc.cliTools import makeOutputFileName
import math
import logging
from pprint import pformat

__all__ = [
    "planWeightAxis",
    "planWidthAxis",
    "planSlantAxis",
    "planOpticalSizeAxis",
    "planAxis",
    "sanitizeWeight",
    "sanitizeWidth",
    "sanitizeSlant",
    "measureWeight",
    "measureWidth",
    "measureSlant",
    "normalizeLinear",
    "interpolateLinear",
    "normalizeLog",
    "interpolateLog",
    "makeDesignspaceSnippet",
    "addEmptyAvar",
    "main",
]

log = logging.getLogger("fontTools.varLib.avarPlanner")

WEIGHTS = [
    50,
    100,
    150,
    200,
    250,
    300,
    350,
    400,
    450,
    500,
    550,
    600,
    650,
    700,
    750,
    800,
    850,
    900,
    950,
]

WIDTHS = [
    25.0,
    37.5,
    50.0,
    62.5,
    75.0,
    87.5,
    100.0,
    112.5,
    125.0,
    137.5,
    150.0,
    162.5,
    175.0,
    187.5,
    200.0,
]

SLANTS = list(math.degrees(math.atan(d / 20.0)) for d in range(-20, 21))

SIZES = [
    8,
    9,
    10,
    11,
    12,
    14,
    18,
    24,
    30,
    36,
    48,
    60,
    72,
    96,
    120,
    144,
]


SAMPLES = 8


def normalizeLinear(value, rangeMin, rangeMax):
    """Linearly normalize value in [rangeMin, rangeMax] to [0, 1], with extrapolation."""
    return (value - rangeMin) / (rangeMax - rangeMin)


def interpolateLinear(t, a, b):
    """Linear interpolation between a and b, with t typically in [0, 1]."""
    return a + t * (b - a)


def normalizeLog(value, rangeMin, rangeMax):
    """Logarithmically normalize value in [rangeMin, rangeMax] to [0, 1], with extrapolation."""
    logMin = math.log(rangeMin)
    logMax = math.log(rangeMax)
    return (math.log(value) - logMin) / (logMax - logMin)


def interpolateLog(t, a, b):
    """Logarithmic interpolation between a and b, with t typically in [0, 1]."""
    logA = math.log(a)
    logB = math.log(b)
    return math.exp(logA + t * (logB - logA))


def measureWeight(glyphset, glyphs=None):
    """Measure the perceptual average weight of the given glyphs."""
    if isinstance(glyphs, dict):
        frequencies = glyphs
    else:
        frequencies = {g: 1 for g in glyphs}

    wght_sum = wdth_sum = 0
    for glyph_name in glyphs:
        if frequencies is not None:
            frequency = frequencies.get(glyph_name, 0)
            if frequency == 0:
                continue
        else:
            frequency = 1

        glyph = glyphset[glyph_name]

        pen = AreaPen(glyphset=glyphset)
        glyph.draw(pen)

        mult = glyph.width * frequency
        wght_sum += mult * abs(pen.value)
        wdth_sum += mult

    return wght_sum / wdth_sum


def measureWidth(glyphset, glyphs=None):
    """Measure the average width of the given glyphs."""
    if isinstance(glyphs, dict):
        frequencies = glyphs
    else:
        frequencies = {g: 1 for g in glyphs}

    wdth_sum = 0
    freq_sum = 0
    for glyph_name in glyphs:
        if frequencies is not None:
            frequency = frequencies.get(glyph_name, 0)
            if frequency == 0:
                continue
        else:
            frequency = 1

        glyph = glyphset[glyph_name]

        pen = NullPen()
        glyph.draw(pen)

        wdth_sum += glyph.width * frequency
        freq_sum += frequency

    return wdth_sum / freq_sum


def measureSlant(glyphset, glyphs=None):
    """Measure the perceptual average slant angle of the given glyphs."""
    if isinstance(glyphs, dict):
        frequencies = glyphs
    else:
        frequencies = {g: 1 for g in glyphs}

    slnt_sum = 0
    freq_sum = 0
    for glyph_name in glyphs:
        if frequencies is not None:
            frequency = frequencies.get(glyph_name, 0)
            if frequency == 0:
                continue
        else:
            frequency = 1

        glyph = glyphset[glyph_name]

        pen = StatisticsPen(glyphset=glyphset)
        glyph.draw(pen)

        mult = glyph.width * frequency
        slnt_sum += mult * pen.slant
        freq_sum += mult

    return -math.degrees(math.atan(slnt_sum / freq_sum))


def sanitizeWidth(userTriple, designTriple, pins, measurements):
    """Sanitize the width axis limits."""

    minVal, defaultVal, maxVal = (
        measurements[designTriple[0]],
        measurements[designTriple[1]],
        measurements[designTriple[2]],
    )

    calculatedMinVal = userTriple[1] * (minVal / defaultVal)
    calculatedMaxVal = userTriple[1] * (maxVal / defaultVal)

    log.info("Original width axis limits: %g:%g:%g", *userTriple)
    log.info(
        "Calculated width axis limits: %g:%g:%g",
        calculatedMinVal,
        userTriple[1],
        calculatedMaxVal,
    )

    if (
        abs(calculatedMinVal - userTriple[0]) / userTriple[1] > 0.05
        or abs(calculatedMaxVal - userTriple[2]) / userTriple[1] > 0.05
    ):
        log.warning("Calculated width axis min/max do not match user input.")
        log.warning(
            "  Current width axis limits: %g:%g:%g",
            *userTriple,
        )
        log.warning(
            "  Suggested width axis limits: %g:%g:%g",
            calculatedMinVal,
            userTriple[1],
            calculatedMaxVal,
        )

        return False

    return True


def sanitizeWeight(userTriple, designTriple, pins, measurements):
    """Sanitize the weight axis limits."""

    if len(set(userTriple)) < 3:
        return True

    minVal, defaultVal, maxVal = (
        measurements[designTriple[0]],
        measurements[designTriple[1]],
        measurements[designTriple[2]],
    )

    logMin = math.log(minVal)
    logDefault = math.log(defaultVal)
    logMax = math.log(maxVal)

    t = (userTriple[1] - userTriple[0]) / (userTriple[2] - userTriple[0])
    y = math.exp(logMin + t * (logMax - logMin))
    t = (y - minVal) / (maxVal - minVal)
    calculatedDefaultVal = userTriple[0] + t * (userTriple[2] - userTriple[0])

    log.info("Original weight axis limits: %g:%g:%g", *userTriple)
    log.info(
        "Calculated weight axis limits: %g:%g:%g",
        userTriple[0],
        calculatedDefaultVal,
        userTriple[2],
    )

    if abs(calculatedDefaultVal - userTriple[1]) / userTriple[1] > 0.05:
        log.warning("Calculated weight axis default does not match user input.")

        log.warning(
            "  Current weight axis limits: %g:%g:%g",
            *userTriple,
        )

        log.warning(
            "  Suggested weight axis limits, changing default: %g:%g:%g",
            userTriple[0],
            calculatedDefaultVal,
            userTriple[2],
        )

        t = (userTriple[2] - userTriple[0]) / (userTriple[1] - userTriple[0])
        y = math.exp(logMin + t * (logDefault - logMin))
        t = (y - minVal) / (defaultVal - minVal)
        calculatedMaxVal = userTriple[0] + t * (userTriple[1] - userTriple[0])
        log.warning(
            "  Suggested weight axis limits, changing maximum: %g:%g:%g",
            userTriple[0],
            userTriple[1],
            calculatedMaxVal,
        )

        t = (userTriple[0] - userTriple[2]) / (userTriple[1] - userTriple[2])
        y = math.exp(logMax + t * (logDefault - logMax))
        t = (y - maxVal) / (defaultVal - maxVal)
        calculatedMinVal = userTriple[2] + t * (userTriple[1] - userTriple[2])
        log.warning(
            "  Suggested weight axis limits, changing minimum: %g:%g:%g",
            calculatedMinVal,
            userTriple[1],
            userTriple[2],
        )

        return False

    return True


def sanitizeSlant(userTriple, designTriple, pins, measurements):
    """Sanitize the slant axis limits."""

    log.info("Original slant axis limits: %g:%g:%g", *userTriple)
    log.info(
        "Calculated slant axis limits: %g:%g:%g",
        measurements[designTriple[0]],
        measurements[designTriple[1]],
        measurements[designTriple[2]],
    )

    if (
        abs(measurements[designTriple[0]] - userTriple[0]) > 1
        or abs(measurements[designTriple[1]] - userTriple[1]) > 1
        or abs(measurements[designTriple[2]] - userTriple[2]) > 1
    ):
        log.warning("Calculated slant axis min/default/max do not match user input.")
        log.warning(
            "  Current slant axis limits: %g:%g:%g",
            *userTriple,
        )
        log.warning(
            "  Suggested slant axis limits: %g:%g:%g",
            measurements[designTriple[0]],
            measurements[designTriple[1]],
            measurements[designTriple[2]],
        )

        return False

    return True


def planAxis(
    axisTag,
    measureFunc,
    normalizeFunc,
    interpolateFunc,
    glyphSetFunc,
    axisLimits,
    values=None,
    samples=None,
    glyphs=None,
    designLimits=None,
    pins=None,
    sanitizeFunc=None,
):
    """Plan an axis."""

    if isinstance(axisLimits, fvarAxis):
        axisLimits = (axisLimits.minValue, axisLimits.defaultValue, axisLimits.maxValue)
    minValue, defaultValue, maxValue = axisLimits

    if samples is None:
        samples = SAMPLES
    if glyphs is None:
        glyphs = glyphSetFunc({}).keys()
    if pins is None:
        pins = {}
    else:
        pins = pins.copy()

    log.info("Value min %g / default %g / max %g", minValue, defaultValue, maxValue)
    triple = (minValue, defaultValue, maxValue)

    if designLimits is not None:
        log.info("Value design-limits min %g / default %g / max %g", *designLimits)
    else:
        designLimits = triple

    # if "avar" in font:
    #    log.debug("Checking that font doesn't have axis mapping already.")
    #    existingMapping = font["avar"].segments[axisTag]
    #    if existingMapping and existingMapping != {-1: -1, 0: 0, +1: +1}:
    #        log.error("Font already has a `avar` value mapping. Remove it.")

    if pins:
        log.info("Pins %s", sorted(pins.items()))
    pins.update(
        {
            minValue: designLimits[0],
            defaultValue: designLimits[1],
            maxValue: designLimits[2],
        }
    )

    out = {}
    outNormalized = {}

    axisMeasurements = {}
    for value in sorted({minValue, defaultValue, maxValue} | set(pins.keys())):
        glyphset = glyphSetFunc(location={axisTag: value})
        designValue = pins[value]
        axisMeasurements[designValue] = measureFunc(glyphset, glyphs)

    if sanitizeFunc is not None:
        log.info("Sanitizing axis limit values for the `%s` axis.", axisTag)
        sanitizeFunc(triple, designLimits, pins, axisMeasurements)

    log.debug("Calculated average value:\n%s", pformat(axisMeasurements))

    for (rangeMin, targetMin), (rangeMax, targetMax) in zip(
        list(sorted(pins.items()))[:-1],
        list(sorted(pins.items()))[1:],
    ):
        targetValues = {w for w in values if rangeMin < w < rangeMax}
        if not targetValues:
            continue

        normalizedMin = normalizeValue(rangeMin, triple)
        normalizedMax = normalizeValue(rangeMax, triple)
        normalizedTargetMin = normalizeValue(targetMin, designLimits)
        normalizedTargetMax = normalizeValue(targetMax, designLimits)

        log.info("Planning target values %s.", sorted(targetValues))
        log.info("Sampling %u points in range %g,%g.", samples, rangeMin, rangeMax)
        valueMeasurements = axisMeasurements.copy()
        for sample in range(1, samples + 1):
            value = rangeMin + (rangeMax - rangeMin) * sample / (samples + 1)
            log.debug("Sampling value %g.", value)
            glyphset = glyphSetFunc(location={axisTag: value})
            designValue = piecewiseLinearMap(value, pins)
            valueMeasurements[designValue] = measureFunc(glyphset, glyphs)
        log.debug("Sampled average value:\n%s", pformat(valueMeasurements))

        measurementValue = {}
        for value in sorted(valueMeasurements):
            measurementValue[valueMeasurements[value]] = value

        out[rangeMin] = targetMin
        outNormalized[normalizedMin] = normalizedTargetMin
        for value in sorted(targetValues):
            t = normalizeFunc(value, rangeMin, rangeMax)
            targetMeasurement = interpolateFunc(
                t, valueMeasurements[targetMin], valueMeasurements[targetMax]
            )
            targetValue = piecewiseLinearMap(targetMeasurement, measurementValue)
            log.debug("Planned mapping value %g to %g." % (value, targetValue))
            out[value] = targetValue
            valueNormalized = normalizedMin + (value - rangeMin) / (
                rangeMax - rangeMin
            ) * (normalizedMax - normalizedMin)
            outNormalized[valueNormalized] = normalizedTargetMin + (
                targetValue - targetMin
            ) / (targetMax - targetMin) * (normalizedTargetMax - normalizedTargetMin)
        out[rangeMax] = targetMax
        outNormalized[normalizedMax] = normalizedTargetMax

    log.info("Planned mapping for the `%s` axis:\n%s", axisTag, pformat(out))
    log.info(
        "Planned normalized mapping for the `%s` axis:\n%s",
        axisTag,
        pformat(outNormalized),
    )

    if all(abs(k - v) < 0.02 for k, v in outNormalized.items()):
        log.info("Detected identity mapping for the `%s` axis. Dropping.", axisTag)
        out = {}
        outNormalized = {}

    return out, outNormalized


def planWeightAxis(
    glyphSetFunc,
    axisLimits,
    weights=None,
    samples=None,
    glyphs=None,
    designLimits=None,
    pins=None,
    sanitize=False,
):
    """Plan a weight axis."""

    if weights is None:
        weights = WEIGHTS

    return planAxis(
        "wght",
        measureWeight,
        normalizeLinear,
        interpolateLog,
        glyphSetFunc,
        axisLimits,
        values=weights,
        samples=samples,
        glyphs=glyphs,
        designLimits=designLimits,
        pins=pins,
        sanitizeFunc=sanitizeWeight if sanitize else None,
    )


def planWidthAxis(
    glyphSetFunc,
    axisLimits,
    widths=None,
    samples=None,
    glyphs=None,
    designLimits=None,
    pins=None,
    sanitize=False,
):
    """Plan a width axis."""

    if widths is None:
        widths = WIDTHS

    return planAxis(
        "wdth",
        measureWidth,
        normalizeLinear,
        interpolateLinear,
        glyphSetFunc,
        axisLimits,
        values=widths,
        samples=samples,
        glyphs=glyphs,
        designLimits=designLimits,
        pins=pins,
        sanitizeFunc=sanitizeWidth if sanitize else None,
    )


def planSlantAxis(
    glyphSetFunc,
    axisLimits,
    slants=None,
    samples=None,
    glyphs=None,
    designLimits=None,
    pins=None,
    sanitize=False,
):
    """Plan a slant axis."""

    if slants is None:
        slants = SLANTS

    return planAxis(
        "slnt",
        measureSlant,
        normalizeLinear,
        interpolateLinear,
        glyphSetFunc,
        axisLimits,
        values=slants,
        samples=samples,
        glyphs=glyphs,
        designLimits=designLimits,
        pins=pins,
        sanitizeFunc=sanitizeSlant if sanitize else None,
    )


def planOpticalSizeAxis(
    glyphSetFunc,
    axisLimits,
    sizes=None,
    samples=None,
    glyphs=None,
    designLimits=None,
    pins=None,
    sanitize=False,
):
    """Plan a slant axis."""

    if sizes is None:
        sizes = SIZES

    return planAxis(
        "opsz",
        measureWeight,
        normalizeLog,
        interpolateLinear,
        glyphSetFunc,
        axisLimits,
        values=sizes,
        samples=samples,
        glyphs=glyphs,
        designLimits=designLimits,
        pins=pins,
    )


def makeDesignspaceSnippet(axisTag, axisName, axisLimit, mapping):
    """Make a designspace snippet for a single axis."""

    designspaceSnippet = (
        '    <axis tag="%s" name="%s" minimum="%g" default="%g" maximum="%g"'
        % ((axisTag, axisName) + axisLimit)
    )
    if mapping:
        designspaceSnippet += ">\n"
    else:
        designspaceSnippet += "/>"

    for key, value in mapping.items():
        designspaceSnippet += '      <map input="%g" output="%g"/>\n' % (key, value)

    if mapping:
        designspaceSnippet += "    </axis>"

    return designspaceSnippet


def addEmptyAvar(font):
    """Add an empty `avar` table to the font."""
    font["avar"] = avar = newTable("avar")
    for axis in fvar.axes:
        avar.segments[axis.axisTag] = {}


def main(args=None):
    """Plan the standard axis mappings for a variable font"""
    from fontTools import configLogger

    if args is None:
        import sys

        args = sys.argv[1:]

    from fontTools.ttLib import TTFont
    import argparse

    parser = argparse.ArgumentParser(
        "fonttools varLib.avarPlanner",
        description="Plan `avar` table for variable font",
    )
    parser.add_argument("font", metavar="font.ttf", help="Font file.")
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        help="Output font file name.",
    )
    parser.add_argument(
        "--weights", type=str, help="Space-separate list of weights to generate."
    )
    parser.add_argument(
        "--widths", type=str, help="Space-separate list of widths to generate."
    )
    parser.add_argument(
        "--slants", type=str, help="Space-separate list of slants to generate."
    )
    parser.add_argument(
        "--sizes", type=str, help="Space-separate list of optical-sizes to generate."
    )
    parser.add_argument("--samples", type=int, help="Number of samples.")
    parser.add_argument(
        "-s", "--sanitize", action="store_true", help="Sanitize axis limits"
    )
    parser.add_argument(
        "-g",
        "--glyphs",
        type=str,
        help="Space-separate list of glyphs to use for sampling.",
    )
    parser.add_argument(
        "--weight-design-limits",
        type=str,
        help="min:default:max in design units for the `wght` axis.",
    )
    parser.add_argument(
        "--width-design-limits",
        type=str,
        help="min:default:max in design units for the `wdth` axis.",
    )
    parser.add_argument(
        "--slant-design-limits",
        type=str,
        help="min:default:max in design units for the `slnt` axis.",
    )
    parser.add_argument(
        "--optical-size-design-limits",
        type=str,
        help="min:default:max in design units for the `opsz` axis.",
    )
    parser.add_argument(
        "--weight-pins",
        type=str,
        help="Space-separate list of before:after pins for the `wght` axis.",
    )
    parser.add_argument(
        "--width-pins",
        type=str,
        help="Space-separate list of before:after pins for the `wdth` axis.",
    )
    parser.add_argument(
        "--slant-pins",
        type=str,
        help="Space-separate list of before:after pins for the `slnt` axis.",
    )
    parser.add_argument(
        "--optical-size-pins",
        type=str,
        help="Space-separate list of before:after pins for the `opsz` axis.",
    )
    parser.add_argument(
        "-p", "--plot", action="store_true", help="Plot the resulting mapping."
    )

    logging_group = parser.add_mutually_exclusive_group(required=False)
    logging_group.add_argument(
        "-v", "--verbose", action="store_true", help="Run more verbosely."
    )
    logging_group.add_argument(
        "-q", "--quiet", action="store_true", help="Turn verbosity off."
    )

    options = parser.parse_args(args)

    configLogger(
        level=("DEBUG" if options.verbose else "WARNING" if options.quiet else "INFO")
    )

    font = TTFont(options.font)
    if not "fvar" in font:
        log.error("Not a variable font.")
        sys.exit(1)
    fvar = font["fvar"]
    wghtAxis = wdthAxis = slntAxis = opszAxis = None
    for axis in fvar.axes:
        if axis.axisTag == "wght":
            wghtAxis = axis
        elif axis.axisTag == "wdth":
            wdthAxis = axis
        elif axis.axisTag == "slnt":
            slntAxis = axis
        elif axis.axisTag == "opsz":
            opszAxis = axis

    wghtExistingMapping = (
        wdthExistingMapping
    ) = slntExistingMapping = opszExistingMapping = None
    if "avar" in font:
        if wghtAxis:
            wghtExistingMapping = font["avar"].segments["wght"]
            font["avar"].segments["wght"] = {}
        if wdthAxis:
            wdthExistingMapping = font["avar"].segments["wdth"]
            font["avar"].segments["wdth"] = {}
        if slntAxis:
            slntExistingMapping = font["avar"].segments["slnt"]
            font["avar"].segments["slnt"] = {}
        if opszAxis:
            opszExistingMapping = font["avar"].segments["opsz"]
            font["avar"].segments["opsz"] = {}

    if options.glyphs is not None:
        glyphs = options.glyphs.split()
        if ":" in options.glyphs:
            glyphs = {}
            for g in options.glyphs.split():
                if ":" in g:
                    glyph, frequency = g.split(":")
                    glyphs[glyph] = float(frequency)
                else:
                    glyphs[g] = 1.0
    else:
        glyphs = None

    if wghtAxis:
        log.info("Planning weight axis.")

        if options.weights is not None:
            weights = [float(w) for w in options.weights.split()]
        else:
            weights = None

        if options.weight_design_limits is not None:
            designLimits = [float(d) for d in options.weight_design_limits.split(":")]
            assert (
                len(designLimits) == 3
                and designLimits[0] <= designLimits[1] <= designLimits[2]
            )
        else:
            designLimits = None

        if options.weight_pins is not None:
            pins = {}
            for pin in options.weight_pins.split():
                before, after = pin.split(":")
                pins[float(before)] = float(after)
        else:
            pins = None

        weightMapping, weightMappingNormalized = planWeightAxis(
            font.getGlyphSet,
            wghtAxis,
            weights=weights,
            samples=options.samples,
            glyphs=glyphs,
            designLimits=designLimits,
            pins=pins,
            sanitize=options.sanitize,
        )

        if options.plot:
            from matplotlib import pyplot

            pyplot.plot(
                sorted(weightMappingNormalized),
                [weightMappingNormalized[k] for k in sorted(weightMappingNormalized)],
            )
            pyplot.show()

        if wghtExistingMapping is not None:
            log.info("Existing weight mapping:\n%s", pformat(wghtExistingMapping))

    if wdthAxis:
        log.info("Planning width axis.")

        if options.widths is not None:
            widths = [float(w) for w in options.widths.split()]
        else:
            widths = None

        if options.width_design_limits is not None:
            designLimits = [float(d) for d in options.width_design_limits.split(":")]
            assert (
                len(designLimits) == 3
                and designLimits[0] <= designLimits[1] <= designLimits[2]
            )
        else:
            designLimits = None

        if options.width_pins is not None:
            pins = {}
            for pin in options.width_pins.split():
                before, after = pin.split(":")
                pins[float(before)] = float(after)
        else:
            pins = None

        widthMapping, widthMappingNormalized = planWidthAxis(
            font.getGlyphSet,
            wdthAxis,
            widths=widths,
            samples=options.samples,
            glyphs=glyphs,
            designLimits=designLimits,
            pins=pins,
            sanitize=options.sanitize,
        )

        if options.plot:
            from matplotlib import pyplot

            pyplot.plot(
                sorted(widthMappingNormalized),
                [widthMappingNormalized[k] for k in sorted(widthMappingNormalized)],
            )
            pyplot.show()

        if wdthExistingMapping is not None:
            log.info("Existing width mapping:\n%s", pformat(wdthExistingMapping))

    if slntAxis:
        log.info("Planning slant axis.")

        if options.slants is not None:
            slants = [float(w) for w in options.slants.split()]
        else:
            slants = None

        if options.slant_design_limits is not None:
            designLimits = [float(d) for d in options.slant_design_limits.split(":")]
            assert (
                len(designLimits) == 3
                and designLimits[0] <= designLimits[1] <= designLimits[2]
            )
        else:
            designLimits = None

        if options.slant_pins is not None:
            pins = {}
            for pin in options.slant_pins.split():
                before, after = pin.split(":")
                pins[float(before)] = float(after)
        else:
            pins = None

        slantMapping, slantMappingNormalized = planSlantAxis(
            font.getGlyphSet,
            slntAxis,
            slants=slants,
            samples=options.samples,
            glyphs=glyphs,
            designLimits=designLimits,
            pins=pins,
            sanitize=options.sanitize,
        )

        if options.plot:
            from matplotlib import pyplot

            pyplot.plot(
                sorted(slantMappingNormalized),
                [slantMappingNormalized[k] for k in sorted(slantMappingNormalized)],
            )
            pyplot.show()

        if slntExistingMapping is not None:
            log.info("Existing slant mapping:\n%s", pformat(slntExistingMapping))

    if opszAxis:
        log.info("Planning optical-size axis.")

        if options.sizes is not None:
            sizes = [float(w) for w in options.sizes.split()]
        else:
            sizes = None

        if options.optical_size_design_limits is not None:
            designLimits = [
                float(d) for d in options.optical_size_design_limits.split(":")
            ]
            assert (
                len(designLimits) == 3
                and designLimits[0] <= designLimits[1] <= designLimits[2]
            )
        else:
            designLimits = None

        if options.optical_size_pins is not None:
            pins = {}
            for pin in options.optical_size_pins.split():
                before, after = pin.split(":")
                pins[float(before)] = float(after)
        else:
            pins = None

        opticalSizeMapping, opticalSizeMappingNormalized = planOpticalSizeAxis(
            font.getGlyphSet,
            opszAxis,
            sizes=sizes,
            samples=options.samples,
            glyphs=glyphs,
            designLimits=designLimits,
            pins=pins,
            sanitize=options.sanitize,
        )

        if options.plot:
            from matplotlib import pyplot

            pyplot.plot(
                sorted(opticalSizeMappingNormalized),
                [
                    opticalSizeMappingNormalized[k]
                    for k in sorted(opticalSizeMappingNormalized)
                ],
            )
            pyplot.show()

        if opszExistingMapping is not None:
            log.info("Existing size mapping:\n%s", pformat(opszExistingMapping))

    if "avar" not in font:
        addEmptyAvar(font)

    avar = font["avar"]

    log.info("Designspace snippet:")

    if wghtAxis:
        avar.segments["wght"] = weightMappingNormalized
        designspaceSnippet = makeDesignspaceSnippet(
            "wght",
            "Weight",
            (wghtAxis.minValue, wghtAxis.defaultValue, wghtAxis.maxValue),
            weightMapping,
        )
        print(designspaceSnippet)

    if wdthAxis:
        avar.segments["wdth"] = widthMappingNormalized
        designspaceSnippet = makeDesignspaceSnippet(
            "wdth",
            "Width",
            (wdthAxis.minValue, wdthAxis.defaultValue, wdthAxis.maxValue),
            widthMapping,
        )
        print(designspaceSnippet)

    if slntAxis:
        avar.segments["slnt"] = slantMappingNormalized
        designspaceSnippet = makeDesignspaceSnippet(
            "slnt",
            "Slant",
            (slntAxis.minValue, slntAxis.defaultValue, slntAxis.maxValue),
            slantMapping,
        )
        print(designspaceSnippet)

    if opszAxis:
        avar.segments["opsz"] = opticalSizeMappingNormalized
        designspaceSnippet = makeDesignspaceSnippet(
            "opsz",
            "OpticalSize",
            (opszAxis.minValue, opszAxis.defaultValue, opszAxis.maxValue),
            opticalSizeMapping,
        )
        print(designspaceSnippet)

    if options.output_file is None:
        outfile = makeOutputFileName(options.font, overWrite=True, suffix=".avar")
    else:
        outfile = options.output_file
    if outfile:
        log.info("Saving %s", outfile)
        font.save(outfile)


if __name__ == "__main__":
    import sys

    sys.exit(main())
