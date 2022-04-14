import contextlib
import logging
import os
from pathlib import Path
from subprocess import run
from typing import List, Optional, Tuple

import pytest
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.otBase import OTTableWriter


def test_main(tmpdir: Path):
    """Check that calling the main function on an input TTF works."""
    glyphs = ".notdef space A Aacute B D".split()
    features = """
    @A = [A Aacute];
    @B = [B D];
    feature kern {
        pos @A @B -50;
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
            "--gpos-compression-level",
            "5",
            str(input),
            "-o",
            str(output),
        ],
        check=True,
    )
    assert output.exists()


# Copy-pasted from https://stackoverflow.com/questions/2059482/python-temporarily-modify-the-current-processs-environment
# TODO: remove when moving to the Config class
@contextlib.contextmanager
def set_env(**environ):
    """
    Temporarily set the process environment variables.

    >>> with set_env(PLUGINS_DIR=u'test/plugins'):
    ...   "PLUGINS_DIR" in os.environ
    True

    >>> "PLUGINS_DIR" in os.environ
    False

    :type environ: dict[str, unicode]
    :param environ: Environment variables to set
    """
    old_environ = dict(os.environ)
    os.environ.update(environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


def count_pairpos_subtables(font: TTFont) -> int:
    subtables = 0
    for lookup in font["GPOS"].table.LookupList.Lookup:
        if lookup.LookupType == 2:
            subtables += len(lookup.SubTable)
        elif lookup.LookupType == 9:
            for subtable in lookup.SubTable:
                if subtable.ExtensionLookupType == 2:
                    subtables += 1
    return subtables


def count_pairpos_bytes(font: TTFont) -> int:
    bytes = 0
    gpos = font["GPOS"]
    for lookup in font["GPOS"].table.LookupList.Lookup:
        if lookup.LookupType == 2:
            w = OTTableWriter(tableTag=gpos.tableTag)
            lookup.compile(w, font)
            bytes += len(w.getAllData())
        elif lookup.LookupType == 9:
            if any(subtable.ExtensionLookupType == 2 for subtable in lookup.SubTable):
                w = OTTableWriter(tableTag=gpos.tableTag)
                lookup.compile(w, font)
                bytes += len(w.getAllData())
    return bytes


def get_kerning_by_blocks(blocks: List[Tuple[int, int]]) -> Tuple[List[str], str]:
    """Generate a highly compressible font by generating a bunch of rectangular
    blocks on the diagonal that can easily be sliced into subtables.

    Returns the list of glyphs and feature code of the font.
    """
    value = 0
    glyphs: List[str] = []
    rules = []
    # Each block is like a script in a multi-script font
    for script, (width, height) in enumerate(blocks):
        glyphs.extend(f"g_{script}_{i}" for i in range(max(width, height)))
        for l in range(height):
            for r in range(width):
                value += 1
                rules.append((f"g_{script}_{l}", f"g_{script}_{r}", value))
    classes = "\n".join([f"@{g} = [{g}];" for g in glyphs])
    statements = "\n".join([f"pos @{l} @{r} {v};" for (l, r, v) in rules])
    features = f"""
        {classes}
        feature kern {{
            {statements}
        }} kern;
    """
    return glyphs, features


@pytest.mark.parametrize(
    ("blocks", "level", "expected_subtables", "expected_bytes"),
    [
        # Level = 0 = no optimization leads to 650 bytes of GPOS
        ([(15, 3), (2, 10)], None, 1, 602),
        # Optimization level 1 recognizes the 2 blocks and splits into 2
        # subtables = adds 1 subtable leading to a size reduction of
        # (602-298)/602 = 50%
        ([(15, 3), (2, 10)], 1, 2, 298),
        # On a bigger block configuration, we see that mode=5 doesn't create
        # as many subtables as it could, because of the stop criteria
        ([(4, 4) for _ in range(20)], 5, 14, 2042),
        # while level=9 creates as many subtables as there were blocks on the
        # diagonal and yields a better saving
        ([(4, 4) for _ in range(20)], 9, 20, 1886),
        # On a fully occupied kerning matrix, even the strategy 9 doesn't
        # split anything.
        ([(10, 10)], 9, 1, 304),
    ],
)
def test_optimization_mode(
    caplog,
    blocks: List[Tuple[int, int]],
    level: Optional[int],
    expected_subtables: int,
    expected_bytes: int,
):
    """Check that the optimizations are off by default, and that increasing
    the optimization level creates more subtables and a smaller byte size.
    """
    caplog.set_level(logging.DEBUG)

    glyphs, features = get_kerning_by_blocks(blocks)
    glyphs = [".notdef space"] + glyphs

    fb = FontBuilder(1000)
    if level is not None:
        fb.font.cfg["fontTools.otlLib.optimize.gpos:COMPRESSION_LEVEL"] = level
    fb.setupGlyphOrder(glyphs)
    addOpenTypeFeaturesFromString(fb.font, features)
    assert expected_subtables == count_pairpos_subtables(fb.font)
    assert expected_bytes == count_pairpos_bytes(fb.font)
