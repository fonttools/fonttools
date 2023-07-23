from fontTools.ttLib import newTable
from fontTools.pens.areaPen import AreaPen
from fontTools.varLib.models import piecewiseLinearMap
from fontTools.misc.cliTools import makeOutputFileName
import math
import logging
from pprint import pformat

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

SAMPLES = 8


__all__ = ["planWeightAxis", "addEmptyAvar", "getGlyphsetBlackness", "main"]


def getGlyphsetBlackness(glyphset, glyphs=None):
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


def planWeightAxis(
    glyphSetFunc,
    minValue,
    defaultValue,
    maxValue,
    weights=None,
    samples=None,
    glyphs=None,
):
    if weights is None:
        weights = WEIGHTS
    if samples is None:
        samples = SAMPLES
    if glyphs is None:
        glyphs = glyphSetFunc({}).keys()

    log.info("Weight min %g / default %g / max %g", minValue, defaultValue, maxValue)

    # if "avar" in font:
    #    log.debug("Checking that font doesn't have weight mapping already.")
    #    existingMapping = font["avar"].segments["wght"]
    #    if existingMapping and existingMapping != {-1: -1, 0: 0, +1: +1}:
    #        log.error("Font already has a `avar` weight mapping. Remove it.")

    out = {}
    outNormalized = {}

    upem = 1  # font["head"].unitsPerEm
    axisWeightAverage = {}
    for weight in sorted({minValue, defaultValue, maxValue}):
        glyphset = glyphSetFunc(location={"wght": weight})
        axisWeightAverage[weight] = getGlyphsetBlackness(glyphset, glyphs) / (
            upem * upem
        )

    log.debug("Calculated average glyph black ratio:\n%s", pformat(axisWeightAverage))

    outNormalized[-1] = -1
    for extremeValue in sorted({minValue, maxValue} - {defaultValue}):
        rangeMin = min(defaultValue, extremeValue)
        rangeMax = max(defaultValue, extremeValue)
        targetWeights = {w for w in weights if rangeMin < w < rangeMax}
        if not targetWeights:
            continue

        bias = -1 if extremeValue < defaultValue else 0

        log.info("Planning target weights %s.", sorted(targetWeights))
        log.info("Sampling %u points in range %g,%g.", samples, rangeMin, rangeMax)
        weightBlackness = axisWeightAverage.copy()
        for sample in range(1, samples + 1):
            weight = rangeMin + (rangeMax - rangeMin) * sample / (samples + 1)
            log.info("Sampling weight %g.", weight)
            glyphset = glyphSetFunc(location={"wght": weight})
            weightBlackness[weight] = getGlyphsetBlackness(glyphset, glyphs) / (
                upem * upem
            )
        log.debug("Sampled average glyph black ratio:\n%s", pformat(weightBlackness))

        blacknessWeight = {}
        for weight in sorted(weightBlackness):
            blacknessWeight[weightBlackness[weight]] = weight

        logMin = math.log(weightBlackness[rangeMin])
        logMax = math.log(weightBlackness[rangeMax])
        out[rangeMin] = rangeMin
        outNormalized[bias] = bias
        for weight in sorted(targetWeights):
            t = (weight - rangeMin) / (rangeMax - rangeMin)
            targetBlackness = math.exp(logMin + t * (logMax - logMin))
            targetWeight = piecewiseLinearMap(targetBlackness, blacknessWeight)
            log.info("Planned mapping weight %g to %g." % (weight, targetWeight))
            out[weight] = targetWeight
            outNormalized[t + bias] = (targetWeight - rangeMin) / (
                rangeMax - rangeMin
            ) + bias
        out[rangeMax] = rangeMax
        outNormalized[bias + 1] = bias + 1
    outNormalized[+1] = +1

    log.info("Planned mapping:\n%s", pformat(out))
    log.info("Planned normalized mapping:\n%s", pformat(outNormalized))
    return out, outNormalized


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
        "-w", "--weights", type=str, help="Space-separate list of weights to generate."
    )
    parser.add_argument("-s", "--samples", type=int, help="Number of samples.")
    parser.add_argument(
        "-g",
        "--glyphs",
        type=str,
        help="Space-separate list of glyphs to use for sampling.",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        help="Output font file name.",
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
        level=("DEBUG" if options.verbose else "ERROR" if options.quiet else "INFO")
    )

    font = TTFont(options.font)
    if not "fvar" in font:
        log.error("Not a variable font.")
        sys.exit(1)
    fvar = font["fvar"]
    wghtAxis = None
    for axis in fvar.axes:
        if axis.axisTag == "wght":
            wghtAxis = axis
            break

    if "avar" in font:
        existingMapping = font["avar"].segments["wght"]
        if wghtAxis:
            font["avar"].segments["wght"] = {}
    else:
        existingMapping = None

    if wghtAxis:
        if options.weights is not None:
            weights = [float(w) for w in options.weights.split()]
        else:
            weights = options.weights

        if options.glyphs is not None:
            glyphs = options.glyphs.split()
        else:
            glyphs = None

        out, outNormalized = planWeightAxis(
            font.getGlyphSet,
            wghtAxis.minValue,
            wghtAxis.defaultValue,
            wghtAxis.maxValue,
            weights=weights,
            samples=options.samples,
            glyphs=glyphs,
        )

        if options.plot:
            from matplotlib import pyplot

            pyplot.plot(
                sorted(outNormalized), [outNormalized[k] for k in sorted(outNormalized)]
            )
            pyplot.show()

        if existingMapping is not None:
            log.info("Existing weight mapping:\n%s", pformat(existingMapping))

    if "avar" not in font:
        addEmptyAvar(font)

    avar = font["avar"]
    if wghtAxis:
        avar.segments["wght"] = outNormalized

    designspaceSnippet = (
        '    <axis tag="wght" name="Weight" minimum="%g" maximum="%g" default="%g">\n'
        % (wghtAxis.minValue, wghtAxis.maxValue, wghtAxis.defaultValue)
    )
    for key, value in out.items():
        designspaceSnippet += '      <map input="%g" output="%g"/>\n' % (key, value)
    designspaceSnippet += "    </axis>"
    log.info("Designspace snippet:")
    print(designspaceSnippet)

    if options.output_file is None:
        outfile = makeOutputFileName(options.font, overWrite=True, suffix=".avar")
    else:
        outfile = options.output_file
    log.info("Saving %s", outfile)
    font.save(outfile)


if __name__ == "__main__":
    import sys

    sys.exit(main())
