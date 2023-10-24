import pytest
from io import StringIO
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.misc.roundTools import noRound
from fontTools.varLib.models import VariationModel
from fontTools.varLib.varStore import OnlineVarStoreBuilder, VarStoreInstancer
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.ttLib.tables.otBase import OTTableReader, OTTableWriter
from fontTools.ttLib.tables.otTables import VarStore


@pytest.mark.parametrize(
    "locations, masterValues",
    [
        (
            [{}, {"a": 1}],
            [
                [10, 10],  # Test NO_VARIATION_INDEX
                [100, 2000],
                [100, 22000],
            ],
        ),
        (
            [{}, {"a": 1}, {"b": 1}, {"a": 1, "b": 1}],
            [
                [10, 20, 40, 60],
                [100, 2000, 400, 6000],
                [7100, 22000, 4000, 30000],
            ],
        ),
        (
            [{}, {"a": 1}],
            [
                [10, 20],
                [42000, 100],
                [100, 52000],
            ],
        ),
        (
            [{}, {"a": 1}, {"b": 1}, {"a": 1, "b": 1}],
            [
                [10, 20, 40, 60],
                [40000, 42000, 400, 6000],
                [100, 22000, 4000, 173000],
            ],
        ),
    ],
)
def test_onlineVarStoreBuilder(locations, masterValues):
    axisTags = sorted({k for loc in locations for k in loc})
    model = VariationModel(locations)
    builder = OnlineVarStoreBuilder(axisTags)
    builder.setModel(model)
    varIdxs = []
    for masters in masterValues:
        _, varIdx = builder.storeMasters(masters)
        varIdxs.append(varIdx)

    varStore = builder.finish()
    mapping = varStore.optimize()
    varIdxs = [mapping[varIdx] for varIdx in varIdxs]

    dummyFont = TTFont()
    writer = OTTableWriter()
    varStore.compile(writer, dummyFont)
    data = writer.getAllData()
    reader = OTTableReader(data)
    varStore = VarStore()
    varStore.decompile(reader, dummyFont)

    fvarAxes = [buildAxis(axisTag) for axisTag in axisTags]
    instancer = VarStoreInstancer(varStore, fvarAxes)
    for masters, varIdx in zip(masterValues, varIdxs):
        base, *rest = masters
        for expectedValue, loc in zip(masters, locations):
            instancer.setLocation(loc)
            value = base + instancer[varIdx]
            assert expectedValue == value


def buildAxis(axisTag):
    axis = Axis()
    axis.axisTag = axisTag
    return axis


@pytest.mark.parametrize(
    "numRegions, varData, expectedNumVarData, expectedBytes",
    [
        (
            5,
            [
                [10, 10, 0, 0, 20],
                {3: 300},
            ],
            1,
            126,
        ),
        (
            5,
            [
                [10, 10, 0, 0, 20],
                [10, 11, 0, 0, 20],
                [10, 12, 0, 0, 20],
                [10, 13, 0, 0, 20],
                {3: 300},
            ],
            1,
            175,
        ),
        (
            5,
            [
                [10, 11, 0, 0, 20],
                [10, 300, 0, 0, 20],
                [10, 301, 0, 0, 20],
                [10, 302, 0, 0, 20],
                [10, 303, 0, 0, 20],
                [10, 304, 0, 0, 20],
            ],
            1,
            180,
        ),
        (
            5,
            [
                [0, 11, 12, 0, 20],
                [0, 13, 12, 0, 20],
                [0, 14, 12, 0, 20],
                [0, 15, 12, 0, 20],
                [0, 16, 12, 0, 20],
                [10, 300, 0, 0, 20],
                [10, 301, 0, 0, 20],
                [10, 302, 0, 0, 20],
                [10, 303, 0, 0, 20],
                [10, 304, 0, 0, 20],
            ],
            1,
            200,
        ),
        (
            5,
            [
                [0, 11, 12, 0, 20],
                [0, 13, 12, 0, 20],
                [0, 14, 12, 0, 20],
                [0, 15, 12, 0, 20],
                [0, 16, 12, 0, 20],
                [0, 17, 12, 0, 20],
                [0, 18, 12, 0, 20],
                [0, 19, 12, 0, 20],
                [0, 20, 12, 0, 20],
                [10, 300, 0, 0, 20],
                [10, 301, 0, 0, 20],
                [10, 302, 0, 0, 20],
                [10, 303, 0, 0, 20],
                [10, 304, 0, 0, 20],
            ],
            2,
            218,
        ),
        (
            3,
            [
                [10, 10, 10],
            ],
            0,
            12,
        ),
    ],
)
def test_optimize(numRegions, varData, expectedNumVarData, expectedBytes):
    locations = [{i: i / 16384.0} for i in range(numRegions)]
    axisTags = sorted({k for loc in locations for k in loc})

    model = VariationModel(locations)
    builder = OnlineVarStoreBuilder(axisTags)
    builder.setModel(model)

    for data in varData:
        if type(data) is dict:
            newData = [0] * numRegions
            for k, v in data.items():
                newData[k] = v
            data = newData

        builder.storeMasters(data)

    varStore = builder.finish()
    varStore.optimize()

    dummyFont = TTFont()

    writer = XMLWriter(StringIO())
    varStore.toXML(writer, dummyFont)
    xml = writer.file.getvalue()

    assert len(varStore.VarData) == expectedNumVarData, xml

    writer = OTTableWriter()
    varStore.compile(writer, dummyFont)
    data = writer.getAllData()

    assert len(data) == expectedBytes, xml


@pytest.mark.parametrize(
    "quantization, expectedBytes",
    [
        (1, 200),
        (2, 180),
        (3, 170),
        (4, 175),
        (8, 170),
        (32, 92),
        (64, 56),
    ],
)
def test_quantize(quantization, expectedBytes):
    varData = [
        [0, 11, 12, 0, 20],
        [0, 13, 12, 0, 20],
        [0, 14, 12, 0, 20],
        [0, 15, 12, 0, 20],
        [0, 16, 12, 0, 20],
        [10, 300, 0, 0, 20],
        [10, 301, 0, 0, 20],
        [10, 302, 0, 0, 20],
        [10, 303, 0, 0, 20],
        [10, 304, 0, 0, 20],
    ]

    numRegions = 5
    locations = [{i: i / 16384.0} for i in range(numRegions)]
    axisTags = sorted({k for loc in locations for k in loc})

    model = VariationModel(locations)

    builder = OnlineVarStoreBuilder(axisTags)
    builder.setModel(model)

    for data in varData:
        builder.storeMasters(data)

    varStore = builder.finish()
    varStore.optimize(quantization=quantization)

    dummyFont = TTFont()

    writer = XMLWriter(StringIO())
    varStore.toXML(writer, dummyFont)
    xml = writer.file.getvalue()

    writer = OTTableWriter()
    varStore.compile(writer, dummyFont)
    data = writer.getAllData()

    assert len(data) == expectedBytes, xml


def test_optimize_overflow():
    numRegions = 1
    locations = [{"wght": 0}, {"wght": 0.5}]
    axisTags = ["wght"]

    model = VariationModel(locations)
    builder = OnlineVarStoreBuilder(axisTags)
    builder.setModel(model)

    for data in range(0, 0xFFFF * 2):
        data = [0, data]
        builder.storeMasters(data, round=noRound)

    varStore = builder.finish()
    varStore.optimize()

    for s in varStore.VarData:
        print(len(s.Item))

    # 5 data-sets:
    # - 0..127: 1-byte dataset
    # - 128..32767: 2-byte dataset
    # - 32768..32768+65535-1: 4-byte dataset
    # - 32768+65535..65535+65535-1: 4-byte dataset
    assert len(varStore.VarData) == 4
