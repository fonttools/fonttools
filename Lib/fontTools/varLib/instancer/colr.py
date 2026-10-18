"""Instantiate COLRv1 paint values and their item variation store."""

from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otConverters import BaseFixedValue, Angle
from fontTools.misc.roundTools import otRound
from math import ceil, floor, gcd
from copy import copy


def _instantiateRadialGradient(paint):
    if paint.Format != ot.PaintFormat.PaintVarRadialGradient:
        return
    r0, r1 = paint.r0, paint.r1
    if r0 >= 0 and r1 >= 0:
        return
    line = paint.ColorLine
    if r0 == r1 or not line.ColorStop:
        # Equal negative radii have no nonnegative-radius intersection.
        paint.__dict__.clear()
        paint.Format = ot.PaintFormat.PaintSolid
        paint.PaletteIndex, paint.Alpha = 0xFFFF, 0
        return
    dr = r1 - r0
    ordered = sorted(line.ColorStop, key=lambda stop: stop.StopOffset)
    first = ordered[0].StopOffset
    last = ordered[-1].StopOffset
    # Fractional shifts must preserve both integer circles and F2Dot14 stops.
    lattice = gcd(16384, paint.x1 - paint.x0, paint.y1 - paint.y0, dr)
    for shift in range(16):
        b = 1 << shift
        coarse = ceil(-r0 / dr) if dr > 0 else floor(r0 / -dr) - b
        fine = (
            ceil(-r0 / dr * lattice) / lattice
            if dr > 0
            else floor(r0 / -dr * lattice) / lattice - b
        )
        for a in (coarse, fine):
            # omega = a + b*q, with positive b, preserves the largest valid root.
            geometry = (
                paint.x0 + a * (paint.x1 - paint.x0),
                paint.y0 + a * (paint.y1 - paint.y0),
                r0 + a * dr,
                paint.x0 + (a + b) * (paint.x1 - paint.x0),
                paint.y0 + (a + b) * (paint.y1 - paint.y0),
                r0 + (a + b) * dr,
            )
            if any(not -32768 <= geometry[i] <= 32767 for i in (0, 1, 3, 4)) or any(
                not 0 <= geometry[i] <= 65535 for i in (2, 5)
            ):
                continue
            stops = ordered
            offsets = [(stop.StopOffset - a) / b for stop in stops]
            tip = -geometry[2] / (b * dr)
            if line.Extend == ot.ExtendMode.PAD:
                if dr > 0 and offsets[-1] <= tip:
                    stops, offsets = [stops[-1]], [0]
                elif dr < 0 and offsets[0] > tip:
                    stops, offsets = [stops[0]], [0]
            else:
                period = (last - first) / b
                if line.Extend == ot.ExtendMode.REFLECT:
                    period *= 2
                if period <= 0:
                    paint.__dict__.clear()
                    paint.Format = ot.PaintFormat.PaintSolid
                    paint.PaletteIndex, paint.Alpha = 0xFFFF, 0
                    return
                # Moving a repeating color line by whole periods changes no colors.
                n = ceil((-2 - offsets[0]) / period)
                if n > floor(((32767 / 16384) - offsets[-1]) / period):
                    continue
                offsets = [offset + n * period for offset in offsets]
            if any(
                not -32768 <= offset * 16384 <= 32767
                or offset * 16384 != otRound(offset * 16384)
                for offset in offsets
            ):
                continue
            paint.x0, paint.y0, paint.r0, paint.x1, paint.y1, paint.r1 = map(
                int, geometry
            )
            # Color lines can be shared by gradients with different geometries.
            paint.ColorLine = copy(line)
            paint.ColorLine.ColorStop = [copy(stop) for stop in stops]
            paint.ColorLine.StopCount = len(stops)
            for stop, offset in zip(paint.ColorLine.ColorStop, offsets):
                stop.StopOffset = offset
            return
    raise ValueError(
        "COLR radial gradient with negative radii cannot be represented without rounding"
    )


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
                if isinstance(table, ot.ClipBox):
                    delta = floor(delta) if name in ("xMin", "yMin") else ceil(delta)
                value += otRound(delta)
                if name in ("r0", "r1") and not static:
                    value = min(65535, max(0, value))
            setattr(table, name, value)

        if static:
            if isinstance(table, ot.Paint):
                _instantiateScale(table)
                _instantiateRadialGradient(table)
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
    elif mapping:
        # An explicit map keeps VarIndexBase sequences valid when rows move.
        varIndexMapping = colr.VarStore.optimize()
        colr.VarIndexMap.mapping = [varIndexMapping[index] for index in mapping]
