from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc.testTools import parseXML, FakeFont
from fontTools.misc.xmlWriter import XMLWriter
import fontTools.ttLib.tables.otTables as otTables
import unittest


def makeCoverage(glyphs):
    coverage = otTables.Coverage()
    coverage.glyphs = glyphs
    return coverage


class SingleSubstTest(unittest.TestCase):
    def setUp(self):
        self.glyphs = ".notdef A B C D E a b c d e".split()
        self.font = FakeFont(self.glyphs)

    def test_postRead_format1(self):
        table = otTables.SingleSubst()
        table.Format = 1
        rawTable = {
            "Coverage": makeCoverage(["A", "B", "C"]),
            "DeltaGlyphID": 5
        }
        table.postRead(rawTable, self.font)
        self.assertEqual(table.mapping, {"A": "a", "B": "b", "C": "c"})

    def test_postRead_format2(self):
        table = otTables.SingleSubst()
        table.Format = 2
        rawTable = {
            "Coverage": makeCoverage(["A", "B", "C"]),
            "GlyphCount": 3,
            "Substitute": ["c", "b", "a"]
        }
        table.postRead(rawTable, self.font)
        self.assertEqual(table.mapping, {"A": "c", "B": "b", "C": "a"})

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
        self.assertEqual(writer.file.getvalue().splitlines()[1:], [
            '<Substitution in="A" out="a"/>',
            '<Substitution in="B" out="b"/>',
            '<Substitution in="C" out="c"/>',
        ])

    def test_fromXML(self):
        table = otTables.SingleSubst()
        for name, attrs, content in parseXML(
                '<Substitution in="A" out="a"/>'
                '<Substitution in="B" out="b"/>'
                '<Substitution in="C" out="c"/>'):
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
            "Sequence": [
                makeSequence(["c", "t"]),
                makeSequence(["f", "f", "i"])
            ]
        }
        table.postRead(rawTable, self.font)
        self.assertEqual(table.mapping, {
            "c_t": ["c", "t"],
            "f_f_i": ["f", "f", "i"]
        })

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

    def test_toXML2(self):
        writer = XMLWriter(StringIO())
        table = otTables.MultipleSubst()
        table.mapping = {"c_t": ["c", "t"], "f_f_i": ["f", "f", "i"]}
        table.toXML2(writer, self.font)
        self.assertEqual(writer.file.getvalue().splitlines()[1:], [
            '<Substitution in="c_t" out="c,t"/>',
            '<Substitution in="f_f_i" out="f,f,i"/>',
        ])

    def test_fromXML(self):
        table = otTables.MultipleSubst()
        for name, attrs, content in parseXML(
                '<Substitution in="c_t" out="c,t"/>'
                '<Substitution in="f_f_i" out="f,f,i"/>'):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.mapping,
                         {'c_t': ['c', 't'], 'f_f_i': ['f', 'f', 'i']})

    def test_fromXML_oldFormat(self):
        table = otTables.MultipleSubst()
        for name, attrs, content in parseXML(
                '<Coverage>'
                '  <Glyph value="c_t"/>'
                '  <Glyph value="f_f_i"/>'
                '</Coverage>'
                '<Sequence index="0">'
                '  <Substitute index="0" value="c"/>'
                '  <Substitute index="1" value="t"/>'
                '</Sequence>'
                '<Sequence index="1">'
                '  <Substitute index="0" value="f"/>'
                '  <Substitute index="1" value="f"/>'
                '  <Substitute index="2" value="i"/>'
                '</Sequence>'):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.mapping,
                         {'c_t': ['c', 't'], 'f_f_i': ['f', 'f', 'i']})

    def test_fromXML_oldFormat_bug385(self):
        # https://github.com/behdad/fonttools/issues/385
        table = otTables.MultipleSubst()
        table.Format = 1
        for name, attrs, content in parseXML(
                '<Coverage Format="1">'
                '  <Glyph value="o"/>'
                '  <Glyph value="l"/>'
                '</Coverage>'
                '<Sequence>'
                '  <Substitute value="o"/>'
                '  <Substitute value="l"/>'
                '  <Substitute value="o"/>'
                '</Sequence>'
                '<Sequence>'
                '  <Substitute value="o"/>'
                '</Sequence>'):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.mapping,
                         {'o': ['o', 'l', 'o'], 'l': ['o']})


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
            "LigatureSet": [ligs_c, ligs_f]
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

    def test_postRead_formatUnknown(self):
        table = otTables.LigatureSubst()
        table.Format = 987
        rawTable = {"Coverage": makeCoverage(["f"])}
        self.assertRaises(AssertionError, table.postRead, rawTable, self.font)

    def test_preWrite_format1(self):
        table = otTables.LigatureSubst()
        table.ligatures = {
            "c": self.makeLigatures("ct"),
            "f": self.makeLigatures("ffi ff fi")
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

    def test_toXML2(self):
        writer = XMLWriter(StringIO())
        table = otTables.LigatureSubst()
        table.ligatures = {
            "c": self.makeLigatures("ct"),
            "f": self.makeLigatures("ffi ff fi")
        }
        table.toXML2(writer, self.font)
        self.assertEqual(writer.file.getvalue().splitlines()[1:], [
            '<LigatureSet glyph="c">',
            '  <Ligature components="c,t" glyph="c_t"/>',
            '</LigatureSet>',
            '<LigatureSet glyph="f">',
            '  <Ligature components="f,f,i" glyph="f_f_i"/>',
            '  <Ligature components="f,f" glyph="f_f"/>',
            '  <Ligature components="f,i" glyph="f_i"/>',
            '</LigatureSet>'
        ])

    def test_fromXML(self):
        table = otTables.LigatureSubst()
        for name, attrs, content in parseXML(
                '<LigatureSet glyph="f">'
                '  <Ligature components="f,f,i" glyph="f_f_i"/>'
                '  <Ligature components="f,f" glyph="f_f"/>'
                '</LigatureSet>'):
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
                self.makeAlternateSet("G.alt1 G.alt2"),
                self.makeAlternateSet("Z.fina")
            ]
        }
        table.postRead(rawTable, self.font)
        self.assertEqual(table.alternates, {
            "G": ["G.alt1", "G.alt2"],
            "Z": ["Z.fina"]
        })

    def test_postRead_formatUnknown(self):
        table = otTables.AlternateSubst()
        table.Format = 987
        self.assertRaises(AssertionError, table.postRead, {}, self.font)

    def test_preWrite_format1(self):
        table = otTables.AlternateSubst()
        table.alternates = {"G": ["G.alt1", "G.alt2"], "Z": ["Z.fina"]}
        rawTable = table.preWrite(self.font)
        self.assertEqual(table.Format, 1)
        self.assertEqual(rawTable["Coverage"].glyphs, ["G", "Z"])
        [g, z] = rawTable["AlternateSet"]
        self.assertIsInstance(g, otTables.AlternateSet)
        self.assertEqual(g.Alternate, ["G.alt1", "G.alt2"])
        self.assertIsInstance(z, otTables.AlternateSet)
        self.assertEqual(z.Alternate, ["Z.fina"])

    def test_toXML2(self):
        writer = XMLWriter(StringIO())
        table = otTables.AlternateSubst()
        table.alternates = {"G": ["G.alt1", "G.alt2"], "Z": ["Z.fina"]}
        table.toXML2(writer, self.font)
        self.assertEqual(writer.file.getvalue().splitlines()[1:], [
            '<AlternateSet glyph="G">',
            '  <Alternate glyph="G.alt1"/>',
            '  <Alternate glyph="G.alt2"/>',
            '</AlternateSet>',
            '<AlternateSet glyph="Z">',
            '  <Alternate glyph="Z.fina"/>',
            '</AlternateSet>'
        ])

    def test_fromXML(self):
        table = otTables.AlternateSubst()
        for name, attrs, content in parseXML(
                '<AlternateSet glyph="G">'
                '  <Alternate glyph="G.alt1"/>'
                '  <Alternate glyph="G.alt2"/>'
                '</AlternateSet>'
                '<AlternateSet glyph="Z">'
                '  <Alternate glyph="Z.fina"/>'
                '</AlternateSet>'):
            table.fromXML(name, attrs, content, self.font)
        self.assertEqual(table.alternates, {
            "G": ["G.alt1", "G.alt2"],
            "Z": ["Z.fina"]
        })


if __name__ == "__main__":
    unittest.main()
