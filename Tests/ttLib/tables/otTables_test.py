from fontTools.misc.testTools import getXML, parseXML, parseXmlInto, FakeFont
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib.tables.otBase import CountReference, OTTableReader, OTTableWriter
import fontTools.ttLib.tables.otTables as otTables
from io import StringIO
from textwrap import dedent
import unittest


def makeCoverage(glyphs):
    coverage = otTables.Coverage()
    coverage.glyphs = glyphs
    return coverage


def compileTable(table, font):
    localState = None
    if hasattr(table.__class__, "LookupType"):
        lookupType = {"LookupType": None}
        localState = {
            "LookupType": CountReference(lookupType, "LookupType"),
        }
    writer = OTTableWriter(localState=localState)
    table.compile(writer, font)
    return hexStr(writer.getAllData())


def decompileTable(table, data, font):
    table.decompile(OTTableReader(deHexStr(data)), font)
    return table


class SparseFakeFont:
    def __init__(self, glyphMap):
        self.glyphMap = glyphMap
        self.reverseGlyphMap = {glyphID: name for name, glyphID in glyphMap.items()}
        self.lazy = False

    def getGlyphID(self, name):
        return self.glyphMap[name]

    def getGlyphIDMany(self, names):
        return [self.getGlyphID(name) for name in names]

    def getGlyphName(self, glyphID):
        return self.reverseGlyphMap[glyphID]

    def getGlyphNameMany(self, glyphIDs):
        return [self.getGlyphName(glyphID) for glyphID in glyphIDs]

    def hasExtendedGlyphIDs(self):
        return True


class CoverageTest(unittest.TestCase):
    def setUp(self):
        self.font = SparseFakeFont(
            {"a": 0x10000, "b": 0x10001, "c": 0x10002, "d": 0x10003}
        )

    def test_postRead_format3(self):
        table = otTables.Coverage()
        table.Format = 3
        table.postRead({"GlyphArray": ["a", "c"]}, self.font)
        self.assertEqual(table.glyphs, ["a", "c"])

    def test_postRead_format4(self):
        record = otTables.RangeRecord2()
        record.Start = "a"
        record.End = "d"
        record.StartCoverageIndex = 0
        table = otTables.Coverage()
        table.Format = 4
        table.postRead({"RangeRecord": [record]}, self.font)
        self.assertEqual(table.glyphs, ["a", "b", "c", "d"])

    def test_decompile_format4(self):
        table = decompileTable(
            otTables.Coverage(),
            "0004000001010000010003000000",
            self.font,
        )
        self.assertEqual(table.glyphs, ["a", "b", "c", "d"])

    def test_preWrite_format3(self):
        table = makeCoverage(["a", "c"])
        rawTable = table.preWrite(self.font)
        self.assertEqual(table.Format, 3)
        self.assertEqual(rawTable["GlyphArray"], ["a", "c"])
        self.assertEqual(compileTable(table, self.font), "0003000002010000010002")

    def test_preWrite_format4(self):
        table = makeCoverage(["a", "b", "c", "d"])
        rawTable = table.preWrite(self.font)
        self.assertEqual(table.Format, 4)
        self.assertIsInstance(rawTable["RangeRecord"][0], otTables.RangeRecord2)
        self.assertEqual(compileTable(table, self.font), "0004000001010000010003000000")


class ClassDefTest(unittest.TestCase):
    def setUp(self):
        self.font = SparseFakeFont(
            {"a": 0x10000, "b": 0x10001, "c": 0x20000, "d": 0x20001}
        )

    def test_postRead_format3(self):
        table = otTables.ClassDef()
        table.Format = 3
        table.postRead(
            {"StartGlyph": "a", "ClassValueArray": [1, 2]},
            self.font,
        )
        self.assertEqual(table.classDefs, {"a": 1, "b": 2})

    def test_postRead_format4(self):
        record = otTables.ClassRangeRecord2()
        record.Start = "c"
        record.End = "d"
        record.Class = 3
        table = otTables.ClassDef()
        table.Format = 4
        table.postRead({"ClassRangeRecord": [record]}, self.font)
        self.assertEqual(table.classDefs, {"c": 3, "d": 3})

    def test_decompile_format4(self):
        table = decompileTable(
            otTables.ClassDef(),
            "000400000201000001000000010200000200000002",
            self.font,
        )
        self.assertEqual(table.classDefs, {"a": 1, "c": 2})

    def test_preWrite_format3(self):
        table = otTables.ClassDef()
        table.classDefs = {"a": 1, "b": 2}
        rawTable = table.preWrite(self.font)
        self.assertEqual(table.Format, 3)
        self.assertEqual(rawTable["ClassValueArray"], [1, 2])
        self.assertEqual(compileTable(table, self.font), "000301000000000200010002")

    def test_preWrite_format4(self):
        table = otTables.ClassDef()
        table.classDefs = {"a": 1, "c": 2}
        rawTable = table.preWrite(self.font)
        self.assertEqual(table.Format, 4)
        self.assertIsInstance(
            rawTable["ClassRangeRecord"][0], otTables.ClassRangeRecord2
        )
        self.assertEqual(
            compileTable(table, self.font),
            "000400000201000001000000010200000200000002",
        )


class SingleSubstTest(unittest.TestCase):
    def setUp(self):
        self.glyphs = ".notdef A B C D E a b c d e".split()
        self.font = FakeFont(self.glyphs)

    def test_postRead_format1(self):
        table = otTables.SingleSubst()
        table.Format = 1
        rawTable = {"Coverage": makeCoverage(["A", "B", "C"]), "DeltaGlyphID": 5}
        table.postRead(rawTable, self.font)
        self.assertEqual(table.mapping, {"A": "a", "B": "b", "C": "c"})

    def test_postRead_format2(self):
        table = otTables.SingleSubst()
        table.Format = 2
        rawTable = {
            "Coverage": makeCoverage(["A", "B", "C"]),
            "GlyphCount": 3,
            "Substitute": ["c", "b", "a"],
        }
        table.postRead(rawTable, self.font)
        self.assertEqual(table.mapping, {"A": "c", "B": "b", "C": "a"})

    def test_postRead_format3(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x10002})
        table = otTables.SingleSubst()
        table.Format = 3
        table.postRead(
            {"Coverage": makeCoverage(["a", "b"]), "DeltaGlyphID": 1},
            font,
        )
        self.assertEqual(table.mapping, {"a": "b", "b": "c"})

    def test_postRead_format4(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        table = otTables.SingleSubst()
        table.Format = 4
        table.postRead(
            {
                "Coverage": makeCoverage(["a", "b"]),
                "GlyphCount": 2,
                "Substitute": ["c", "a"],
            },
            font,
        )
        self.assertEqual(table.mapping, {"a": "c", "b": "a"})

    def test_postRead_formatUnknown(self):
        table = otTables.SingleSubst()
        table.Format = 987
        rawTable = {"Coverage": makeCoverage(["A", "B", "C"])}
        self.assertRaises(AssertionError, table.postRead, rawTable, self.font)

    def test_preWrite_format1(self):
        table = otTables.SingleSubst()
        table.mapping = {"A": "a", "B": "b", "C": "c"}
        rawTable = table.preWrite(self.font)
        self.assertEqual(table.Format, 1)
        self.assertEqual(rawTable["Coverage"].glyphs, ["A", "B", "C"])
        self.assertEqual(rawTable["DeltaGlyphID"], 5)

    def test_preWrite_format2(self):
        table = otTables.SingleSubst()
        table.mapping = {"A": "c", "B": "b", "C": "a"}
        rawTable = table.preWrite(self.font)
        self.assertEqual(table.Format, 2)
        self.assertEqual(rawTable["Coverage"].glyphs, ["A", "B", "C"])
        self.assertEqual(rawTable["Substitute"], ["c", "b", "a"])

    def test_preWrite_format3(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x10002})
        table = otTables.SingleSubst()
        table.mapping = {"a": "b", "b": "c"}
        rawTable = table.preWrite(font)
        self.assertEqual(table.Format, 3)
        self.assertEqual(rawTable["DeltaGlyphID"], 1)
        self.assertEqual(
            compileTable(table, font),
            "0003000000090000010003000002010000010001",
        )

    def test_preWrite_format4(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        table = otTables.SingleSubst()
        table.mapping = {"a": "c", "b": "a"}
        rawTable = table.preWrite(font)
        self.assertEqual(table.Format, 4)
        self.assertEqual(rawTable["Substitute"], ["c", "a"])
        self.assertEqual(
            compileTable(table, font),
            "00040000000f0000020200000100000003000002010000010001",
        )

    def test_preWrite_emptyMapping(self):
        table = otTables.SingleSubst()
        table.mapping = {}
        rawTable = table.preWrite(self.font)
        self.assertEqual(table.Format, 2)
        self.assertEqual(rawTable["Coverage"].glyphs, [])
        self.assertEqual(rawTable["Substitute"], [])

    def test_toXML2(self):
        writer = XMLWriter(StringIO())
        table = otTables.SingleSubst()
        table.mapping = {"A": "a", "B": "b", "C": "c"}
        table.toXML2(writer, self.font)
        self.assertEqual(
            writer.file.getvalue().splitlines()[1:],
            [
                '<Substitution in="A" out="a"/>',
                '<Substitution in="B" out="b"/>',
                '<Substitution in="C" out="c"/>',
            ],
        )

    def test_fromXML(self):
        table = otTables.SingleSubst()
        for name, attrs, content in parseXML(
            '<Substitution in="A" out="a"/>'
            '<Substitution in="B" out="b"/>'
            '<Substitution in="C" out="c"/>'
        ):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.mapping, {"A": "a", "B": "b", "C": "c"})


class MultipleSubstTest(unittest.TestCase):
    def setUp(self):
        self.glyphs = ".notdef c f i t c_t f_f_i".split()
        self.font = FakeFont(self.glyphs)

    def test_postRead_format1(self):
        makeSequence = otTables.MultipleSubst.makeSequence_
        table = otTables.MultipleSubst()
        table.Format = 1
        rawTable = {
            "Coverage": makeCoverage(["c_t", "f_f_i"]),
            "Sequence": [makeSequence(["c", "t"]), makeSequence(["f", "f", "i"])],
        }
        table.postRead(rawTable, self.font)
        self.assertEqual(table.mapping, {"c_t": ["c", "t"], "f_f_i": ["f", "f", "i"]})

    def test_postRead_format2(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        table = otTables.MultipleSubst()
        table.Format = 2
        rawTable = {
            "Coverage": makeCoverage(["a"]),
            "Sequence": [table.makeSequence_(["b", "c"], extended=True)],
        }
        table.postRead(rawTable, font)
        self.assertEqual(table.mapping, {"a": ["b", "c"]})

    def test_decompile_format2(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        table = decompileTable(
            otTables.MultipleSubst(),
            "00020000000d0000010000001500030000010100000002010001020000",
            font,
        )
        self.assertEqual(table.mapping, {"a": ["b", "c"]})

    def test_postRead_formatUnknown(self):
        table = otTables.MultipleSubst()
        table.Format = 987
        self.assertRaises(AssertionError, table.postRead, {}, self.font)

    def test_preWrite_format1(self):
        table = otTables.MultipleSubst()
        table.mapping = {"c_t": ["c", "t"], "f_f_i": ["f", "f", "i"]}
        rawTable = table.preWrite(self.font)
        self.assertEqual(table.Format, 1)
        self.assertEqual(rawTable["Coverage"].glyphs, ["c_t", "f_f_i"])

    def test_preWrite_format2(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        table = otTables.MultipleSubst()
        table.mapping = {"a": ["b", "c"]}
        rawTable = table.preWrite(font)
        self.assertEqual(table.Format, 2)
        self.assertIsInstance(rawTable["Sequence"][0], otTables.Sequence2)
        self.assertEqual(rawTable["Sequence"][0].Substitute, ["b", "c"])
        self.assertEqual(
            compileTable(table, font),
            "00020000000d0000010000001500030000010100000002010001020000",
        )

    def test_toXML2(self):
        writer = XMLWriter(StringIO())
        table = otTables.MultipleSubst()
        table.mapping = {"c_t": ["c", "t"], "f_f_i": ["f", "f", "i"]}
        table.toXML2(writer, self.font)
        self.assertEqual(
            writer.file.getvalue().splitlines()[1:],
            [
                '<Substitution in="c_t" out="c,t"/>',
                '<Substitution in="f_f_i" out="f,f,i"/>',
            ],
        )

    def test_fromXML(self):
        table = otTables.MultipleSubst()
        for name, attrs, content in parseXML(
            '<Substitution in="c_t" out="c,t"/>'
            '<Substitution in="f_f_i" out="f,f,i"/>'
        ):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.mapping, {"c_t": ["c", "t"], "f_f_i": ["f", "f", "i"]})

    def test_fromXML_oldFormat(self):
        table = otTables.MultipleSubst()
        for name, attrs, content in parseXML(
            "<Coverage>"
            '  <Glyph value="c_t"/>'
            '  <Glyph value="f_f_i"/>'
            "</Coverage>"
            '<Sequence index="0">'
            '  <Substitute index="0" value="c"/>'
            '  <Substitute index="1" value="t"/>'
            "</Sequence>"
            '<Sequence index="1">'
            '  <Substitute index="0" value="f"/>'
            '  <Substitute index="1" value="f"/>'
            '  <Substitute index="2" value="i"/>'
            "</Sequence>"
        ):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.mapping, {"c_t": ["c", "t"], "f_f_i": ["f", "f", "i"]})

    def test_fromXML_oldFormat_bug385(self):
        # https://github.com/fonttools/fonttools/issues/385
        table = otTables.MultipleSubst()
        table.Format = 1
        for name, attrs, content in parseXML(
            "<Coverage>"
            '  <Glyph value="o"/>'
            '  <Glyph value="l"/>'
            "</Coverage>"
            "<Sequence>"
            '  <Substitute value="o"/>'
            '  <Substitute value="l"/>'
            '  <Substitute value="o"/>'
            "</Sequence>"
            "<Sequence>"
            '  <Substitute value="o"/>'
            "</Sequence>"
        ):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.mapping, {"o": ["o", "l", "o"], "l": ["o"]})


class LigatureSubstTest(unittest.TestCase):
    def setUp(self):
        self.glyphs = ".notdef c f i t c_t f_f f_i f_f_i".split()
        self.font = FakeFont(self.glyphs)

    def makeLigature(self, s):
        """'ffi' --> Ligature(LigGlyph='f_f_i', Component=['f', 'f', 'i'])"""
        lig = otTables.Ligature()
        lig.Component = list(s)
        lig.LigGlyph = "_".join(lig.Component)
        return lig

    def makeLigatures(self, s):
        """'ffi fi' --> [otTables.Ligature, otTables.Ligature]"""
        return [self.makeLigature(lig) for lig in s.split()]

    def test_postRead_format1(self):
        table = otTables.LigatureSubst()
        table.Format = 1
        ligs_c = otTables.LigatureSet()
        ligs_c.Ligature = self.makeLigatures("ct")
        ligs_f = otTables.LigatureSet()
        ligs_f.Ligature = self.makeLigatures("ffi ff fi")
        rawTable = {
            "Coverage": makeCoverage(["c", "f"]),
            "LigatureSet": [ligs_c, ligs_f],
        }
        table.postRead(rawTable, self.font)
        self.assertEqual(set(table.ligatures.keys()), {"c", "f"})
        self.assertEqual(len(table.ligatures["c"]), 1)
        self.assertEqual(table.ligatures["c"][0].LigGlyph, "c_t")
        self.assertEqual(table.ligatures["c"][0].Component, ["c", "t"])
        self.assertEqual(len(table.ligatures["f"]), 3)
        self.assertEqual(table.ligatures["f"][0].LigGlyph, "f_f_i")
        self.assertEqual(table.ligatures["f"][0].Component, ["f", "f", "i"])
        self.assertEqual(table.ligatures["f"][1].LigGlyph, "f_f")
        self.assertEqual(table.ligatures["f"][1].Component, ["f", "f"])
        self.assertEqual(table.ligatures["f"][2].LigGlyph, "f_i")
        self.assertEqual(table.ligatures["f"][2].Component, ["f", "i"])

    def test_postRead_format2(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        ligature = otTables.Ligature2()
        ligature.LigGlyph = "c"
        ligature.Component = ["b"]
        ligatureSet = otTables.LigatureSet2()
        ligatureSet.Ligature = [ligature]
        table = otTables.LigatureSubst()
        table.Format = 2
        table.postRead(
            {
                "Coverage": makeCoverage(["a"]),
                "LigatureSet": [ligatureSet],
            },
            font,
        )
        self.assertEqual(table.ligatures["a"][0].LigGlyph, "c")
        self.assertEqual(table.ligatures["a"][0].Component, ["b"])

    def test_decompile_format2(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        table = decompileTable(
            otTables.LigatureSubst(),
            "00020000001b0000010000000d00010000000602000000020100010003000001010000",
            font,
        )
        self.assertEqual(table.ligatures["a"][0].LigGlyph, "c")
        self.assertEqual(table.ligatures["a"][0].Component, ["b"])

    def test_postRead_formatUnknown(self):
        table = otTables.LigatureSubst()
        table.Format = 987
        rawTable = {"Coverage": makeCoverage(["f"])}
        self.assertRaises(AssertionError, table.postRead, rawTable, self.font)

    def test_preWrite_format1(self):
        table = otTables.LigatureSubst()
        table.ligatures = {
            "c": self.makeLigatures("ct"),
            "f": self.makeLigatures("ffi ff fi"),
        }
        rawTable = table.preWrite(self.font)
        self.assertEqual(table.Format, 1)
        self.assertEqual(rawTable["Coverage"].glyphs, ["c", "f"])
        [c, f] = rawTable["LigatureSet"]
        self.assertIsInstance(c, otTables.LigatureSet)
        self.assertIsInstance(f, otTables.LigatureSet)
        [ct] = c.Ligature
        self.assertIsInstance(ct, otTables.Ligature)
        self.assertEqual(ct.LigGlyph, "c_t")
        self.assertEqual(ct.Component, ["c", "t"])
        [ffi, ff, fi] = f.Ligature
        self.assertIsInstance(ffi, otTables.Ligature)
        self.assertEqual(ffi.LigGlyph, "f_f_i")
        self.assertEqual(ffi.Component, ["f", "f", "i"])
        self.assertIsInstance(ff, otTables.Ligature)
        self.assertEqual(ff.LigGlyph, "f_f")
        self.assertEqual(ff.Component, ["f", "f"])
        self.assertIsInstance(fi, otTables.Ligature)
        self.assertEqual(fi.LigGlyph, "f_i")
        self.assertEqual(fi.Component, ["f", "i"])

    def test_preWrite_format2(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        ligature = otTables.Ligature()
        ligature.LigGlyph = "c"
        ligature.Component = ["b"]
        table = otTables.LigatureSubst()
        table.ligatures = {"a": [ligature]}
        rawTable = table.preWrite(font)
        self.assertEqual(table.Format, 2)
        self.assertIsInstance(rawTable["LigatureSet"][0], otTables.LigatureSet2)
        self.assertIsInstance(
            rawTable["LigatureSet"][0].Ligature[0],
            otTables.Ligature2,
        )
        self.assertEqual(
            compileTable(table, font),
            "00020000001b0000010000000d00010000000602000000020100010003000001010000",
        )

    def test_preWrite_format2_highLevel(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        table = otTables.LigatureSubst()
        table.ligatures = {("a", "b"): "c"}
        rawTable = table.preWrite(font)
        self.assertEqual(table.Format, 2)
        self.assertIsInstance(rawTable["LigatureSet"][0], otTables.LigatureSet2)
        self.assertIsInstance(
            rawTable["LigatureSet"][0].Ligature[0],
            otTables.Ligature2,
        )

    def test_toXML2(self):
        writer = XMLWriter(StringIO())
        table = otTables.LigatureSubst()
        table.ligatures = {
            "c": self.makeLigatures("ct"),
            "f": self.makeLigatures("ffi ff fi"),
        }
        table.toXML2(writer, self.font)
        self.assertEqual(
            writer.file.getvalue().splitlines()[1:],
            [
                '<LigatureSet glyph="c">',
                '  <Ligature components="c,t" glyph="c_t"/>',
                "</LigatureSet>",
                '<LigatureSet glyph="f">',
                '  <Ligature components="f,f,i" glyph="f_f_i"/>',
                '  <Ligature components="f,f" glyph="f_f"/>',
                '  <Ligature components="f,i" glyph="f_i"/>',
                "</LigatureSet>",
            ],
        )

    def test_fromXML(self):
        table = otTables.LigatureSubst()
        for name, attrs, content in parseXML(
            '<LigatureSet glyph="f">'
            '  <Ligature components="f,f,i" glyph="f_f_i"/>'
            '  <Ligature components="f,f" glyph="f_f"/>'
            "</LigatureSet>"
        ):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(set(table.ligatures.keys()), {"f"})
        [ffi, ff] = table.ligatures["f"]
        self.assertEqual(ffi.LigGlyph, "f_f_i")
        self.assertEqual(ffi.Component, ["f", "f", "i"])
        self.assertEqual(ff.LigGlyph, "f_f")
        self.assertEqual(ff.Component, ["f", "f"])


class AlternateSubstTest(unittest.TestCase):
    def setUp(self):
        self.glyphs = ".notdef G G.alt1 G.alt2 Z Z.fina".split()
        self.font = FakeFont(self.glyphs)

    def makeAlternateSet(self, s):
        result = otTables.AlternateSet()
        result.Alternate = s.split()
        return result

    def test_postRead_format1(self):
        table = otTables.AlternateSubst()
        table.Format = 1
        rawTable = {
            "Coverage": makeCoverage(["G", "Z"]),
            "AlternateSet": [
                self.makeAlternateSet("G.alt2 G.alt1"),
                self.makeAlternateSet("Z.fina"),
            ],
        }
        table.postRead(rawTable, self.font)
        self.assertEqual(table.alternates, {"G": ["G.alt2", "G.alt1"], "Z": ["Z.fina"]})

    def test_postRead_format2(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        alternateSet = otTables.AlternateSet2()
        alternateSet.Alternate = ["b", "c"]
        table = otTables.AlternateSubst()
        table.Format = 2
        table.postRead(
            {
                "Coverage": makeCoverage(["a"]),
                "AlternateSet": [alternateSet],
            },
            font,
        )
        self.assertEqual(table.alternates, {"a": ["b", "c"]})

    def test_decompile_format2(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        table = decompileTable(
            otTables.AlternateSubst(),
            "0002000000150000010000000d00020100010200000003000001010000",
            font,
        )
        self.assertEqual(table.alternates, {"a": ["b", "c"]})

    def test_postRead_formatUnknown(self):
        table = otTables.AlternateSubst()
        table.Format = 987
        self.assertRaises(AssertionError, table.postRead, {}, self.font)

    def test_preWrite_format1(self):
        table = otTables.AlternateSubst()
        table.alternates = {"G": ["G.alt2", "G.alt1"], "Z": ["Z.fina"]}
        rawTable = table.preWrite(self.font)
        self.assertEqual(table.Format, 1)
        self.assertEqual(rawTable["Coverage"].glyphs, ["G", "Z"])
        [g, z] = rawTable["AlternateSet"]
        self.assertIsInstance(g, otTables.AlternateSet)
        self.assertEqual(g.Alternate, ["G.alt2", "G.alt1"])
        self.assertIsInstance(z, otTables.AlternateSet)
        self.assertEqual(z.Alternate, ["Z.fina"])

    def test_preWrite_format2(self):
        font = SparseFakeFont({"a": 0x10000, "b": 0x10001, "c": 0x20000})
        table = otTables.AlternateSubst()
        table.alternates = {"a": ["b", "c"]}
        rawTable = table.preWrite(font)
        self.assertEqual(table.Format, 2)
        self.assertIsInstance(rawTable["AlternateSet"][0], otTables.AlternateSet2)
        self.assertEqual(rawTable["AlternateSet"][0].Alternate, ["b", "c"])
        self.assertEqual(
            compileTable(table, font),
            "0002000000150000010000000d00020100010200000003000001010000",
        )

    def test_toXML2(self):
        writer = XMLWriter(StringIO())
        table = otTables.AlternateSubst()
        table.alternates = {"G": ["G.alt2", "G.alt1"], "Z": ["Z.fina"]}
        table.toXML2(writer, self.font)
        self.assertEqual(
            writer.file.getvalue().splitlines()[1:],
            [
                '<AlternateSet glyph="G">',
                '  <Alternate glyph="G.alt2"/>',
                '  <Alternate glyph="G.alt1"/>',
                "</AlternateSet>",
                '<AlternateSet glyph="Z">',
                '  <Alternate glyph="Z.fina"/>',
                "</AlternateSet>",
            ],
        )

    def test_fromXML(self):
        table = otTables.AlternateSubst()
        for name, attrs, content in parseXML(
            '<AlternateSet glyph="G">'
            '  <Alternate glyph="G.alt2"/>'
            '  <Alternate glyph="G.alt1"/>'
            "</AlternateSet>"
            '<AlternateSet glyph="Z">'
            '  <Alternate glyph="Z.fina"/>'
            "</AlternateSet>"
        ):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.alternates, {"G": ["G.alt2", "G.alt1"], "Z": ["Z.fina"]})


class RearrangementMorphActionTest(unittest.TestCase):
    def setUp(self):
        self.font = FakeFont([".notdef", "A", "B", "C"])

    def testCompile(self):
        r = otTables.RearrangementMorphAction()
        r.NewState = 0x1234
        r.MarkFirst = r.DontAdvance = r.MarkLast = True
        r.ReservedFlags, r.Verb = 0x1FF0, 0xD
        writer = OTTableWriter()
        r.compile(writer, self.font, actionIndex=None)
        self.assertEqual(hexStr(writer.getAllData()), "1234fffd")

    def testCompileActions(self):
        act = otTables.RearrangementMorphAction()
        self.assertEqual(act.compileActions(self.font, []), (None, None))

    def testDecompileToXML(self):
        r = otTables.RearrangementMorphAction()
        r.decompile(OTTableReader(deHexStr("1234fffd")), self.font, actionReader=None)
        toXML = lambda w, f: r.toXML(w, f, {"Test": "Foo"}, "Transition")
        self.assertEqual(
            getXML(toXML, self.font),
            [
                '<Transition Test="Foo">',
                '  <NewState value="4660"/>',  # 0x1234 = 4660
                '  <Flags value="MarkFirst,DontAdvance,MarkLast"/>',
                '  <ReservedFlags value="0x1FF0"/>',
                '  <Verb value="13"/><!-- ABxCD ⇒ CDxBA -->',
                "</Transition>",
            ],
        )


class ContextualMorphActionTest(unittest.TestCase):
    def setUp(self):
        self.font = FakeFont([".notdef", "A", "B", "C"])

    def testCompile(self):
        a = otTables.ContextualMorphAction()
        a.NewState = 0x1234
        a.SetMark, a.DontAdvance, a.ReservedFlags = True, True, 0x3117
        a.MarkIndex, a.CurrentIndex = 0xDEAD, 0xBEEF
        writer = OTTableWriter()
        a.compile(writer, self.font, actionIndex=None)
        self.assertEqual(hexStr(writer.getAllData()), "1234f117deadbeef")

    def testCompileActions(self):
        act = otTables.ContextualMorphAction()
        self.assertEqual(act.compileActions(self.font, []), (None, None))

    def testDecompileToXML(self):
        a = otTables.ContextualMorphAction()
        a.decompile(
            OTTableReader(deHexStr("1234f117deadbeef")), self.font, actionReader=None
        )
        toXML = lambda w, f: a.toXML(w, f, {"Test": "Foo"}, "Transition")
        self.assertEqual(
            getXML(toXML, self.font),
            [
                '<Transition Test="Foo">',
                '  <NewState value="4660"/>',  # 0x1234 = 4660
                '  <Flags value="SetMark,DontAdvance"/>',
                '  <ReservedFlags value="0x3117"/>',
                '  <MarkIndex value="57005"/>',  # 0xDEAD = 57005
                '  <CurrentIndex value="48879"/>',  # 0xBEEF = 48879
                "</Transition>",
            ],
        )


class LigatureMorphActionTest(unittest.TestCase):
    def setUp(self):
        self.font = FakeFont([".notdef", "A", "B", "C"])

    def testDecompileToXML(self):
        a = otTables.LigatureMorphAction()
        actionReader = OTTableReader(deHexStr("DEADBEEF 7FFFFFFE 80000003"))
        a.decompile(OTTableReader(deHexStr("1234FAB30001")), self.font, actionReader)
        toXML = lambda w, f: a.toXML(w, f, {"Test": "Foo"}, "Transition")
        self.assertEqual(
            getXML(toXML, self.font),
            [
                '<Transition Test="Foo">',
                '  <NewState value="4660"/>',  # 0x1234 = 4660
                '  <Flags value="SetComponent,DontAdvance"/>',
                '  <ReservedFlags value="0x1AB3"/>',
                '  <Action GlyphIndexDelta="-2" Flags="Store"/>',
                '  <Action GlyphIndexDelta="3"/>',
                "</Transition>",
            ],
        )

    def testCompileActions_empty(self):
        act = otTables.LigatureMorphAction()
        actions, actionIndex = act.compileActions(self.font, [])
        self.assertEqual(actions, b"")
        self.assertEqual(actionIndex, {})

    def testCompileActions_shouldShareSubsequences(self):
        state = otTables.AATState()
        t = state.Transitions = {i: otTables.LigatureMorphAction() for i in range(3)}
        ligs = [otTables.LigAction() for _ in range(3)]
        for i, lig in enumerate(ligs):
            lig.GlyphIndexDelta = i
        t[0].Actions = ligs[1:2]
        t[1].Actions = ligs[0:3]
        t[2].Actions = ligs[1:3]
        actions, actionIndex = t[0].compileActions(self.font, [state])
        self.assertEqual(actions, deHexStr("00000000 00000001 80000002 80000001"))
        self.assertEqual(
            actionIndex,
            {
                deHexStr("00000000 00000001 80000002"): 0,
                deHexStr("00000001 80000002"): 1,
                deHexStr("80000002"): 2,
                deHexStr("80000001"): 3,
            },
        )


class InsertionMorphActionTest(unittest.TestCase):
    MORPH_ACTION_XML = [
        '<Transition Test="Foo">',
        '  <NewState value="4660"/>',  # 0x1234 = 4660
        '  <Flags value="SetMark,DontAdvance,CurrentIsKashidaLike,'
        'MarkedIsKashidaLike,CurrentInsertBefore,MarkedInsertBefore"/>',
        '  <CurrentInsertionAction glyph="B"/>',
        '  <CurrentInsertionAction glyph="C"/>',
        '  <MarkedInsertionAction glyph="B"/>',
        '  <MarkedInsertionAction glyph="A"/>',
        '  <MarkedInsertionAction glyph="D"/>',
        "</Transition>",
    ]

    def setUp(self):
        self.font = FakeFont([".notdef", "A", "B", "C", "D"])
        self.maxDiff = None

    def testDecompileToXML(self):
        a = otTables.InsertionMorphAction()
        actionReader = OTTableReader(
            deHexStr("DEAD BEEF 0002 0001 0004 0002 0003 DEAD BEEF")
        )
        a.decompile(
            OTTableReader(deHexStr("1234 FC43 0005 0002")), self.font, actionReader
        )
        toXML = lambda w, f: a.toXML(w, f, {"Test": "Foo"}, "Transition")
        self.assertEqual(getXML(toXML, self.font), self.MORPH_ACTION_XML)

    def testCompileFromXML(self):
        a = otTables.InsertionMorphAction()
        for name, attrs, content in parseXML(self.MORPH_ACTION_XML):
            a.fromXML(name, attrs, content, self.font)
        writer = OTTableWriter()
        a.compile(
            writer,
            self.font,
            actionIndex={("B", "C"): 9, ("B", "A", "D"): 7},
        )
        self.assertEqual(hexStr(writer.getAllData()), "1234fc4300090007")

    def testCompileActions_empty(self):
        act = otTables.InsertionMorphAction()
        actions, actionIndex = act.compileActions(self.font, [])
        self.assertEqual(actions, b"")
        self.assertEqual(actionIndex, {})

    def testCompileActions_shouldShareSubsequences(self):
        state = otTables.AATState()
        t = state.Transitions = {i: otTables.InsertionMorphAction() for i in range(3)}
        t[1].CurrentInsertionAction = []
        t[0].MarkedInsertionAction = ["A"]
        t[1].CurrentInsertionAction = ["C", "D"]
        t[1].MarkedInsertionAction = ["B"]
        t[2].CurrentInsertionAction = ["B", "C", "D"]
        t[2].MarkedInsertionAction = ["C", "D"]
        actions, actionIndex = t[0].compileActions(self.font, [state])
        self.assertEqual(actions, deHexStr("0002 0003 0004 0001"))
        self.assertEqual(
            actionIndex,
            {
                ("A",): 3,
                ("B",): 0,
                ("B", "C"): 0,
                ("B", "C", "D"): 0,
                ("C",): 1,
                ("C", "D"): 1,
                ("D",): 2,
            },
        )


class SplitMultipleSubstTest:
    def overflow(self, itemName, itemRecord):
        from fontTools.otlLib.builder import buildMultipleSubstSubtable
        from fontTools.ttLib.tables.otBase import OverflowErrorRecord

        oldSubTable = buildMultipleSubstSubtable(
            {"e": 1, "a": 2, "b": 3, "c": 4, "d": 5}
        )
        newSubTable = otTables.MultipleSubst()

        ok = otTables.splitMultipleSubst(
            oldSubTable,
            newSubTable,
            OverflowErrorRecord((None, None, None, itemName, itemRecord)),
        )

        assert ok
        return oldSubTable.mapping, newSubTable.mapping

    def test_Coverage(self):
        oldMapping, newMapping = self.overflow("Coverage", None)
        assert oldMapping == {"a": 2, "b": 3}
        assert newMapping == {"c": 4, "d": 5, "e": 1}

    def test_RangeRecord(self):
        oldMapping, newMapping = self.overflow("RangeRecord", None)
        assert oldMapping == {"a": 2, "b": 3}
        assert newMapping == {"c": 4, "d": 5, "e": 1}

    def test_Sequence(self):
        oldMapping, newMapping = self.overflow("Sequence", 4)
        assert oldMapping == {"a": 2, "b": 3, "c": 4}
        assert newMapping == {"d": 5, "e": 1}


def test_splitMarkBasePos():
    from fontTools.otlLib.builder import buildAnchor, buildMarkBasePosSubtable

    marks = {
        "acutecomb": (0, buildAnchor(0, 600)),
        "gravecomb": (0, buildAnchor(0, 590)),
        "cedillacomb": (1, buildAnchor(0, 0)),
    }
    bases = {
        "a": {
            0: buildAnchor(350, 500),
            1: None,
        },
        "c": {
            0: buildAnchor(300, 700),
            1: buildAnchor(300, 0),
        },
    }
    glyphOrder = ["a", "c", "acutecomb", "gravecomb", "cedillacomb"]
    glyphMap = {g: i for i, g in enumerate(glyphOrder)}

    oldSubTable = buildMarkBasePosSubtable(marks, bases, glyphMap)
    newSubTable = otTables.MarkBasePos()

    ok = otTables.splitMarkBasePos(oldSubTable, newSubTable, overflowRecord=None)

    assert ok

    assert getXML(oldSubTable.toXML) == [
        '<MarkBasePos Format="1">',
        "  <MarkCoverage>",
        '    <Glyph value="acutecomb"/>',
        '    <Glyph value="gravecomb"/>',
        "  </MarkCoverage>",
        "  <BaseCoverage>",
        '    <Glyph value="a"/>',
        '    <Glyph value="c"/>',
        "  </BaseCoverage>",
        "  <!-- ClassCount=1 -->",
        "  <MarkArray>",
        "    <!-- MarkCount=2 -->",
        '    <MarkRecord index="0">',
        '      <Class value="0"/>',
        '      <MarkAnchor Format="1">',
        '        <XCoordinate value="0"/>',
        '        <YCoordinate value="600"/>',
        "      </MarkAnchor>",
        "    </MarkRecord>",
        '    <MarkRecord index="1">',
        '      <Class value="0"/>',
        '      <MarkAnchor Format="1">',
        '        <XCoordinate value="0"/>',
        '        <YCoordinate value="590"/>',
        "      </MarkAnchor>",
        "    </MarkRecord>",
        "  </MarkArray>",
        "  <BaseArray>",
        "    <!-- BaseCount=2 -->",
        '    <BaseRecord index="0">',
        '      <BaseAnchor index="0" Format="1">',
        '        <XCoordinate value="350"/>',
        '        <YCoordinate value="500"/>',
        "      </BaseAnchor>",
        "    </BaseRecord>",
        '    <BaseRecord index="1">',
        '      <BaseAnchor index="0" Format="1">',
        '        <XCoordinate value="300"/>',
        '        <YCoordinate value="700"/>',
        "      </BaseAnchor>",
        "    </BaseRecord>",
        "  </BaseArray>",
        "</MarkBasePos>",
    ]

    assert getXML(newSubTable.toXML) == [
        '<MarkBasePos Format="1">',
        "  <MarkCoverage>",
        '    <Glyph value="cedillacomb"/>',
        "  </MarkCoverage>",
        "  <BaseCoverage>",
        '    <Glyph value="a"/>',
        '    <Glyph value="c"/>',
        "  </BaseCoverage>",
        "  <!-- ClassCount=1 -->",
        "  <MarkArray>",
        "    <!-- MarkCount=1 -->",
        '    <MarkRecord index="0">',
        '      <Class value="0"/>',
        '      <MarkAnchor Format="1">',
        '        <XCoordinate value="0"/>',
        '        <YCoordinate value="0"/>',
        "      </MarkAnchor>",
        "    </MarkRecord>",
        "  </MarkArray>",
        "  <BaseArray>",
        "    <!-- BaseCount=2 -->",
        '    <BaseRecord index="0">',
        '      <BaseAnchor index="0" empty="1"/>',
        "    </BaseRecord>",
        '    <BaseRecord index="1">',
        '      <BaseAnchor index="0" Format="1">',
        '        <XCoordinate value="300"/>',
        '        <YCoordinate value="0"/>',
        "      </BaseAnchor>",
        "    </BaseRecord>",
        "  </BaseArray>",
        "</MarkBasePos>",
    ]


class ColrV1Test(unittest.TestCase):
    def setUp(self):
        self.font = FakeFont([".notdef", "meh"])

    def test_traverseEmptyPaintColrLayersNeedsNoLayerList(self):
        colr = parseXmlInto(
            self.font,
            otTables.COLR(),
            """
          <Version value="1"/>
          <BaseGlyphList>
            <BaseGlyphPaintRecord index="0">
              <BaseGlyph value="meh"/>
              <Paint Format="1"><!-- PaintColrLayers -->
                <NumLayers value="0"/>
                <FirstLayerIndex value="42"/>
              </Paint>
            </BaseGlyphPaintRecord>
          </BaseGlyphList>
          """,
        )
        paint = colr.BaseGlyphList.BaseGlyphPaintRecord[0].Paint

        # Just want to confirm we don't crash
        visited = []
        paint.traverse(colr, lambda p: visited.append(p))
        assert len(visited) == 1


def test_parse_Device_DeltaValue_from_XML_and_compile():
    # https://github.com/fonttools/fonttools/pull/3757
    font = FakeFont([".notdef", "five"])

    gpos_xml = dedent(
        """\
        <Version value="0x00010000"/>
        <ScriptList>
          <!-- ScriptCount=1 -->
          <ScriptRecord index="0">
            <ScriptTag value="DFLT"/>
            <Script>
              <DefaultLangSys>
                <ReqFeatureIndex value="65535"/>
                <!-- FeatureCount=1 -->
                <FeatureIndex index="0" value="0"/>
              </DefaultLangSys>
              <!-- LangSysCount=0 -->
            </Script>
          </ScriptRecord>
        </ScriptList>
        <FeatureList>
          <!-- FeatureCount=1 -->
          <FeatureRecord index="0">
            <FeatureTag value="curs"/>
            <Feature>
              <!-- LookupCount=1 -->
              <LookupListIndex index="0" value="0"/>
            </Feature>
          </FeatureRecord>
        </FeatureList>
        <LookupList>
          <!-- LookupCount=1 -->
          <Lookup index="0">
            <LookupType value="3"/>
            <LookupFlag value="0"/>
            <!-- SubTableCount=1 -->
            <CursivePos index="0" Format="1">
              <Coverage>
                <Glyph value="five"/>
              </Coverage>
              <!-- EntryExitCount=1 -->
              <EntryExitRecord index="0">
                <EntryAnchor Format="3">
                  <XCoordinate value="124"/>
                  <YCoordinate value="-4"/>
                  <XDeviceTable>
                    <StartSize value="8"/>
                    <EndSize value="9"/>
                    <DeltaFormat value="2"/>
                    <DeltaValue value="[1, 2]"/>
                  </XDeviceTable>
                  <YDeviceTable>
                    <StartSize value="7"/>
                    <EndSize value="7"/>
                    <DeltaFormat value="2"/>
                    <DeltaValue value="[3]"/>
                  </YDeviceTable>
                </EntryAnchor>
                <ExitAnchor Format="2">
                  <XCoordinate value="3"/>
                  <YCoordinate value="4"/>
                  <AnchorPoint value="2"/>
                </ExitAnchor>
              </EntryExitRecord>
            </CursivePos>
          </Lookup>
        </LookupList>"""
    )

    gpos = parseXmlInto(font, otTables.GPOS(), gpos_xml)

    anchor = gpos.LookupList.Lookup[0].SubTable[0].EntryExitRecord[0].EntryAnchor
    assert anchor.XDeviceTable.DeltaValue == [1, 2]
    assert anchor.YDeviceTable.DeltaValue == [3]

    writer = OTTableWriter()
    gpos.compile(writer, font)
    data = writer.getAllData()

    reader = OTTableReader(data, tableTag="GPOS")
    gpos2 = otTables.GPOS()
    gpos2.decompile(reader, font)

    assert dedent("\n".join(getXML(gpos2.toXML, font)[1:-1])) == gpos_xml


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
