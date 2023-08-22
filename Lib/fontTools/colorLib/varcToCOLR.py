from fontTools.colorLib.builder import buildCOLR
from fontTools.ttLib.tables import otTables as ot
from fontTools.misc.fixedTools import floatToFixed as fl2fi


def varcToCOLR(font):
    glyf = font["glyf"]

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
                    paint = {'Format': ot.PaintFormat.PaintScale,
                             'Paint': paint,
                             'scaleX': transform.scaleX,
                             'scaleY': transform.scaleY}

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
