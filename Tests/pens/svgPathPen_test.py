from pathlib import Path

from fontTools.pens.svgPathPen import main
from fontTools.ttLib import TTFont
from fontTools.ttLib.beyond64k import upper_tables


DATA_DIR = Path(__file__).parent.parent / "ttLib" / "data"


def test_main_beyond64k_hhea(tmp_path, capsys):
    font = TTFont()
    font.importXML(DATA_DIR / "TestTTF-Regular.ttx")
    upper_tables(font)

    font_path = tmp_path / "TestTTF-Regular.ttf"
    font.save(font_path)

    main([str(font_path), "--glyphs", "period"])

    output = capsys.readouterr().out
    assert "<svg " in output
    assert "<path " in output
