from fontTools.colorLib.builder import buildCOLR
from fontTools.ttLib.tables import otTables as ot
from fontTools.misc.fixedTools import floatToFixed as fl2fi


def varcToCOLR(font):
    glyf = font["glyf"]

    axisTags = glyf.axisTags
    axisIndices = {tag: i for i, tag in enumerate(axisTags)}

    paintForeground = {'Format': ot.PaintFormat.PaintSolid,
                       'PaletteIndex': 0xFFFF,
                       'Alpha': 1.0}

    colorGlyphs = {}
    for glyphName in glyf.keys():
        glyph = glyf[glyphName]
        if glyph.isVarComposite():

            layers = []

            for component in glyph.components:
                if glyf[component.glyphName].isVarComposite():

                    paint = {'Format': ot.PaintFormat.PaintColrGlyph,
                             'Glyph': component.glyphName}
                else:
                    paint = {'Format': ot.PaintFormat.PaintGlyph,
                             'Paint': paintForeground,
                             'Glyph': component.glyphName}

                transform = component.transform

                # Check for non-integer values

                if (transform.translateX or transform.translateY or
                    transform.tCenterX or transform.tCenterY):
                    paint = {'Format': ot.PaintFormat.PaintTranslate,
                             'Paint': paint,
                             'dx': transform.translateX + transform.tCenterX,
                             'dy': transform.translateY + transform.tCenterY}

                if transform.rotation:
                    paint = {'Format': ot.PaintFormat.PaintRotate,
                             'Paint': paint,
                             'angle': transform.rotation}

                if transform.scaleX != 1.0 or transform.scaleY != 1.0:
                    if (abs(transform.scaleX) < 2.0 and abs(transform.scaleY) < 2.0):
                        paint = {'Format': ot.PaintFormat.PaintScale,
                                 'Paint': paint,
                                 'scaleX': transform.scaleX,
                                 'scaleY': transform.scaleY}
                    else:
                        affine = ot.Affine2x3()
                        affine.xx = transform.scaleX
                        affine.xy = 0.0
                        affine.yx = 0.0
                        affine.yy = transform.scaleX
                        affine.dx = 0.0
                        affine.dy = 0.0
                        paint = {'Format': ot.PaintFormat.PaintTransform,
                                 'Paint': paint,
                                 'Transform': affine}

                if transform.skewX or transform.skewY:
                    paint = {'Format': ot.PaintFormat.PaintSkew,
                             'Paint': paint,
                             'xSkewAngle': transform.skewX,
                             'ySkewAngle': -transform.skewY}

                if transform.tCenterX or transform.tCenterY:
                    paint = {'Format': ot.PaintFormat.PaintTranslate,
                             'Paint': paint,
                             'dx': -transform.tCenterX,
                             'dy': -transform.tCenterY}

                if component.location:
                    axisList = []
                    axisValues = []
                    for axisTag, value in component.location.items():
                        axisList.append(axisIndices[axisTag])
                        axisValues.append(value)

                    AxisList = ot.AxisList()
                    AxisList.Axis = axisList

                    AxisValues = ot.AxisValues()
                    AxisValues.Value = axisValues

                    paint = {'Format': ot.PaintFormat.PaintLocation,
                             'Paint': paint,
                             'AxisList': AxisList,
                             'AxisValues': AxisValues}

                layers.append(paint)

            colorGlyphs[glyphName] = {'Format': ot.PaintFormat.PaintColrLayers,
                                      'Layers': layers}

    for glyphName in colorGlyphs:
        glyf[glyphName].numberOfContours = 0

    colr = buildCOLR(colorGlyphs,
                     version=1,
                     glyphMap=font.getReverseGlyphMap())
    font["COLR"] = colr


if __name__ == "__main__":
    import sys
    from fontTools.ttLib import TTFont

    font = TTFont(sys.argv[1])

    varcToCOLR(font)

    font.save(sys.argv[2])
