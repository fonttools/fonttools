from fontTools.misc.roundTools import noRound
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otBase import OTTableWriter
from fontTools.varLib import HVAR_FIELDS, VVAR_FIELDS
from fontTools.varLib import builder, models, varStore
from fontTools.misc.fixedTools import fixedToFloat as fi2fl
from fontTools.misc.cliTools import makeOutputFileName
from itertools import product
import logging

log = logging.getLogger("fontTools.varLib.avar")


def add_VHVAR(font, tableFields):
    tableTag = tableFields.tableTag
    if tableTag in font:
        log.warning(tableTag + " table already present, overwriting.")
        del font[tableTag]
    log.info("Generating " + tableTag)
    VHVAR = newTable(tableTag)
    tableClass = getattr(ot, tableTag)
    vhvar = VHVAR.table = tableClass()
    vhvar.Version = 0x00010000
    font[tableTag] = VHVAR

    glyphOrder = font.getGlyphOrder()
    vhmtx = font[tableFields.metricsTag]
    advances = {g: vhmtx.metrics[g][0] for g in glyphOrder}
    phantomIndex = tableFields.phantomIndex

    axisTags = [a.axisTag for a in font["fvar"].axes]
    storeBuilder = varStore.OnlineVarStoreBuilder(axisTags)

    # There's two ways we can go from here:
    # 1. For each glyph, at each master peak, compute the value of the
    #    advance width at that peak.  Then pass these all to a VariationModel
    #    builder to compute back the deltas.
    # 2. For each master peak, pull out the deltas of the advance width directly,
    #    and feed these to the VarStoreBuilder, forgoing the remoding step.
    # We'll go with the second option, as it's simpler, faster, and more direct.
    gvar = font["gvar"]
    advMapping = {}
    allSupports = {}
    allDeltas = {}
    for glyphName in glyphOrder:
        supports = []
        deltas = []
        variations = gvar.variations[glyphName]

        for tv in variations:
            supports.append(tv.axes)
            phantoms = tv.coordinates[-4:]
            phantoms = phantoms[phantomIndex * 2 : phantomIndex * 2 + 2]
            assert len(phantoms) == 2
            phantoms[0] = phantoms[0][phantomIndex] if phantoms[0] is not None else 0
            phantoms[1] = phantoms[1][phantomIndex] if phantoms[1] is not None else 0
            deltas.append(phantoms[1] - phantoms[0])

        storeBuilder.setSupports(supports)
        advMapping[glyphName] = storeBuilder.storeDeltas(deltas, round=noRound)

        allSupports[glyphName] = supports
        allDeltas[glyphName] = deltas

    singleModel = models.allEqual(allSupports.values())

    directStore = None
    if singleModel:
        # Build direct mapping
        supports = supports
        varTupleList = builder.buildVarRegionList(supports, axisTags)
        varTupleIndexes = list(range(len(supports)))
        varData = builder.buildVarData(varTupleIndexes, [], optimize=False)
        for glyphName in glyphOrder:
            varData.addItem(allDeltas[glyphName], round=noRound)
        varData.optimize()
        directStore = builder.buildVarStore(varTupleList, [varData])

    # Build optimized indirect mapping
    indirectStore = storeBuilder.finish()
    mapping2 = indirectStore.optimize(use_NO_VARIATION_INDEX=False)
    advMapping = [mapping2[advMapping[g]] for g in glyphOrder]
    advanceMapping = builder.buildVarIdxMap(advMapping, glyphOrder)

    useDirect = False
    if directStore:
        # Compile both, see which is more compact

        writer = OTTableWriter()
        directStore.compile(writer, font)
        directSize = len(writer.getAllData())

        writer = OTTableWriter()
        indirectStore.compile(writer, font)
        advanceMapping.compile(writer, font)
        indirectSize = len(writer.getAllData())

        useDirect = directSize < indirectSize

    if useDirect:
        metricsStore = directStore
        advanceMapping = None
    else:
        metricsStore = indirectStore

    vhvar.VarStore = metricsStore
    setattr(vhvar, tableFields.advMapping, advanceMapping)
    setattr(vhvar, tableFields.sb1, None)
    setattr(vhvar, tableFields.sb2, None)


def add_HVAR(font):
    add_VHVAR(font, HVAR_FIELDS)


def add_VVAR(font):
    add_VHVAR(font, VVAR_FIELDS)


def main(args=None):
    """Add `HVAR` table to variable font."""

    if args is None:
        import sys

        args = sys.argv[1:]

    from fontTools import configLogger
    from fontTools.designspaceLib import DesignSpaceDocument
    import argparse

    parser = argparse.ArgumentParser(
        "fonttools varLib.hvar",
        description="Add `HVAR` table from to variable font.",
    )
    parser.add_argument("font", metavar="varfont.ttf", help="Variable-font file.")
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        help="Output font file name.",
    )

    options = parser.parse_args(args)

    configLogger(level="WARNING")

    font = TTFont(options.font)
    if not "fvar" in font:
        log.error("Not a variable font.")
        return 1

    add_HVAR(font)
    if "vmtx" in font:
        add_VVAR(font)

    if options.output_file is None:
        outfile = makeOutputFileName(options.font, overWrite=True, suffix=".hvar")
    else:
        outfile = options.output_file
    if outfile:
        log.info("Saving %s", outfile)
        font.save(outfile)


if __name__ == "__main__":
    import sys

    sys.exit(main())
