from fontTools.ttLib.tables import otTables as ot
from fontTools.colorLib.builder import buildColrV1
from fontTools.colorLib.unbuilder import unbuildColrV1
import pytest


TEST_COLOR_GLYPHS = {
    "glyph00010": {
        "Format": int(ot.PaintFormat.PaintColrLayers),
        "Layers": [
            {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintSolid),
                    "PaletteIndex": 2,
                    "Alpha": 0.5,
                },
                "Glyph": "glyph00011",
            },
            {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintVarLinearGradient),
                    "ColorLine": {
                        "Extend": "repeat",
                        "ColorStop": [
                            {
                                "StopOffset": 0.0,
                                "PaletteIndex": 3,
                                "Alpha": 1.0,
                                "VarIndexBase": 0,
                            },
                            {
                                "StopOffset": 0.5,
                                "PaletteIndex": 4,
                                "Alpha": 1.0,
                                "VarIndexBase": 1,
                            },
                            {
                                "StopOffset": 1.0,
                                "PaletteIndex": 5,
                                "Alpha": 1.0,
                                "VarIndexBase": 2,
                            },
                        ],
                    },
                    "x0": 1,
                    "y0": 2,
                    "x1": -3,
                    "y1": -4,
                    "x2": 5,
                    "y2": 6,
                    "VarIndexBase": 0xFFFFFFFF,
                },
                "Glyph": "glyph00012",
            },
            {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintVarTransform),
                    "Paint": {
                        "Format": int(ot.PaintFormat.PaintRadialGradient),
                        "ColorLine": {
                            "Extend": "pad",
                            "ColorStop": [
                                {
                                    "StopOffset": 0,
                                    "PaletteIndex": 6,
                                    "Alpha": 1.0,
                                },
                                {
                                    "StopOffset": 1.0,
                                    "PaletteIndex": 7,
                                    "Alpha": 0.4,
                                },
                            ],
                        },
                        "x0": 7,
                        "y0": 8,
                        "r0": 9,
                        "x1": 10,
                        "y1": 11,
                        "r1": 12,
                    },
                    "Transform": {
                        "xx": -13.0,
                        "yx": 14.0,
                        "xy": 15.0,
                        "yy": -17.0,
                        "dx": 18.0,
                        "dy": 19.0,
                        "VarIndexBase": 3,
                    },
                },
                "Glyph": "glyph00013",
            },
            {
                "Format": int(ot.PaintFormat.PaintVarTranslate),
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintRotate),
                    "Paint": {
                        "Format": int(ot.PaintFormat.PaintVarSkew),
                        "Paint": {
                            "Format": int(ot.PaintFormat.PaintGlyph),
                            "Paint": {
                                "Format": int(ot.PaintFormat.PaintSolid),
                                "PaletteIndex": 2,
                                "Alpha": 0.5,
                            },
                            "Glyph": "glyph00011",
                        },
                        "xSkewAngle": -11.0,
                        "ySkewAngle": 5.0,
                        "VarIndexBase": 4,
                    },
                    "angle": 45.0,
                },
                "dx": 257.0,
                "dy": 258.0,
                "VarIndexBase": 5,
            },
        ],
    },
    "glyph00014": {
        "Format": int(ot.PaintFormat.PaintComposite),
        "SourcePaint": {
            "Format": int(ot.PaintFormat.PaintColrGlyph),
            "Glyph": "glyph00010",
        },
        "CompositeMode": "src_over",
        "BackdropPaint": {
            "Format": int(ot.PaintFormat.PaintTransform),
            "Paint": {
                "Format": int(ot.PaintFormat.PaintColrGlyph),
                "Glyph": "glyph00010",
            },
            "Transform": {
                "xx": 1.0,
                "yx": 0.0,
                "xy": 0.0,
                "yy": 1.0,
                "dx": 300.0,
                "dy": 0.0,
            },
        },
    },
    "glyph00015": {
        "Format": int(ot.PaintFormat.PaintGlyph),
        "Paint": {
            "Format": int(ot.PaintFormat.PaintSweepGradient),
            "ColorLine": {
                "Extend": "pad",
                "ColorStop": [
                    {
                        "StopOffset": 0.0,
                        "PaletteIndex": 3,
                        "Alpha": 1.0,
                    },
                    {
                        "StopOffset": 1.0,
                        "PaletteIndex": 5,
                        "Alpha": 1.0,
                    },
                ],
            },
            "centerX": 259,
            "centerY": 300,
            "startAngle": 45.0,
            "endAngle": 135.0,
        },
        "Glyph": "glyph00011",
    },
    "glyph00016": {
        "Format": int(ot.PaintFormat.PaintColrLayers),
        "Layers": [
            {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintVarSolid),
                    "PaletteIndex": 2,
                    "Alpha": 0.5,
                    "VarIndexBase": 6,
                },
                "Glyph": "glyph00011",
            },
            {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintVarLinearGradient),
                    "ColorLine": {
                        "Extend": "repeat",
                        "ColorStop": [
                            {
                                "StopOffset": 0.0,
                                "PaletteIndex": 3,
                                "Alpha": 1.0,
                                "VarIndexBase": 7,
                            },
                            {
                                "StopOffset": 0.5,
                                "PaletteIndex": 4,
                                "Alpha": 1.0,
                                "VarIndexBase": 8,
                            },
                            {
                                "StopOffset": 1.0,
                                "PaletteIndex": 5,
                                "Alpha": 1.0,
                                "VarIndexBase": 9,
                            },
                        ],
                    },
                    "x0": 1,
                    "y0": 2,
                    "x1": -3,
                    "y1": -4,
                    "x2": 5,
                    "y2": 6,
                    "VarIndexBase": 0xFFFFFFFF,
                },
                "Glyph": "glyph00012",
            },
        ],
    },
    # When PaintColrLayers contains more than 255 layers, we build a tree
    # of nested PaintColrLayers of max 255 items (NumLayers field is a uint8).
    # Below we test that unbuildColrV1 restores a flat list of layers without
    # nested PaintColrLayers.
    "glyph00017": {
        "Format": int(ot.PaintFormat.PaintColrLayers),
        "Layers": [
            {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintSolid),
                    "PaletteIndex": i,
                    "Alpha": 1.0,
                },
                "Glyph": "glyph{str(18 + i).zfill(5)}",
            }
            for i in range(256)
        ],
    },
}


def test_unbuildColrV1():
    layers, baseGlyphs = buildColrV1(TEST_COLOR_GLYPHS)
    colorGlyphs = unbuildColrV1(layers, baseGlyphs)
    assert colorGlyphs == TEST_COLOR_GLYPHS


def test_unbuildColrV1_noLayers():
    _, baseGlyphsV1 = buildColrV1(TEST_COLOR_GLYPHS)
    # Just looking to see we don't crash
    unbuildColrV1(None, baseGlyphsV1)
