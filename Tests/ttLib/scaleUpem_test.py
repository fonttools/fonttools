from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.beyond64k import upper_tables
from fontTools.ttLib.scaleUpem import ScalerVisitor, scale_upem
from fontTools.ttLib.tables import otTables
from io import BytesIO
import difflib
import os
import shutil
import sys
import tempfile
import unittest
import pytest


class ScaleUpemTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = None
        self.num_tempfiles = 0

    def tearDown(self):
        if self.tempdir:
            shutil.rmtree(self.tempdir)

    @staticmethod
    def get_path(test_file_or_folder):
        parent_dir = os.path.dirname(__file__)
        return os.path.join(parent_dir, "data", test_file_or_folder)

    def temp_path(self, suffix):
        self.temp_dir()
        self.num_tempfiles += 1
        return os.path.join(self.tempdir, "tmp%d%s" % (self.num_tempfiles, suffix))

    def temp_dir(self):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp()

    def read_ttx(self, path):
        lines = []
        with open(path, "r", encoding="utf-8") as ttx:
            for line in ttx.readlines():
                # Elide ttFont attributes because ttLibVersion may change.
                if line.startswith("<ttFont "):
                    lines.append("<ttFont>\n")
                else:
                    lines.append(line.rstrip() + "\n")
        return lines

    def expect_ttx(self, font, expected_ttx, tables):
        path = self.temp_path(suffix=".ttx")
        font.saveXML(path, tables=tables)
        actual = self.read_ttx(path)
        expected = self.read_ttx(expected_ttx)
        if actual != expected:
            for line in difflib.unified_diff(
                expected, actual, fromfile=expected_ttx, tofile=path
            ):
                sys.stdout.write(line)
            self.fail("TTX output is different from expected")

    def test_scale_upem_ttf(self):
        font = TTFont(self.get_path("I.ttf"))
        tables = [table_tag for table_tag in font.keys() if table_tag != "head"]

        scale_upem(font, 512)

        expected_ttx_path = self.get_path("I-512upem.ttx")
        self.expect_ttx(font, expected_ttx_path, tables)

    def test_scale_upem_beyond64k_ttf(self):
        font = TTFont(self.get_path("I.ttf"))
        upper_tables(font)

        scale_upem(font, 512)

        assert font["head"].unitsPerEm == 512
        assert font["HHEA"].ascent == 475
        assert font["HHEA"].descent == -125
        assert font["HMTX"]["I"] == (136, 44)
        assert font["GLYF"]["I"].xMin == 44
        assert font["GLYF"]["I"].xMax == 92
        assert font["GVAR"].variations["I"][0].coordinates[1] == (-24, 0)

        # Save / load to ensure calculated companion-table values are valid.
        iobytes = BytesIO()
        font.save(iobytes)
        iobytes.seek(0)
        font = TTFont(iobytes)
        assert {"GLYF", "LOCA", "MAXP", "HHEA", "HMTX"} <= set(font.keys())
        assert font["HMTX"]["I"] == (136, 44)

    def test_scale_upem_otf(self):
        # Just test that it doesn't crash

        font = TTFont(self.get_path("TestVGID-Regular.otf"))

        scale_upem(font, 500)

    def test_scale_upem_vorg(self):
        font = TTFont(self.get_path("TestVGID-Regular.otf"))
        order = font.getGlyphOrder()
        vorg = font["VORG"] = newTable("VORG")
        vorg.majorVersion, vorg.minorVersion = 1, 0
        vorg.defaultVertOriginY = 800
        vorg.VOriginRecords = {order[1]: 900, order[2]: -321}

        scale_upem(font, font["head"].unitsPerEm * 2)

        stream = BytesIO()
        font.save(stream)
        font = TTFont(BytesIO(stream.getvalue()))
        assert font["VORG"].defaultVertOriginY == 1600
        assert font["VORG"][order[0]] == 1600
        assert font["VORG"].VOriginRecords == {order[1]: 1800, order[2]: -642}


def test_scale_upem_paint_glyph2():
    paint = otTables.Paint()
    paint.Format = otTables.PaintFormat.PaintGlyph2
    paint.Glyph = "high"
    paint.Paint = otTables.Paint()
    paint.Paint.Format = otTables.PaintFormat.PaintSolid
    paint.Paint.PaletteIndex = 0
    paint.Paint.Alpha = 1.0

    ScalerVisitor(2).visit(paint)

    assert paint.Format == otTables.PaintFormat.PaintScaleUniform
    assert paint.Paint.Format == otTables.PaintFormat.PaintGlyph2
    assert paint.Paint.Glyph == "high"


@pytest.mark.parametrize(
    "filename",
    [
        "varc-ac00-ac01.ttf",
        "varc-6868.ttf",
        "varc-ac01-conditional.ttf",
        "varc-static-gvar.ttf",
    ],
)
@pytest.mark.parametrize("use_visitor", [False, True])
@pytest.mark.parametrize("uppercase", [False, True])
def test_scale_upem_rejects_varc(filename, use_visitor, uppercase):
    font = TTFont(ScaleUpemTest.get_path(filename), recalcTimestamp=False)
    if uppercase:
        upper_tables(font)
    font.ensureDecompiled()
    before = BytesIO()
    font.save(before)
    with pytest.raises(NotImplementedError, match="VARC"):
        if use_visitor:
            ScalerVisitor(0.5).visit(font["VARC"])
        else:
            scale_upem(font, font["head"].unitsPerEm // 2)
    after = BytesIO()
    font.save(after)
    assert after.getvalue() == before.getvalue()
