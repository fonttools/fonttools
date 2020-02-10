from fontTools.ttLib import newTable
from .errors import ColorLibError


def buildCOLR(colorLayers):
    """Build COLR table from color layers mapping.

    Args:
        colorLayers: Dict[str, List[Tuple[str, int]]]: map of base glyph names (str)
            to lists of layer glyph names (str) and palette indices (int) tuples.

    Return:
        A new COLRv0 table.
    """
    from fontTools.ttLib.tables.C_O_L_R_ import LayerRecord

    colorLayerLists = {}
    for baseGlyphName, layers in colorLayers.items():
        colorLayerLists[baseGlyphName] = [
            LayerRecord(layerGlyphName, colorID) for layerGlyphName, colorID in layers
        ]

    colr = newTable("COLR")
    colr.version = 0
    colr.ColorLayers = colorLayerLists
    return colr


def buildCPAL(palettes):
    """Build CPAL table from list of color palettes.

    Args:
        palettes: List[List[Tuple[float, float, float, float]]]: list of lists
            colors encoded as tuples of (R, G, B, A) floats.

    Return:
        A new CPALv0 table.
    """
    from fontTools.ttLib.tables.C_P_A_L_ import Color

    if len({len(p) for p in palettes}) != 1:
        raise ColorLibError("color palettes have different lengths")
    cpal = newTable("CPAL")
    # TODO(anthotype): Support version 1 with palette types, labels and entry labels.
    cpal.version = 0
    cpal.numPaletteEntries = len(palettes[0])
    cpal.palettes = [
        [
            Color(*(round(v * 255) for v in (blue, green, red, alpha)))
            for red, green, blue, alpha in palette
        ]
        for palette in palettes
    ]
    return cpal
