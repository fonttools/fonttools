from pathlib import Path

import pytest

from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.ttLib import TTFont
from fontTools.varLib import build
from fontTools.varLib.errors import VarLibCFFMergeError


def build_with_masks(tmp_path, operator, masks):
    designspace = DesignSpaceDocument.fromfile(
        Path(__file__).parent / "data" / "TestCFF2.designspace"
    )
    for source, mask in zip(designspace.sources, masks, strict=True):
        font = TTFont()
        ttx_path = Path(source.path).with_suffix(".ttx")
        font.importXML(ttx_path)
        glyph = font["CFF "].cff.topDictIndex[0].CharStrings["A"]
        glyph.program[:0] = [0, 10, 5, 15, "hstemhm", operator, mask]
        source.path = str(tmp_path / ttx_path.with_suffix(".otf").name)
        font.save(source.path)
    font, _, _ = build(designspace)
    return font


@pytest.mark.parametrize("operator", ["hintmask", "cntrmask"])
def test_merge_matching_masks(tmp_path, operator):
    font = build_with_masks(tmp_path, operator, [b"\xc0"] * 3)
    program = font["CFF2"].cff.topDictIndex[0].CharStrings["A"].program
    assert program[program.index(operator) + 1] == b"\xc0"


@pytest.mark.parametrize("operator", ["hintmask", "cntrmask"])
def test_merge_different_masks(tmp_path, operator):
    with pytest.raises(VarLibCFFMergeError, match=f"Glyph 'A'.*{operator}"):
        build_with_masks(tmp_path, operator, [b"\xc0", b"\xc0", b"\x80"])
