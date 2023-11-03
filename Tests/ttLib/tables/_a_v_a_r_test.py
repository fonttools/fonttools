from fontTools.misc.testTools import parseXML
from fontTools.misc.textTools import deHexStr
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.misc.fixedTools import floatToFixed as fl2fi
from fontTools.ttLib import TTFont, TTLibError
import fontTools.ttLib.tables.otTables as otTables
from fontTools.ttLib.tables._a_v_a_r import table__a_v_a_r
from fontTools.ttLib.tables._f_v_a_r import table__f_v_a_r, Axis
import fontTools.varLib.models as models
import fontTools.varLib.varStore as varStore
from io import BytesIO
import unittest


TEST_DATA = deHexStr(
    "00 01 00 00 00 00 00 02 "
    "00 04 C0 00 C0 00 00 00 00 00 13 33 33 33 40 00 40 00 "
    "00 03 C0 00 C0 00 00 00 00 00 40 00 40 00"
)


class AxisVariationTableTest(unittest.TestCase):
    def assertAvarAlmostEqual(self, segments1, segments2):
        self.assertSetEqual(set(segments1.keys()), set(segments2.keys()))
        for axisTag, mapping1 in segments1.items():
            mapping2 = segments2[axisTag]
            self.assertEqual(len(mapping1), len(mapping2))
            for (k1, v1), (k2, v2) in zip(
                sorted(mapping1.items()), sorted(mapping2.items())
            ):
                self.assertAlmostEqual(k1, k2)
                self.assertAlmostEqual(v1, v2)

    def test_compile(self):
        avar = table__a_v_a_r()
        avar.segments["wdth"] = {-1.0: -1.0, 0.0: 0.0, 0.3: 0.8, 1.0: 1.0}
        avar.segments["wght"] = {-1.0: -1.0, 0.0: 0.0, 1.0: 1.0}
        self.assertEqual(TEST_DATA, avar.compile(self.makeFont(["wdth", "wght"])))

    def test_decompile(self):
        avar = table__a_v_a_r()
        avar.decompile(TEST_DATA, self.makeFont(["wdth", "wght"]))
        self.assertAvarAlmostEqual(
            {
                "wdth": {-1.0: -1.0, 0.0: 0.0, 0.2999878: 0.7999878, 1.0: 1.0},
                "wght": {-1.0: -1.0, 0.0: 0.0, 1.0: 1.0},
            },
            avar.segments,
        )

    def test_toXML(self):
        avar = table__a_v_a_r()
        avar.segments["opsz"] = {-1.0: -1.0, 0.0: 0.0, 0.2999878: 0.7999878, 1.0: 1.0}
        writer = XMLWriter(BytesIO())
        avar.toXML(writer, self.makeFont(["opsz"]))
        self.assertEqual(
            [
                '<version major="1" minor="0"/>',
                '<segment axis="opsz">',
                '<mapping from="-1.0" to="-1.0"/>',
                '<mapping from="0.0" to="0.0"/>',
                '<mapping from="0.3" to="0.8"/>',
                '<mapping from="1.0" to="1.0"/>',
                "</segment>",
            ],
            self.xml_lines(writer),
        )

    def test_fromXML(self):
        avar = table__a_v_a_r()
        for name, attrs, content in parseXML(
            '<segment axis="wdth">'
            '    <mapping from="-1.0" to="-1.0"/>'
            '    <mapping from="0.0" to="0.0"/>'
            '    <mapping from="0.7" to="0.2"/>'
            '    <mapping from="1.0" to="1.0"/>'
            "</segment>"
        ):
            avar.fromXML(name, attrs, content, ttFont=None)
        self.assertAvarAlmostEqual(
            {"wdth": {-1: -1, 0: 0, 0.7000122: 0.2000122, 1.0: 1.0}}, avar.segments
        )

    @staticmethod
    def makeFont(axisTags):
        """['opsz', 'wdth'] --> ttFont"""
        fvar = table__f_v_a_r()
        for tag in axisTags:
            axis = Axis()
            axis.axisTag = tag
            fvar.axes.append(axis)
        font = TTFont()
        font["fvar"] = fvar
        return font

    @staticmethod
    def xml_lines(writer):
        content = writer.file.getvalue().decode("utf-8")
        return [line.strip() for line in content.splitlines()][1:]


class Avar2Test(unittest.TestCase):
    def test(self):
        axisTags = ["wght", "wdth"]
        fvar = table__f_v_a_r()
        for tag in axisTags:
            axis = Axis()
            axis.axisTag = tag
            fvar.axes.append(axis)

        master_locations_normalized = [
            {},
            {"wght": 1, "wdth": -1},
        ]
        data = [
            {},
            {"wdth": -0.8},
        ]

        model = models.VariationModel(master_locations_normalized, axisTags)
        store_builder = varStore.OnlineVarStoreBuilder(axisTags)
        store_builder.setModel(model)
        varIdxes = {}
        for axis in axisTags:
            masters = [fl2fi(m.get(axis, 0), 14) for m in data]
            varIdxes[axis] = store_builder.storeMasters(masters)[1]
        store = store_builder.finish()
        mapping = store.optimize()
        varIdxes = {axis: mapping[value] for axis, value in varIdxes.items()}
        del model, store_builder, mapping

        varIdxMap = otTables.DeltaSetIndexMap()
        varIdxMap.Format = 1
        varIdxMap.mapping = []
        for tag in axisTags:
            varIdxMap.mapping.append(varIdxes[tag])

        avar = table__a_v_a_r()
        avar.segments["wght"] = {}
        avar.segments["wdth"] = {-1.0: -1.0, 0.0: 0.0, 0.4: 0.5, 1.0: 1.0}

        avar.majorVersion = 2
        avar.table = otTables.avar()
        avar.table.VarIdxMap = varIdxMap
        avar.table.VarStore = store

        font = TTFont()
        font["fvar"] = fvar
        font["avar"] = avar

        b = BytesIO()
        font.save(b)
        b.seek(0)
        font2 = TTFont(b)

        assert font2["avar"].table.VarStore.VarRegionList.RegionAxisCount == 2
        assert font2["avar"].table.VarStore.VarRegionList.RegionCount == 1

        xml1 = BytesIO()
        writer = XMLWriter(xml1)
        font["avar"].toXML(writer, font)

        xml2 = BytesIO()
        writer = XMLWriter(xml2)
        font2["avar"].toXML(writer, font2)

        assert xml1.getvalue() == xml2.getvalue(), (xml1.getvalue(), xml2.getvalue())

        avar = table__a_v_a_r()
        xml = b"".join(xml2.getvalue().splitlines()[1:])
        for name, attrs, content in parseXML(xml):
            avar.fromXML(name, attrs, content, ttFont=TTFont())
        assert avar.table.VarStore.VarRegionList.RegionAxisCount == 2
        assert avar.table.VarStore.VarRegionList.RegionCount == 1


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
