from fontTools.ttLib import TTFont
from fontTools.ttLib import ttGlyphSet
from fontTools.pens.recordingPen import (
    RecordingPen,
    RecordingPointPen,
    DecomposingRecordingPen,
)
from fontTools.misc.roundTools import otRound
from fontTools.misc.transform import DecomposedTransform
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
        with pytest.deprecated_call():
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

    def test_glyphset_varComposite_components(self):
        font = TTFont(self.getpath("varc-ac00-ac01.ttf"))
        glyphset = font.getGlyphSet()

        pen = RecordingPen()
        glyph = glyphset["uniAC00"]

        glyph.draw(pen)
        actual = pen.value

        expected = [
            (
                "addVarComponent",
                (
                    "glyph00003",
                    DecomposedTransform(460.0, 676.0, 0, 1, 1, 0, 0, 0, 0),
                    {
                        "0000": 0.84661865234375,
                        "0001": 0.98944091796875,
                        "0002": 0.47283935546875,
                        "0003": 0.446533203125,
                    },
                ),
            ),
            (
                "addVarComponent",
                (
                    "glyph00004",
                    DecomposedTransform(932.0, 382.0, 0, 1, 1, 0, 0, 0, 0),
                    {
                        "0000": 0.93359375,
                        "0001": 0.916015625,
                        "0002": 0.523193359375,
                        "0003": 0.32806396484375,
                        "0004": 0.85089111328125,
                    },
                ),
            ),
        ]

        assert actual == expected, (actual, expected)

    def test_glyphset_varComposite1(self):
        font = TTFont(self.getpath("varc-ac00-ac01.ttf"))
        glyphset = font.getGlyphSet(location={"wght": 600})

        pen = DecomposingRecordingPen(glyphset)
        glyph = glyphset["uniAC00"]

        glyph.draw(pen)
        actual = pen.value

        expected = [
            ("moveTo", ((432, 678),)),
            ("lineTo", ((432, 620),)),
            (
                "qCurveTo",
                (
                    (419, 620),
                    (374, 621),
                    (324, 619),
                    (275, 618),
                    (237, 617),
                    (228, 616),
                ),
            ),
            ("qCurveTo", ((218, 616), (188, 612), (160, 605), (149, 601))),
            ("qCurveTo", ((127, 611), (83, 639), (67, 654))),
            ("qCurveTo", ((64, 657), (63, 662), (64, 666))),
            ("lineTo", ((72, 678),)),
            ("qCurveTo", ((93, 674), (144, 672), (164, 672))),
            (
                "qCurveTo",
                (
                    (173, 672),
                    (213, 672),
                    (266, 673),
                    (323, 674),
                    (377, 675),
                    (421, 678),
                    (432, 678),
                ),
            ),
            ("closePath", ()),
            ("moveTo", ((525, 619),)),
            ("lineTo", ((412, 620),)),
            ("lineTo", ((429, 678),)),
            ("lineTo", ((466, 697),)),
            ("qCurveTo", ((470, 698), (482, 698), (486, 697))),
            ("qCurveTo", ((494, 693), (515, 682), (536, 670), (541, 667))),
            ("qCurveTo", ((545, 663), (545, 656), (543, 652))),
            ("lineTo", ((525, 619),)),
            ("closePath", ()),
            ("moveTo", ((63, 118),)),
            ("lineTo", ((47, 135),)),
            ("qCurveTo", ((42, 141), (48, 146))),
            ("qCurveTo", ((135, 213), (278, 373), (383, 541), (412, 620))),
            ("lineTo", ((471, 642),)),
            ("lineTo", ((525, 619),)),
            ("qCurveTo", ((496, 529), (365, 342), (183, 179), (75, 121))),
            ("qCurveTo", ((72, 119), (65, 118), (63, 118))),
            ("closePath", ()),
            ("moveTo", ((925, 372),)),
            ("lineTo", ((739, 368),)),
            ("lineTo", ((739, 427),)),
            ("lineTo", ((822, 430),)),
            ("lineTo", ((854, 451),)),
            ("qCurveTo", ((878, 453), (930, 449), (944, 445))),
            ("qCurveTo", ((961, 441), (962, 426))),
            ("qCurveTo", ((964, 411), (956, 386), (951, 381))),
            ("qCurveTo", ((947, 376), (931, 372), (925, 372))),
            ("closePath", ()),
            ("moveTo", ((729, -113),)),
            ("lineTo", ((674, -113),)),
            ("qCurveTo", ((671, -98), (669, -42), (666, 22), (665, 83), (665, 102))),
            ("lineTo", ((665, 763),)),
            ("qCurveTo", ((654, 780), (608, 810), (582, 820))),
            ("lineTo", ((593, 850),)),
            ("qCurveTo", ((594, 852), (599, 856), (607, 856))),
            ("qCurveTo", ((628, 855), (684, 846), (736, 834), (752, 827))),
            ("qCurveTo", ((766, 818), (766, 802))),
            ("lineTo", ((762, 745),)),
            ("lineTo", ((762, 134),)),
            ("qCurveTo", ((762, 107), (757, 43), (749, -25), (737, -87), (729, -113))),
            ("closePath", ()),
        ]

        actual = [
            (op, tuple((otRound(pt[0]), otRound(pt[1])) for pt in args))
            for op, args in actual
        ]

        assert actual == expected, (actual, expected)

        # Test that drawing twice works, we accidentally don't change the component
        pen = DecomposingRecordingPen(glyphset)
        glyph.draw(pen)
        actual = pen.value
        actual = [
            (op, tuple((otRound(pt[0]), otRound(pt[1])) for pt in args))
            for op, args in actual
        ]
        assert actual == expected, (actual, expected)

        pen = RecordingPointPen()
        glyph.drawPoints(pen)
        assert pen.value

    def test_glyphset_varComposite2(self):
        # This test font has axis variations

        font = TTFont(self.getpath("varc-6868.ttf"))
        glyphset = font.getGlyphSet(location={"wght": 600})

        pen = DecomposingRecordingPen(glyphset)
        glyph = glyphset["uni6868"]

        glyph.draw(pen)
        actual = pen.value

        expected = [
            ("moveTo", ((460, 565),)),
            (
                "qCurveTo",
                (
                    (482, 577),
                    (526, 603),
                    (568, 632),
                    (607, 663),
                    (644, 698),
                    (678, 735),
                    (708, 775),
                    (721, 796),
                ),
            ),
            ("lineTo", ((632, 835),)),
            (
                "qCurveTo",
                (
                    (621, 817),
                    (595, 784),
                    (566, 753),
                    (534, 724),
                    (499, 698),
                    (462, 675),
                    (423, 653),
                    (403, 644),
                ),
            ),
            ("closePath", ()),
            ("moveTo", ((616, 765),)),
            ("lineTo", ((590, 682),)),
            ("lineTo", ((830, 682),)),
            ("lineTo", ((833, 682),)),
            ("lineTo", ((828, 693),)),
            (
                "qCurveTo",
                (
                    (817, 671),
                    (775, 620),
                    (709, 571),
                    (615, 525),
                    (492, 490),
                    (413, 480),
                ),
            ),
            ("lineTo", ((454, 386),)),
            (
                "qCurveTo",
                (
                    (544, 403),
                    (687, 455),
                    (798, 519),
                    (877, 590),
                    (926, 655),
                    (937, 684),
                ),
            ),
            ("lineTo", ((937, 765),)),
            ("closePath", ()),
            ("moveTo", ((723, 555),)),
            (
                "qCurveTo",
                (
                    (713, 563),
                    (693, 579),
                    (672, 595),
                    (651, 610),
                    (629, 625),
                    (606, 638),
                    (583, 651),
                    (572, 657),
                ),
            ),
            ("lineTo", ((514, 590),)),
            (
                "qCurveTo",
                (
                    (525, 584),
                    (547, 572),
                    (568, 559),
                    (589, 545),
                    (609, 531),
                    (629, 516),
                    (648, 500),
                    (657, 492),
                ),
            ),
            ("closePath", ()),
            ("moveTo", ((387, 375),)),
            ("lineTo", ((387, 830),)),
            ("lineTo", ((289, 830),)),
            ("lineTo", ((289, 375),)),
            ("closePath", ()),
            ("moveTo", ((96, 383),)),
            (
                "qCurveTo",
                (
                    (116, 390),
                    (156, 408),
                    (194, 427),
                    (231, 449),
                    (268, 472),
                    (302, 497),
                    (335, 525),
                    (351, 539),
                ),
            ),
            ("lineTo", ((307, 610),)),
            (
                "qCurveTo",
                (
                    (291, 597),
                    (257, 572),
                    (221, 549),
                    (185, 528),
                    (147, 509),
                    (108, 492),
                    (69, 476),
                    (48, 469),
                ),
            ),
            ("closePath", ()),
            ("moveTo", ((290, 653),)),
            (
                "qCurveTo",
                (
                    (281, 664),
                    (261, 687),
                    (240, 708),
                    (219, 729),
                    (196, 749),
                    (173, 768),
                    (148, 786),
                    (136, 794),
                ),
            ),
            ("lineTo", ((69, 727),)),
            (
                "qCurveTo",
                (
                    (81, 719),
                    (105, 702),
                    (129, 684),
                    (151, 665),
                    (173, 645),
                    (193, 625),
                    (213, 604),
                    (222, 593),
                ),
            ),
            ("closePath", ()),
            ("moveTo", ((913, -57),)),
            ("lineTo", ((953, 30),)),
            (
                "qCurveTo",
                (
                    (919, 41),
                    (854, 67),
                    (790, 98),
                    (729, 134),
                    (671, 173),
                    (616, 217),
                    (564, 264),
                    (540, 290),
                ),
            ),
            ("lineTo", ((522, 286),)),
            ("qCurveTo", ((511, 267), (498, 235), (493, 213), (492, 206))),
            ("lineTo", ((515, 209),)),
            ("qCurveTo", ((569, 146), (695, 44), (835, -32), (913, -57))),
            ("closePath", ()),
            ("moveTo", ((474, 274),)),
            ("lineTo", ((452, 284),)),
            (
                "qCurveTo",
                (
                    (428, 260),
                    (377, 214),
                    (323, 172),
                    (266, 135),
                    (206, 101),
                    (144, 71),
                    (80, 46),
                    (47, 36),
                ),
            ),
            ("lineTo", ((89, -53),)),
            ("qCurveTo", ((163, -29), (299, 46), (423, 142), (476, 201))),
            ("lineTo", ((498, 196),)),
            ("qCurveTo", ((498, 203), (494, 225), (482, 255), (474, 274))),
            ("closePath", ()),
            ("moveTo", ((450, 250),)),
            ("lineTo", ((550, 250),)),
            ("lineTo", ((550, 379),)),
            ("lineTo", ((450, 379),)),
            ("closePath", ()),
            ("moveTo", ((68, 215),)),
            ("lineTo", ((932, 215),)),
            ("lineTo", ((932, 305),)),
            ("lineTo", ((68, 305),)),
            ("closePath", ()),
            ("moveTo", ((450, -71),)),
            ("lineTo", ((550, -71),)),
            ("lineTo", ((550, -71),)),
            ("lineTo", ((550, 267),)),
            ("lineTo", ((450, 267),)),
            ("lineTo", ((450, -71),)),
            ("closePath", ()),
        ]

        actual = [
            (op, tuple((otRound(pt[0]), otRound(pt[1])) for pt in args))
            for op, args in actual
        ]

        assert actual == expected, (actual, expected)

        pen = RecordingPointPen()
        glyph.drawPoints(pen)
        assert pen.value

    def test_cubic_glyf(self):
        font = TTFont(self.getpath("dot-cubic.ttf"))
        glyphset = font.getGlyphSet()

        expected = [
            ("moveTo", ((76, 181),)),
            ("curveTo", ((103, 181), (125, 158), (125, 131))),
            ("curveTo", ((125, 104), (103, 82), (76, 82))),
            ("curveTo", ((48, 82), (26, 104), (26, 131))),
            ("curveTo", ((26, 158), (48, 181), (76, 181))),
            ("closePath", ()),
        ]

        pen = RecordingPen()
        glyphset["one"].draw(pen)
        assert pen.value == expected

        expectedPoints = [
            ("beginPath", (), {}),
            ("addPoint", ((76, 181), "curve", False, None), {}),
            ("addPoint", ((103, 181), None, False, None), {}),
            ("addPoint", ((125, 158), None, False, None), {}),
            ("addPoint", ((125, 104), None, False, None), {}),
            ("addPoint", ((103, 82), None, False, None), {}),
            ("addPoint", ((76, 82), "curve", False, None), {}),
            ("addPoint", ((48, 82), None, False, None), {}),
            ("addPoint", ((26, 104), None, False, None), {}),
            ("addPoint", ((26, 158), None, False, None), {}),
            ("addPoint", ((48, 181), None, False, None), {}),
            ("endPath", (), {}),
        ]
        pen = RecordingPointPen()
        glyphset["one"].drawPoints(pen)
        assert pen.value == expectedPoints

        pen = RecordingPen()
        glyphset["two"].draw(pen)
        assert pen.value == expected

        expectedPoints = [
            ("beginPath", (), {}),
            ("addPoint", ((26, 158), None, False, None), {}),
            ("addPoint", ((48, 181), None, False, None), {}),
            ("addPoint", ((76, 181), "curve", False, None), {}),
            ("addPoint", ((103, 181), None, False, None), {}),
            ("addPoint", ((125, 158), None, False, None), {}),
            ("addPoint", ((125, 104), None, False, None), {}),
            ("addPoint", ((103, 82), None, False, None), {}),
            ("addPoint", ((76, 82), "curve", False, None), {}),
            ("addPoint", ((48, 82), None, False, None), {}),
            ("addPoint", ((26, 104), None, False, None), {}),
            ("endPath", (), {}),
        ]
        pen = RecordingPointPen()
        glyphset["two"].drawPoints(pen)
        assert pen.value == expectedPoints

        pen = RecordingPen()
        glyphset["three"].draw(pen)
        assert pen.value == expected

        expectedPoints = [
            ("beginPath", (), {}),
            ("addPoint", ((48, 82), None, False, None), {}),
            ("addPoint", ((26, 104), None, False, None), {}),
            ("addPoint", ((26, 158), None, False, None), {}),
            ("addPoint", ((48, 181), None, False, None), {}),
            ("addPoint", ((76, 181), "curve", False, None), {}),
            ("addPoint", ((103, 181), None, False, None), {}),
            ("addPoint", ((125, 158), None, False, None), {}),
            ("addPoint", ((125, 104), None, False, None), {}),
            ("addPoint", ((103, 82), None, False, None), {}),
            ("addPoint", ((76, 82), "curve", False, None), {}),
            ("endPath", (), {}),
        ]
        pen = RecordingPointPen()
        glyphset["three"].drawPoints(pen)
        assert pen.value == expectedPoints

        pen = RecordingPen()
        glyphset["four"].draw(pen)
        assert pen.value == [
            ("moveTo", ((75.5, 181),)),
            ("curveTo", ((103, 181), (125, 158), (125, 131))),
            ("curveTo", ((125, 104), (103, 82), (75.5, 82))),
            ("curveTo", ((48, 82), (26, 104), (26, 131))),
            ("curveTo", ((26, 158), (48, 181), (75.5, 181))),
            ("closePath", ()),
        ]

        # Ouch! We can't represent all-cubic-offcurves in pointPen!
        # https://github.com/fonttools/fonttools/issues/3191
        expectedPoints = [
            ("beginPath", (), {}),
            ("addPoint", ((103, 181), None, False, None), {}),
            ("addPoint", ((125, 158), None, False, None), {}),
            ("addPoint", ((125, 104), None, False, None), {}),
            ("addPoint", ((103, 82), None, False, None), {}),
            ("addPoint", ((48, 82), None, False, None), {}),
            ("addPoint", ((26, 104), None, False, None), {}),
            ("addPoint", ((26, 158), None, False, None), {}),
            ("addPoint", ((48, 181), None, False, None), {}),
            ("endPath", (), {}),
        ]
        pen = RecordingPointPen()
        glyphset["four"].drawPoints(pen)
        print(pen.value)
        assert pen.value == expectedPoints
