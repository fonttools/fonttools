from fontTools.pens.areaPen import AreaPen
from fontTools.varLib.models import piecewiseLinearMap
from fontTools.misc.cliTools import makeOutputFileName
from math import exp, log

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


def getGlyphsetBlackness(glyphset, frequencies=None):
    wght_sum = wdth_sum = 0
    for glyph_name in glyphset:
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
    font, minValue, defaultValue, maxValue, weights=WEIGHTS, frequencies=None
):
    print("Weight min/default/max:", minValue, defaultValue, maxValue)

    out = {}
    outNormalized = {}

    upem = font["head"].unitsPerEm
    axisWeightAverage = {}
    for weight in sorted({minValue, defaultValue, maxValue}):
        glyphset = font.getGlyphSet(location={"wght": weight})
        axisWeightAverage[weight] = getGlyphsetBlackness(glyphset, frequencies) / (
            upem * upem
        )

    print("Calculated average glyph black ratio:", axisWeightAverage)

    outNormalized[-1] = -1
    for extremeValue in sorted({minValue, maxValue} - {defaultValue}):
        rangeMin = min(defaultValue, extremeValue)
        rangeMax = max(defaultValue, extremeValue)
        targetWeights = {w for w in weights if rangeMin < w < rangeMax}
        if not targetWeights:
            continue

        bias = -1 if extremeValue < defaultValue else 0

        print("Planning target weights", sorted(targetWeights))
        print("Sampling", SAMPLES, "points in range", rangeMin, rangeMax)
        weightBlackness = axisWeightAverage.copy()
        for sample in range(1, SAMPLES + 1):
            weight = rangeMin + (rangeMax - rangeMin) * sample / (SAMPLES + 1)
            print("Sampling weight", weight)
            glyphset = font.getGlyphSet(location={"wght": weight})
            weightBlackness[weight] = getGlyphsetBlackness(glyphset, frequencies) / (
                upem * upem
            )
        print("Sampled average glyph black ratio:", weightBlackness)

        blacknessWeight = {}
        for weight in sorted(weightBlackness):
            blacknessWeight[weightBlackness[weight]] = weight

        logMin = log(weightBlackness[rangeMin])
        logMax = log(weightBlackness[rangeMax])
        out[rangeMin] = rangeMin
        outNormalized[bias] = bias
        for weight in sorted(targetWeights):
            t = (weight - rangeMin) / (rangeMax - rangeMin)
            targetBlackness = exp(logMin + t * (logMax - logMin))
            targetWeight = piecewiseLinearMap(targetBlackness, blacknessWeight)
            print("Planned mapping weight %g to %g" % (weight, targetWeight))
            out[weight] = targetWeight
            outNormalized[t + bias] = (targetWeight - rangeMin) / (
                rangeMax - rangeMin
            ) + bias
        out[rangeMax] = rangeMax
        outNormalized[bias + 1] = bias + 1
    outNormalized[+1] = +1

    from matplotlib import pyplot

    pyplot.plot(
        sorted(outNormalized), [outNormalized[k] for k in sorted(outNormalized)]
    )
    pyplot.show()

    print("Planned mapping:", out)
    print("Planned normalized mapping:", outNormalized)
    return out, outNormalized


def main(args=None):
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

    options = parser.parse_args(args)

    font = TTFont(options.font)
    fvar = font["fvar"]
    wghtAxis = slntAxis = None
    for axis in fvar.axes:
        if axis.axisTag == "wght":
            wghtAxis = axis
        elif axis.axisTag == "slnt":
            slntAxis = axis

    if "avar" in font:
        existingMapping = font["avar"].segments["wght"]
    else:
        existingMapping = None

    _, mapping = planWeightAxis(
        font, wghtAxis.minValue, wghtAxis.defaultValue, wghtAxis.maxValue
    )

    if existingMapping is not None:
        print("Existing weight mapping:", existingMapping)

    if "avar" not in font:
        font["avar"] = newTable("avar")
    avar = font["avar"]
    avar.segments["wght"] = mapping

    print("Saving font")
    outfile = makeOutputFileName(options.font, overWrite=True, suffix=".avar")
    font.save(outfile)


if __name__ == "__main__":
    import sys

    sys.exit(main())
