from pathlib import Path
import pytest

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen, main
from fontTools.ttLib import TTFont
from fontTools.ttLib.beyond64k import upper_tables
from fontTools.svgLib.path import parse_path

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


@pytest.mark.parametrize(
    "kwargs, expected_bounds",
    [
        ({}, (1.234567, 2.345678, 3.456789, 4.567891)),
        ({"precision": 2}, (1.23, 2.35, 3.46, 4.57)),
        ({"precision": 0}, (1, 2, 3, 5)),
        (
            {"precision": 2, "ntos": lambda value: f"{value:.4f}"},
            (1.2346, 2.3457, 3.4568, 4.5679),
        ),
    ],
)
def test_number_precision_geometry(kwargs, expected_bounds):
    pen = SVGPathPen(None, **kwargs)
    pen.moveTo((1.234567, 2.345678))
    pen.lineTo((3.456789, 4.567891))
    pen.endPath()
    bounds = BoundsPen(None)
    parse_path(pen.getCommands(), bounds)

    assert bounds.bounds == expected_bounds
