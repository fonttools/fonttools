from fontTools.ttLib import TTFont
import os


CURR_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(CURR_DIR, "data")


def test_duplicate_glyph_names():
    font_path = os.path.join(DATA_DIR, "duplicate_glyph_name.ttf")
    font = TTFont(font_path)

    assert font.getGlyphOrder() == [".notdef", "space", "A", "A.2", "A.1"]

    post = font["post"]
    assert post.mapping == {"A.2": "A"}
