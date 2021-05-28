from pathlib import Path
from subprocess import run

from fontTools.ttLib import TTFont, newTable
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString


def test_main(tmpdir: Path):
    """Check that calling the main function on an input TTF works."""
    glyphs = ".notdef space A B C a b c".split()
    features = """
    lookup GPOS_EXT useExtension {
        pos a b -10;
    } GPOS_EXT;

    feature kern {
        pos A 20;
        pos A B -50;
        pos A B' 10 C;
        lookup GPOS_EXT;
    } kern;
    """
    font = TTFont()
    font.setGlyphOrder(glyphs)
    addOpenTypeFeaturesFromString(font, features)
    font["maxp"] = maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    maxp.maxZones = 1
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = 0
    maxp.maxPoints = 0
    maxp.maxContours = 0
    maxp.maxCompositePoints = 0
    maxp.maxCompositeContours = 0
    maxp.maxComponentDepth = 0
    maxp.compile(font)
    input = tmpdir / "in.ttf"
    font.save(str(input))
    output = tmpdir / "out.ttf"
    run(["fonttools", "otlLib.optimize", str(input), "-o", str(output)], check=True)
    assert output.exists()
