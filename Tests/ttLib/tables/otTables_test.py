from fontTools.misc.testTools import getXML, parseXML, parseXmlInto, FakeFont
from fontTools.misc.textTools import deHexStr, hexStr
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.ttLib.tables.otBase import CountReference, OTTableReader, OTTableWriter
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.beyond64k import upper_tables
import fontTools.ttLib.tables.otTables as otTables
from io import StringIO
from types import SimpleNamespace
from textwrap import dedent
import unittest

import pytest


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
        self.assertEqual(compileTable(table, self.font), "0003010000000002000001000002")

    def test_preWrite_format3_large_classes(self):
        font = FakeFont(["a", "b"])
        table = otTables.ClassDef()
        table.classDefs = {"a": 0x10000, "b": 0xFFFFFF}
        rawTable = table.preWrite(font)
        self.assertEqual(table.Format, 3)
        self.assertEqual(rawTable["ClassValueArray"], [0x10000, 0xFFFFFF])
        self.assertEqual(compileTable(table, font), "0003000000000002010000ffffff")

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


def test_VarIdxMap_format0_roundtrip():
    # VarIdxMap is the HVAR/VVAR glyph-indexed delta-set index map; it shares the
    # format-switching DeltaSetIndexMap wire format (Format 0 here).
    font = FakeFont([".notdef", "a", "b", "c"])
    table = otTables.VarIdxMap()
    table.mapping = {".notdef": 0, "a": 1, "b": 0, "c": 0}
    data = compileTable(table, font)
    assert data[:2] == "00"  # Format 0 (uint8)
    table2 = decompileTable(otTables.VarIdxMap(), data, font)
    assert table2.mapping == {".notdef": 0, "a": 1, "b": 0, "c": 0}
    # Format is derived in preWrite; it is not retained after decompile, so it is
    # not emitted to TTX (matching Coverage/ClassDef).
    assert not hasattr(table2, "Format")


def test_FeatureVariations_version_1_1_roundtrip():
    condition = otTables.ConditionTable()
    condition.Format = 1
    condition.AxisIndex = 1
    condition.FilterRangeMinValue = -0.5
    condition.FilterRangeMaxValue = 0.75

    lookupIndices = otTables.LookupIndexList()
    lookupIndices.LookupIndex = [3, 5]
    lookupIndices.LookupIndexCount = len(lookupIndices.LookupIndex)

    lookupCondition = otTables.LookupConditionRecord()
    lookupCondition.ConditionTable = condition
    lookupCondition.LookupIndexList = lookupIndices

    featureLookups = otTables.FeatureLookupsTable()
    featureLookups.Version = 0x00010000
    featureLookups.Flags = 1
    featureLookups.LookupConditionRecord = [lookupCondition]
    featureLookups.LookupConditionCount = len(featureLookups.LookupConditionRecord)

    lookupVariation = otTables.LookupVariationRecord()
    lookupVariation.FeatureIndex = 2
    lookupVariation.FeatureLookupsTable = featureLookups

    table = otTables.FeatureVariations()
    table.Version = 0x00010001
    table.FeatureVariationRecord = []
    table.FeatureVariationCount = 0
    table.LookupVariationRecord = [lookupVariation]
    table.LookupVariationCount = len(table.LookupVariationRecord)

    data = compileTable(table, FakeFont([]))
    assert data == (
        "000100010000000000000001000200000012"
        "00010000000100000001000000120000001a"
        "00010001e0003000000200030005"
    )

    roundtripped = decompileTable(otTables.FeatureVariations(), data, FakeFont([]))
    assert roundtripped.Version == 0x00010001
    assert roundtripped.FeatureVariationCount == 0
    assert roundtripped.LookupVariationCount == 1
    record = roundtripped.LookupVariationRecord[0]
    assert record.FeatureIndex == 2
    assert record.FeatureLookupsTable.Flags == 1
    lookupCondition = record.FeatureLookupsTable.LookupConditionRecord[0]
    assert lookupCondition.ConditionTable.AxisIndex == 1
    assert lookupCondition.ConditionTable.FilterRangeMinValue == -0.5
    assert lookupCondition.ConditionTable.FilterRangeMaxValue == 0.75
    assert lookupCondition.LookupIndexList.LookupIndex == [3, 5]


def test_VarIdxMap_format1_beyond_64k():
    # 65537 glyphs; only the highest (gid 0x10000 > 0xFFFF) varies, so the map
    # cannot be trimmed below 65536 entries and must use Format 1.
    glyphs = [".notdef"] + ["g%05d" % i for i in range(1, 0x10001)]
    font = FakeFont(glyphs)
    table = otTables.VarIdxMap()
    table.mapping = {g: 0 for g in glyphs}
    table.mapping[glyphs[-1]] = 1
    data = compileTable(table, font)
    assert data[:2] == "01"  # Format 1 (uint8)
    assert data[4:12] == "00010001"  # uint32 MappingCount = 0x10001
    table2 = decompileTable(otTables.VarIdxMap(), data, font)
    assert table2.mapping[glyphs[-1]] == 1
    assert table2.mapping[glyphs[0]] == 0
    assert not hasattr(table2, "Format")


def _feature_variations_table(
    font, table_tag, features, substitutions, *, extended=False
):
    font.setGlyphOrder([".notdef", "a", "b"])
    if table_tag == "GSUB":
        lookup = '<SingleSubst><Substitution in="a" out="b"/></SingleSubst>'
    else:
        lookup = (
            '<SinglePos Format="1"><Coverage><Glyph value="a"/></Coverage>'
            '<ValueFormat value="1"/><Value XPlacement="10"/></SinglePos>'
        )
    lookups = "".join(
        f'<Lookup index="{i}"><LookupType value="1"/><LookupFlag value="0"/>'
        f"{lookup}</Lookup>"
        for i in range(2)
    )
    feature_records = "".join(
        f'<FeatureRecord index="{i}"><FeatureTag value="{tag}"/>'
        '<Feature><LookupListIndex index="0" value="0"/></Feature></FeatureRecord>'
        for i, tag in enumerate(features)
    )
    substitution_records = "".join(
        f'<SubstitutionRecord index="{i}"><FeatureIndex value="{index}"/>'
        f'<Feature>{params}<LookupListIndex index="0" value="1"/></Feature>'
        "</SubstitutionRecord>"
        for i, (index, params) in enumerate(substitutions)
    )
    table = newTable(table_tag)
    table.table = parseXmlInto(
        font,
        getattr(otTables, table_tag)(),
        f'<Version value="0x00010001"/><ScriptList/><LookupList>{lookups}</LookupList>'
        f"<FeatureList>{feature_records}</FeatureList>"
        '<FeatureVariations><Version value="0x00010000"/>'
        '<FeatureVariationRecord index="0"><ConditionSet/>'
        '<FeatureTableSubstitution><Version value="0x00010000"/>'
        f"{substitution_records}</FeatureTableSubstitution>"
        "</FeatureVariationRecord></FeatureVariations>",
    )
    if extended:
        font[table_tag] = table
        upper_tables(font, tables=[table_tag], validate=False)
    return table


FEATURE_PARAMS = [
    ("kern", "", None),
    (
        "size",
        '<FeatureParamsSize><DesignSize value="12.0"/><SubfamilyID value="1"/>'
        '<SubfamilyNameID value="256"/><RangeStart value="10.0"/>'
        '<RangeEnd value="14.0"/></FeatureParamsSize>',
        otTables.FeatureParamsSize,
    ),
    (
        "ss02",
        '<FeatureParamsStylisticSet><Version value="0"/>'
        '<UINameID value="270"/></FeatureParamsStylisticSet>',
        otTables.FeatureParamsStylisticSet,
    ),
    (
        "cv01",
        '<FeatureParamsCharacterVariants><Format value="0"/>'
        '<FeatUILabelNameID value="256"/><FeatUITooltipTextNameID value="257"/>'
        '<SampleTextNameID value="258"/><NumNamedParameters value="2"/>'
        '<FirstParamUILabelNameID value="259"/>'
        '<Character index="0" value="0x0041"/>'
        '<Character index="1" value="0x10000"/></FeatureParamsCharacterVariants>',
        otTables.FeatureParamsCharacterVariants,
    ),
]


@pytest.mark.parametrize("table_tag", ["GSUB", "GPOS"])
@pytest.mark.parametrize("lazy", [False, True])
@pytest.mark.parametrize("extended", [False, True])
@pytest.mark.parametrize("feature_count", [1, 10])
@pytest.mark.parametrize(
    "feature_tag,params,param_class", FEATURE_PARAMS, ids=[c[0] for c in FEATURE_PARAMS]
)
def test_feature_variations_params_roundtrip(
    table_tag, lazy, extended, feature_count, feature_tag, params, param_class
):
    font = TTFont(lazy=lazy)
    # Unrelated features precede the referenced feature, including a lazy array.
    features = ["aalt"] * (feature_count - 1) + [feature_tag]
    table = _feature_variations_table(
        font, table_tag, features, [(feature_count - 1, params)], extended=extended
    )
    data = table.compile(font)
    rebuilt = newTable(table_tag)
    rebuilt.decompile(data, font)
    variation = rebuilt.table.FeatureVariations.FeatureVariationRecord[0]
    record = variation.FeatureTableSubstitution.SubstitutionRecord[0]
    assert record.FeatureIndex == feature_count - 1
    assert record.Feature.LookupListIndex == [1]
    feature_list = rebuilt.table.FeatureList2 if extended else rebuilt.table.FeatureList
    assert feature_list.FeatureRecord[-1].Feature.LookupListIndex == [0]
    actual = record.Feature.FeatureParams
    assert type(actual) is (param_class or type(None))
    expected = table.table.FeatureVariations.FeatureVariationRecord[0]
    expected = expected.FeatureTableSubstitution.SubstitutionRecord[
        0
    ].Feature.FeatureParams
    if actual is not None:
        assert getXML(actual.toXML, font) == getXML(expected.toXML, font)
    xml_roundtrip = newTable(table_tag)
    xml_roundtrip.table = parseXmlInto(
        font,
        getattr(otTables, table_tag)(),
        "\n".join(getXML(rebuilt.table.toXML, font)[1:-1]),
    )
    assert xml_roundtrip.compile(font) == data


@pytest.mark.parametrize("table_tag", ["GSUB", "GPOS"])
@pytest.mark.parametrize("lazy", [False, True])
@pytest.mark.parametrize("extended", [False, True])
def test_feature_variations_params_mixed_tags(table_tag, lazy, extended):
    font = TTFont(lazy=lazy)
    cases = sorted(FEATURE_PARAMS * 3, key=lambda case: case[0])
    features = ["aalt"] * 8 + [tag for tag, _, _ in cases]
    table = _feature_variations_table(
        font,
        table_tag,
        features,
        [(8 + i, params) for i, (_, params, _) in enumerate(cases)],
        extended=extended,
    )
    data = table.compile(font)
    rebuilt = newTable(table_tag)
    rebuilt.decompile(data, font)
    records = rebuilt.table.FeatureVariations.FeatureVariationRecord[0]
    records = records.FeatureTableSubstitution.SubstitutionRecord
    # Access in reverse order; tags must not depend on the previous lazy read.
    for i in reversed(range(len(cases))):
        record = records[i]
        assert record.FeatureIndex == 8 + i
        assert type(record.Feature.FeatureParams) is (cases[i][2] or type(None))
        if record.Feature.FeatureParams is not None:
            expected = table.table.FeatureVariations.FeatureVariationRecord[0]
            expected = expected.FeatureTableSubstitution.SubstitutionRecord[
                i
            ].Feature.FeatureParams
            assert getXML(record.Feature.FeatureParams.toXML, font) == getXML(
                expected.toXML, font
            )
    assert rebuilt.compile(font) == data


@pytest.mark.parametrize("table_tag", ["GSUB", "GPOS"])
@pytest.mark.parametrize("extended", [False, True])
def test_feature_variations_params_wrong_type(table_tag, extended):
    font = TTFont()
    table = _feature_variations_table(
        font, table_tag, ["cv01"], [(0, FEATURE_PARAMS[2][1])], extended=extended
    )
    with pytest.raises(
        AssertionError, match="Wrong FeatureParams type for feature 'cv01'"
    ):
        table.compile(font)


@pytest.mark.parametrize("table_tag", ["GSUB", "GPOS"])
@pytest.mark.parametrize("extended", [False, True])
def test_feature_variations_params_after_feature_list_mutation(table_tag, extended):
    font = TTFont(lazy=True)
    table = _feature_variations_table(
        font,
        table_tag,
        ["aalt", "ss02"],
        [(1, FEATURE_PARAMS[2][1])],
        extended=extended,
    )
    data = table.compile(font)
    rebuilt = newTable(table_tag)
    rebuilt.decompile(data, font)
    # Subsetting edits FeatureList before it decompiles/remaps FeatureVariations.
    feature_list = rebuilt.table.FeatureList2 if extended else rebuilt.table.FeatureList
    feature_list.FeatureRecord.pop(0)
    record = rebuilt.table.FeatureVariations.FeatureVariationRecord[0]
    record = record.FeatureTableSubstitution.SubstitutionRecord[0]
    assert record.FeatureIndex == 1
    assert type(record.Feature.FeatureParams) is otTables.FeatureParamsStylisticSet
    assert record.Feature.FeatureParams.UINameID == 270
    record.FeatureIndex = 0
    assert rebuilt.compile(font)


@pytest.mark.parametrize("table_tag", ["GSUB", "GPOS"])
@pytest.mark.parametrize(
    "version,has_variations",
    [(0x00010000, False), (0x00010001, False), (0x00010001, True)],
)
def test_empty_feature_list_compile(table_tag, version, has_variations):
    font = TTFont()
    font.setGlyphOrder([".notdef"])
    table = newTable(table_tag)
    table.table = getattr(otTables, table_tag)()
    table.table.Version = version
    table.table.ScriptList = otTables.ScriptList()
    table.table.FeatureList = otTables.FeatureList()
    table.table.LookupList = otTables.LookupList()
    # Missing repeated fields compile as empty arrays without populateDefaults.
    if has_variations:
        table.table.FeatureVariations = otTables.FeatureVariations()
        table.table.FeatureVariations.Version = 0x00010000
    data = table.compile(font)
    rebuilt = newTable(table_tag)
    rebuilt.decompile(data, font)
    assert rebuilt.table.FeatureList.FeatureCount == 0
    assert rebuilt.table.FeatureList.FeatureRecord == []
    if has_variations:
        assert rebuilt.table.FeatureVariations.FeatureVariationRecord == []


@pytest.mark.parametrize("table_tag", ["GSUB", "GPOS"])
@pytest.mark.parametrize("version", [0x00010000, 0x00010001, 0x00010002])
@pytest.mark.parametrize("feature_count", [0, 10])
def test_feature_list_stays_lazy_without_variations(table_tag, version, feature_count):
    font = TTFont(lazy=True)
    table = _feature_variations_table(
        font, table_tag, ["aalt"] * feature_count, [], extended=version >= 0x00010002
    )
    table.table.Version = version
    table.table.FeatureVariations = None
    data = table.compile(font)
    rebuilt = newTable(table_tag)
    rebuilt.decompile(data, font)
    feature_list = (
        rebuilt.table.FeatureList2
        if version >= 0x00010002
        else rebuilt.table.FeatureList
    )
    assert "reader" in feature_list.__dict__
    assert "FeatureRecord" not in feature_list.__dict__
    assert feature_list.FeatureCount == feature_count


def test_feature_variations_params_null_offset():
    converter = otTables.FeatureTableSubstitutionRecord().getConverterByName("Feature")
    font = TTFont()
    # Null offsets don't require a referenced FeatureRecord or tag context.
    record = {"FeatureIndex": 0xFFFF}
    assert converter.read(OTTableReader(b"\0\0\0\0"), font, record) is None
    writer = OTTableWriter()
    converter.write(writer, font, record, None)
    assert writer.getAllData() == b"\0\0\0\0"


@pytest.mark.parametrize("operation", ["read", "write"])
def test_feature_variations_params_without_context(operation):
    # A standalone record without parameters does not need a FeatureList.
    data = deHexStr("0000 00000006 0000 0000")
    font = TTFont()
    record = otTables.FeatureTableSubstitutionRecord()
    if operation == "read":
        record.decompile(OTTableReader(data), font)
        assert record.FeatureIndex == 0
        assert record.Feature.FeatureParams is None
        assert record.Feature.LookupListIndex == []
    else:
        record.FeatureIndex = 0
        record.Feature = otTables.Feature()
        record.Feature.FeatureParams = None
        record.Feature.LookupListIndex = []
        writer = OTTableWriter()
        record.compile(writer, font)
        assert writer.getAllData() == data


@pytest.mark.parametrize("table_tag", ["GSUB", "GPOS"])
@pytest.mark.parametrize("lazy", [False, True])
@pytest.mark.parametrize("extended", [False, True])
def test_feature_variations_params_decompile(table_tag, lazy, extended):
    # Independently encoded layout table: ss02 FeatureParams is in an alternate
    # Feature table only. A compiler regression must not mask a reader regression.
    header = (
        "00010002 0000 0000 0000 0000002a 0000001a 0000001c 00000028"
        if extended
        else "00010001 000e 0010 001c 0000001e"
    )
    data = deHexStr(
        header + "0000"  # ScriptList
        "0001 73733032 0008 0000 0000"  # FeatureList + ss02 Feature
        "0000"  # LookupList
        "00010000 00000001 00000010 00000012"  # FeatureVariations + record
        "0000"  # ConditionSet
        "00010000 0001 0000 0000000c"  # FeatureTableSubstitution + record
        "0004 0000 0000 010e"  # alternate Feature + ss02 Version/UINameID
    )
    font = TTFont(lazy=lazy)
    table = newTable(table_tag)
    table.decompile(data, font)
    record = table.table.FeatureVariations.FeatureVariationRecord[0]
    params = record.FeatureTableSubstitution.SubstitutionRecord[0].Feature.FeatureParams
    assert isinstance(params, otTables.FeatureParamsStylisticSet)
    assert params.Version == 0
    assert params.UINameID == 270


@pytest.mark.parametrize("table_tag", ["GSUB", "GPOS"])
@pytest.mark.parametrize("lazy", [False, True])
@pytest.mark.parametrize("feature_index", [1, 0xFFFF])
def test_feature_variations_out_of_range_index_decompile(
    table_tag, lazy, feature_index
):
    # Encode this independently so a compiler failure cannot mask a reader failure.
    data = deHexStr(
        "00010001 000e 0010 001c 0000001e"  # layout header
        "0000"  # ScriptList
        "0001 73733032 0008 0000 0000"  # FeatureList + ss02 Feature
        "0000"  # LookupList
        "00010000 00000001 00000010 00000012"  # FeatureVariations + record
        "0000"  # ConditionSet
        f"00010000 0001 {feature_index:04x} 0000000c"  # substitution + record
        "0000 0000"  # alternate Feature without parameters or lookups
    )
    font = TTFont(lazy=lazy)
    table = newTable(table_tag)
    table.decompile(data, font)
    record = table.table.FeatureVariations.FeatureVariationRecord[0]
    record = record.FeatureTableSubstitution.SubstitutionRecord[0]
    assert record.FeatureIndex == feature_index
    assert record.Feature.FeatureParams is None
    assert record.Feature.LookupListIndex == []


@pytest.mark.parametrize("table_tag", ["GSUB", "GPOS"])
@pytest.mark.parametrize("features", [[], ["ss02"]], ids=["empty", "one-feature"])
@pytest.mark.parametrize("max_index", [False, True], ids=["past-end", "max-index"])
@pytest.mark.parametrize("omit_params", [False, True])
def test_feature_variations_out_of_range_index_compile(
    table_tag, features, max_index, omit_params
):
    font = TTFont()
    feature_index = 0xFFFF if max_index else len(features)
    table = _feature_variations_table(font, table_tag, features, [(feature_index, "")])
    if omit_params:
        record = table.table.FeatureVariations.FeatureVariationRecord[0]
        del record.FeatureTableSubstitution.SubstitutionRecord[0].Feature.FeatureParams
    data = table.compile(font)
    rebuilt = newTable(table_tag)
    rebuilt.decompile(data, font)
    record = rebuilt.table.FeatureVariations.FeatureVariationRecord[0]
    record = record.FeatureTableSubstitution.SubstitutionRecord[0]
    assert record.FeatureIndex == feature_index
    assert record.Feature.FeatureParams is None
    assert record.Feature.LookupListIndex == [1]
    xml_roundtrip = newTable(table_tag)
    xml_roundtrip.table = parseXmlInto(
        font,
        getattr(otTables, table_tag)(),
        "\n".join(getXML(rebuilt.table.toXML, font)[1:-1]),
    )
    assert xml_roundtrip.compile(font) == data


@pytest.mark.parametrize("scale_x", [-0.5, 0, 0.5, 1, 2])
@pytest.mark.parametrize("scale_y", [None, 0.25, 1])
def test_var_component_xml_scale_y(scale_x, scale_y):
    font = TTFont()
    font.setGlyphOrder([".notdef", "a"])
    xml = f'<glyphName value="a"/><scaleX value="{scale_x}"/>'
    if scale_y is not None:
        xml += f'<scaleY value="{scale_y}"/>'
    component = otTables.VarComponent()
    component.fromXML("VarComponent", {}, list(parseXML(xml)), font)

    assert component.transform.scaleX == scale_x
    assert component.transform.scaleY == (scale_x if scale_y is None else scale_y)
    assert bool(component.flags & otTables.VarComponentFlags.HAVE_SCALE_Y) == (
        scale_y is not None
    )

    roundtripped = otTables.VarComponent()
    assert roundtripped.decompile(component.compile(font), font, {}) == b""
    assert roundtripped.transform == component.transform


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
            "00020000000c00000100001400030000010100000002010001020000",
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
            "00020000000c00000100001400030000010100000002010001020000",
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
            "00020000001900000100000c000100000502000000020100010003000001010000",
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
            "00020000001900000100000c000100000502000000020100010003000001010000",
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
            "00020000001400000100000c00020100010200000003000001010000",
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
            "00020000001400000100000c00020100010200000003000001010000",
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


def test_fixLookupOverFlows_promotes_lookup_to_extension():
    from fontTools.ttLib.tables.otBase import OverflowErrorRecord

    font = FakeFont([".notdef"])
    gsub = font["GSUB"] = SimpleNamespace(table=otTables.GSUB())
    gsub.table.LookupList = otTables.LookupList()
    lookup = otTables.Lookup()
    lookup.LookupType = otTables.SingleSubst.LookupType
    subTable = otTables.SingleSubst()
    lookup.SubTable = [subTable]
    gsub.table.LookupList.Lookup = [lookup]

    ok = otTables.fixLookupOverFlows(
        font, OverflowErrorRecord(("GSUB", 0, 0, None, None))
    )

    assert ok
    assert lookup.LookupType == otTables.ExtensionSubst.LookupType
    assert isinstance(lookup.SubTable[0], otTables.ExtensionSubst)
    assert lookup.SubTable[0].ExtSubTable is subTable


def test_fixLookupOverFlows_returns_false_without_progress():
    from fontTools.ttLib.tables.otBase import OverflowErrorRecord

    font = FakeFont([".notdef"])
    gsub = font["GSUB"] = SimpleNamespace(table=otTables.GSUB())
    gsub.table.LookupList = otTables.LookupList()
    lookup = otTables.Lookup()
    lookup.LookupType = otTables.ExtensionSubst.LookupType
    lookup.SubTable = [otTables.SingleSubst()]
    gsub.table.LookupList.Lookup = [lookup]

    ok = otTables.fixLookupOverFlows(
        font, OverflowErrorRecord(("GSUB", 0, 0, None, None))
    )

    assert not ok
    assert lookup.SubTable[0].__class__ is otTables.SingleSubst


def _allExtensionGPOS(numLookups=2):
    font = FakeFont([".notdef"])
    gpos = font["GPOS"] = SimpleNamespace(table=otTables.GPOS())
    gpos.table.LookupList = otTables.LookupList()
    lookups = []
    for _ in range(numLookups):
        ext = otTables.ExtensionPos()
        ext.Format = 1
        ext.ExtSubTable = otTables.SinglePos()
        lookup = otTables.Lookup()
        lookup.LookupType = otTables.ExtensionPos.LookupType
        lookup.SubTable = [ext]
        lookups.append(lookup)
    gpos.table.LookupList.Lookup = lookups
    return font


@pytest.mark.parametrize("have_uharfbuzz", [False, True])
def test_fixLookupOverFlows_all_extension_logs_error(
    caplog, monkeypatch, have_uharfbuzz
):
    import logging

    from fontTools.ttLib.tables.otBase import OverflowErrorRecord

    # A LookupList -> Lookup offset overflow (SubTableIndex is None) where every
    # lookup is already an Extension lookup: there is nothing left to promote, so
    # recovery must fail with an actionable error rather than silently giving up.
    # The "install uharfbuzz" hint only makes sense when it isn't installed.
    font = _allExtensionGPOS()
    monkeypatch.setattr(otTables, "have_uharfbuzz", have_uharfbuzz)

    with caplog.at_level(logging.ERROR, logger="fontTools.ttLib.tables.otTables"):
        ok = otTables.fixLookupOverFlows(
            font, OverflowErrorRecord(("GPOS", 1, None, None, None))
        )

    assert not ok
    [message] = [record.message for record in caplog.records]
    assert "already Extension" in message
    assert ("install uharfbuzz" in message) is not have_uharfbuzz


def test_fixLookupOverFlows_subtable_overflow_does_not_log_lookuplist_message(caplog):
    import logging

    from fontTools.ttLib.tables.otBase import OverflowErrorRecord

    # fixLookupOverFlows is also the fallback for subtable offset overflows
    # (SubTableIndex is not None); the "LookupList offset overflowed" message
    # would be misleading there, so it must not be emitted.
    font = _allExtensionGPOS()

    with caplog.at_level(logging.ERROR, logger="fontTools.ttLib.tables.otTables"):
        ok = otTables.fixLookupOverFlows(
            font, OverflowErrorRecord(("GPOS", 1, 0, None, None))
        )

    assert not ok
    assert not any(
        "LookupList offset overflowed" in record.message for record in caplog.records
    )


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


def test_splitSinglePos():
    from fontTools.otlLib.builder import buildSinglePosSubtable, buildValue

    mapping = {
        "a": buildValue({"XPlacement": -10}),
        "b": buildValue({"XPlacement": -20}),
        "c": buildValue({"XPlacement": -30}),
    }
    glyphMap = {g: i for i, g in enumerate(["a", "b", "c"])}

    oldSubTable = buildSinglePosSubtable(mapping, glyphMap)
    assert oldSubTable.Format == 2
    newSubTable = otTables.SinglePos()

    ok = otTables.splitSinglePos(oldSubTable, newSubTable, overflowRecord=None)
    assert ok

    assert oldSubTable.Coverage.glyphs == ["a"]
    assert [v.XPlacement for v in oldSubTable.Value] == [-10]
    assert oldSubTable.ValueCount == 1

    assert newSubTable.Format == 2
    assert newSubTable.Coverage.glyphs == ["b", "c"]
    assert [v.XPlacement for v in newSubTable.Value] == [-20, -30]
    assert newSubTable.ValueCount == 2


def test_splitSinglePos_format1():
    # Format 1 has a single shared Value with nothing to split.
    subTable = otTables.SinglePos()
    subTable.Format = 1
    subTable.Coverage = otTables.Coverage()
    subTable.Coverage.glyphs = ["a", "b"]
    assert not otTables.splitSinglePos(subTable, otTables.SinglePos(), None)


def test_splitSinglePos_overflow_end_to_end():
    # A SinglePos Format 2 whose ValueArray pushes its own Coverage offset past
    # uint16 must be split when packing. With ValueFormat=1 (2 bytes per Value)
    # the Coverage offset is ~8 + 2*N bytes, so it overflows above ~32763 glyphs.
    # https://github.com/fonttools/fonttools/issues/4091
    from fontTools.ttLib import TTFont, getTableClass

    N = 40000
    glyphs = [f"g{i}" for i in range(N)]
    font = TTFont()
    font.setGlyphOrder([".notdef"] + glyphs)
    # exercise the pure-fontTools overflow recovery, not the harfbuzz repacker
    font.cfg["fontTools.ttLib.tables.otBase:USE_HARFBUZZ_REPACKER"] = False

    subTable = otTables.SinglePos()
    subTable.Format = 2
    subTable.Coverage = otTables.Coverage()
    subTable.Coverage.glyphs = list(glyphs)
    subTable.ValueFormat = 0x0001  # XPlacement
    subTable.Value = []
    for i in range(N):
        value = otTables.ValueRecord()
        value.XPlacement = -(i % 100 + 1)
        subTable.Value.append(value)

    lookup = otTables.Lookup()
    lookup.LookupType = 1
    lookup.LookupFlag = 0
    lookup.SubTable = [subTable]

    feature = otTables.Feature()
    feature.FeatureParams = None
    feature.LookupListIndex = [0]
    featureRecord = otTables.FeatureRecord()
    featureRecord.FeatureTag = "kern"
    featureRecord.Feature = feature
    langSys = otTables.DefaultLangSys()
    langSys.LookupOrder = None
    langSys.ReqFeatureIndex = 0xFFFF
    langSys.FeatureIndex = [0]
    script = otTables.Script()
    script.DefaultLangSys = langSys
    script.LangSysRecord = []
    scriptRecord = otTables.ScriptRecord()
    scriptRecord.ScriptTag = "DFLT"
    scriptRecord.Script = script

    gpos = otTables.GPOS()
    gpos.Version = 0x00010000
    gpos.ScriptList = otTables.ScriptList()
    gpos.ScriptList.ScriptRecord = [scriptRecord]
    gpos.FeatureList = otTables.FeatureList()
    gpos.FeatureList.FeatureRecord = [featureRecord]
    gpos.LookupList = otTables.LookupList()
    gpos.LookupList.Lookup = [lookup]

    table = getTableClass("GPOS")()
    table.table = gpos
    font["GPOS"] = table

    data = table.compile(font)

    rebuilt = getTableClass("GPOS")()
    rebuilt.decompile(data, font)
    subTables = rebuilt.table.LookupList.Lookup[0].SubTable
    assert len(subTables) > 1  # the oversized subtable was split
    coverage = [g for st in subTables for g in st.Coverage.glyphs]
    values = [v.XPlacement for st in subTables for v in st.Value]
    assert coverage == glyphs
    assert values == [-(i % 100 + 1) for i in range(N)]


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

    def testPaintGlyph2RoundTrip(self):
        font = SparseFakeFont({"high": 0x10000})
        paint = otTables.Paint()
        paint.Format = otTables.PaintFormat.PaintGlyph2
        paint.Glyph = "high"
        paint.Paint = otTables.Paint()
        paint.Paint.Format = otTables.PaintFormat.PaintSolid
        paint.Paint.PaletteIndex = 3
        paint.Paint.Alpha = 1.0

        data = "210000070100000200034000"
        self.assertEqual(compileTable(paint, font), data)

        rebuilt = decompileTable(otTables.Paint(), data, font)
        self.assertEqual(rebuilt.Format, otTables.PaintFormat.PaintGlyph2)
        self.assertEqual(rebuilt.Glyph, "high")
        self.assertEqual(rebuilt.Paint.Format, otTables.PaintFormat.PaintSolid)


def test_parse_Device_DeltaValue_from_XML_and_compile():
    # https://github.com/fonttools/fonttools/pull/3757
    font = FakeFont([".notdef", "five"])

    gpos_xml = dedent("""\
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
        </LookupList>""")

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
