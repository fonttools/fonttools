"""Instantiate COLRv1 paint values and their item variation store."""

from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables.otConverters import BaseFixedValue, Angle, Short, UShort
from fontTools.misc.roundTools import otRound
from fontTools.varLib.builder import buildVarRegion
from math import trunc


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
        for xx, yx, xy, yy, dx, dy in reversed(matrices):
            matrix = ot.Affine2x3()
            matrix.xx, matrix.yx, matrix.xy, matrix.yy = xx, yx, xy, yy
            matrix.dx, matrix.dy = dx, dy
            wrapper = ot.Paint()
            wrapper.Format = ot.PaintFormat.PaintTransform
            wrapper.Paint, wrapper.Transform = child, matrix
            child = wrapper
        transform, child = child.Transform, child.Paint
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
                if name in ("r0", "r1"):
                    value = min(65535, max(0, value))
            setattr(table, name, value)

        if static and apply:
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
