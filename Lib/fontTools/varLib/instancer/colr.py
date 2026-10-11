"""Instantiate COLRv1 paint values and their item variation store."""

from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otConverters import BaseFixedValue, Angle, Short, UShort
from fontTools.misc.roundTools import otRound
from fontTools.varLib.builder import buildVarRegion
from math import trunc, ceil, floor
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
    for shift in range(16):
        b = 1 << shift
        a = (-r0 + dr - 1) // dr if dr > 0 else r0 // -dr - b
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
        paint.x0, paint.y0, paint.r0, paint.x1, paint.y1, paint.r1 = geometry
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


def _scaleMatrices(sx, sy):
    """Bound affine fields while retaining a large scale's fractional bits."""
    if -32768 <= sx < 32768 and -32768 <= sy < 32768:
        return [(sx, 0, 0, sy, 0, 0)]
    matrices = []
    for axis, value in enumerate((sx, sy)):
        if -32768 <= value < 32768:
            factors = [(value, 0, 0, 1, 0, 0)]
        else:
            shifts = 0
            scaled = value
            while abs(scaled) >= 2**28:
                scaled /= 2
                shifts += 1
            unit = 2 ** -max(0, shifts - 2)
            k = 16384
            m = trunc(scaled / k)
            r = (scaled - k * m) / unit
            x = trunc(r / m)
            k += x * unit
            r -= x * m
            # Eliminating the -unit pivot gives diag(value, 1).
            # The pivot permits extra fractional precision after downscaling.
            factors = [
                (2**shifts, 0, 0, 1 / unit, 0, 0),
                (1, 0, k, 1, 0, 0),
                (unit, 0, 0, 1, 0, 0),
                (k, -unit, r, m, 0, 0),
                (1 / unit, 0, 0, 1, 0, 0),
                (1, 0, m, 1, 0, 0),
                (unit, 0, 0, 1, 0, 0),
                (0, 1, -1, 0, 0, 0),
            ]
        for xx, yx, xy, yy, dx, dy in factors:
            matrix = (yy, xy, yx, xx, dy, dx) if axis else (xx, yx, xy, yy, dx, dy)
            if matrix != (1, 0, 0, 1, 0, 0):
                matrices.append(matrix)
    return matrices


def _wrapTransforms(child, matrices):
    for xx, yx, xy, yy, dx, dy in reversed(matrices):
        matrix = ot.Affine2x3()
        matrix.xx, matrix.yx, matrix.xy, matrix.yy = xx, yx, xy, yy
        matrix.dx, matrix.dy = dx, dy
        wrapper = ot.Paint()
        wrapper.Format = ot.PaintFormat.PaintTransform
        wrapper.Paint, wrapper.Transform = child, matrix
        child = wrapper
    return child


def _translateMatrices(dx, dy):
    # T(k*q + r) = S(k) T(q) S(1/k) T(r). Power-of-two factors keep
    # every translation exact while bounding both coefficients and depth.
    k = 16384
    matrices, remainders = [], []
    while not (-32768 <= dx < 32768 and -32768 <= dy < 32768):
        qx, qy = trunc(dx / k), trunc(dy / k)
        remainders.append((dx - qx * k, dy - qy * k))
        matrices.append((k, 0, 0, k, 0, 0))
        dx, dy = qx, qy
    matrices.append((1, 0, 0, 1, dx, dy))
    for dx, dy in reversed(remainders):
        matrices.append((1 / k, 0, 0, 1 / k, 0, 0))
        matrices.append((1, 0, 0, 1, dx, dy))
    return matrices


def _instantiateTranslate(paint):
    if paint.Format != ot.PaintFormat.PaintVarTranslate:
        return
    if -32768 <= paint.dx <= 32767 and -32768 <= paint.dy <= 32767:
        return
    wrapper = _wrapTransforms(paint.Paint, _translateMatrices(paint.dx, paint.dy))
    del paint.dx, paint.dy
    paint.Format = ot.PaintFormat.PaintTransform
    paint.Paint, paint.Transform = wrapper.Paint, wrapper.Transform


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
    child = paint.Paint
    if not all(
        -32768 <= value < 32768 for value in (sx, sy, transform.dx, transform.dy)
    ):
        # Keep large centered translations separate. Halving the center also
        # makes the inverse of -32768 representable in Fixed.
        matrices = _scaleMatrices(sx, sy)
        if cx or cy:
            matrices = (
                [(1, 0, 0, 1, cx / 2, cy / 2)] * 2
                + matrices
                + [(1, 0, 0, 1, -cx / 2, -cy / 2)] * 2
            )
        wrapper = _wrapTransforms(child, matrices)
        transform, child = wrapper.Transform, wrapper.Paint
    for name in ("scale", "scaleX", "scaleY", "centerX", "centerY"):
        if hasattr(paint, name):
            delattr(paint, name)
    paint.Format = ot.PaintFormat.PaintTransform
    paint.Paint = child
    paint.Transform = transform


def _splitLongDeltas(data):
    """Repeat region indices when a rebased column exceeds a signed long."""
    if all(-2147483648 <= value <= 2147483647 for row in data.Item for value in row):
        return
    indices = []
    items = [[] for _ in data.Item]
    for column, region in enumerate(data.VarRegionIndex):
        values = [row[column] for row in data.Item]
        count = max(
            (
                max((d + 2147483646) // 2147483647, (-d + 2147483647) // 2147483648)
                for d in values
            ),
            default=1,
        )
        count = max(1, count)
        if len(indices) + count > 65535:
            raise ValueError("COLR has too many variation columns")
        indices.extend([region] * count)
        for row, delta in zip(items, values):
            for _ in range(count):
                word = min(2147483647, max(-2147483648, delta))
                row.append(word)
                delta -= word
    data.VarRegionIndex = indices
    data.VarRegionCount = len(indices)
    data.Item = items
    longColumns = sum(
        any(not -32768 <= row[column] <= 32767 for row in items)
        for column in range(len(indices))
    )
    if longColumns > 32767:
        raise ValueError("COLR has too many long variation columns")
    data.calculateNumShorts()


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
    preserveDefaults = False

    def visit(table, apply=True):
        nonlocal preserveDefaults
        if id(table) in visited:
            return
        visited.add(id(table))
        table.ensureDecompiled()
        for entry in table.iterSubTables():
            visit(entry.value, apply)

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
                if not apply:
                    limit = 1 << (conv.staticSize * 8 - 1)
                    if not -limit <= bits < limit:
                        preserveDefaults = True
                    continue
                if name == "Alpha" and static:
                    bits = min(1 << 14, max(0, bits))
                elif isinstance(conv, Angle) and isinstance(table, ot.Paint):
                    # Rotation and skew are periodic; sweep angles are not.
                    if table.Format not in (ot.PaintFormat.PaintVarSweepGradient,):
                        bits = (bits + 32768) % 65536 - 32768
                value = conv.fromInt(bits)
            else:
                if not apply:
                    derived = value + otRound(delta)
                    if isinstance(conv, Short):
                        preserveDefaults |= not -32768 <= derived <= 32767
                    elif isinstance(conv, UShort):
                        preserveDefaults |= not 0 <= derived <= 65535
                    continue
                value += otRound(delta)
                if name in ("r0", "r1") and not static:
                    value = min(65535, max(0, value))
            setattr(table, name, value)

        if static and apply:
            if isinstance(table, ot.Paint):
                _instantiateScale(table)
                _instantiateTranslate(table)
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

    roots = []
    if colr.BaseGlyphList is not None:
        roots.extend(record.Paint for record in colr.BaseGlyphList.BaseGlyphPaintRecord)
    if colr.LayerList is not None:
        roots.extend(colr.LayerList.Paint)
    if colr.ClipList is not None:
        roots.extend(colr.ClipList.clips.values())
    if not static:
        for root in roots:
            visit(root, apply=False)
        visited.clear()
    if preserveDefaults:
        # Base fields cannot encode the moved default. Keep them unchanged and
        # represent the default deltas with an always-active variation region.
        regions = colr.VarStore.VarRegionList
        index = len(regions.Region)
        if index >= 32767:
            raise ValueError("COLR has no room for a constant variation region")
        regions.Region.append(buildVarRegion({}, range(regions.RegionAxisCount)))
        regions.RegionCount = len(regions.Region)
        for outer, data in enumerate(colr.VarStore.VarData):
            data.VarRegionIndex.append(index)
            for inner, row in enumerate(data.Item):
                row.append(otRound(deltas[(outer << 16) | inner]))
            data.VarRegionCount = len(data.VarRegionIndex)
            data.calculateNumShorts()
        deltas = dict.fromkeys(deltas, 0)
    for data in colr.VarStore.VarData:
        _splitLongDeltas(data)
    for root in roots:
        visit(root)
    if static:
        colr.VarStore = None
        colr.VarIndexMap = None
