from .ttGlyphSet import _TTGlyphSet, _TTGlyph
from fontTools.misc.transform import Transform
from fontTools.ttLib.tables.otTables import hvglTranslationDelta

from enum import IntEnum
from collections.abc import MutableSequence

# Drawing logic ported from HarfBuzz hb-aat-var-hvgl.cc


class Segment():

    __slots__ = ("_source_list", "_offset")

    def __init__(self, source_list, offset):

        if not (4 <= offset + 4 <= len(source_list)):
            raise ValueError("offset must be within the bounds of the list")

        self._source_list = source_list
        self._offset = offset

    def __getitem__(self, index):
        if 0 <= index < 4:
            return self._source_list[self._offset + index]
        raise IndexError("index out of range")

    def __setitem__(self, index, value):
        if 0 <= index < 4:
            self._source_list[self._offset + index] = value
        else:
            raise IndexError("index out of range")

    def __repr__(self):
        return f"Segment({self._source_list[self._offset:self._offset + 4]})"


class _TTGlyphSetHVF(_TTGlyphSet):
    def __init__(self, font, location):
        self.hvglTable = font["hvgl"].table
        mapping = font.getReverseGlyphMap()
        super().__init__(font, location, mapping)

    def __getitem__(self, glyphName):
        return _TTGlyphHVF(self, glyphName)


class _TTGlyphHVF(_TTGlyph):
    def draw(self, pen):
        """Draw the glyph onto ``pen``. See fontTools.pens.basePen for details
        how that works.
        """
        hvgl = self.glyphSet.hvglTable
        part = hvgl.Parts.Part[self.glyphSet.glyphsMapping[self.name]]

        coords = [0.0] * _partGetTotalNumAxes(part)
        fvarAxes = self.glyphSet.font["fvar"].axes
        location = self.glyphSet.location
        for i, axis in enumerate(fvarAxes[: len(coords)]):
            coords[i] = location.get(axis.axisTag, 0)

        transforms = [Transform() for _ in range(_partGetTotalNumParts(part))]

        _drawPart(part, pen, self.glyphSet, coords, 0, transforms, 0)

    def drawPoints(self, pen):
        """Draw the glyph onto ``pen``. See fontTools.pens.pointPen for details
        how that works.
        """
        from fontTools.pens.pointPen import SegmentToPointPen

        self.draw(SegmentToPointPen(pen))


def _partGetTotalNumAxes(part):
    if part.Format == 0:
        return part.AxisCount
    elif part.Format == 1:
        return part.TotalNumAxes
    else:
        raise NotImplementedError("Unknown part flags: %s" % part.Format)


def _partGetTotalNumParts(part):
    if part.Format == 0:
        return 1
    elif part.Format == 1:
        return part.TotalNumParts
    else:
        raise NotImplementedError("Unknown part flags: %s" % part.Format)


class SegmentPoint(IntEnum):
    ON_CURVE_X = 0
    ON_CURVE_Y = 1
    OFF_CURVE_X = 2
    OFF_CURVE_Y = 3


class BlendType(IntEnum):
    CURVE = 0
    CORNER = 1
    TANGENT = 2
    TANGENT_PAIR_FIRST = 3
    TANGENT_PAIR_SECOND = 4


def _project_on_curve_to_tangent(offcurve1, oncurve, offcurve2):
    x = oncurve[SegmentPoint.ON_CURVE_X]
    y = oncurve[SegmentPoint.ON_CURVE_Y]

    x1 = offcurve1[SegmentPoint.OFF_CURVE_X]
    y1 = offcurve1[SegmentPoint.OFF_CURVE_Y]
    x2 = offcurve2[SegmentPoint.OFF_CURVE_X]
    y2 = offcurve2[SegmentPoint.OFF_CURVE_Y]

    dx = x2 - x1
    dy = y2 - y1

    l2 = dx * dx + dy * dy
    t = l2 if l2 else (dx * (x - x1) + dy * (y - y1)) / l2
    t = max(0, min(1, t))

    x = x1 + dx * t
    y = y1 + dy * t

    oncurve[SegmentPoint.ON_CURVE_X] = x
    oncurve[SegmentPoint.ON_CURVE_Y] = y


def _drawPartShape(part, pen, _glyphSet, coords, coordsOffset, transforms, transformOffset):
    transform = transforms[transformOffset]

    v = list(part.Master.Coords)

    # Apply deltas
    deltas = part.Deltas.Delta
    for axis_index in range(part.AxisCount):
        coord = coords[coordsOffset+axis_index]
        if coord == 0:
            continue
        pos = coord > 0
        column_idx = axis_index * 2 + pos
        scalar = abs(coord)

        column = deltas[column_idx]
        for i, delta in enumerate(column.Coords):
            v[i] += delta * scalar

    start = 0
    for pathSegmentCount in part.SegmentCountPerPath:
        end = start + pathSegmentCount

        if start == end:
            continue

        # Resolve blend types
        segment = Segment(v, (end - 1) * 4)
        for i in range(start, end):
            blendType = part.BlendTypes[i]
            prev_segment = segment
            segment = Segment(v, i * 4)

            if blendType == BlendType.CURVE:

                t = segment[SegmentPoint.ON_CURVE_X]
                t = max(0, min(1, t))

                # Interpolate between the off-curve points
                x = (
                    prev_segment[SegmentPoint.OFF_CURVE_X]
                    + (
                        segment[SegmentPoint.OFF_CURVE_X]
                        - prev_segment[SegmentPoint.OFF_CURVE_X]
                    )
                    * t
                )
                y = (
                    prev_segment[SegmentPoint.OFF_CURVE_Y]
                    + (
                        segment[SegmentPoint.OFF_CURVE_Y]
                        - prev_segment[SegmentPoint.OFF_CURVE_Y]
                    )
                    * t
                )

                segment[0] = x
                segment[1] = y

            elif blendType == BlendType.CORNER:
                pass

            elif blendType == BlendType.TANGENT:
                # Project onto the line between the off-curve point
                # of the previous segment and the off-curve point of
                # this segment */
                _project_on_curve_to_tangent(prev_segment, segment, segment)
                pass
            elif blendType == BlendType.TANGENT_PAIR_FIRST:
                next_i = start if i == end - 1 else i + 1
                next_segment = Segment(v, next_i * 4)

                _project_on_curve_to_tangent(prev_segment, segment, next_segment)
                _project_on_curve_to_tangent(prev_segment, next_segment, next_segment)
                pass
            elif blendType == BlendType.TANGENT_PAIR_SECOND:
                pass
            else:
                raise NotImplementedError("Unknown blend type: %s" % blendType)

        # Draw
        next_segment = Segment(v, start * 4)
        x0 = next_segment[SegmentPoint.ON_CURVE_X]
        y0 = next_segment[SegmentPoint.ON_CURVE_Y]
        p0 = transform.transformPoint((x0, y0))
        pen.moveTo(p0)
        for i in range(start, end):
            segment = next_segment
            next_i = start if i == end - 1 else i + 1
            next_segment = Segment(v, next_i * 4)

            x1 = segment[SegmentPoint.OFF_CURVE_X]
            y1 = segment[SegmentPoint.OFF_CURVE_Y]
            x2 = next_segment[SegmentPoint.ON_CURVE_X]
            y2 = next_segment[SegmentPoint.ON_CURVE_Y]
            p1 = transform.transformPoint((x1, y1))
            p2 = transform.transformPoint((x2, y2))
            pen.qCurveTo(p1, p2)
        pen.closePath()

        start = end


def _partCompositeApplyToCoords(part, out_coords, coords):
    ecs = part.ExtremumColumnStarts  # Worst named member ever

    for row_index, delta in zip(
        ecs.MasterRowIndex, part.MasterAxisValueDeltas.MasterAxisValueDelta
    ):
        out_coords[row_index] += delta

    for axis_idx, coord in enumerate(coords):
        if coord == 0:
            continue
        pos = coord > 0
        column_idx = axis_idx * 2 + pos
        scalar = abs(coord)

        sparse_row_start = ecs.ExtremumColumnStart[column_idx]
        sparse_row_end = ecs.ExtremumColumnStart[column_idx + 1]
        for row_idx in range(sparse_row_start, sparse_row_end):
            row = ecs.ExtremumRowIndex[row_idx]
            delta = part.ExtremumAxisValueDeltas.ExtremumAxisValueDelta[row_idx]
            if delta:
                out_coords[row] += delta * scalar


def _partCompositeApplyToTransforms(part, transforms, transformOffset, coords):
    master_rotation_index = list(part.AllRotations.MasterRotationIndex)
    master_rotation_delta = list(part.AllRotations.MasterRotationDelta)
    master_translation_index = list(part.AllTranslations.MasterTranslationIndex)
    master_translation_delta = list(part.AllTranslations.MasterTranslationDelta)
    extremum_translation_index = list(part.AllTranslations.ExtremumTranslationIndex)
    extremum_translation_delta = list(part.AllTranslations.ExtremumTranslationDelta)
    extremum_rotation_index = list(part.AllRotations.ExtremumRotationIndex)
    extremum_rotation_delta = list(part.AllRotations.ExtremumRotationDelta)

    while True:
        row = len(transforms) - transformOffset
        if master_translation_index:
            row = min(row, master_translation_index[0])
        if master_rotation_index:
            row = min(row, master_rotation_index[0])
        if extremum_translation_index:
            row = min(row, extremum_translation_index[0].row)
        if extremum_rotation_index:
            row = min(row, extremum_rotation_index[0].row)
        if row == len(transforms) - transformOffset:
            break

        transform = Transform()

        if master_rotation_index and master_rotation_index[0] == row:
            transform = transform.rotate(master_rotation_delta[0], True)
            master_rotation_index.pop(0)
            master_rotation_delta.pop(0)

        if master_translation_index and master_translation_index[0] == row:
            transform = transform.translate(
                master_translation_delta[0].x, master_translation_delta[0].y, True
            )
            master_translation_index.pop(0)
            master_translation_delta.pop(0)

        while True:
            translation_delta = hvglTranslationDelta()
            rotation_delta = 0

            column = 2 * part.AxisCount
            if extremum_translation_index and extremum_translation_index[0].row == row:
                column = min(column, extremum_translation_index[0].column)
            if extremum_rotation_index and extremum_rotation_index[0].row == row:
                column = min(column, extremum_rotation_index[0].column)
            if column == 2 * part.AxisCount:
                break

            if (
                extremum_translation_index
                and extremum_translation_index[0].row == row
                and extremum_translation_index[0].column == column
            ):
                translation_delta = extremum_translation_delta[0]
                extremum_translation_index.pop(0)
                extremum_translation_delta.pop(0)
            if (
                extremum_rotation_index
                and extremum_rotation_index[0].row == row
                and extremum_rotation_index[0].column == column
            ):
                rotation_delta = extremum_rotation_delta[0]
                extremum_rotation_index.pop(0)
                extremum_rotation_delta.pop(0)

            axis_idx = column // 2
            coord = coords[axis_idx]
            if coord == 0:
                continue
            pos = column & 1
            if pos != (coord > 0):
                continue
            scalar = abs(coord)

            if rotation_delta:
                t = complex(translation_delta.x, translation_delta.y)
                _1_minus_e_iangle = 1 - complex(0, 1) * rotation_delta
                eigen = t / _1_minus_e_iangle
                eigen_x = eigen.real
                eigen_y = eigen.imag
                transform2 = Transform()
                transform2.translate(-eigen_x, -eigen_y, True)
                transform2.rotate(rotation_delta * scalar, True)
                transform2.translate(eigen_x, eigen_y, True)
                transform = transform.transform(transform2)
            else:
                # No rotation, just scale the translate
                transform = transform.translate(
                    translation_delta.x * scalar,
                    translation_delta.y * scalar,
                )

        transforms[transformOffset+row] = transforms[transformOffset+row].transform(transform, True)


def _drawPartComposite(part, pen, glyphSet, coords, coordsOffset, transforms, transformOffset):
    hvgl = glyphSet.hvglTable

    coords_head = coords[coordsOffset:coordsOffset+part.AxisCount]
    coords_tail = coords[coordsOffset+part.AxisCount:coordsOffset+part.TotalNumAxes]
    del coords

    _partCompositeApplyToCoords(part, coords_tail, coords_head)

    transforms_head = transforms[transformOffset]

    _partCompositeApplyToTransforms(part, transforms, transformOffset+1, coords_head)

    for subPart in part.SubParts.SubPart:
        subpartTransformOffset = transformOffset+1+subPart.TreeTransformIndex
        transforms[subpartTransformOffset] = transforms[subpartTransformOffset].transform(transforms_head, True)
        subpart = hvgl.Parts.Part[subPart.PartIndex]
        _drawPart(subpart, pen, glyphSet,
                  coords_tail, subPart.TreeAxisIndex,
                  transforms, subpartTransformOffset)


def _drawPart(part, pen, glyphSet, coords, coordsOffset, transforms, transformOffset):
    if part.Format == 0:
        _drawPartShape(part, pen, glyphSet, coords, coordsOffset, transforms, transformOffset)
    elif part.Format == 1:
        _drawPartComposite(part, pen, glyphSet, coords, coordsOffset, transforms, transformOffset)
    else:
        raise NotImplementedError("Unknown part flags: %s" % part.flags)
