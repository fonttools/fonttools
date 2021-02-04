from fontTools.ttLib.tables import otTables as ot


def unbuildColrV1(layerV1List, baseGlyphV1List, ignoreVarIdx=False):
    unbuilder = LayerV1ListUnbuilder(layerV1List.Paint, ignoreVarIdx=ignoreVarIdx)
    return {
        rec.BaseGlyph: unbuilder.unbuildPaint(rec.Paint)
        for rec in baseGlyphV1List.BaseGlyphV1Record
    }


def _unbuildVariableValue(v, ignoreVarIdx=False):
    return v.value if ignoreVarIdx else (v.value, v.varIdx)


def unbuildColorStop(colorStop, ignoreVarIdx=False):
    return {
        "offset": _unbuildVariableValue(
            colorStop.StopOffset, ignoreVarIdx=ignoreVarIdx
        ),
        "paletteIndex": colorStop.Color.PaletteIndex,
        "alpha": _unbuildVariableValue(
            colorStop.Color.Alpha, ignoreVarIdx=ignoreVarIdx
        ),
    }


def unbuildColorLine(colorLine, ignoreVarIdx=False):
    return {
        "stops": [
            unbuildColorStop(stop, ignoreVarIdx=ignoreVarIdx)
            for stop in colorLine.ColorStop
        ],
        "extend": colorLine.Extend.name.lower(),
    }


def unbuildAffine2x3(transform, ignoreVarIdx=False):
    return tuple(
        _unbuildVariableValue(getattr(transform, attr), ignoreVarIdx=ignoreVarIdx)
        for attr in ("xx", "yx", "xy", "yy", "dx", "dy")
    )


def _flatten(lst):
    for el in lst:
        if isinstance(el, list):
            yield from _flatten(el)
        else:
            yield el


class LayerV1ListUnbuilder:
    def __init__(self, layers, ignoreVarIdx=False):
        self.layers = layers
        self.ignoreVarIdx = ignoreVarIdx

    def unbuildPaint(self, paint):
        try:
            return self._unbuildFunctions[paint.Format](self, paint)
        except KeyError:
            raise ValueError(f"Unrecognized paint format: {paint.Format}")

    def unbuildVariableValue(self, value):
        return _unbuildVariableValue(value, ignoreVarIdx=self.ignoreVarIdx)

    def unbuildPaintColrLayers(self, paint):
        return list(
            _flatten(
                [
                    self.unbuildPaint(childPaint)
                    for childPaint in self.layers[
                        paint.FirstLayerIndex : paint.FirstLayerIndex + paint.NumLayers
                    ]
                ]
            )
        )

    def unbuildPaintSolid(self, paint):
        return {
            "format": int(paint.Format),
            "paletteIndex": paint.Color.PaletteIndex,
            "alpha": self.unbuildVariableValue(paint.Color.Alpha),
        }

    def unbuildPaintLinearGradient(self, paint):
        p0 = (self.unbuildVariableValue(paint.x0), self.unbuildVariableValue(paint.y0))
        p1 = (self.unbuildVariableValue(paint.x1), self.unbuildVariableValue(paint.y1))
        p2 = (self.unbuildVariableValue(paint.x2), self.unbuildVariableValue(paint.y2))
        return {
            "format": int(ot.Paint.Format.PaintLinearGradient),
            "colorLine": unbuildColorLine(
                paint.ColorLine, ignoreVarIdx=self.ignoreVarIdx
            ),
            "p0": p0,
            "p1": p1,
            "p2": p2,
        }

    def unbuildPaintRadialGradient(self, paint):
        c0 = (self.unbuildVariableValue(paint.x0), self.unbuildVariableValue(paint.y0))
        r0 = self.unbuildVariableValue(paint.r0)
        c1 = (self.unbuildVariableValue(paint.x1), self.unbuildVariableValue(paint.y1))
        r1 = self.unbuildVariableValue(paint.r1)
        return {
            "format": int(ot.Paint.Format.PaintRadialGradient),
            "colorLine": unbuildColorLine(
                paint.ColorLine, ignoreVarIdx=self.ignoreVarIdx
            ),
            "c0": c0,
            "r0": r0,
            "c1": c1,
            "r1": r1,
        }

    def unbuildPaintSweepGradient(self, paint):
        return {
            "format": int(ot.Paint.Format.PaintSweepGradient),
            "colorLine": unbuildColorLine(
                paint.ColorLine, ignoreVarIdx=self.ignoreVarIdx
            ),
            "centerX": self.unbuildVariableValue(paint.centerX),
            "centerY": self.unbuildVariableValue(paint.centerY),
            "startAngle": self.unbuildVariableValue(paint.startAngle),
            "endAngle": self.unbuildVariableValue(paint.endAngle),
        }

    def unbuildPaintGlyph(self, paint):
        return {
            "format": int(ot.Paint.Format.PaintGlyph),
            "glyph": paint.Glyph,
            "paint": self.unbuildPaint(paint.Paint),
        }

    def unbuildPaintColrGlyph(self, paint):
        return {
            "format": int(ot.Paint.Format.PaintColrGlyph),
            "glyph": paint.Glyph,
        }

    def unbuildPaintTransform(self, paint):
        return {
            "format": int(ot.Paint.Format.PaintTransform),
            "transform": unbuildAffine2x3(
                paint.Transform, ignoreVarIdx=self.ignoreVarIdx
            ),
            "paint": self.unbuildPaint(paint.Paint),
        }

    def unbuildPaintTranslate(self, paint):
        return {
            "format": int(ot.Paint.Format.PaintTranslate),
            "dx": self.unbuildVariableValue(paint.dx),
            "dy": self.unbuildVariableValue(paint.dy),
            "paint": self.unbuildPaint(paint.Paint),
        }

    def unbuildPaintRotate(self, paint):
        return {
            "format": int(ot.Paint.Format.PaintRotate),
            "angle": self.unbuildVariableValue(paint.angle),
            "centerX": self.unbuildVariableValue(paint.centerX),
            "centerY": self.unbuildVariableValue(paint.centerY),
            "paint": self.unbuildPaint(paint.Paint),
        }

    def unbuildPaintSkew(self, paint):
        return {
            "format": int(ot.Paint.Format.PaintSkew),
            "xSkewAngle": self.unbuildVariableValue(paint.xSkewAngle),
            "ySkewAngle": self.unbuildVariableValue(paint.ySkewAngle),
            "centerX": self.unbuildVariableValue(paint.centerX),
            "centerY": self.unbuildVariableValue(paint.centerY),
            "paint": self.unbuildPaint(paint.Paint),
        }

    def unbuildPaintComposite(self, paint):
        return {
            "format": int(ot.Paint.Format.PaintComposite),
            "mode": paint.CompositeMode.name.lower(),
            "source": self.unbuildPaint(paint.SourcePaint),
            "backdrop": self.unbuildPaint(paint.BackdropPaint),
        }


LayerV1ListUnbuilder._unbuildFunctions = {
    pf.value: getattr(LayerV1ListUnbuilder, "unbuild" + pf.name)
    for pf in ot.Paint.Format
}


if __name__ == "__main__":
    from pprint import pprint
    import sys
    from fontTools.ttLib import TTFont

    try:
        fontfile = sys.argv[1]
    except IndexError:
        sys.exit("usage: fonttools colorLib.unbuilder FONTFILE")

    font = TTFont(fontfile)
    colr = font["COLR"]
    if colr.version < 1:
        sys.exit(f"error: No COLR table version=1 found in {fontfile}")

    colorGlyphs = unbuildColrV1(
        colr.table.LayerV1List,
        colr.table.BaseGlyphV1List,
        ignoreVarIdx=not colr.table.VarStore,
    )

    pprint(colorGlyphs)
