from fontTools.varLib import _add_avar, load_designspace
from fontTools.varLib.models import VariationModel
from fontTools.varLib.varStore import VarStoreInstancer
from fontTools.misc.fixedTools import fixedToFloat as fi2fl
from fontTools.misc.cliTools import makeOutputFileName
from itertools import product
import logging

log = logging.getLogger("fontTools.varLib.avar")


def _denormalize(v, axis):
    return axis.defaultValue + v * (
        (axis.maxValue if v >= 0 else axis.minValue) - axis.defaultValue
    )


def mappings_from_avar(font, denormalize=True):
    fvarAxes = font["fvar"].axes
    axisMap = {a.axisTag: a for a in fvarAxes}
    axisTags = [a.axisTag for a in fvarAxes]
    axisIndexes = {a.axisTag: i for i, a in enumerate(fvarAxes)}
    if "avar" not in font:
        return {}, {}
    avar = font["avar"]
    axisMaps = {
        tag: seg
        for tag, seg in avar.segments.items()
        if seg and seg != {-1: -1, 0: 0, 1: 1}
    }
    mappings = []
    poles = set()

    if getattr(avar, "majorVersion", 1) == 2:
        varStore = avar.table.VarStore
        regions = varStore.VarRegionList.Region
        inputLocations = set()
        for varData in varStore.VarData:
            regionIndices = varData.VarRegionIndex
            for regionIndex in regionIndices:
                peakLocation = []
                corners = []
                region = regions[regionIndex]
                for axisIndex, axis in enumerate(region.VarRegionAxis):
                    if axis.PeakCoord == 0:
                        continue
                    axisTag = axisTags[axisIndex]
                    peakLocation.append((axisTag, axis.PeakCoord))
                    corner = []
                    if axis.StartCoord != 0:
                        corner.append((axisTag, axis.StartCoord))
                    if axis.EndCoord != 0:
                        corner.append((axisTag, axis.EndCoord))
                    corners.append(corner)
                corners = set(product(*corners))
                peakLocation = tuple(peakLocation)
                poles.add(peakLocation)
                inputLocations.add(peakLocation)
                inputLocations.update(corners)

        inputLocations = [
            dict(t)
            for t in sorted(
                inputLocations,
                key=lambda t: (len(t), tuple(axisIndexes[tag] for tag, _ in t)),
            )
        ]

        varIdxMap = avar.table.VarIdxMap
        instancer = VarStoreInstancer(varStore, fvarAxes)
        for location in inputLocations:
            instancer.setLocation(location)
            outputLocation = {}
            for axisIndex, axisTag in enumerate(axisTags):
                varIdx = axisIndex
                if varIdxMap is not None:
                    varIdx = varIdxMap[varIdx]
                delta = instancer[varIdx]
                if delta != 0:
                    v = location.get(axisTag, 0)
                    v = v + fi2fl(delta, 14)
                    # See https://github.com/fonttools/fonttools/pull/3598#issuecomment-2266082009
                    # v = max(-1, min(1, v))
                    outputLocation[axisTag] = v
            mappings.append((location, outputLocation))

        # Now we have all the mappings, find which ones are redundant
        # and remove them.
        inputLocations.insert(0, {})
        model = VariationModel(inputLocations, axisTags)
        modelMapping = model.mapping
        modelSupports = model.supports
        pins = set(poles)
        for pole in poles:
            location = dict(pole)
            i = inputLocations.index(location)
            i = modelMapping[i]
            support = modelSupports[i]
            supportAxes = set(support.keys())
            for supportIndex, (axisTag, (minV, _, maxV)) in enumerate(support.items()):
                for v in (minV, maxV):
                    for pin in pins:
                        pinLocation = dict(pin)
                        pinAxes = set(pinLocation.keys())
                        if pinAxes != supportAxes:
                            continue
                        if axisTag not in pinAxes:
                            continue
                        if pinLocation[axisTag] == v:
                            break
                else:
                    # No pin found. Go through the previous masters
                    # and find a suitable pin.
                    for candidateIdx in range(supportIndex):
                        candidate = modelSupports[candidateIdx]
                        candidateAxes = set(candidate.keys())
                        if candidateAxes != supportAxes:
                            continue
                        if axisTag not in candidateAxes:
                            continue
                        if candidateLocation[axisTag] == v:
                            pins.add(tuple(candidateLocation.items()))
        mappings = [
            (inputLoc, outputLoc)
            for inputLoc, outputLoc in mappings
            if tuple(inputLoc.items()) in pins
        ]

    if denormalize:
        for tag, seg in axisMaps.items():
            if tag not in axisMap:
                raise ValueError(f"Unknown axis tag {tag}")
            denorm = lambda v: _denormalize(v, axisMap[tag])
            axisMaps[tag] = {denorm(k): denorm(v) for k, v in seg.items()}

        for i, (inputLoc, outputLoc) in enumerate(mappings):
            inputLoc = {
                tag: _denormalize(val, axisMap[tag]) for tag, val in inputLoc.items()
            }
            outputLoc = {
                tag: _denormalize(val, axisMap[tag]) for tag, val in outputLoc.items()
            }
            mappings[i] = (inputLoc, outputLoc)

    return axisMaps, mappings


def main(args=None):
    """Add `avar` table from designspace file to variable font."""

    if args is None:
        import sys

        args = sys.argv[1:]

    from fontTools import configLogger
    from fontTools.ttLib import TTFont
    from fontTools.designspaceLib import DesignSpaceDocument
    import argparse

    parser = argparse.ArgumentParser(
        "fonttools varLib.avar",
        description="Add `avar` table from designspace file to variable font.",
    )
    parser.add_argument("font", metavar="varfont.ttf", help="Variable-font file.")
    parser.add_argument(
        "designspace",
        metavar="family.designspace",
        help="Designspace file.",
        nargs="?",
        default=None,
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        help="Output font file name.",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Run more verbosely."
    )

    options = parser.parse_args(args)

    configLogger(level=("INFO" if options.verbose else "WARNING"))

    font = TTFont(options.font)
    if not "fvar" in font:
        log.error("Not a variable font.")
        return 1

    if options.designspace is None:
        from pprint import pprint

        segments, mappings = mappings_from_avar(font)
        pprint(segments)
        pprint(mappings)
        print(len(mappings))
        return

    axisTags = [a.axisTag for a in font["fvar"].axes]

    ds = load_designspace(options.designspace, require_sources=False)

    if "avar" in font:
        log.warning("avar table already present, overwriting.")
        del font["avar"]

    _add_avar(font, ds.axes, ds.axisMappings, axisTags)

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
