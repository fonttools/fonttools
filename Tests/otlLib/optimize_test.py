from pathlib import Path
from subprocess import run

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder


def test_main(tmpdir: Path):
    """Check that calling the main function on an input TTF works."""
    glyphs = ".notdef space A B".split()
    features = """
    feature kern {
        pos A B -50;
    } kern;
    """
    fb = FontBuilder(1000)
    fb.setupGlyphOrder(glyphs)
    addOpenTypeFeaturesFromString(fb.font, features)
    input = tmpdir / "in.ttf"
    fb.save(str(input))
    output = tmpdir / "out.ttf"
    run(
        [
            "fonttools",
            "otlLib.optimize",
            "--gpos-compact-mode",
            "5",
            str(input),
            "-o",
            str(output),
        ],
        check=True,
    )
    assert output.exists()
