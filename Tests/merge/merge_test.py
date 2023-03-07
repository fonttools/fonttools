import io
import itertools
from fontTools import ttLib
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.fontBuilder import FontBuilder
from fontTools.merge import Merger, main as merge_main
import difflib
import os
import re
import shutil
import sys
import tempfile
import unittest
import pathlib
import pytest


class MergeIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = None
        self.num_tempfiles = 0

    def tearDown(self):
        if self.tempdir:
            shutil.rmtree(self.tempdir)

    @staticmethod
    def getpath(testfile):
        path, _ = os.path.split(__file__)
        return os.path.join(path, "data", testfile)

    def temp_path(self, suffix):
        if not self.tempdir:
            self.tempdir = tempfile.mkdtemp()
        self.num_tempfiles += 1
        return os.path.join(self.tempdir, "tmp%d%s" % (self.num_tempfiles, suffix))

    IGNORED_LINES_RE = re.compile(
        "^(<ttFont |    <(checkSumAdjustment|created|modified) ).*"
    )

    def read_ttx(self, path):
        lines = []
        with open(path, "r", encoding="utf-8") as ttx:
            for line in ttx.readlines():
                # Elide lines with data that often change.
                if self.IGNORED_LINES_RE.match(line):
                    lines.append("\n")
                else:
                    lines.append(line.rstrip() + "\n")
        return lines

    def expect_ttx(self, font, expected_ttx, tables=None):
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

    def compile_font(self, path, suffix):
        savepath = self.temp_path(suffix=suffix)
        font = ttLib.TTFont(recalcBBoxes=False, recalcTimestamp=False)
        font.importXML(path)
        font.save(savepath, reorderTables=None)
        return font, savepath

    # -----
    # Tests
    # -----

    def test_merge_cff(self):
        _, fontpath1 = self.compile_font(self.getpath("CFFFont1.ttx"), ".otf")
        _, fontpath2 = self.compile_font(self.getpath("CFFFont2.ttx"), ".otf")
        mergedpath = self.temp_path(".otf")
        merge_main([fontpath1, fontpath2, "--output-file=%s" % mergedpath])
        mergedfont = ttLib.TTFont(mergedpath)
        self.expect_ttx(mergedfont, self.getpath("CFFFont_expected.ttx"))


class gaspMergeUnitTest(unittest.TestCase):
    def setUp(self):
        self.merger = Merger()

        self.table1 = ttLib.newTable("gasp")
        self.table1.version = 1
        self.table1.gaspRange = {
            0x8: 0xA,
            0x10: 0x5,
        }

        self.table2 = ttLib.newTable("gasp")
        self.table2.version = 1
        self.table2.gaspRange = {
            0x6: 0xB,
            0xFF: 0x4,
        }

        self.result = ttLib.newTable("gasp")

    def test_gasp_merge_basic(self):
        result = self.result.merge(self.merger, [self.table1, self.table2])
        self.assertEqual(result, self.table1)

        result = self.result.merge(self.merger, [self.table2, self.table1])
        self.assertEqual(result, self.table2)

    def test_gasp_merge_notImplemented(self):
        result = self.result.merge(self.merger, [NotImplemented, self.table1])
        self.assertEqual(result, NotImplemented)

        result = self.result.merge(self.merger, [self.table1, NotImplemented])
        self.assertEqual(result, self.table1)


class CmapMergeUnitTest(unittest.TestCase):
    def setUp(self):
        self.merger = Merger()
        self.table1 = ttLib.newTable("cmap")
        self.table2 = ttLib.newTable("cmap")
        self.mergedTable = ttLib.newTable("cmap")
        pass

    def tearDown(self):
        pass

    def makeSubtable(self, format, platformID, platEncID, cmap):
        module = ttLib.getTableModule("cmap")
        subtable = module.cmap_classes[format](format)
        (subtable.platformID, subtable.platEncID, subtable.language, subtable.cmap) = (
            platformID,
            platEncID,
            0,
            cmap,
        )
        return subtable

    # 4-3-1 table merged with 12-3-10 table with no dupes with codepoints outside BMP
    def test_cmap_merge_no_dupes(self):
        table1 = self.table1
        table2 = self.table2
        mergedTable = self.mergedTable

        cmap1 = {0x2603: "SNOWMAN"}
        table1.tables = [self.makeSubtable(4, 3, 1, cmap1)]

        cmap2 = {0x26C4: "SNOWMAN WITHOUT SNOW"}
        cmap2Extended = {0x1F93C: "WRESTLERS"}
        cmap2Extended.update(cmap2)
        table2.tables = [
            self.makeSubtable(4, 3, 1, cmap2),
            self.makeSubtable(12, 3, 10, cmap2Extended),
        ]

        self.merger.alternateGlyphsPerFont = [{}, {}]
        mergedTable.merge(self.merger, [table1, table2])

        expectedCmap = cmap2.copy()
        expectedCmap.update(cmap1)
        expectedCmapExtended = cmap2Extended.copy()
        expectedCmapExtended.update(cmap1)
        self.assertEqual(mergedTable.numSubTables, 2)
        self.assertEqual(
            [
                (table.format, table.platformID, table.platEncID, table.language)
                for table in mergedTable.tables
            ],
            [(4, 3, 1, 0), (12, 3, 10, 0)],
        )
        self.assertEqual(mergedTable.tables[0].cmap, expectedCmap)
        self.assertEqual(mergedTable.tables[1].cmap, expectedCmapExtended)

    # Tests Issue #322
    def test_cmap_merge_three_dupes(self):
        table1 = self.table1
        table2 = self.table2
        mergedTable = self.mergedTable

        cmap1 = {0x20: "space#0", 0xA0: "space#0"}
        table1.tables = [self.makeSubtable(4, 3, 1, cmap1)]
        cmap2 = {0x20: "space#1", 0xA0: "uni00A0#1"}
        table2.tables = [self.makeSubtable(4, 3, 1, cmap2)]

        self.merger.duplicateGlyphsPerFont = [{}, {}]
        mergedTable.merge(self.merger, [table1, table2])

        expectedCmap = cmap1.copy()
        self.assertEqual(mergedTable.numSubTables, 1)
        table = mergedTable.tables[0]
        self.assertEqual(
            (table.format, table.platformID, table.platEncID, table.language),
            (4, 3, 1, 0),
        )
        self.assertEqual(table.cmap, expectedCmap)
        self.assertEqual(
            self.merger.duplicateGlyphsPerFont, [{}, {"space#0": "space#1"}]
        )


def _compile(ttFont):
    buf = io.BytesIO()
    ttFont.save(buf)
    buf.seek(0)
    return buf


def _make_fontfile_with_OS2(*, version, **kwargs):
    upem = 1000
    glyphOrder = [".notdef", "a"]
    cmap = {0x61: "a"}
    glyphs = {gn: Glyph() for gn in glyphOrder}
    hmtx = {gn: (500, 0) for gn in glyphOrder}
    names = {"familyName": "TestOS2", "styleName": "Regular"}

    fb = FontBuilder(unitsPerEm=upem)
    fb.setupGlyphOrder(glyphOrder)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(hmtx)
    fb.setupHorizontalHeader()
    fb.setupNameTable(names)
    fb.setupOS2(version=version, **kwargs)

    return _compile(fb.font)


def _merge_and_recompile(fontfiles, options=None):
    merger = Merger(options)
    merged = merger.merge(fontfiles)
    buf = _compile(merged)
    return ttLib.TTFont(buf)


@pytest.mark.parametrize("v1, v2", list(itertools.permutations(range(5 + 1), 2)))
def test_merge_OS2_mixed_versions(v1, v2):
    # https://github.com/fonttools/fonttools/issues/1865
    fontfiles = [
        _make_fontfile_with_OS2(version=v1),
        _make_fontfile_with_OS2(version=v2),
    ]
    merged = _merge_and_recompile(fontfiles)
    assert merged["OS/2"].version == max(v1, v2)


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
