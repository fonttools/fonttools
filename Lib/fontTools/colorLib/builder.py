"""
colorLib.builder: Build COLR/CPAL tables from scratch

"""
import collections
import copy
import enum
from functools import partial
from math import ceil, log
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from fontTools.misc.fixedTools import fixedToFloat
from fontTools.ttLib.tables import C_O_L_R_
from fontTools.ttLib.tables import C_P_A_L_
from fontTools.ttLib.tables import _n_a_m_e
from fontTools.ttLib.tables.otBase import BaseTable
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otTables import (
    ExtendMode,
    CompositeMode,
    VariableValue,
    VariableFloat,
    VariableInt,
)
from .errors import ColorLibError
from .geometry import round_start_circle_stable_containment


# TODO move type aliases to colorLib.types?
T = TypeVar("T")
_Kwargs = Mapping[str, Any]
_PaintInput = Union[int, _Kwargs, ot.Paint, Tuple[str, "_PaintInput"]]
_PaintInputList = Sequence[_PaintInput]
_ColorGlyphsDict = Dict[str, Union[_PaintInputList, _PaintInput]]
_ColorGlyphsV0Dict = Dict[str, Sequence[Tuple[str, int]]]
_Number = Union[int, float]
_ScalarInput = Union[_Number, VariableValue, Tuple[_Number, int]]
_ColorStopTuple = Tuple[_ScalarInput, int]
_ColorStopInput = Union[_ColorStopTuple, _Kwargs, ot.ColorStop]
_ColorStopsList = Sequence[_ColorStopInput]
_ExtendInput = Union[int, str, ExtendMode]
_CompositeInput = Union[int, str, CompositeMode]
_ColorLineInput = Union[_Kwargs, ot.ColorLine]
_PointTuple = Tuple[_ScalarInput, _ScalarInput]
_AffineTuple = Tuple[
    _ScalarInput, _ScalarInput, _ScalarInput, _ScalarInput, _ScalarInput, _ScalarInput
]
_AffineInput = Union[_AffineTuple, ot.Affine2x3]

MAX_PAINT_COLR_LAYER_COUNT = 255


def populateCOLRv0(
    table: ot.COLR,
    colorGlyphsV0: _ColorGlyphsV0Dict,
    glyphMap: Optional[Mapping[str, int]] = None,
):
    """Build v0 color layers and add to existing COLR table.

    Args:
        table: a raw otTables.COLR() object (not ttLib's table_C_O_L_R_).
        colorGlyphsV0: map of base glyph names to lists of (layer glyph names,
            color palette index) tuples.
        glyphMap: a map from glyph names to glyph indices, as returned from
            TTFont.getReverseGlyphMap(), to optionally sort base records by GID.
    """
    if glyphMap is not None:
        colorGlyphItems = sorted(
            colorGlyphsV0.items(), key=lambda item: glyphMap[item[0]]
        )
    else:
        colorGlyphItems = colorGlyphsV0.items()
    baseGlyphRecords = []
    layerRecords = []
    for baseGlyph, layers in colorGlyphItems:
        baseRec = ot.BaseGlyphRecord()
        baseRec.BaseGlyph = baseGlyph
        baseRec.FirstLayerIndex = len(layerRecords)
        baseRec.NumLayers = len(layers)
        baseGlyphRecords.append(baseRec)

        for layerGlyph, paletteIndex in layers:
            layerRec = ot.LayerRecord()
            layerRec.LayerGlyph = layerGlyph
            layerRec.PaletteIndex = paletteIndex
            layerRecords.append(layerRec)

    table.BaseGlyphRecordCount = len(baseGlyphRecords)
    table.BaseGlyphRecordArray = ot.BaseGlyphRecordArray()
    table.BaseGlyphRecordArray.BaseGlyphRecord = baseGlyphRecords
    table.LayerRecordArray = ot.LayerRecordArray()
    table.LayerRecordArray.LayerRecord = layerRecords
    table.LayerRecordCount = len(layerRecords)


def buildCOLR(
    colorGlyphs: _ColorGlyphsDict,
    version: Optional[int] = None,
    glyphMap: Optional[Mapping[str, int]] = None,
    varStore: Optional[ot.VarStore] = None,
) -> C_O_L_R_.table_C_O_L_R_:
    """Build COLR table from color layers mapping.

    Args:
        colorGlyphs: map of base glyph name to, either list of (layer glyph name,
            color palette index) tuples for COLRv0; or a single Paint (dict) or
            list of Paint for COLRv1.
        version: the version of COLR table. If None, the version is determined
            by the presence of COLRv1 paints or variation data (varStore), which
            require version 1; otherwise, if all base glyphs use only simple color
            layers, version 0 is used.
        glyphMap: a map from glyph names to glyph indices, as returned from
            TTFont.getReverseGlyphMap(), to optionally sort base records by GID.
        varStore: Optional ItemVarationStore for deltas associated with v1 layer.

    Return:
        A new COLR table.
    """
    self = C_O_L_R_.table_C_O_L_R_()

    if varStore is not None and version == 0:
        raise ValueError("Can't add VarStore to COLRv0")

    if version in (None, 0) and not varStore:
        # split color glyphs into v0 and v1 and encode separately
        colorGlyphsV0, colorGlyphsV1 = _split_color_glyphs_by_version(colorGlyphs)
        if version == 0 and colorGlyphsV1:
            raise ValueError("Can't encode COLRv1 glyphs in COLRv0")
    else:
        # unless explicitly requested for v1 or have variations, in which case
        # we encode all color glyph as v1
        colorGlyphsV0, colorGlyphsV1 = None, colorGlyphs

    colr = ot.COLR()

    if colorGlyphsV0:
        populateCOLRv0(colr, colorGlyphsV0, glyphMap)
    else:
        colr.BaseGlyphRecordCount = colr.LayerRecordCount = 0
        colr.BaseGlyphRecordArray = colr.LayerRecordArray = None

    if colorGlyphsV1:
        colr.LayerV1List, colr.BaseGlyphV1List = buildColrV1(colorGlyphsV1, glyphMap)

    if version is None:
        version = 1 if (varStore or colorGlyphsV1) else 0
    elif version not in (0, 1):
        raise NotImplementedError(version)
    self.version = colr.Version = version

    if version == 0:
        self._fromOTTable(colr)
    else:
        colr.VarStore = varStore
        self.table = colr

    return self


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
    labels: Iterable[_OptionalLocalizedString], nameTable: _n_a_m_e.table__n_a_m_e
) -> List[Optional[int]]:
    return [
        nameTable.addMultilingualName(l, mac=False)
        if isinstance(l, dict)
        else C_P_A_L_.table_C_P_A_L_.NO_NAME_ID
        if l is None
        else nameTable.addMultilingualName({"en": l}, mac=False)
        for l in labels
    ]


def buildCPAL(
    palettes: Sequence[Sequence[Tuple[float, float, float, float]]],
    paletteTypes: Optional[Sequence[ColorPaletteType]] = None,
    paletteLabels: Optional[Sequence[_OptionalLocalizedString]] = None,
    paletteEntryLabels: Optional[Sequence[_OptionalLocalizedString]] = None,
    nameTable: Optional[_n_a_m_e.table__n_a_m_e] = None,
) -> C_P_A_L_.table_C_P_A_L_:
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

    cpal = C_P_A_L_.table_C_P_A_L_()
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
            colors.append(
                C_P_A_L_.Color(*(round(v * 255) for v in (blue, green, red, alpha)))
            )
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
            cpal.paletteTypes = [C_P_A_L_.table_C_P_A_L_.DEFAULT_PALETTE_TYPE] * len(
                palettes
            )

        if paletteLabels is not None:
            if len(paletteLabels) != len(palettes):
                raise ColorLibError(
                    f"Expected {len(palettes)} paletteLabels, got {len(paletteLabels)}"
                )
            cpal.paletteLabels = buildPaletteLabels(paletteLabels, nameTable)
        else:
            cpal.paletteLabels = [C_P_A_L_.table_C_P_A_L_.NO_NAME_ID] * len(palettes)

        if paletteEntryLabels is not None:
            if len(paletteEntryLabels) != cpal.numPaletteEntries:
                raise ColorLibError(
                    f"Expected {cpal.numPaletteEntries} paletteEntryLabels, "
                    f"got {len(paletteEntryLabels)}"
                )
            cpal.paletteEntryLabels = buildPaletteLabels(paletteEntryLabels, nameTable)
        else:
            cpal.paletteEntryLabels = [
                C_P_A_L_.table_C_P_A_L_.NO_NAME_ID
            ] * cpal.numPaletteEntries
    else:
        cpal.version = 0

    return cpal


# COLR v1 tables
# See draft proposal at: https://github.com/googlefonts/colr-gradients-spec

_DEFAULT_ALPHA = VariableFloat(1.0)


def _is_colrv0_layer(layer: Any) -> bool:
    # Consider as COLRv0 layer any sequence of length 2 (be it tuple or list) in which
    # the first element is a str (the layerGlyph) and the second element is an int
    # (CPAL paletteIndex).
    # https://github.com/googlefonts/ufo2ft/issues/426
    try:
        layerGlyph, paletteIndex = layer
    except (TypeError, ValueError):
        return False
    else:
        return isinstance(layerGlyph, str) and isinstance(paletteIndex, int)


def _split_color_glyphs_by_version(
    colorGlyphs: _ColorGlyphsDict,
) -> Tuple[_ColorGlyphsV0Dict, _ColorGlyphsDict]:
    colorGlyphsV0 = {}
    colorGlyphsV1 = {}
    for baseGlyph, layers in colorGlyphs.items():
        if all(_is_colrv0_layer(l) for l in layers):
            colorGlyphsV0[baseGlyph] = layers
        else:
            colorGlyphsV1[baseGlyph] = layers

    # sanity check
    assert set(colorGlyphs) == (set(colorGlyphsV0) | set(colorGlyphsV1))

    return colorGlyphsV0, colorGlyphsV1


def _to_variable_value(
    value: _ScalarInput,
    cls: Type[VariableValue] = VariableFloat,
    minValue: Optional[_Number] = None,
    maxValue: Optional[_Number] = None,
) -> VariableValue:
    if not isinstance(value, cls):
        try:
            it = iter(value)
        except TypeError:  # not iterable
            value = cls(value)
        else:
            value = cls._make(it)
    if minValue is not None and value.value < minValue:
        raise OverflowError(f"{cls.__name__}: {value.value} < {minValue}")
    if maxValue is not None and value.value > maxValue:
        raise OverflowError(f"{cls.__name__}: {value.value} < {maxValue}")
    return value


_to_variable_f16dot16_float = partial(
    _to_variable_value,
    cls=VariableFloat,
    minValue=-(2 ** 15),
    maxValue=fixedToFloat(2 ** 31 - 1, 16),
)
_to_variable_f2dot14_float = partial(
    _to_variable_value,
    cls=VariableFloat,
    minValue=-2.0,
    maxValue=fixedToFloat(2 ** 15 - 1, 14),
)
_to_variable_int16 = partial(
    _to_variable_value,
    cls=VariableInt,
    minValue=-(2 ** 15),
    maxValue=2 ** 15 - 1,
)
_to_variable_uint16 = partial(
    _to_variable_value,
    cls=VariableInt,
    minValue=0,
    maxValue=2 ** 16,
)


def buildColorIndex(
    paletteIndex: int, alpha: _ScalarInput = _DEFAULT_ALPHA
) -> ot.ColorIndex:
    self = ot.ColorIndex()
    self.PaletteIndex = int(paletteIndex)
    self.Alpha = _to_variable_f2dot14_float(alpha)
    return self


def buildColorStop(
    offset: _ScalarInput,
    paletteIndex: int,
    alpha: _ScalarInput = _DEFAULT_ALPHA,
) -> ot.ColorStop:
    self = ot.ColorStop()
    self.StopOffset = _to_variable_f2dot14_float(offset)
    self.Color = buildColorIndex(paletteIndex, alpha)
    return self


def _to_enum_value(v: Union[str, int, T], enumClass: Type[T]) -> T:
    if isinstance(v, enumClass):
        return v
    elif isinstance(v, str):
        try:
            return getattr(enumClass, v.upper())
        except AttributeError:
            raise ValueError(f"{v!r} is not a valid {enumClass.__name__}")
    return enumClass(v)


def _to_extend_mode(v: _ExtendInput) -> ExtendMode:
    return _to_enum_value(v, ExtendMode)


def _to_composite_mode(v: _CompositeInput) -> CompositeMode:
    return _to_enum_value(v, CompositeMode)


def buildColorLine(
    stops: _ColorStopsList, extend: _ExtendInput = ExtendMode.PAD
) -> ot.ColorLine:
    self = ot.ColorLine()
    self.Extend = _to_extend_mode(extend)
    self.StopCount = len(stops)
    self.ColorStop = [
        stop
        if isinstance(stop, ot.ColorStop)
        else buildColorStop(**stop)
        if isinstance(stop, collections.abc.Mapping)
        else buildColorStop(*stop)
        for stop in stops
    ]
    return self


def _to_color_line(obj):
    if isinstance(obj, ot.ColorLine):
        return obj
    elif isinstance(obj, collections.abc.Mapping):
        return buildColorLine(**obj)
    raise TypeError(obj)


def _reuse_ranges(num_layers: int) -> Generator[Tuple[int, int], None, None]:
    # TODO feels like something itertools might have already
    for lbound in range(num_layers):
        # TODO may want a max length to limit scope of search
        # Reuse of very large #s of layers is relatively unlikely
        # +2: we want sequences of at least 2
        # otData handles single-record duplication
        for ubound in range(lbound + 2, num_layers + 1):
            yield (lbound, ubound)


class LayerV1ListBuilder:
    slices: List[ot.Paint]
    layers: List[ot.Paint]
    reusePool: Mapping[Tuple[Any, ...], int]
    tuples: Mapping[int, Tuple[Any, ...]]
    keepAlive: List[ot.Paint]  # we need id to remain valid

    def __init__(self):
        self.slices = []
        self.layers = []
        self.reusePool = {}
        self.tuples = {}
        self.keepAlive = []

    def _paint_tuple(self, paint: ot.Paint):
        # start simple, who even cares about cyclic graphs or interesting field types
        def _tuple_safe(value):
            if isinstance(value, enum.Enum):
                return value
            elif hasattr(value, "__dict__"):
                return tuple(
                    (k, _tuple_safe(v)) for k, v in sorted(value.__dict__.items())
                )
            elif isinstance(value, collections.abc.MutableSequence):
                return tuple(_tuple_safe(e) for e in value)
            return value

        # Cache the tuples for individual Paint instead of the whole sequence
        # because the seq could be a transient slice
        result = self.tuples.get(id(paint), None)
        if result is None:
            result = _tuple_safe(paint)
            self.tuples[id(paint)] = result
            self.keepAlive.append(paint)
        return result

    def _as_tuple(self, paints: Sequence[ot.Paint]) -> Tuple[Any, ...]:
        return tuple(self._paint_tuple(p) for p in paints)

    def buildPaintSolid(
        self, paletteIndex: int, alpha: _ScalarInput = _DEFAULT_ALPHA
    ) -> ot.Paint:
        ot_paint = ot.Paint()
        ot_paint.Format = int(ot.Paint.Format.PaintSolid)
        ot_paint.Color = buildColorIndex(paletteIndex, alpha)
        return ot_paint

    def buildPaintLinearGradient(
        self,
        colorLine: _ColorLineInput,
        p0: _PointTuple,
        p1: _PointTuple,
        p2: Optional[_PointTuple] = None,
    ) -> ot.Paint:
        ot_paint = ot.Paint()
        ot_paint.Format = int(ot.Paint.Format.PaintLinearGradient)
        ot_paint.ColorLine = _to_color_line(colorLine)

        if p2 is None:
            p2 = copy.copy(p1)
        for i, (x, y) in enumerate((p0, p1, p2)):
            setattr(ot_paint, f"x{i}", _to_variable_int16(x))
            setattr(ot_paint, f"y{i}", _to_variable_int16(y))

        return ot_paint

    def buildPaintRadialGradient(
        self,
        colorLine: _ColorLineInput,
        c0: _PointTuple,
        c1: _PointTuple,
        r0: _ScalarInput,
        r1: _ScalarInput,
    ) -> ot.Paint:

        ot_paint = ot.Paint()
        ot_paint.Format = int(ot.Paint.Format.PaintRadialGradient)
        ot_paint.ColorLine = _to_color_line(colorLine)

        # normalize input types (which may or may not specify a varIdx)
        x0, y0 = _to_variable_value(c0[0]), _to_variable_value(c0[1])
        r0 = _to_variable_value(r0)
        x1, y1 = _to_variable_value(c1[0]), _to_variable_value(c1[1])
        r1 = _to_variable_value(r1)

        # avoid abrupt change after rounding when c0 is near c1's perimeter
        c = round_start_circle_stable_containment(
            (x0.value, y0.value), r0.value, (x1.value, y1.value), r1.value
        )
        x0, y0 = x0._replace(value=c.centre[0]), y0._replace(value=c.centre[1])
        r0 = r0._replace(value=c.radius)

        for i, (x, y, r) in enumerate(((x0, y0, r0), (x1, y1, r1))):
            # rounding happens here as floats are converted to integers
            setattr(ot_paint, f"x{i}", _to_variable_int16(x))
            setattr(ot_paint, f"y{i}", _to_variable_int16(y))
            setattr(ot_paint, f"r{i}", _to_variable_uint16(r))

        return ot_paint

    def buildPaintGlyph(self, glyph: str, paint: _PaintInput) -> ot.Paint:
        ot_paint = ot.Paint()
        ot_paint.Format = int(ot.Paint.Format.PaintGlyph)
        ot_paint.Glyph = glyph
        ot_paint.Paint = self.buildPaint(paint)
        return ot_paint

    def buildPaintColrGlyph(self, glyph: str) -> ot.Paint:
        ot_paint = ot.Paint()
        ot_paint.Format = int(ot.Paint.Format.PaintColrGlyph)
        ot_paint.Glyph = glyph
        return ot_paint

    def buildPaintTransform(
        self, transform: _AffineInput, paint: _PaintInput
    ) -> ot.Paint:
        ot_paint = ot.Paint()
        ot_paint.Format = int(ot.Paint.Format.PaintTransform)
        if not isinstance(transform, ot.Affine2x3):
            transform = buildAffine2x3(transform)
        ot_paint.Transform = transform
        ot_paint.Paint = self.buildPaint(paint)
        return ot_paint

    def buildPaintTranslate(
        self, paint: _PaintInput, dx: _ScalarInput, dy: _ScalarInput
    ):
        ot_paint = ot.Paint()
        ot_paint.Format = int(ot.Paint.Format.PaintTranslate)
        ot_paint.Paint = self.buildPaint(paint)
        ot_paint.dx = _to_variable_f16dot16_float(dx)
        ot_paint.dy = _to_variable_f16dot16_float(dy)
        return ot_paint

    def buildPaintRotate(
        self,
        paint: _PaintInput,
        angle: _ScalarInput,
        centerX: _ScalarInput,
        centerY: _ScalarInput,
    ) -> ot.Paint:
        ot_paint = ot.Paint()
        ot_paint.Format = int(ot.Paint.Format.PaintRotate)
        ot_paint.Paint = self.buildPaint(paint)
        ot_paint.angle = _to_variable_f16dot16_float(angle)
        ot_paint.centerX = _to_variable_f16dot16_float(centerX)
        ot_paint.centerY = _to_variable_f16dot16_float(centerY)
        return ot_paint

    def buildPaintSkew(
        self,
        paint: _PaintInput,
        xSkewAngle: _ScalarInput,
        ySkewAngle: _ScalarInput,
        centerX: _ScalarInput,
        centerY: _ScalarInput,
    ) -> ot.Paint:
        ot_paint = ot.Paint()
        ot_paint.Format = int(ot.Paint.Format.PaintSkew)
        ot_paint.Paint = self.buildPaint(paint)
        ot_paint.xSkewAngle = _to_variable_f16dot16_float(xSkewAngle)
        ot_paint.ySkewAngle = _to_variable_f16dot16_float(ySkewAngle)
        ot_paint.centerX = _to_variable_f16dot16_float(centerX)
        ot_paint.centerY = _to_variable_f16dot16_float(centerY)
        return ot_paint

    def buildPaintComposite(
        self,
        mode: _CompositeInput,
        source: _PaintInput,
        backdrop: _PaintInput,
    ):
        ot_paint = ot.Paint()
        ot_paint.Format = int(ot.Paint.Format.PaintComposite)
        ot_paint.SourcePaint = self.buildPaint(source)
        ot_paint.CompositeMode = _to_composite_mode(mode)
        ot_paint.BackdropPaint = self.buildPaint(backdrop)
        return ot_paint

    def buildColrLayers(self, paints: List[_PaintInput]) -> ot.Paint:
        ot_paint = ot.Paint()
        ot_paint.Format = int(ot.Paint.Format.PaintColrLayers)
        self.slices.append(ot_paint)

        paints = [
            self.buildPaint(p)
            for p in _build_n_ary_tree(paints, n=MAX_PAINT_COLR_LAYER_COUNT)
        ]

        # Look for reuse, with preference to longer sequences
        found_reuse = True
        while found_reuse:
            found_reuse = False

            ranges = sorted(
                _reuse_ranges(len(paints)),
                key=lambda t: (t[1] - t[0], t[1], t[0]),
                reverse=True,
            )
            for lbound, ubound in ranges:
                reuse_lbound = self.reusePool.get(
                    self._as_tuple(paints[lbound:ubound]), -1
                )
                if reuse_lbound == -1:
                    continue
                new_slice = ot.Paint()
                new_slice.Format = int(ot.Paint.Format.PaintColrLayers)
                new_slice.NumLayers = ubound - lbound
                new_slice.FirstLayerIndex = reuse_lbound
                paints = paints[:lbound] + [new_slice] + paints[ubound:]
                found_reuse = True
                break

        ot_paint.NumLayers = len(paints)
        ot_paint.FirstLayerIndex = len(self.layers)
        self.layers.extend(paints)

        # Register our parts for reuse
        for lbound, ubound in _reuse_ranges(len(paints)):
            self.reusePool[self._as_tuple(paints[lbound:ubound])] = (
                lbound + ot_paint.FirstLayerIndex
            )

        return ot_paint

    def buildPaint(self, paint: _PaintInput) -> ot.Paint:
        if isinstance(paint, ot.Paint):
            return paint
        elif isinstance(paint, int):
            paletteIndex = paint
            return self.buildPaintSolid(paletteIndex)
        elif isinstance(paint, tuple):
            layerGlyph, paint = paint
            return self.buildPaintGlyph(layerGlyph, paint)
        elif isinstance(paint, list):
            # implicit PaintColrLayers for a list of > 1
            if len(paint) == 0:
                raise ValueError("An empty list is hard to paint")
            elif len(paint) == 1:
                return self.buildPaint(paint[0])
            else:
                return self.buildColrLayers(paint)
        elif isinstance(paint, collections.abc.Mapping):
            kwargs = dict(paint)
            fmt = kwargs.pop("format")
            try:
                return LayerV1ListBuilder._buildFunctions[fmt](self, **kwargs)
            except KeyError:
                raise NotImplementedError(fmt)
        raise TypeError(f"Not sure what to do with {type(paint).__name__}: {paint!r}")

    def build(self) -> ot.LayerV1List:
        layers = ot.LayerV1List()
        layers.LayerCount = len(self.layers)
        layers.Paint = self.layers
        return layers


LayerV1ListBuilder._buildFunctions = {
    pf.value: getattr(LayerV1ListBuilder, "build" + pf.name)
    for pf in ot.Paint.Format
    if pf != ot.Paint.Format.PaintColrLayers
}


def buildAffine2x3(transform: _AffineTuple) -> ot.Affine2x3:
    if len(transform) != 6:
        raise ValueError(f"Expected 6-tuple of floats, found: {transform!r}")
    self = ot.Affine2x3()
    # COLRv1 Affine2x3 uses the same column-major order to serialize a 2D
    # Affine Transformation as the one used by fontTools.misc.transform.
    # However, for historical reasons, the labels 'xy' and 'yx' are swapped.
    # Their fundamental meaning is the same though.
    # COLRv1 Affine2x3 follows the names found in FreeType and Cairo.
    # In all case, the second element in the 6-tuple correspond to the
    # y-part of the x basis vector, and the third to the x-part of the y
    # basis vector.
    # See https://github.com/googlefonts/colr-gradients-spec/pull/85
    for i, attr in enumerate(("xx", "yx", "xy", "yy", "dx", "dy")):
        setattr(self, attr, _to_variable_f16dot16_float(transform[i]))
    return self


def buildBaseGlyphV1Record(
    baseGlyph: str, layerBuilder: LayerV1ListBuilder, paint: _PaintInput
) -> ot.BaseGlyphV1List:
    self = ot.BaseGlyphV1Record()
    self.BaseGlyph = baseGlyph
    self.Paint = layerBuilder.buildPaint(paint)
    return self


def _format_glyph_errors(errors: Mapping[str, Exception]) -> str:
    lines = []
    for baseGlyph, error in sorted(errors.items()):
        lines.append(f"    {baseGlyph} => {type(error).__name__}: {error}")
    return "\n".join(lines)


def buildColrV1(
    colorGlyphs: _ColorGlyphsDict,
    glyphMap: Optional[Mapping[str, int]] = None,
) -> Tuple[ot.LayerV1List, ot.BaseGlyphV1List]:
    if glyphMap is not None:
        colorGlyphItems = sorted(
            colorGlyphs.items(), key=lambda item: glyphMap[item[0]]
        )
    else:
        colorGlyphItems = colorGlyphs.items()

    errors = {}
    baseGlyphs = []
    layerBuilder = LayerV1ListBuilder()
    for baseGlyph, paint in colorGlyphItems:
        try:
            baseGlyphs.append(buildBaseGlyphV1Record(baseGlyph, layerBuilder, paint))

        except (ColorLibError, OverflowError, ValueError, TypeError) as e:
            errors[baseGlyph] = e

    if errors:
        failed_glyphs = _format_glyph_errors(errors)
        exc = ColorLibError(f"Failed to build BaseGlyphV1List:\n{failed_glyphs}")
        exc.errors = errors
        raise exc from next(iter(errors.values()))

    layers = layerBuilder.build()
    glyphs = ot.BaseGlyphV1List()
    glyphs.BaseGlyphCount = len(baseGlyphs)
    glyphs.BaseGlyphV1Record = baseGlyphs
    return (layers, glyphs)


def _build_n_ary_tree(leaves, n):
    """Build N-ary tree from sequence of leaf nodes.

    Return a list of lists where each non-leaf node is a list containing
    max n nodes.
    """
    if not leaves:
        return []

    assert n > 1

    depth = ceil(log(len(leaves), n))

    if depth <= 1:
        return list(leaves)

    # Fully populate complete subtrees of root until we have enough leaves left
    root = []
    unassigned = None
    full_step = n ** (depth - 1)
    for i in range(0, len(leaves), full_step):
        subtree = leaves[i : i + full_step]
        if len(subtree) < full_step:
            unassigned = subtree
            break
        while len(subtree) > n:
            subtree = [subtree[k : k + n] for k in range(0, len(subtree), n)]
        root.append(subtree)

    if unassigned:
        # Recurse to fill the last subtree, which is the only partially populated one
        subtree = _build_n_ary_tree(unassigned, n)
        if len(subtree) <= n - len(root):
            # replace last subtree with its children if they can still fit
            root.extend(subtree)
        else:
            root.append(subtree)
        assert len(root) <= n

    return root
