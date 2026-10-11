"""Instantiate COLRv1 paint values and their item variation store."""

from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otConverters import BaseFixedValue, Angle
from fontTools.misc.roundTools import otRound


def _instantiateScale(paint):
    """Use an affine transform when a static scale no longer fits F2Dot14."""
    if paint.Format not in (
        ot.PaintFormat.PaintVarScale,
        ot.PaintFormat.PaintVarScaleAroundCenter,
        ot.PaintFormat.PaintVarScaleUniform,
        ot.PaintFormat.PaintVarScaleUniformAroundCenter,
    ):
        return
    if hasattr(paint, "scale"):
        sx = sy = paint.scale
    else:
        sx, sy = paint.scaleX, paint.scaleY
    if -2 <= sx < 2 and -2 <= sy < 2:
        return
    cx, cy = getattr(paint, "centerX", 0), getattr(paint, "centerY", 0)
    transform = ot.Affine2x3()
    transform.xx, transform.yx = sx, 0
    transform.xy, transform.yy = 0, sy
    transform.dx, transform.dy = cx * (1 - sx), cy * (1 - sy)
    for name in ("scale", "scaleX", "scaleY", "centerX", "centerY"):
        if hasattr(paint, name):
            delattr(paint, name)
    paint.Format = ot.PaintFormat.PaintTransform
    paint.Transform = transform


def instantiateCOLR(varfont, axisLimits):
    from . import instantiateItemVariationStore

    if "COLR" not in varfont or varfont["COLR"].version < 1:
        return
    colr = varfont["COLR"].table
    if colr.VarStore is None:
        return
    deltas = instantiateItemVariationStore(
        colr.VarStore, varfont["fvar"].axes, axisLimits
    )
    static = not any(any(row) for data in colr.VarStore.VarData for row in data.Item)
    mapping = colr.VarIndexMap.mapping if colr.VarIndexMap is not None else []
    visited = set()

    def visit(table):
        if id(table) in visited:
            return
        visited.add(id(table))
        table.ensureDecompiled()
        for entry in table.iterSubTables():
            visit(entry.value)

        for name in table.getVariableAttrs():
            conv = table.getConverterByName(name)
            base = table.VarIndexBase
            if base == ot.NO_VARIATION_INDEX:
                delta = 0
            else:
                index = base + conv.getVarIndexOffset()
                if mapping:
                    index = mapping[min(index, len(mapping) - 1)]
                delta = deltas[index]
            value = getattr(table, name)
            if isinstance(conv, BaseFixedValue):
                bits = otRound(conv.toInt(value) + delta)
                if name == "Alpha" and static:
                    bits = min(1 << 14, max(0, bits))
                elif isinstance(conv, Angle) and isinstance(table, ot.Paint):
                    # Rotation and skew are periodic; sweep angles are not.
                    if table.Format not in (ot.PaintFormat.PaintVarSweepGradient,):
                        bits = (bits + 32768) % 65536 - 32768
                value = conv.fromInt(bits)
            else:
                value += otRound(delta)
                if name in ("r0", "r1"):
                    value = min(65535, max(0, value))
            setattr(table, name, value)

        if static:
            if isinstance(table, ot.Paint):
                _instantiateScale(table)
            if hasattr(table, "VarIndexBase"):
                del table.VarIndexBase
            if (
                isinstance(table, ot.Paint)
                and ot.PaintFormat(table.Format).is_variable()
            ):
                table.Format -= 1
            elif isinstance(table, ot.ClipBox) and table.Format == 2:
                table.Format = 1
            elif hasattr(type(table), "NoVarType"):
                table.__class__ = type(table).NoVarType

    if colr.BaseGlyphList is not None:
        for record in colr.BaseGlyphList.BaseGlyphPaintRecord:
            visit(record.Paint)
    if colr.LayerList is not None:
        for paint in colr.LayerList.Paint:
            visit(paint)
    if colr.ClipList is not None:
        for clip in colr.ClipList.clips.values():
            visit(clip)
    if static:
        colr.VarStore = None
        colr.VarIndexMap = None
