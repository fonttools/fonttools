"""
Loads a COLRv1 font and upgrades it to COLRv2.
"""

from fontTools.ttLib.tables.otBase import OTTableWriter
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otTables import Paint, PaintFormat
from fontTools.misc.cliTools import makeOutputFileName
from collections import defaultdict
import logging
from pprint import pformat

__all__ = [
    "main",
]

log = logging.getLogger("fontTools.colorLib.COLRv1ToCOLRv2")


def objectToTuple(obj, layerList):
    if isinstance(obj, (int, float, str)):
        return obj

    name = type(obj).__name__

    if type(obj) == Paint and obj.Format == PaintFormat.PaintColrLayers:
        obj = [
            p
            for p in layerList[
                obj.FirstLayerIndex : obj.FirstLayerIndex + obj.NumLayers
            ]
        ]
        name = "PaintColrLayers"

    if isinstance(obj, (list, tuple)):
        return (name,) + tuple(objectToTuple(o, layerList) for o in obj)

    return (name,) + tuple(
        (attr, objectToTuple(getattr(obj, attr), layerList))
        for attr in sorted(obj.__dict__.keys())
    )


def replaceSelfAndDeltaPaintGlyphs(glyphName, obj, reverseGlyphMap=None):
    if isinstance(obj, (int, float, str)):
        return obj

    if obj[0] in ("list", "PaintColrLayers"):
        return tuple(
            replaceSelfAndDeltaPaintGlyphs(glyphName, o, reverseGlyphMap) for o in obj
        )

    if obj[0] != "Paint":
        return obj

    paintFormat = None
    paintGlyphName = None
    paintPaint = None
    for attr, val in obj[1:]:
        if attr == "Format":
            paintFormat = val
        if attr == "Glyph":
            paintGlyphName = val
        elif attr == "Paint":
            paintPaint = val

    if paintFormat != PaintFormat.PaintGlyph:
        return ("Paint",) + tuple(
            (k, replaceSelfAndDeltaPaintGlyphs(glyphName, v, reverseGlyphMap))
            for k, v in obj[1:]
        )

    # PaintGlyph

    if glyphName == paintGlyphName:
        return ("Paint", ("Format", PaintFormat.PaintGlyphSelf), ("Paint", paintPaint))

    if reverseGlyphMap is not None:
        glyphID = reverseGlyphMap.get(glyphName)
        paintGlyphID = reverseGlyphMap.get(paintGlyphName)
        delta = (paintGlyphID - glyphID) % 65536

        if abs(delta) > 8:
            return obj

        if delta < 65536 and ((glyphID + delta) % 65536 == paintGlyphID):
            return (
                "Paint",
                ("Format", PaintFormat.PaintGlyphDelta),
                ("DeltaGlyphID", delta),
                ("Paint", paintPaint),
            )

    return obj


def templateForObjectTuple(objTuple):
    if not isinstance(objTuple, tuple):
        return objTuple

    if objTuple[0] == "Paint":
        if all(
            not isinstance(o[1], tuple) or o[1][0] not in ("Paint", "PaintColrLayers")
            for o in objTuple[1:]
        ):
            # Leaf paint. Replace with variable.
            return ("PaintTemplateArgument",)

    return tuple(templateForObjectTuple(o) for o in objTuple)


def templateIsAllArguments(template):
    if template[0] == "PaintTemplateArgument":
        return True
    return template[0] == "PaintColrLayers" and all(
        templateIsAllArguments(o) for o in template[1:]
    )


def templateForObjectTuples(allTuples, arguments):
    assert isinstance(allTuples, (list, tuple))
    v0 = allTuples[0]
    t0 = type(v0)
    if any(type(t) != t0 for t in allTuples):
        return None

    if t0 in (int, float, str):
        if any(v != v0 for v in allTuples):
            return None
        return v0

    assert t0 == tuple
    if all(v == v0 for v in allTuples):
        return v0

    l0 = len(v0)
    if any(len(v) != l0 for v in allTuples):
        return None

    ret = tuple(templateForObjectTuples(l, arguments) for l in zip(*allTuples))
    if ret is not None and None in ret:
        ret = None

    if ret is not None:
        return ret

    if v0[0] == "Paint":
        paint = (
            "Paint",
            ("Format", PaintFormat.PaintTemplateArgument),
            ("ArgumentIndex", len(arguments)),
        )
        arguments.append(allTuples)

        return paint

    return None


# TODO Move to fontTools.ttLib.tables.otTables
PAINT_FORMAT_COST = {
    PaintFormat.PaintColrLayers: 5,
    PaintFormat.PaintSolid: 5,
    PaintFormat.PaintVarSolid: 9,
    PaintFormat.PaintLinearGradient: 16,
    PaintFormat.PaintVarLinearGradient: 20,
    PaintFormat.PaintRadialGradient: 16,
    PaintFormat.PaintVarRadialGradient: 20,
    PaintFormat.PaintSweepGradient: 12,
    PaintFormat.PaintVarSweepGradient: 16,
    PaintFormat.PaintGlyph: 6,
    PaintFormat.PaintColrGlyph: 3,
    PaintFormat.PaintTransform: 7,
    PaintFormat.PaintVarTransform: 11,
    PaintFormat.PaintTranslate: 8,
    PaintFormat.PaintVarTranslate: 12,
    PaintFormat.PaintScale: 8,
    PaintFormat.PaintVarScale: 12,
    PaintFormat.PaintScaleAroundCenter: 12,
    PaintFormat.PaintVarScaleAroundCenter: 16,
    PaintFormat.PaintScaleUniform: 6,
    PaintFormat.PaintVarScaleUniform: 10,
    PaintFormat.PaintScaleUniformAroundCenter: 10,
    PaintFormat.PaintVarScaleUniformAroundCenter: 14,
    PaintFormat.PaintRotate: 6,
    PaintFormat.PaintVarRotate: 10,
    PaintFormat.PaintRotateAroundCenter: 10,
    PaintFormat.PaintVarRotateAroundCenter: 14,
    PaintFormat.PaintSkew: 8,
    PaintFormat.PaintVarSkew: 12,
    PaintFormat.PaintSkewAroundCenter: 12,
    PaintFormat.PaintVarSkewAroundCenter: 16,
    PaintFormat.PaintComposite: 8,
    PaintFormat.PaintTemplateInstance: lambda numArgs: 5 + 3 * numArgs,
    PaintFormat.PaintTemplateArgument: 2,
}


def getSpecializedTemplateCost(template):
    if not isinstance(template, tuple):
        return 0, False
    if template[0] == "list":
        return 0, False
    if template[:2] == ("Paint", ("Format", PaintFormat.PaintTemplateArgument)):
        # Assume that PaintTemplateArguments are shared and insignificant as such.
        return 0, True
    if template[0] == "PaintColrLayers":
        results = [getSpecializedTemplateCost(o) for o in template[1:]]
        if not any(r[1] for r in results):
            return 0, False

        cost = sum(r[0] for r in results)
        return (
            PAINT_FORMAT_COST[PaintFormat.PaintColrLayers]
            + 4 * (len(template) - 1)
            + cost
        ), True

    results = [getSpecializedTemplateCost(o[1]) for o in template[1:]]
    if not any(r[1] for r in results):
        return 0, False

    cost = sum(r[0] for r in results)

    assert template[0] == "Paint"
    for attr, value in template[1:]:
        if attr == "Format":
            cost += PAINT_FORMAT_COST[value]
            break
    else:
        assert False, "PaintFormat not found in template"

    return cost, True


def getSpecializedNoTemplateCost(template, depth=0):
    if not isinstance(template, tuple):
        return 0, False
    if template[0] == "list":
        return 0, False
    if template[:2] == ("Paint", ("Format", PaintFormat.PaintTemplateArgument)):
        return 0, True
    if template[0] == "PaintColrLayers":
        results = [getSpecializedNoTemplateCost(o, depth + 1) for o in template[1:]]
        if depth > 0:
            # Assume the layers for this are shared from somewhere else.
            return PAINT_FORMAT_COST[PaintFormat.PaintColrLayers], False
        if not any(r[1] for r in results):
            return 0, False
        cost = sum(r[0] for r in results)
        return (
            PAINT_FORMAT_COST[PaintFormat.PaintColrLayers]
            + 4 * (len(template) - 1)
            + cost
        ), True

    results = [getSpecializedNoTemplateCost(o[1], depth + 1) for o in template[1:]]
    if not any(r[1] for r in results):
        return 0, False

    cost = sum(r[0] for r in results)

    assert template[0] == "Paint"
    for attr, value in template[1:]:
        if attr == "Format":
            cost += PAINT_FORMAT_COST[value]
            break
    else:
        assert False, "PaintFormat not found in template"

    return cost, True


def serializeObjectTuple(objTuple):
    if not isinstance(objTuple, tuple):
        return objTuple

    if objTuple[0] == "PaintColrLayers":
        paint = Paint()
        paint.Format = PaintFormat.PaintColrLayers

        layersTuple = objTuple[1:]

        layers = [serializeObjectTuple(layer) for layer in layersTuple]
        paint.layers = layers
        paint.layersTuple = layersTuple

        return paint

    if objTuple[0] == "list":
        return [serializeObjectTuple(o) for o in objTuple[1:]]

    obj = getattr(ot, objTuple[0])()
    for attr, value in objTuple[1:]:
        setattr(obj, attr, serializeObjectTuple(value))
    return obj


def collectPaintColrLayers(paint, allPaintColrLayers):
    if not isinstance(paint, Paint):
        return
    if hasattr(paint, "layers"):
        allPaintColrLayers.append(paint)
        for layer in paint.layers:
            collectPaintColrLayers(layer, allPaintColrLayers)
        return

    for value in paint.__dict__.values():
        collectPaintColrLayers(value, allPaintColrLayers)


def serializeLayers(glyphList, layerList):
    allPaintColrLayers = []
    for glyph in glyphList:
        collectPaintColrLayers(glyph.Paint, allPaintColrLayers)

    allPaintColrLayers = sorted(
        allPaintColrLayers, key=lambda p: (len(p.layers), p.layersTuple), reverse=True
    )

    layerListCache = {}
    for paint in allPaintColrLayers:
        paint.NumLayers = len(paint.layers)
        cached = layerListCache.get(paint.layersTuple)
        if cached is not None:
            paint.FirstLayerIndex = cached
        else:
            assert len(paint.layers) > 1, paint.layersTuple
            firstLayerIndex = paint.FirstLayerIndex = len(layerList)
            layerList.extend(paint.layers)

            layersTuple = paint.layersTuple
            layerListCache[layersTuple] = firstLayerIndex
            # Build cache entries for all sublists as well
            for i in range(0, len(layersTuple) - 1):
                # min() matches behavior of fontTools.colorLib.builder
                for j in range(i + 2, min(len(layersTuple) + 1, i + 2 + 32)):
                    sliceTuple = layersTuple[i:j]

                    # The following slows things down and has no effect on the result
                    # if sliceTuple in layerListCache:
                    #    continue

                    layerListCache[sliceTuple] = firstLayerIndex + i

        del paint.layers
        del paint.layersTuple


def rebuildColr(font, paintTuples):
    colr = font["COLR"].table
    glyphList = colr.BaseGlyphList.BaseGlyphPaintRecord
    for glyph in glyphList:
        glyphName = glyph.BaseGlyph
        glyph.Paint = serializeObjectTuple(paintTuples[glyphName])

    layerList = colr.LayerList.Paint = []
    serializeLayers(glyphList, layerList)

    log.info("%d glyph paints", len(glyphList))
    log.info("%d layer paints", len(layerList))

    font["COLR"].table = colr

    if log.isEnabledFor(logging.INFO):
        writer = OTTableWriter()
        colr.compile(writer, font)
        data = writer.getAllData()
        l = len(data)
        log.info("Constructed COLRv2 table is %d bytes", l)
        return l


def main(args=None):
    """Convert a COLRv1 color font to COLRv2"""
    from fontTools import configLogger

    if args is None:
        import sys

        args = sys.argv[1:]

    from fontTools.ttLib import TTFont
    import argparse

    parser = argparse.ArgumentParser(
        "fonttools colorLib.COLRv1ToCOLRv2",
        description="Convert a COLRv1 color font to COLRv2.",
    )
    parser.add_argument("font", metavar="font.ttf", help="Font file.")
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        help="Output font file name.",
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
    if not "COLR" in font:
        log.error("Not a COLR color font.")
        sys.exit(1)

    colr = font["COLR"].table

    glyphList = colr.BaseGlyphList.BaseGlyphPaintRecord
    layerList = colr.LayerList.Paint
    log.info("%d glyph paints", len(glyphList))
    log.info("%d layer paints", len(layerList))

    paintTuples = {}
    for glyph in glyphList:
        glyphName = glyph.BaseGlyph
        paint = glyph.Paint

        paintTuples[glyphName] = objectToTuple(paint, layerList)

    v1Size = None
    if log.isEnabledFor(logging.INFO):
        writer = OTTableWriter()
        colr.compile(writer, font)
        data = writer.getAllData()
        v1Size = len(data)
        log.info("Original COLRv1 table is %d bytes", v1Size)

    if False:
        log.info("Rebuilding original font.")
        rebuildColr(font, paintTuples)

    log.info("Detecting self/delta glyph paints.")
    reverseGlyphMap = font.getReverseGlyphMap()
    paintTuples = {
        k: replaceSelfAndDeltaPaintGlyphs(k, v, reverseGlyphMap)
        for k, v in paintTuples.items()
    }

    log.info("Templatizing paints.")

    genericTemplates = defaultdict(list)
    for glyphName, paintTuple in paintTuples.items():
        paintTemplate = templateForObjectTuple(paintTuple)
        if templateIsAllArguments(paintTemplate):
            continue
        genericTemplates[paintTemplate].append(glyphName)
    genericTemplates = {k: v for k, v in genericTemplates.items() if len(v) > 1}
    log.info(
        "%d unique templates for %d glyphs",
        len(genericTemplates),
        sum(len(v) for v in genericTemplates.values()),
    )

    if log.isEnabledFor(logging.DEBUG):
        log.debug(
            pformat(
                [
                    (len(v), v, k)
                    for k, v in sorted(
                        genericTemplates.items(), key=lambda x: len(x[1])
                    )
                ]
            )
        )

    specializedTemplates = {}
    for template, templateGlyphs in genericTemplates.items():
        allTuples = [paintTuples[g] for g in templateGlyphs]
        arguments = []
        specializedTemplate = templateForObjectTuples(allTuples, arguments)
        specializedTemplates[specializedTemplate] = (templateGlyphs, arguments)

    if log.isEnabledFor(logging.DEBUG):
        log.debug(
            pformat(
                [
                    (len(v), v, k)
                    for k, v in sorted(
                        specializedTemplates.items(), key=lambda x: len(x[0][1])
                    )
                ]
            )
        )

    skipped = 0
    for template, (templateGlyphs, arguments) in specializedTemplates.items():
        if not arguments:
            # Glyphs are identical. No need to templatize.
            skipped += 1
            continue

        numGlyphs = len(templateGlyphs)
        if numGlyphs == 2:
            # Only templatize if the template is cheaper than the non-templatized version.
            # We do this only for numGlyphs==2 because otherwise it's impractical to
            # accurately estimate the cost of the non-templatized version.

            templateCost, _ = getSpecializedTemplateCost(template)
            noTemplateCost, _ = getSpecializedNoTemplateCost(template)
            templatizationCost = (
                PAINT_FORMAT_COST[PaintFormat.PaintTemplateInstance](len(arguments))
                * numGlyphs
                + templateCost
            )
            noTemplatizationCost = noTemplateCost * numGlyphs
            if templatizationCost > noTemplatizationCost:
                skipped += 1
                continue

        for i, glyphName in enumerate(templateGlyphs):
            paintTuple = (
                "Paint",
                ("Format", PaintFormat.PaintTemplateInstance),
                ("TemplatePaint", template),
                ("NumArguments", len(arguments)),
                ("Arguments", ("list",) + tuple(args[i] for args in arguments)),
            )
            paintTuples[glyphName] = paintTuple
    log.info("Skipped %d templates as they didn't save space", skipped)

    log.info("Building COLRv2 font")
    v2Size = rebuildColr(font, paintTuples)

    if v1Size is not None:
        log.info(
            "COLRv2 table is %.3g%% smaller.",
            100 * (1 - v2Size / v1Size),
        )

    if options.output_file is None:
        outfile = makeOutputFileName(options.font, overWrite=True, suffix=".COLRv2")
    else:
        outfile = options.output_file
    if outfile:
        log.info("Saving %s", outfile)
        font.save(outfile)


if __name__ == "__main__":
    import sys

    sys.exit(main())
