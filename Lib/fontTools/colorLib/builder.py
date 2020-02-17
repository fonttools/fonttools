import enum
from typing import Dict, Iterable, List, Optional, Tuple, Union
from fontTools.ttLib.tables.C_O_L_R_ import LayerRecord, table_C_O_L_R_
from fontTools.ttLib.tables.C_P_A_L_ import Color, table_C_P_A_L_
from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e
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


class ColorPaletteType(enum.IntFlag):
    USABLE_WITH_LIGHT_BACKGROUND = 0x0001
    USABLE_WITH_DARK_BACKGROUND = 0x0002

    @classmethod
    def _missing_(cls, value):
        # enforce reserved bits
        if isinstance(value, int) and (value < 0 or value & 0xFFFC != 0):
            raise ValueError(f"{value} is not a valid {cls.__name__}")
        return super()._missing_(value)


# None, 'abc' or {'en': 'abc', 'de': 'xyz'}
_OptionalLocalizedString = Union[None, str, Dict[str, str]]


def buildPaletteLabels(
    labels: List[_OptionalLocalizedString], nameTable: table__n_a_m_e
) -> List[Optional[int]]:
    return [
        nameTable.addMultilingualName(l, mac=False)
        if isinstance(l, dict)
        else table_C_P_A_L_.NO_NAME_ID
        if l is None
        else nameTable.addMultilingualName({"en": l}, mac=False)
        for l in labels
    ]


def buildCPAL(
    palettes: List[List[Tuple[float, float, float, float]]],
    paletteTypes: Optional[List[ColorPaletteType]] = None,
    paletteLabels: Optional[List[_OptionalLocalizedString]] = None,
    paletteEntryLabels: Optional[List[_OptionalLocalizedString]] = None,
    nameTable: Optional[table__n_a_m_e] = None,
) -> table_C_P_A_L_:
    """Build CPAL table from list of color palettes.

    Args:
        palettes: list of lists of colors encoded as tuples of (R, G, B, A) floats
            in the range [0..1].
        paletteTypes: optional list of ColorPaletteType, one for each palette.
        paletteLabels: optional list of palette labels. Each lable can be either:
            None (no label), a string (for for default English labels), or a
            localized string (as a dict keyed with BCP47 language codes).
        paletteEntryLabels: optional list of palette entry labels, one for each
            palette entry (see paletteLabels).
        nameTable: optional name table where to store palette and palette entry
            labels. Required if either paletteLabels or paletteEntryLabels is set.

    Return:
        A new CPAL v0 or v1 table, if custom palette types or labels are specified.
    """
    if len({len(p) for p in palettes}) != 1:
        raise ColorLibError("color palettes have different lengths")

    if (paletteLabels or paletteEntryLabels) and not nameTable:
        raise TypeError(
            "nameTable is required if palette or palette entries have labels"
        )

    cpal = table_C_P_A_L_()
    cpal.numPaletteEntries = len(palettes[0])

    cpal.palettes = []
    for i, palette in enumerate(palettes):
        colors = []
        for j, color in enumerate(palette):
            if not isinstance(color, tuple) or len(color) != 4:
                raise ColorLibError(
                    f"In palette[{i}][{j}]: expected (R, G, B, A) tuple, got {color!r}"
                )
            if any(v > 1 or v < 0 for v in color):
                raise ColorLibError(
                    f"palette[{i}][{j}] has invalid out-of-range [0..1] color: {color!r}"
                )
            # input colors are RGBA, CPAL encodes them as BGRA
            red, green, blue, alpha = color
            colors.append(Color(*(round(v * 255) for v in (blue, green, red, alpha))))
        cpal.palettes.append(colors)

    if any(v is not None for v in (paletteTypes, paletteLabels, paletteEntryLabels)):
        cpal.version = 1

        if paletteTypes is not None:
            if len(paletteTypes) != len(palettes):
                raise ColorLibError(
                    f"Expected {len(palettes)} paletteTypes, got {len(paletteTypes)}"
                )
            cpal.paletteTypes = [ColorPaletteType(t).value for t in paletteTypes]
        else:
            cpal.paletteTypes = [table_C_P_A_L_.DEFAULT_PALETTE_TYPE] * len(palettes)

        if paletteLabels is not None:
            if len(paletteLabels) != len(palettes):
                raise ColorLibError(
                    f"Expected {len(palettes)} paletteLabels, got {len(paletteLabels)}"
                )
            cpal.paletteLabels = buildPaletteLabels(paletteLabels, nameTable)
        else:
            cpal.paletteLabels = [table_C_P_A_L_.NO_NAME_ID] * len(palettes)

        if paletteEntryLabels is not None:
            if len(paletteEntryLabels) != cpal.numPaletteEntries:
                raise ColorLibError(
                    f"Expected {cpal.numPaletteEntries} paletteEntryLabels, "
                    f"got {len(paletteEntryLabels)}"
                )
            cpal.paletteEntryLabels = buildPaletteLabels(paletteEntryLabels, nameTable)
        else:
            cpal.paletteEntryLabels = [
                table_C_P_A_L_.NO_NAME_ID
            ] * cpal.numPaletteEntries
    else:
        cpal.version = 0

    return cpal
