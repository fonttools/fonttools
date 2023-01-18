from fontTools.ttLib import TTFont
from fontTools.ttLib import ttGlyphSet
from fontTools.pens.recordingPen import RecordingPen
from fontTools.misc.roundTools import otRound
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

        assert actual == expected, (location, actual, expected)

    def test_glyphset_varComposite(self):
        font = TTFont(self.getpath("varc-ac00-ac01.ttf"))
        glyphset = font.getGlyphSet()

        pen = RecordingPen()
        glyph = glyphset["uniAC00"]

        glyph.draw(pen)
        actual = pen.value

        expected = [
            ("moveTo", ((460, 676),)),
            ("lineTo", ((460, 640),)),
            (
                "qCurveTo",
                (
                    (445, 641),
                    (391, 640),
                    (330, 638),
                    (269, 638),
                    (222, 636),
                    (213, 634),
                ),
            ),
            ("qCurveTo", ((204, 635), (178, 630), (153, 624), (143, 621))),
            ("qCurveTo", ((125, 628), (87, 647), (73, 657))),
            ("qCurveTo", ((71, 659), (71, 662), (71, 665))),
            ("lineTo", ((76, 675),)),
            ("qCurveTo", ((94, 671), (138, 669), (155, 669))),
            (
                "qCurveTo",
                (
                    (165, 669),
                    (211, 669),
                    (271, 670),
                    (336, 672),
                    (399, 674),
                    (447, 677),
                    (460, 676),
                ),
            ),
            ("closePath", ()),
            ("moveTo", ((524, 635),)),
            ("lineTo", ((458, 640),)),
            ("lineTo", ((455, 675),)),
            ("lineTo", ((488, 692),)),
            ("qCurveTo", ((491, 693), (499, 693), (502, 692))),
            ("qCurveTo", ((507, 689), (521, 683), (535, 675), (539, 673))),
            ("qCurveTo", ((543, 671), (542, 666), (540, 663))),
            ("lineTo", ((524, 635),)),
            ("closePath", ()),
            ("moveTo", ((59, 119),)),
            ("lineTo", ((50, 130),)),
            ("qCurveTo", ((45, 133), (50, 136))),
            ("qCurveTo", ((147, 210), (307, 378), (426, 556), (458, 640))),
            ("lineTo", ((495, 654),)),
            ("lineTo", ((524, 635),)),
            ("qCurveTo", ((494, 546), (360, 356), (173, 185), (66, 121))),
            ("qCurveTo", ((65, 120), (60, 119), (59, 119))),
            ("closePath", ()),
            ("moveTo", ((932, 382),)),
            ("lineTo", ((741, 380),)),
            ("lineTo", ((741, 412),)),
            ("lineTo", ((827, 416),)),
            ("lineTo", ((859, 434),)),
            ("qCurveTo", ((882, 435), (933, 431), (948, 428))),
            ("qCurveTo", ((959, 424), (959, 415))),
            ("qCurveTo", ((959, 403), (952, 388), (948, 385))),
            ("qCurveTo", ((945, 383), (935, 382), (932, 382))),
            ("closePath", ()),
            ("moveTo", ((733, -110),)),
            ("lineTo", ((701, -110),)),
            ("qCurveTo", ((699, -93), (699, -49), (699, 0), (699, 47), (699, 63))),
            ("lineTo", ((699, 780),)),
            ("qCurveTo", ((685, 795), (636, 820), (610, 829))),
            ("lineTo", ((617, 849),)),
            ("qCurveTo", ((617, 852), (622, 853), (627, 853))),
            ("qCurveTo", ((645, 852), (689, 845), (730, 836), (743, 830))),
            ("qCurveTo", ((754, 825), (754, 812))),
            ("lineTo", ((751, 762),)),
            ("lineTo", ((751, 84),)),
            ("qCurveTo", ((751, 61), (748, 11), (744, -42), (737, -89), (733, -110))),
            ("closePath", ()),
        ]

        actual = [
            (op, tuple((otRound(pt[0]), otRound(pt[1])) for pt in args))
            for op, args in actual
        ]

        assert actual == expected, (actual, expected)
