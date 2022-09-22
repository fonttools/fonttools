from fontTools.ttLib import TTFont
from fontTools.ttLib import ttGlyphSet
from fontTools.pens.recordingPen import RecordingPen
import os
import pytest


class TTGlyphSetTest(object):
    @staticmethod
    def getpath(testfile):
        path = os.path.dirname(__file__)
        return os.path.join(path, "data", testfile)

    @pytest.mark.parametrize(
        "fontfile, location, expected",
        [
            (
                "I.ttf",
                None,
                [
                    ("moveTo", ((175, 0),)),
                    ("lineTo", ((367, 0),)),
                    ("lineTo", ((367, 1456),)),
                    ("lineTo", ((175, 1456),)),
                    ("closePath", ()),
                ],
            ),
            (
                "I.ttf",
                {},
                [
                    ("moveTo", ((175, 0),)),
                    ("lineTo", ((367, 0),)),
                    ("lineTo", ((367, 1456),)),
                    ("lineTo", ((175, 1456),)),
                    ("closePath", ()),
                ],
            ),
            (
                "I.ttf",
                {"wght": 100},
                [
                    ("moveTo", ((175, 0),)),
                    ("lineTo", ((271, 0),)),
                    ("lineTo", ((271, 1456),)),
                    ("lineTo", ((175, 1456),)),
                    ("closePath", ()),
                ],
            ),
            (
                "I.ttf",
                {"wght": 1000},
                [
                    ("moveTo", ((128, 0),)),
                    ("lineTo", ((550, 0),)),
                    ("lineTo", ((550, 1456),)),
                    ("lineTo", ((128, 1456),)),
                    ("closePath", ()),
                ],
            ),
            (
                "I.ttf",
                {"wght": 1000, "wdth": 25},
                [
                    ("moveTo", ((140, 0),)),
                    ("lineTo", ((553, 0),)),
                    ("lineTo", ((553, 1456),)),
                    ("lineTo", ((140, 1456),)),
                    ("closePath", ()),
                ],
            ),
            (
                "I.ttf",
                {"wght": 1000, "wdth": 50},
                [
                    ("moveTo", ((136, 0),)),
                    ("lineTo", ((552, 0),)),
                    ("lineTo", ((552, 1456),)),
                    ("lineTo", ((136, 1456),)),
                    ("closePath", ()),
                ],
            ),
            (
                "I.otf",
                {"wght": 1000},
                [
                    ("moveTo", ((179, 74),)),
                    ("lineTo", ((28, 59),)),
                    ("lineTo", ((28, 0),)),
                    ("lineTo", ((367, 0),)),
                    ("lineTo", ((367, 59),)),
                    ("lineTo", ((212, 74),)),
                    ("lineTo", ((179, 74),)),
                    ("closePath", ()),
                    ("moveTo", ((179, 578),)),
                    ("lineTo", ((212, 578),)),
                    ("lineTo", ((367, 593),)),
                    ("lineTo", ((367, 652),)),
                    ("lineTo", ((28, 652),)),
                    ("lineTo", ((28, 593),)),
                    ("lineTo", ((179, 578),)),
                    ("closePath", ()),
                    ("moveTo", ((98, 310),)),
                    ("curveTo", ((98, 205), (98, 101), (95, 0))),
                    ("lineTo", ((299, 0),)),
                    ("curveTo", ((296, 103), (296, 207), (296, 311))),
                    ("lineTo", ((296, 342),)),
                    ("curveTo", ((296, 447), (296, 551), (299, 652))),
                    ("lineTo", ((95, 652),)),
                    ("curveTo", ((98, 549), (98, 445), (98, 342))),
                    ("lineTo", ((98, 310),)),
                    ("closePath", ()),
                ],
            ),
            (
                # In this font, /I has an lsb of 30, but an xMin of 25, so an
                # offset of 5 units needs to be applied when drawing the outline.
                # See https://github.com/fonttools/fonttools/issues/2824
                "issue2824.ttf",
                None,
                [
                    ("moveTo", ((309, 180),)),
                    ("qCurveTo", ((274, 151), (187, 136), (104, 166), (74, 201))),
                    ("qCurveTo", ((45, 236), (30, 323), (59, 407), (95, 436))),
                    ("qCurveTo", ((130, 466), (217, 480), (301, 451), (330, 415))),
                    ("qCurveTo", ((360, 380), (374, 293), (345, 210), (309, 180))),
                    ("closePath", ()),
                ],
            ),
        ],
    )
    def test_glyphset(self, fontfile, location, expected):
        font = TTFont(self.getpath(fontfile))
        glyphset = font.getGlyphSet(location=location)

        assert isinstance(glyphset, ttGlyphSet._TTGlyphSet)

        assert list(glyphset.keys()) == [".notdef", "I"]

        assert "I" in glyphset
        assert glyphset.has_key("I")  # we should really get rid of this...

        assert len(glyphset) == 2

        pen = RecordingPen()
        glyph = glyphset["I"]

        assert glyphset.get("foobar") is None

        assert isinstance(glyph, ttGlyphSet._TTGlyph)
        is_glyf = fontfile.endswith(".ttf")
        glyphType = ttGlyphSet._TTGlyphGlyf if is_glyf else ttGlyphSet._TTGlyphCFF
        assert isinstance(glyph, glyphType)

        glyph.draw(pen)
        actual = pen.value

        print(actual)
        assert actual == expected, (location, actual, expected)
