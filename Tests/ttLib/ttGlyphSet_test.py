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
        "location, expected",
        [
            (
                None,
                [
                 ('moveTo', ((175, 0),)),
                 ('lineTo', ((367, 0),)),
                 ('lineTo', ((367, 1456),)),
                 ('lineTo', ((175, 1456),)),
                 ('closePath', ())
                ]
            ),
            (
                {},
                [
                 ('moveTo', ((175, 0),)),
                 ('lineTo', ((367, 0),)),
                 ('lineTo', ((367, 1456),)),
                 ('lineTo', ((175, 1456),)),
                 ('closePath', ())
                ]
            ),
            (
                {'wght': 100},
                [
                 ('moveTo', ((175, 0),)),
                 ('lineTo', ((271, 0),)),
                 ('lineTo', ((271, 1456),)),
                 ('lineTo', ((175, 1456),)),
                 ('closePath', ())
                ]
            ),
            (
                {'wght': 1000},
                [
                 ('moveTo', ((128, 0),)),
                 ('lineTo', ((550, 0),)),
                 ('lineTo', ((550, 1456),)),
                 ('lineTo', ((128, 1456),)),
                 ('closePath', ())
                ]
            ),
            (
                {'wght': 1000, 'wdth': 25},
                [
                 ('moveTo', ((140, 0),)),
                 ('lineTo', ((553, 0),)),
                 ('lineTo', ((553, 1456),)),
                 ('lineTo', ((140, 1456),)),
                 ('closePath', ())
                ]
            ),
            (
                {'wght': 1000, 'wdth': 50},
                [
                 ('moveTo', ((136, 0),)),
                 ('lineTo', ((552, 0),)),
                 ('lineTo', ((552, 1456),)),
                 ('lineTo', ((136, 1456),)),
                 ('closePath', ())
                ]
            ),
        ]
    )
    def test_glyphset(
        self, location, expected
    ):
        # TODO: also test loading CFF-flavored fonts
        font = TTFont(self.getpath("I.ttf"))
        glyphset = font.getGlyphSet(location=location)

        assert isinstance(glyphset, ttGlyphSet._TTGlyphSet)
        if location:
            assert isinstance(glyphset, ttGlyphSet._TTVarGlyphSet)

        assert list(glyphset.keys()) == [".notdef", "I"]

        assert "I" in glyphset
        assert glyphset.has_key("I")  # we should really get rid of this...

        assert len(glyphset) == 2

        pen = RecordingPen()
        glyph = glyphset['I']

        assert glyphset.get("foobar") is None

        assert isinstance(glyph, ttGlyphSet._TTGlyph)
        if location:
            assert isinstance(glyph, ttGlyphSet._TTVarGlyphGlyf)
        else:
            assert isinstance(glyph, ttGlyphSet._TTGlyphGlyf)

        glyph.draw(pen)
        actual = pen.value

        assert actual == expected, (location, actual, expected)
