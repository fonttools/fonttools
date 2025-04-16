from fontTools.misc.testTools import parseXML, getXML
from fontTools.misc.textTools import deHexStr
from fontTools.ttLib import TTFont, newTable, TTLibError
from fontTools.misc.loggingTools import CapturingLogHandler
from fontTools.ttLib.tables._h_m_t_x import table__h_m_t_x, log
import struct
import unittest


class HmtxTableTest(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        # Python 3 renamed assertRaisesRegexp to assertRaisesRegex,
        # and fires deprecation warnings if a program uses the old name.
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    @classmethod
    def setUpClass(cls):
        cls.tableClass = table__h_m_t_x
        cls.tag = "hmtx"

    def makeFont(self, numGlyphs, numberOfMetrics):
        font = TTFont()
        maxp = font["maxp"] = newTable("maxp")
        maxp.numGlyphs = numGlyphs
        # from A to ...
        font.glyphOrder = [chr(i) for i in range(65, 65 + numGlyphs)]
        headerTag = self.tableClass.headerTag
        font[headerTag] = newTable(headerTag)
        numberOfMetricsName = self.tableClass.numberOfMetricsName
        setattr(font[headerTag], numberOfMetricsName, numberOfMetrics)
        return font

    def test_decompile(self):
        font = self.makeFont(numGlyphs=3, numberOfMetrics=3)
        data = deHexStr("02A2 FFF5 0278 004F 02C6 0036")

        mtxTable = newTable(self.tag)
        mtxTable.decompile(data, font)

        self.assertEqual(mtxTable["A"], (674, -11))
        self.assertEqual(mtxTable["B"], (632, 79))
        self.assertEqual(mtxTable["C"], (710, 54))

    def test_decompile_additional_SB(self):
        font = self.makeFont(numGlyphs=4, numberOfMetrics=2)
        metrics = deHexStr("02A2 FFF5 0278 004F")
        extraSideBearings = deHexStr("0036 FFFC")
        data = metrics + extraSideBearings

        mtxTable = newTable(self.tag)
        mtxTable.decompile(data, font)

        self.assertEqual(mtxTable["A"], (674, -11))
        self.assertEqual(mtxTable["B"], (632, 79))
        # all following have same width as the previous
        self.assertEqual(mtxTable["C"], (632, 54))
        self.assertEqual(mtxTable["D"], (632, -4))

    def test_decompile_not_enough_data(self):
        font = self.makeFont(numGlyphs=1, numberOfMetrics=1)
        mtxTable = newTable(self.tag)
        msg = "not enough '%s' table data" % self.tag

        with self.assertRaisesRegex(TTLibError, msg):
            mtxTable.decompile(b"\0\0\0", font)

    def test_decompile_too_much_data(self):
        font = self.makeFont(numGlyphs=1, numberOfMetrics=1)
        mtxTable = newTable(self.tag)
        msg = "too much '%s' table data" % self.tag

        with CapturingLogHandler(log, "WARNING") as captor:
            mtxTable.decompile(b"\0\0\0\0\0", font)

        self.assertTrue(len([r for r in captor.records if msg == r.msg]) == 1)

    def test_decompile_num_metrics_greater_than_glyphs(self):
        font = self.makeFont(numGlyphs=1, numberOfMetrics=2)
        mtxTable = newTable(self.tag)
        msg = "The %s.%s exceeds the maxp.numGlyphs" % (
            self.tableClass.headerTag,
            self.tableClass.numberOfMetricsName,
        )

        with CapturingLogHandler(log, "WARNING") as captor:
            mtxTable.decompile(b"\0\0\0\0", font)

        self.assertTrue(len([r for r in captor.records if msg == r.msg]) == 1)

    def test_decompile_possibly_negative_advance(self):
        font = self.makeFont(numGlyphs=1, numberOfMetrics=1)
        # we warn if advance is > 0x7FFF as it might be interpreted as signed
        # by some authoring tools
        data = deHexStr("8000 0000")
        mtxTable = newTable(self.tag)

        with CapturingLogHandler(log, "WARNING") as captor:
            mtxTable.decompile(data, font)

        self.assertTrue(
            len([r for r in captor.records if "has a huge advance" in r.msg]) == 1
        )

    def test_decompile_no_header_table(self):
        font = TTFont()
        maxp = font["maxp"] = newTable("maxp")
        maxp.numGlyphs = 3
        font.glyphOrder = ["A", "B", "C"]

        self.assertNotIn(self.tableClass.headerTag, font)

        data = deHexStr("0190 001E 0190 0028 0190 0032")
        mtxTable = newTable(self.tag)
        mtxTable.decompile(data, font)

        self.assertEqual(
            mtxTable.metrics,
            {
                "A": (400, 30),
                "B": (400, 40),
                "C": (400, 50),
            },
        )

    def test_compile(self):
        # we set the wrong 'numberOfMetrics' to check it gets adjusted
        font = self.makeFont(numGlyphs=3, numberOfMetrics=4)
        mtxTable = font[self.tag] = newTable(self.tag)
        mtxTable.metrics = {
            "A": (674, -11),
            "B": (632, 79),
            "C": (710, 54),
        }

        data = mtxTable.compile(font)

        self.assertEqual(data, deHexStr("02A2 FFF5 0278 004F 02C6 0036"))

        headerTable = font[self.tableClass.headerTag]
        self.assertEqual(getattr(headerTable, self.tableClass.numberOfMetricsName), 3)

    def test_compile_additional_SB(self):
        font = self.makeFont(numGlyphs=4, numberOfMetrics=1)
        mtxTable = font[self.tag] = newTable(self.tag)
        mtxTable.metrics = {
            "A": (632, -11),
            "B": (632, 79),
            "C": (632, 54),
            "D": (632, -4),
        }

        data = mtxTable.compile(font)

        self.assertEqual(data, deHexStr("0278 FFF5 004F 0036 FFFC"))

    def test_compile_negative_advance(self):
        font = self.makeFont(numGlyphs=1, numberOfMetrics=1)
        mtxTable = font[self.tag] = newTable(self.tag)
        mtxTable.metrics = {"A": [-1, 0]}

        with CapturingLogHandler(log, "ERROR") as captor:
            with self.assertRaisesRegex(TTLibError, "negative advance"):
                mtxTable.compile(font)

        self.assertTrue(
            len(
                [r for r in captor.records if "Glyph 'A' has negative advance" in r.msg]
            )
            == 1
        )

    def test_compile_struct_out_of_range(self):
        font = self.makeFont(numGlyphs=1, numberOfMetrics=1)
        mtxTable = font[self.tag] = newTable(self.tag)
        mtxTable.metrics = {"A": (0xFFFF + 1, -0x8001)}

        with self.assertRaises(struct.error):
            mtxTable.compile(font)

    def test_compile_round_float_values(self):
        font = self.makeFont(numGlyphs=3, numberOfMetrics=2)
        mtxTable = font[self.tag] = newTable(self.tag)
        mtxTable.metrics = {
            "A": (0.5, 0.5),  # round -> (1, 1)
            "B": (0.1, 0.9),  # round -> (0, 1)
            "C": (0.1, 0.1),  # round -> (0, 0)
        }

        data = mtxTable.compile(font)

        self.assertEqual(data, deHexStr("0001 0001 0000 0001 0000"))

    def test_compile_no_header_table(self):
        font = TTFont()
        maxp = font["maxp"] = newTable("maxp")
        maxp.numGlyphs = 3
        font.glyphOrder = [chr(i) for i in range(65, 68)]
        mtxTable = font[self.tag] = newTable(self.tag)
        mtxTable.metrics = {
            "A": (400, 30),
            "B": (400, 40),
            "C": (400, 50),
        }

        self.assertNotIn(self.tableClass.headerTag, font)

        data = mtxTable.compile(font)

        self.assertEqual(data, deHexStr("0190 001E 0190 0028 0190 0032"))

    def test_toXML(self):
        font = self.makeFont(numGlyphs=2, numberOfMetrics=2)
        mtxTable = font[self.tag] = newTable(self.tag)
        mtxTable.metrics = {"B": (632, 79), "A": (674, -11)}

        self.assertEqual(
            getXML(mtxTable.toXML),
            (
                '<mtx name="A" %s="674" %s="-11"/>\n'
                '<mtx name="B" %s="632" %s="79"/>'
                % ((self.tableClass.advanceName, self.tableClass.sideBearingName) * 2)
            ).split("\n"),
        )

    def test_fromXML(self):
        mtxTable = newTable(self.tag)

        for name, attrs, content in parseXML(
            '<mtx name="A" %s="674" %s="-11"/>'
            '<mtx name="B" %s="632" %s="79"/>'
            % ((self.tableClass.advanceName, self.tableClass.sideBearingName) * 2)
        ):
            mtxTable.fromXML(name, attrs, content, ttFont=None)

        self.assertEqual(mtxTable.metrics, {"A": (674, -11), "B": (632, 79)})

    def test_delitem(self):
        mtxTable = newTable(self.tag)
        mtxTable.metrics = {"A": (0, 0)}

        del mtxTable["A"]

        self.assertTrue("A" not in mtxTable.metrics)

    def test_setitem(self):
        mtxTable = newTable(self.tag)
        mtxTable.metrics = {"A": (674, -11), "B": (632, 79)}
        mtxTable["B"] = [0, 0]  # list is converted to tuple

        self.assertEqual(mtxTable.metrics, {"A": (674, -11), "B": (0, 0)})


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
