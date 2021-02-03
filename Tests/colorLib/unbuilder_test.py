from fontTools.ttLib.tables import otTables as ot
from fontTools.colorLib.builder import buildColrV1
from fontTools.colorLib.unbuilder import unbuildColrV1
import pytest


TEST_COLOR_GLYPHS = {
    "glyph00010": [
        {
            "format": int(ot.Paint.Format.PaintGlyph),
            "glyph": "glyph00011",
            "paint": {
                "format": int(ot.Paint.Format.PaintSolid),
                "paletteIndex": 2,
                "alpha": 0.5,
            },
        },
        {
            "format": int(ot.Paint.Format.PaintGlyph),
            "glyph": "glyph00012",
            "paint": {
                "format": int(ot.Paint.Format.PaintLinearGradient),
                "colorLine": {
                    "stops": [
                        {"offset": 0.0, "paletteIndex": 3, "alpha": 1.0},
                        {"offset": 0.5, "paletteIndex": 4, "alpha": 1.0},
                        {"offset": 1.0, "paletteIndex": 5, "alpha": 1.0},
                    ],
                    "extend": "repeat",
                },
                "p0": (1, 2),
                "p1": (-3, -4),
                "p2": (5, 6),
            },
        },
        {
            "format": int(ot.Paint.Format.PaintGlyph),
            "glyph": "glyph00013",
            "paint": {
                "format": int(ot.Paint.Format.PaintTransform),
                "transform": (-13.0, 14.0, 15.0, -17.0, 18.0, 19.0),
                "paint": {
                    "format": int(ot.Paint.Format.PaintRadialGradient),
                    "colorLine": {
                        "stops": [
                            {"offset": 0.0, "paletteIndex": 6, "alpha": 1.0},
                            {
                                "offset": 1.0,
                                "paletteIndex": 7,
                                "alpha": 0.4,
                            },
                        ],
                        "extend": "pad",
                    },
                    "c0": (7, 8),
                    "r0": 9,
                    "c1": (10, 11),
                    "r1": 12,
                },
            },
        },
        {
            "format": int(ot.Paint.Format.PaintTranslate),
            "dx": 257.0,
            "dy": 258.0,
            "paint": {
                "format": int(ot.Paint.Format.PaintRotate),
                "angle": 45.0,
                "centerX": 255.0,
                "centerY": 256.0,
                "paint": {
                    "format": int(ot.Paint.Format.PaintSkew),
                    "xSkewAngle": -11.0,
                    "ySkewAngle": 5.0,
                    "centerX": 253.0,
                    "centerY": 254.0,
                    "paint": {
                        "format": int(ot.Paint.Format.PaintGlyph),
                        "glyph": "glyph00011",
                        "paint": {
                            "format": int(ot.Paint.Format.PaintSolid),
                            "paletteIndex": 2,
                            "alpha": 0.5,
                        },
                    },
                },
            },
        },
    ],
    "glyph00014": {
        "format": int(ot.Paint.Format.PaintComposite),
        "mode": "src_over",
        "source": {
            "format": int(ot.Paint.Format.PaintColrGlyph),
            "glyph": "glyph00010",
        },
        "backdrop": {
            "format": int(ot.Paint.Format.PaintTransform),
            "transform": (1.0, 0.0, 0.0, 1.0, 300.0, 0.0),
            "paint": {
                "format": int(ot.Paint.Format.PaintColrGlyph),
                "glyph": "glyph00010",
            },
        },
    },
    "glyph00015": [
        {
            "format": int(ot.Paint.Format.PaintGlyph),
            "glyph": "glyph00011",
            "paint": {
                "format": int(ot.Paint.Format.PaintSolid),
                "paletteIndex": 2,
                "alpha": 0.5,
            },
        },
        {
            "format": int(ot.Paint.Format.PaintGlyph),
            "glyph": "glyph00012",
            "paint": {
                "format": int(ot.Paint.Format.PaintLinearGradient),
                "colorLine": {
                    "stops": [
                        {"offset": 0.0, "paletteIndex": 3, "alpha": 1.0},
                        {"offset": 0.5, "paletteIndex": 4, "alpha": 1.0},
                        {"offset": 1.0, "paletteIndex": 5, "alpha": 1.0},
                    ],
                    "extend": "repeat",
                },
                "p0": (1, 2),
                "p1": (-3, -4),
                "p2": (5, 6),
            },
        },
    ],
}


def test_unbuildColrV1():
    layersV1, baseGlyphsV1 = buildColrV1(TEST_COLOR_GLYPHS)
    colorGlyphs = unbuildColrV1(layersV1, baseGlyphsV1, ignoreVarIdx=True)
    assert colorGlyphs == TEST_COLOR_GLYPHS
