from fontTools.ttLib.tables import otTables as ot
from fontTools.colorLib.builder import buildColrV1
from fontTools.colorLib.unbuilder import unbuildColrV1
import pytest


TEST_COLOR_GLYPHS = {
    "glyph00010": (
        ot.PaintFormat.PaintColrLayers,
        [
            {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Glyph": "glyph00011",
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintSolid),
                    "Color": {
                        "PaletteIndex": 2,
                        "Alpha": 0.5,
                    },
                },
            },
            {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Glyph": "glyph00012",
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintLinearGradient),
                    "ColorLine": {
                        "ColorStop": [
                            {
                                "StopOffset": 0.0,
                                "Color": {"PaletteIndex": 3, "Alpha": 1.0},
                            },
                            {
                                "StopOffset": 0.5,
                                "Color": {"PaletteIndex": 4, "Alpha": 1.0},
                            },
                            {
                                "StopOffset": 1.0,
                                "Color": {"PaletteIndex": 5, "Alpha": 1.0},
                            },
                        ],
                        "Extend": "repeat",
                    },
                    "x0": 1,
                    "y0": 2,
                    "x1": -3,
                    "y1": -4,
                    "x2": 5,
                    "y2": 6,
                },
            },
            {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Glyph": "glyph00013",
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintTransform),
                    "Transform": (-13.0, 14.0, 15.0, -17.0, 18.0, 19.0),
                    "Paint": {
                        "Format": int(ot.PaintFormat.PaintRadialGradient),
                        "ColorLine": {
                            "ColorStop": [
                                {
                                    "StopOffset": 0.0,
                                    "Color": {"PaletteIndex": 6, "Alpha": 1.0},
                                },
                                {
                                    "StopOffset": 1.0,
                                    "Color": {
                                        "PaletteIndex": 7,
                                        "Alpha": 0.4,
                                    },
                                },
                            ],
                            "Extend": "pad",
                        },
                        "x0": 7,
                        "y0": 8,
                        "r0": 9,
                        "x1": 10,
                        "y1": 11,
                        "r1": 12,
                    },
                },
            },
            {
                "Format": int(ot.PaintFormat.PaintTranslate),
                "dx": 257.0,
                "dy": 258.0,
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintRotate),
                    "angle": 45.0,
                    "centerX": 255.0,
                    "centerY": 256.0,
                    "Paint": {
                        "Format": int(ot.PaintFormat.PaintSkew),
                        "xSkewAngle": -11.0,
                        "ySkewAngle": 5.0,
                        "centerX": 253.0,
                        "centerY": 254.0,
                        "Paint": {
                            "Format": int(ot.PaintFormat.PaintGlyph),
                            "Glyph": "glyph00011",
                            "Paint": {
                                "Format": int(ot.PaintFormat.PaintSolid),
                                "Color": {
                                    "PaletteIndex": 2,
                                    "Alpha": 0.5,
                                },
                            },
                        },
                    },
                },
            },
        ],
    ),
    "glyph00014": {
        "Format": int(ot.PaintFormat.PaintComposite),
        "CompositeMode": "src_over",
        "SourcePaint": {
            "Format": int(ot.PaintFormat.PaintColrGlyph),
            "Glyph": "glyph00010",
        },
        "BackdropPaint": {
            "Format": int(ot.PaintFormat.PaintTransform),
            "Transform": (1.0, 0.0, 0.0, 1.0, 300.0, 0.0),
            "Paint": {
                "Format": int(ot.PaintFormat.PaintColrGlyph),
                "Glyph": "glyph00010",
            },
        },
    },
    "glyph00015": {
        "Format": int(ot.PaintFormat.PaintGlyph),
        "Glyph": "glyph00011",
        "Paint": {
            "Format": int(ot.PaintFormat.PaintSweepGradient),
            "ColorLine": {
                "ColorStop": [
                    {"StopOffset": 0.0, "Color": {"PaletteIndex": 3, "Alpha": 1.0}},
                    {"StopOffset": 1.0, "Color": {"PaletteIndex": 5, "Alpha": 1.0}},
                ],
                "Extend": "pad",
            },
            "centerX": 259,
            "centerY": 300,
            "startAngle": 45.0,
            "endAngle": 135.0,
        },
    },
    "glyph00016": (
        ot.PaintFormat.PaintColrLayers,
        [
            {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Glyph": "glyph00011",
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintSolid),
                    "Color": {
                        "PaletteIndex": 2,
                        "Alpha": 0.5,
                    },
                },
            },
            {
                "Format": int(ot.PaintFormat.PaintGlyph),
                "Glyph": "glyph00012",
                "Paint": {
                    "Format": int(ot.PaintFormat.PaintLinearGradient),
                    "ColorLine": {
                        "ColorStop": [
                            {
                                "StopOffset": 0.0,
                                "Color": {"PaletteIndex": 3, "Alpha": 1.0},
                            },
                            {
                                "StopOffset": 0.5,
                                "Color": {"PaletteIndex": 4, "Alpha": 1.0},
                            },
                            {
                                "StopOffset": 1.0,
                                "Color": {"PaletteIndex": 5, "Alpha": 1.0},
                            },
                        ],
                        "Extend": "repeat",
                    },
                    "x0": 1,
                    "y0": 2,
                    "x1": -3,
                    "y1": -4,
                    "x2": 5,
                    "y2": 6,
                },
            },
        ],
    ),
}


def test_unbuildColrV1():
    layersV1, baseGlyphsV1 = buildColrV1(TEST_COLOR_GLYPHS)
    colorGlyphs = unbuildColrV1(layersV1, baseGlyphsV1, ignoreVarIdx=True)
    assert colorGlyphs == TEST_COLOR_GLYPHS
