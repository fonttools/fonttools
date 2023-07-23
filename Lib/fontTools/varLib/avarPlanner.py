from fontTools.ttLib import newTable
from fontTools.pens.areaPen import AreaPen
from fontTools.varLib.models import piecewiseLinearMap, normalizeValue
from fontTools.misc.cliTools import makeOutputFileName
import math
import logging
from pprint import pformat

__all__ = [
    "planWeightAxis",
    "planWidthAxis",
    "planAxis",
    "sanitizeWeight",
    "sanitizeWidth",
    "measureBlackness",
    "measureWidth",
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

SAMPLES = 8


def measureBlackness(glyphset, glyphs=None):
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

        wght_sum += abs(pen.value) * glyph.width * frequency
        wdth_sum += glyph.width * frequency

    return wght_sum / wdth_sum


def measureWidth(glyphset, glyphs=None):
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

        pen = AreaPen(glyphset=glyphset)
        glyph.draw(pen)

        wdth_sum += glyph.width * frequency
        freq_sum += frequency

    return wdth_sum / freq_sum


def sanitizeWidth(userTriple, designTriple, pins, measurements):
    if len(set(userTriple)) < 3:
        return True

    minVal, defaultVal, maxVal = (
        measurements[designTriple[0]],
        measurements[designTriple[1]],
        measurements[designTriple[2]],
    )

    calculatedMinVal = userTriple[0] * (minVal / defaultVal)
    calculatedMaxVal = userTriple[2] * (maxVal / defaultVal)

    log.info("Original axis limits: %g:%g:%g", *userTriple)
    log.info(
        "Calculated axis limits: %g:%g:%g",
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
            "  Suggested axis limits: %g:%g:%g",
            calculatedMinVal,
            userTriple[1],
            calculatedMaxVal,
        )

        return False

    return True


def sanitizeWeight(userTriple, designTriple, pins, measurements):
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

    log.info("Original axis limits: %g:%g:%g", *userTriple)
    log.info(
        "Calculated axis limits: %g:%g:%g",
        userTriple[0],
        calculatedDefaultVal,
        userTriple[2],
    )

    if abs(calculatedDefaultVal - userTriple[1]) / userTriple[1] > 0.05:
        log.warning("Calculated axis default does not match user input.")
        log.warning(
            "  Suggested axis limits, changing default: %g:%g:%g",
            userTriple[0],
            calculatedDefaultVal,
            userTriple[2],
        )

        t = (userTriple[2] - userTriple[0]) / (userTriple[1] - userTriple[0])
        y = math.exp(logMin + t * (logDefault - logMin))
        t = (y - minVal) / (defaultVal - minVal)
        calculatedMaxVal = userTriple[0] + t * (userTriple[1] - userTriple[0])
        log.warning(
            "  Suggested axis limits, changing maximum: %g:%g:%g",
            userTriple[0],
            userTriple[1],
            calculatedMaxVal,
        )

        t = (userTriple[0] - userTriple[2]) / (userTriple[1] - userTriple[2])
        y = math.exp(logMax + t * (logDefault - logMax))
        t = (y - maxVal) / (defaultVal - maxVal)
        calculatedMinVal = userTriple[2] + t * (userTriple[1] - userTriple[2])
        log.warning(
            "  Suggested axis limits, changing minimum: %g:%g:%g",
            calculatedMinVal,
            userTriple[1],
            userTriple[2],
        )

        return False

    return True


def planAxis(
    axisTag,
    measureFunc,
    glyphSetFunc,
    minValue,
    defaultValue,
    maxValue,
    values=None,
    samples=None,
    glyphs=None,
    designUnits=None,
    pins=None,
    sanitizeFunc=None,
):
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

    if designUnits is not None:
        log.info("Value design-units min %g / default %g / max %g", *designUnits)
    else:
        designUnits = triple

    # if "avar" in font:
    #    log.debug("Checking that font doesn't have axis mapping already.")
    #    existingMapping = font["avar"].segments[axisTag]
    #    if existingMapping and existingMapping != {-1: -1, 0: 0, +1: +1}:
    #        log.error("Font already has a `avar` value mapping. Remove it.")

    if pins:
        log.info("Pins %s", sorted(pins.items()))
    pins.update(
        {
            minValue: designUnits[0],
            defaultValue: designUnits[1],
            maxValue: designUnits[2],
        }
    )

    out = {}
    outNormalized = {}

    upem = 1  # font["head"].unitsPerEm
    axisMeasurements = {}
    for value in sorted({minValue, defaultValue, maxValue} | set(pins.values())):
        glyphset = glyphSetFunc(location={axisTag: value})

        designValue = piecewiseLinearMap(value, pins)

        axisMeasurements[designValue] = measureFunc(glyphset, glyphs) / (upem * upem)

    if sanitizeFunc is not None:
        log.info("Sanitizing axis limit values for the `%s` axis.", axisTag)
        sanitizeFunc(triple, designUnits, pins, axisMeasurements)

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
        normalizedTargetMin = normalizeValue(targetMin, designUnits)
        normalizedTargetMax = normalizeValue(targetMax, designUnits)

        log.info("Planning target values %s.", sorted(targetValues))
        log.info("Sampling %u points in range %g,%g.", samples, rangeMin, rangeMax)
        valueMeasurements = axisMeasurements.copy()
        for sample in range(1, samples + 1):
            value = rangeMin + (rangeMax - rangeMin) * sample / (samples + 1)
            log.info("Sampling value %g.", value)
            glyphset = glyphSetFunc(location={axisTag: value})
            designValue = piecewiseLinearMap(value, pins)
            valueMeasurements[designValue] = measureFunc(glyphset, glyphs) / (
                upem * upem
            )
        log.debug("Sampled average value:\n%s", pformat(valueMeasurements))

        measurementValue = {}
        for value in sorted(valueMeasurements):
            measurementValue[valueMeasurements[value]] = value

        logMin = math.log(valueMeasurements[targetMin])
        logMax = math.log(valueMeasurements[targetMax])
        out[rangeMin] = targetMin
        outNormalized[normalizedMin] = normalizedTargetMin
        for value in sorted(targetValues):
            t = (value - rangeMin) / (rangeMax - rangeMin)
            targetMeasurements = math.exp(logMin + t * (logMax - logMin))
            targetValue = piecewiseLinearMap(targetMeasurements, measurementValue)
            log.info("Planned mapping value %g to %g." % (value, targetValue))
            out[value] = targetValue
            outNormalized[
                normalizedMin + t * (normalizedMax - normalizedMin)
            ] = normalizedTargetMin + (targetValue - targetMin) / (
                targetMax - targetMin
            ) * (
                normalizedTargetMax - normalizedTargetMin
            )
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
    minValue,
    defaultValue,
    maxValue,
    weights=None,
    samples=None,
    glyphs=None,
    designUnits=None,
    pins=None,
    sanitize=False,
):
    if weights is None:
        weights = WEIGHTS

    return planAxis(
        "wght",
        measureBlackness,
        glyphSetFunc,
        minValue,
        defaultValue,
        maxValue,
        values=weights,
        samples=samples,
        glyphs=glyphs,
        designUnits=designUnits,
        pins=pins,
        sanitizeFunc=sanitizeWeight if sanitize else None,
    )


def planWidthAxis(
    glyphSetFunc,
    minValue,
    defaultValue,
    maxValue,
    widths=None,
    samples=None,
    glyphs=None,
    designUnits=None,
    pins=None,
    sanitize=False,
):
    if widths is None:
        widths = WIDTHS

    return planAxis(
        "wdth",
        measureWidth,
        glyphSetFunc,
        minValue,
        defaultValue,
        maxValue,
        values=widths,
        samples=samples,
        glyphs=glyphs,
        designUnits=designUnits,
        pins=pins,
        sanitizeFunc=sanitizeWidth if sanitize else None,
    )


def makeDesignspaceSnippet(axisTag, axisName, axisLimit, mapping):
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
    font["avar"] = newTable("avar")
    for axis in fvar.axes:
        font["avar"].segments[axis.axisTag] = {}


def main(args=None):
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
        "--weight-design-units",
        type=str,
        help="min:default:max in design units for the `wght` axis.",
    )
    parser.add_argument(
        "--width-design-units",
        type=str,
        help="min:default:max in design units for the `wdth` axis.",
    )
    parser.add_argument(
        "--weight-pins",
        type=str,
        help="Space-separate list of before:after pins. for the `wght` axis.",
    )
    parser.add_argument(
        "--width-pins",
        type=str,
        help="Space-separate list of before:after pins. for the `wdth` axis.",
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
    wghtAxis = wdthAxis = None
    for axis in fvar.axes:
        if axis.axisTag == "wght":
            wghtAxis = axis
        elif axis.axisTag == "wdth":
            wdthAxis = axis

    if "avar" in font:
        existingMapping = font["avar"].segments["wght"]
        if wghtAxis:
            font["avar"].segments["wght"] = {}
    else:
        existingMapping = None

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

    if wdthAxis:
        log.info("Planning width axis.")

        if options.widths is not None:
            widths = [float(w) for w in options.widths.split()]
        else:
            widths = None

        if options.width_design_units is not None:
            designUnits = [float(d) for d in options.width_design_units.split(":")]
        else:
            designUnits = None

        if options.width_pins is not None:
            pins = {}
            for pin in options.width_pins.split():
                before, after = pin.split(":")
                pins[float(before)] = float(after)
        else:
            pins = None

        widthMapping, widthMappingNormalized = planWidthAxis(
            font.getGlyphSet,
            wdthAxis.minValue,
            wdthAxis.defaultValue,
            wdthAxis.maxValue,
            widths=widths,
            samples=options.samples,
            glyphs=glyphs,
            designUnits=designUnits,
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

        if existingMapping is not None:
            log.info("Existing width mapping:\n%s", pformat(existingMapping))

    if wghtAxis:
        log.info("Planning weight axis.")

        if options.weights is not None:
            weights = [float(w) for w in options.weights.split()]
        else:
            weights = None

        if options.weight_design_units is not None:
            designUnits = [float(d) for d in options.weight_design_units.split(":")]
        else:
            designUnits = None

        if options.weight_pins is not None:
            pins = {}
            for pin in options.weight_pins.split():
                before, after = pin.split(":")
                pins[float(before)] = float(after)
        else:
            pins = None

        weightMapping, weightMappingNormalized = planWeightAxis(
            font.getGlyphSet,
            wghtAxis.minValue,
            wghtAxis.defaultValue,
            wghtAxis.maxValue,
            weights=weights,
            samples=options.samples,
            glyphs=glyphs,
            designUnits=designUnits,
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

        if existingMapping is not None:
            log.info("Existing weight mapping:\n%s", pformat(existingMapping))

    if "avar" not in font:
        addEmptyAvar(font)

    avar = font["avar"]

    if wdthAxis:
        avar.segments["wdth"] = widthMappingNormalized
        designspaceSnippet = makeDesignspaceSnippet(
            "wdth",
            "Width",
            (wdthAxis.minValue, wdthAxis.defaultValue, wdthAxis.maxValue),
            widthMapping,
        )
        log.info("Width axis designspace snippet:")
        print(designspaceSnippet)

    if wghtAxis:
        avar.segments["wght"] = weightMappingNormalized
        designspaceSnippet = makeDesignspaceSnippet(
            "wght",
            "Weight",
            (wghtAxis.minValue, wghtAxis.defaultValue, wghtAxis.maxValue),
            weightMapping,
        )
        log.info("Weight axis designspace snippet:")
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
