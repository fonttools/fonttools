from typing import Dict, List, Tuple
from fontTools.ttLib.tables.C_O_L_R_ import LayerRecord, table_C_O_L_R_
from fontTools.ttLib.tables.C_P_A_L_ import Color, table_C_P_A_L_
from .errors import ColorLibError


def buildCOLR(colorLayers: Dict[str, List[Tuple[str, int]]]) -> table_C_O_L_R_:
    """Build COLR table from color layers mapping.

    Args:
        colorLayers: : map of base glyph names to lists of (layer glyph names,
            palette indices) tuples.

    Return:
        A new COLRv0 table.
    """
    colorLayerLists = {}
    for baseGlyphName, layers in colorLayers.items():
        colorLayerLists[baseGlyphName] = [
            LayerRecord(layerGlyphName, colorID) for layerGlyphName, colorID in layers
        ]

    colr = table_C_O_L_R_()
    colr.version = 0
    colr.ColorLayers = colorLayerLists
    return colr


def buildCPAL(
    palettes: List[List[Tuple[float, float, float, float]]]
) -> table_C_P_A_L_:
    """Build CPAL table from list of color palettes.

    Args:
        palettes: : list of lists of colors encoded as tuples of (R, G, B, A) floats.

    Return:
        A new CPALv0 table.
    """
    if len({len(p) for p in palettes}) != 1:
        raise ColorLibError("color palettes have different lengths")
    cpal = table_C_P_A_L_()
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
