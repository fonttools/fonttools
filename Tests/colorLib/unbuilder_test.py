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
                    "Color": {"PaletteIndex": 2, "Alpha": 0.5},
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
                                "StopOffset": (0.0, 0),
                                "Color": {"PaletteIndex": 3, "Alpha": (1.0, 0)},
                            },
                            {
                                "StopOffset": (0.5, 0),
                                "Color": {"PaletteIndex": 4, "Alpha": (1.0, 0)},
                            },
                            {
                                "StopOffset": (1.0, 0),
                                "Color": {"PaletteIndex": 5, "Alpha": (1.0, 0)},
                            },
                        ],
                    },
                    "x0": (1, 0),
                    "y0": (2, 0),
                    "x1": (-3, 0),
                    "y1": (-4, 0),
                    "x2": (5, 0),
                    "y2": (6, 0),
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
                                    "Color": {"PaletteIndex": 6, "Alpha": 1.0},
                                },
                                {
                                    "StopOffset": 1.0,
                                    "Color": {"PaletteIndex": 7, "Alpha": 0.4},
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
                        "xx": (-13.0, 0),
                        "yx": (14.0, 0),
                        "xy": (15.0, 0),
                        "yy": (-17.0, 0),
                        "dx": (18.0, 0),
                        "dy": (19.0, 0),
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
                                "Color": {"PaletteIndex": 2, "Alpha": 0.5},
                            },
                            "Glyph": "glyph00011",
                        },
                        "xSkewAngle": (-11.0, 0),
                        "ySkewAngle": (5.0, 0),
                        "centerX": (253.0, 0),
                        "centerY": (254.0, 0),
                    },
                    "angle": 45.0,
                    "centerX": 255.0,
                    "centerY": 256.0,
                },
                "dx": (257.0, 0),
                "dy": (258.0, 0),
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
                        "Color": {"PaletteIndex": 3, "Alpha": 1.0},
                    },
                    {
                        "StopOffset": 1.0,
                        "Color": {"PaletteIndex": 5, "Alpha": 1.0},
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
                    "Color": {"PaletteIndex": 2, "Alpha": (0.5, 0)},
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
                                "StopOffset": (0.0, 0),
                                "Color": {"PaletteIndex": 3, "Alpha": (1.0, 0)},
                            },
                            {
                                "StopOffset": (0.5, 0),
                                "Color": {"PaletteIndex": 4, "Alpha": (1.0, 0)},
                            },
                            {
                                "StopOffset": (1.0, 0),
                                "Color": {"PaletteIndex": 5, "Alpha": (1.0, 0)},
                            },
                        ],
                    },
                    "x0": (1, 0),
                    "y0": (2, 0),
                    "x1": (-3, 0),
                    "y1": (-4, 0),
                    "x2": (5, 0),
                    "y2": (6, 0),
                },
                "Glyph": "glyph00012",
            },
        ],
    },
}


def test_unbuildColrV1():
    layersV1, baseGlyphsV1 = buildColrV1(TEST_COLOR_GLYPHS)
    colorGlyphs = unbuildColrV1(layersV1, baseGlyphsV1)
    assert colorGlyphs == TEST_COLOR_GLYPHS
