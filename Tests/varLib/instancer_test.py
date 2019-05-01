from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools import designspaceLib
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib.tables import _f_v_a_r
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools import varLib
from fontTools.varLib import instancer
from fontTools.varLib.mvar import MVAR_ENTRIES
from fontTools.varLib import builder
from fontTools.varLib import models
import collections
from copy import deepcopy
import os
import pytest


TESTDATA = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture
def varfont():
    f = ttLib.TTFont()
    f.importXML(os.path.join(TESTDATA, "PartialInstancerTest-VF.ttx"))
    return f


@pytest.fixture(params=[True, False], ids=["optimize", "no-optimize"])
def optimize(request):
    return request.param


@pytest.fixture
def fvarAxes():
    wght = _f_v_a_r.Axis()
    wght.axisTag = Tag("wght")
    wght.minValue = 100
    wght.defaultValue = 400
    wght.maxValue = 900
    wdth = _f_v_a_r.Axis()
    wdth.axisTag = Tag("wdth")
    wdth.minValue = 70
    wdth.defaultValue = 100
    wdth.maxValue = 100
    return [wght, wdth]


def _get_coordinates(varfont, glyphname):
    # converts GlyphCoordinates to a list of (x, y) tuples, so that pytest's
    # assert will give us a nicer diff
    return list(varfont["glyf"].getCoordinates(glyphname, varfont))


class InstantiateGvarTest(object):
    @pytest.mark.parametrize("glyph_name", ["hyphen"])
    @pytest.mark.parametrize(
        "location, expected",
        [
            pytest.param(
                {"wdth": -1.0},
                {
                    "hyphen": [
                        (27, 229),
                        (27, 310),
                        (247, 310),
                        (247, 229),
                        (0, 0),
                        (274, 0),
                        (0, 536),
                        (0, 0),
                    ]
                },
                id="wdth=-1.0",
            ),
            pytest.param(
                {"wdth": -0.5},
                {
                    "hyphen": [
                        (34, 229),
                        (34, 309),
                        (265, 309),
                        (265, 229),
                        (0, 0),
                        (298, 0),
                        (0, 536),
                        (0, 0),
                    ]
                },
                id="wdth=-0.5",
            ),
            # an axis pinned at the default normalized location (0.0) means
            # the default glyf outline stays the same
            pytest.param(
                {"wdth": 0.0},
                {
                    "hyphen": [
                        (40, 229),
                        (40, 307),
                        (282, 307),
                        (282, 229),
                        (0, 0),
                        (322, 0),
                        (0, 536),
                        (0, 0),
                    ]
                },
                id="wdth=0.0",
            ),
        ],
    )
    def test_pin_and_drop_axis(self, varfont, glyph_name, location, expected, optimize):
        instancer.instantiateGvar(varfont, location, optimize=optimize)

        assert _get_coordinates(varfont, glyph_name) == expected[glyph_name]

        # check that the pinned axis has been dropped from gvar
        assert not any(
            "wdth" in t.axes
            for tuples in varfont["gvar"].variations.values()
            for t in tuples
        )

    def test_full_instance(self, varfont, optimize):
        instancer.instantiateGvar(
            varfont, {"wght": 0.0, "wdth": -0.5}, optimize=optimize
        )

        assert _get_coordinates(varfont, "hyphen") == [
            (34, 229),
            (34, 309),
            (265, 309),
            (265, 229),
            (0, 0),
            (298, 0),
            (0, 536),
            (0, 0),
        ]

        assert "gvar" not in varfont


class InstantiateCvarTest(object):
    @pytest.mark.parametrize(
        "location, expected",
        [
            pytest.param({"wght": -1.0}, [500, -400, 150, 250], id="wght=-1.0"),
            pytest.param({"wdth": -1.0}, [500, -400, 180, 200], id="wdth=-1.0"),
            pytest.param({"wght": -0.5}, [500, -400, 165, 250], id="wght=-0.5"),
            pytest.param({"wdth": -0.3}, [500, -400, 180, 235], id="wdth=-0.3"),
        ],
    )
    def test_pin_and_drop_axis(self, varfont, location, expected):
        instancer.instantiateCvar(varfont, location)

        assert list(varfont["cvt "].values) == expected

        # check that the pinned axis has been dropped from cvar
        pinned_axes = location.keys()
        assert not any(
            axis in t.axes for t in varfont["cvar"].variations for axis in pinned_axes
        )

    def test_full_instance(self, varfont):
        instancer.instantiateCvar(varfont, {"wght": -0.5, "wdth": -0.5})

        assert list(varfont["cvt "].values) == [500, -400, 165, 225]

        assert "cvar" not in varfont


class InstantiateMVARTest(object):
    @pytest.mark.parametrize(
        "location, expected",
        [
            pytest.param(
                {"wght": 1.0},
                {"strs": 100, "undo": -200, "unds": 150, "xhgt": 530},
                id="wght=1.0",
            ),
            pytest.param(
                {"wght": 0.5},
                {"strs": 75, "undo": -150, "unds": 100, "xhgt": 515},
                id="wght=0.5",
            ),
            pytest.param(
                {"wght": 0.0},
                {"strs": 50, "undo": -100, "unds": 50, "xhgt": 500},
                id="wght=0.0",
            ),
            pytest.param(
                {"wdth": -1.0},
                {"strs": 20, "undo": -100, "unds": 50, "xhgt": 500},
                id="wdth=-1.0",
            ),
            pytest.param(
                {"wdth": -0.5},
                {"strs": 35, "undo": -100, "unds": 50, "xhgt": 500},
                id="wdth=-0.5",
            ),
            pytest.param(
                {"wdth": 0.0},
                {"strs": 50, "undo": -100, "unds": 50, "xhgt": 500},
                id="wdth=0.0",
            ),
        ],
    )
    def test_pin_and_drop_axis(self, varfont, location, expected):
        mvar = varfont["MVAR"].table
        # initially we have two VarData: the first contains deltas associated with 3
        # regions: 1 with only wght, 1 with only wdth, and 1 with both wght and wdth
        assert len(mvar.VarStore.VarData) == 2
        assert mvar.VarStore.VarRegionList.RegionCount == 3
        assert mvar.VarStore.VarData[0].VarRegionCount == 3
        assert all(len(item) == 3 for item in mvar.VarStore.VarData[0].Item)
        # The second VarData has deltas associated only with 1 region (wght only).
        assert mvar.VarStore.VarData[1].VarRegionCount == 1
        assert all(len(item) == 1 for item in mvar.VarStore.VarData[1].Item)

        instancer.instantiateMVAR(varfont, location)

        for mvar_tag, expected_value in expected.items():
            table_tag, item_name = MVAR_ENTRIES[mvar_tag]
            assert getattr(varfont[table_tag], item_name) == expected_value

        # check that regions and accompanying deltas have been dropped
        num_regions_left = len(mvar.VarStore.VarRegionList.Region)
        assert num_regions_left < 3
        assert mvar.VarStore.VarRegionList.RegionCount == num_regions_left
        assert mvar.VarStore.VarData[0].VarRegionCount == num_regions_left
        # VarData subtables have been merged
        assert len(mvar.VarStore.VarData) == 1

    @pytest.mark.parametrize(
        "location, expected",
        [
            pytest.param(
                {"wght": 1.0, "wdth": 0.0},
                {"strs": 100, "undo": -200, "unds": 150},
                id="wght=1.0,wdth=0.0",
            ),
            pytest.param(
                {"wght": 0.0, "wdth": -1.0},
                {"strs": 20, "undo": -100, "unds": 50},
                id="wght=0.0,wdth=-1.0",
            ),
            pytest.param(
                {"wght": 0.5, "wdth": -0.5},
                {"strs": 55, "undo": -145, "unds": 95},
                id="wght=0.5,wdth=-0.5",
            ),
            pytest.param(
                {"wght": 1.0, "wdth": -1.0},
                {"strs": 50, "undo": -180, "unds": 130},
                id="wght=0.5,wdth=-0.5",
            ),
        ],
    )
    def test_full_instance(self, varfont, location, expected):
        instancer.instantiateMVAR(varfont, location)

        for mvar_tag, expected_value in expected.items():
            table_tag, item_name = MVAR_ENTRIES[mvar_tag]
            assert getattr(varfont[table_tag], item_name) == expected_value

        assert "MVAR" not in varfont


class InstantiateHVARTest(object):
    # the 'expectedDeltas' below refer to the VarData item deltas for the "hyphen"
    # glyph in the PartialInstancerTest-VF.ttx test font, that are left after
    # partial instancing
    @pytest.mark.parametrize(
        "location, expectedRegions, expectedDeltas",
        [
            ({"wght": -1.0}, [{"wdth": (-1.0, -1.0, 0)}], [-59]),
            ({"wght": 0}, [{"wdth": (-1.0, -1.0, 0)}], [-48]),
            ({"wght": 1.0}, [{"wdth": (-1.0, -1.0, 0)}], [7]),
            (
                {"wdth": -1.0},
                [
                    {"wght": (-1.0, -1.0, 0.0)},
                    {"wght": (0.0, 0.61, 1.0)},
                    {"wght": (0.61, 1.0, 1.0)},
                ],
                [-11, 31, 51],
            ),
            ({"wdth": 0}, [{"wght": (0.61, 1.0, 1.0)}], [-4]),
        ],
    )
    def test_partial_instance(self, varfont, location, expectedRegions, expectedDeltas):
        instancer.instantiateHVAR(varfont, location)

        assert "HVAR" in varfont
        hvar = varfont["HVAR"].table
        varStore = hvar.VarStore

        regions = varStore.VarRegionList.Region
        fvarAxes = [a for a in varfont["fvar"].axes if a.axisTag not in location]
        assert [reg.get_support(fvarAxes) for reg in regions] == expectedRegions

        assert len(varStore.VarData) == 1
        assert varStore.VarData[0].ItemCount == 2

        assert hvar.AdvWidthMap is not None
        advWithMap = hvar.AdvWidthMap.mapping

        assert advWithMap[".notdef"] == advWithMap["space"]
        varIdx = advWithMap[".notdef"]
        # these glyphs have no metrics variations in the test font
        assert varStore.VarData[varIdx >> 16].Item[varIdx & 0xFFFF] == (
            [0] * varStore.VarData[0].VarRegionCount
        )

        varIdx = advWithMap["hyphen"]
        assert varStore.VarData[varIdx >> 16].Item[varIdx & 0xFFFF] == expectedDeltas

    def test_full_instance(self, varfont):
        instancer.instantiateHVAR(varfont, {"wght": 0, "wdth": 0})

        assert "HVAR" not in varfont


class InstantiateItemVariationStoreTest(object):
    def test_VarRegion_get_support(self):
        axisOrder = ["wght", "wdth", "opsz"]
        regionAxes = {"wdth": (-1.0, -1.0, 0.0), "wght": (0.0, 1.0, 1.0)}
        region = builder.buildVarRegion(regionAxes, axisOrder)

        assert len(region.VarRegionAxis) == 3
        assert region.VarRegionAxis[2].PeakCoord == 0

        fvarAxes = [SimpleNamespace(axisTag=axisTag) for axisTag in axisOrder]

        assert region.get_support(fvarAxes) == regionAxes

    @pytest.fixture
    def varStore(self):
        return builder.buildVarStore(
            builder.buildVarRegionList(
                [
                    {"wght": (-1.0, -1.0, 0)},
                    {"wght": (0, 0.5, 1.0)},
                    {"wght": (0.5, 1.0, 1.0)},
                    {"wdth": (-1.0, -1.0, 0)},
                    {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)},
                    {"wght": (0, 0.5, 1.0), "wdth": (-1.0, -1.0, 0)},
                    {"wght": (0.5, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)},
                ],
                ["wght", "wdth"],
            ),
            [
                builder.buildVarData([0, 1, 2], [[100, 100, 100], [100, 100, 100]]),
                builder.buildVarData(
                    [3, 4, 5, 6], [[100, 100, 100, 100], [100, 100, 100, 100]]
                ),
            ],
        )

    @pytest.mark.parametrize(
        "location, expected_deltas, num_regions",
        [
            ({"wght": 0}, [[0, 0], [0, 0]], 1),
            ({"wght": 0.25}, [[50, 50], [0, 0]], 1),
            ({"wdth": 0}, [[0, 0], [0, 0]], 3),
            ({"wdth": -0.75}, [[0, 0], [75, 75]], 3),
            ({"wght": 0, "wdth": 0}, [[0, 0], [0, 0]], 0),
            ({"wght": 0.25, "wdth": 0}, [[50, 50], [0, 0]], 0),
            ({"wght": 0, "wdth": -0.75}, [[0, 0], [75, 75]], 0),
        ],
    )
    def test_instantiate_default_deltas(
        self, varStore, fvarAxes, location, expected_deltas, num_regions
    ):
        defaultDeltas = instancer.instantiateItemVariationStore(
            varStore, fvarAxes, location
        )

        defaultDeltaArray = []
        for varidx, delta in sorted(defaultDeltas.items()):
            major, minor = varidx >> 16, varidx & 0xFFFF
            if major == len(defaultDeltaArray):
                defaultDeltaArray.append([])
            assert len(defaultDeltaArray[major]) == minor
            defaultDeltaArray[major].append(delta)

        assert defaultDeltaArray == expected_deltas
        assert varStore.VarRegionList.RegionCount == num_regions


class TupleVarStoreAdapterTest(object):
    def test_instantiate(self):
        regions = [
            {"wght": (-1.0, -1.0, 0)},
            {"wght": (0.0, 1.0, 1.0)},
            {"wdth": (-1.0, -1.0, 0)},
            {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)},
            {"wght": (0, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)},
        ]
        axisOrder = ["wght", "wdth"]
        tupleVarData = [
            [
                TupleVariation({"wght": (-1.0, -1.0, 0)}, [10, 70]),
                TupleVariation({"wght": (0.0, 1.0, 1.0)}, [30, 90]),
                TupleVariation(
                    {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)}, [-40, -100]
                ),
                TupleVariation(
                    {"wght": (0, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)}, [-60, -120]
                ),
            ],
            [
                TupleVariation({"wdth": (-1.0, -1.0, 0)}, [5, 45]),
                TupleVariation(
                    {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)}, [-15, -55]
                ),
                TupleVariation(
                    {"wght": (0, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)}, [-35, -75]
                ),
            ],
        ]
        adapter = instancer._TupleVarStoreAdapter(
            regions, axisOrder, tupleVarData, itemCounts=[2, 2]
        )

        defaultDeltaArray = adapter.instantiate({"wght": 0.5})

        assert defaultDeltaArray == [[15, 45], [0, 0]]
        assert adapter.regions == [{"wdth": (-1.0, -1.0, 0)}]
        assert adapter.tupleVarData == [
            [TupleVariation({"wdth": (-1.0, -1.0, 0)}, [-30, -60])],
            [TupleVariation({"wdth": (-1.0, -1.0, 0)}, [-12, 8])],
        ]

    def test_dropAxes(self):
        regions = [
            {"wght": (-1.0, -1.0, 0)},
            {"wght": (0.0, 1.0, 1.0)},
            {"wdth": (-1.0, -1.0, 0)},
            {"opsz": (0.0, 1.0, 1.0)},
            {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)},
            {"wght": (0, 0.5, 1.0), "wdth": (-1.0, -1.0, 0)},
            {"wght": (0.5, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)},
        ]
        axisOrder = ["wght", "wdth", "opsz"]
        adapter = instancer._TupleVarStoreAdapter(regions, axisOrder, [], itemCounts=[])

        adapter.dropAxes({"wdth"})

        assert adapter.regions == [
            {"wght": (-1.0, -1.0, 0)},
            {"wght": (0.0, 1.0, 1.0)},
            {"opsz": (0.0, 1.0, 1.0)},
            {"wght": (0.0, 0.5, 1.0)},
            {"wght": (0.5, 1.0, 1.0)},
        ]

        adapter.dropAxes({"wght", "opsz"})

        assert adapter.regions == []

    def test_roundtrip(self, fvarAxes):
        regions = [
            {"wght": (-1.0, -1.0, 0)},
            {"wght": (0, 0.5, 1.0)},
            {"wght": (0.5, 1.0, 1.0)},
            {"wdth": (-1.0, -1.0, 0)},
            {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)},
            {"wght": (0, 0.5, 1.0), "wdth": (-1.0, -1.0, 0)},
            {"wght": (0.5, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)},
        ]
        axisOrder = [axis.axisTag for axis in fvarAxes]

        itemVarStore = builder.buildVarStore(
            builder.buildVarRegionList(regions, axisOrder),
            [
                builder.buildVarData(
                    [0, 1, 2, 4, 5, 6],
                    [[10, -20, 30, -40, 50, -60], [70, -80, 90, -100, 110, -120]],
                ),
                builder.buildVarData(
                    [3, 4, 5, 6], [[5, -15, 25, -35], [45, -55, 65, -75]]
                ),
            ],
        )

        adapter = instancer._TupleVarStoreAdapter.fromItemVarStore(
            itemVarStore, fvarAxes
        )

        assert adapter.tupleVarData == [
            [
                TupleVariation({"wght": (-1.0, -1.0, 0)}, [10, 70]),
                TupleVariation({"wght": (0, 0.5, 1.0)}, [-20, -80]),
                TupleVariation({"wght": (0.5, 1.0, 1.0)}, [30, 90]),
                TupleVariation(
                    {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)}, [-40, -100]
                ),
                TupleVariation(
                    {"wght": (0, 0.5, 1.0), "wdth": (-1.0, -1.0, 0)}, [50, 110]
                ),
                TupleVariation(
                    {"wght": (0.5, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)}, [-60, -120]
                ),
            ],
            [
                TupleVariation({"wdth": (-1.0, -1.0, 0)}, [5, 45]),
                TupleVariation(
                    {"wght": (-1.0, -1.0, 0), "wdth": (-1.0, -1.0, 0)}, [-15, -55]
                ),
                TupleVariation(
                    {"wght": (0, 0.5, 1.0), "wdth": (-1.0, -1.0, 0)}, [25, 65]
                ),
                TupleVariation(
                    {"wght": (0.5, 1.0, 1.0), "wdth": (-1.0, -1.0, 0)}, [-35, -75]
                ),
            ],
        ]
        assert adapter.itemCounts == [data.ItemCount for data in itemVarStore.VarData]
        assert adapter.regions == regions
        assert adapter.axisOrder == axisOrder

        itemVarStore2 = adapter.asItemVarStore()

        assert [
            reg.get_support(fvarAxes) for reg in itemVarStore2.VarRegionList.Region
        ] == regions

        assert itemVarStore2.VarDataCount == 2
        assert itemVarStore2.VarData[0].VarRegionIndex == [0, 1, 2, 4, 5, 6]
        assert itemVarStore2.VarData[0].Item == [
            [10, -20, 30, -40, 50, -60],
            [70, -80, 90, -100, 110, -120],
        ]
        assert itemVarStore2.VarData[1].VarRegionIndex == [3, 4, 5, 6]
        assert itemVarStore2.VarData[1].Item == [[5, -15, 25, -35], [45, -55, 65, -75]]


def makeTTFont(glyphOrder, features):
    font = ttLib.TTFont()
    font.setGlyphOrder(glyphOrder)
    addOpenTypeFeaturesFromString(font, features)
    font["name"] = ttLib.newTable("name")
    return font


def _makeDSAxesDict(axes):
    dsAxes = collections.OrderedDict()
    for axisTag, axisValues in axes:
        axis = designspaceLib.AxisDescriptor()
        axis.name = axis.tag = axis.labelNames["en"] = axisTag
        axis.minimum, axis.default, axis.maximum = axisValues
        dsAxes[axis.tag] = axis
    return dsAxes


def makeVariableFont(masters, baseIndex, axes, masterLocations):
    vf = deepcopy(masters[baseIndex])
    dsAxes = _makeDSAxesDict(axes)
    fvar = varLib._add_fvar(vf, dsAxes, instances=())
    axisTags = [axis.axisTag for axis in fvar.axes]
    normalizedLocs = [models.normalizeLocation(m, dict(axes)) for m in masterLocations]
    model = models.VariationModel(normalizedLocs, axisOrder=axisTags)
    varLib._merge_OTL(vf, model, masters, axisTags)
    return vf


def makeParametrizedVF(glyphOrder, features, values, increments):
    # Create a test VF with given glyphs and parametrized OTL features.
    # The VF is built from 9 masters (3 x 3 along wght and wdth), with
    # locations hard-coded and base master at wght=400 and wdth=100.
    # 'values' is a list of initial values that are interpolated in the
    # 'features' string, and incremented for each subsequent master by the
    # given 'increments' (list of 2-tuple) along the two axes.
    assert values and len(values) == len(increments)
    assert all(len(i) == 2 for i in increments)
    masterLocations = [
        {"wght": 100, "wdth": 50},
        {"wght": 100, "wdth": 100},
        {"wght": 100, "wdth": 150},
        {"wght": 400, "wdth": 50},
        {"wght": 400, "wdth": 100},  # base master
        {"wght": 400, "wdth": 150},
        {"wght": 700, "wdth": 50},
        {"wght": 700, "wdth": 100},
        {"wght": 700, "wdth": 150},
    ]
    n = len(values)
    values = list(values)
    masters = []
    for _ in range(3):
        for _ in range(3):
            master = makeTTFont(glyphOrder, features=features % tuple(values))
            masters.append(master)
            for i in range(n):
                values[i] += increments[i][1]
        for i in range(n):
            values[i] += increments[i][0]
    baseIndex = 4
    axes = [("wght", (100, 400, 700)), ("wdth", (50, 100, 150))]
    vf = makeVariableFont(masters, baseIndex, axes, masterLocations)
    return vf


@pytest.fixture
def varfontGDEF():
    glyphOrder = [".notdef", "f", "i", "f_i"]
    features = (
        "feature liga { sub f i by f_i;} liga;"
        "table GDEF { LigatureCaretByPos f_i %d; } GDEF;"
    )
    values = [100]
    increments = [(+30, +10)]
    return makeParametrizedVF(glyphOrder, features, values, increments)


@pytest.fixture
def varfontGPOS():
    glyphOrder = [".notdef", "V", "A"]
    features = "feature kern { pos V A %d; } kern;"
    values = [-80]
    increments = [(-10, -5)]
    return makeParametrizedVF(glyphOrder, features, values, increments)


@pytest.fixture
def varfontGPOS2():
    glyphOrder = [".notdef", "V", "A", "acutecomb"]
    features = (
        "markClass [acutecomb] <anchor 150 -10> @TOP_MARKS;"
        "feature mark {"
        "  pos base A <anchor %d 450> mark @TOP_MARKS;"
        "} mark;"
        "feature kern {"
        "  pos V A %d;"
        "} kern;"
    )
    values = [200, -80]
    increments = [(+30, +10), (-10, -5)]
    return makeParametrizedVF(glyphOrder, features, values, increments)


class InstantiateOTLTest(object):
    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0}, 110),  # -60
            ({"wght": 0}, 170),
            ({"wght": 0.5}, 200),  # +30
            ({"wght": 1.0}, 230),  # +60
            ({"wdth": -1.0}, 160),  # -10
            ({"wdth": -0.3}, 167),  # -3
            ({"wdth": 0}, 170),
            ({"wdth": 1.0}, 180),  # +10
        ],
    )
    def test_pin_and_drop_axis_GDEF(self, varfontGDEF, location, expected):
        vf = varfontGDEF
        assert "GDEF" in vf

        instancer.instantiateOTL(vf, location)

        assert "GDEF" in vf
        gdef = vf["GDEF"].table
        assert gdef.Version == 0x00010003
        assert gdef.VarStore
        assert gdef.LigCaretList
        caretValue = gdef.LigCaretList.LigGlyph[0].CaretValue[0]
        assert caretValue.Format == 3
        assert hasattr(caretValue, "DeviceTable")
        assert caretValue.DeviceTable.DeltaFormat == 0x8000
        assert caretValue.Coordinate == expected

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0, "wdth": -1.0}, 100),  # -60 - 10
            ({"wght": -1.0, "wdth": 0.0}, 110),  # -60
            ({"wght": -1.0, "wdth": 1.0}, 120),  # -60 + 10
            ({"wght": 0.0, "wdth": -1.0}, 160),  # -10
            ({"wght": 0.0, "wdth": 0.0}, 170),
            ({"wght": 0.0, "wdth": 1.0}, 180),  # +10
            ({"wght": 1.0, "wdth": -1.0}, 220),  # +60 - 10
            ({"wght": 1.0, "wdth": 0.0}, 230),  # +60
            ({"wght": 1.0, "wdth": 1.0}, 240),  # +60 + 10
        ],
    )
    def test_full_instance_GDEF(self, varfontGDEF, location, expected):
        vf = varfontGDEF
        assert "GDEF" in vf

        instancer.instantiateOTL(vf, location)

        assert "GDEF" in vf
        gdef = vf["GDEF"].table
        assert gdef.Version == 0x00010000
        assert not hasattr(gdef, "VarStore")
        assert gdef.LigCaretList
        caretValue = gdef.LigCaretList.LigGlyph[0].CaretValue[0]
        assert caretValue.Format == 1
        assert not hasattr(caretValue, "DeviceTable")
        assert caretValue.Coordinate == expected

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0}, -85),  # +25
            ({"wght": 0}, -110),
            ({"wght": 1.0}, -135),  # -25
            ({"wdth": -1.0}, -105),  # +5
            ({"wdth": 0}, -110),
            ({"wdth": 1.0}, -115),  # -5
        ],
    )
    def test_pin_and_drop_axis_GPOS_kern(self, varfontGPOS, location, expected):
        vf = varfontGPOS
        assert "GDEF" in vf
        assert "GPOS" in vf

        instancer.instantiateOTL(vf, location)

        gdef = vf["GDEF"].table
        gpos = vf["GPOS"].table
        assert gdef.Version == 0x00010003
        assert gdef.VarStore

        assert gpos.LookupList.Lookup[0].LookupType == 2  # PairPos
        pairPos = gpos.LookupList.Lookup[0].SubTable[0]
        valueRec1 = pairPos.PairSet[0].PairValueRecord[0].Value1
        assert valueRec1.XAdvDevice
        assert valueRec1.XAdvDevice.DeltaFormat == 0x8000
        assert valueRec1.XAdvance == expected

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0, "wdth": -1.0}, -80),  # +25 + 5
            ({"wght": -1.0, "wdth": 0.0}, -85),  # +25
            ({"wght": -1.0, "wdth": 1.0}, -90),  # +25 - 5
            ({"wght": 0.0, "wdth": -1.0}, -105),  # +5
            ({"wght": 0.0, "wdth": 0.0}, -110),
            ({"wght": 0.0, "wdth": 1.0}, -115),  # -5
            ({"wght": 1.0, "wdth": -1.0}, -130),  # -25 + 5
            ({"wght": 1.0, "wdth": 0.0}, -135),  # -25
            ({"wght": 1.0, "wdth": 1.0}, -140),  # -25 - 5
        ],
    )
    def test_full_instance_GPOS_kern(self, varfontGPOS, location, expected):
        vf = varfontGPOS
        assert "GDEF" in vf
        assert "GPOS" in vf

        instancer.instantiateOTL(vf, location)

        assert "GDEF" not in vf
        gpos = vf["GPOS"].table

        assert gpos.LookupList.Lookup[0].LookupType == 2  # PairPos
        pairPos = gpos.LookupList.Lookup[0].SubTable[0]
        valueRec1 = pairPos.PairSet[0].PairValueRecord[0].Value1
        assert not hasattr(valueRec1, "XAdvDevice")
        assert valueRec1.XAdvance == expected

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0}, (210, -85)),  # -60, +25
            ({"wght": 0}, (270, -110)),
            ({"wght": 0.5}, (300, -122)),  # +30, -12
            ({"wght": 1.0}, (330, -135)),  # +60, -25
            ({"wdth": -1.0}, (260, -105)),  # -10, +5
            ({"wdth": -0.3}, (267, -108)),  # -3, +2
            ({"wdth": 0}, (270, -110)),
            ({"wdth": 1.0}, (280, -115)),  # +10, -5
        ],
    )
    def test_pin_and_drop_axis_GPOS_mark_and_kern(
        self, varfontGPOS2, location, expected
    ):
        vf = varfontGPOS2
        assert "GDEF" in vf
        assert "GPOS" in vf

        instancer.instantiateOTL(vf, location)

        v1, v2 = expected
        gdef = vf["GDEF"].table
        gpos = vf["GPOS"].table
        assert gdef.Version == 0x00010003
        assert gdef.VarStore
        assert gdef.GlyphClassDef

        assert gpos.LookupList.Lookup[0].LookupType == 4  # MarkBasePos
        markBasePos = gpos.LookupList.Lookup[0].SubTable[0]
        baseAnchor = markBasePos.BaseArray.BaseRecord[0].BaseAnchor[0]
        assert baseAnchor.Format == 3
        assert baseAnchor.XDeviceTable
        assert baseAnchor.XDeviceTable.DeltaFormat == 0x8000
        assert not baseAnchor.YDeviceTable
        assert baseAnchor.XCoordinate == v1
        assert baseAnchor.YCoordinate == 450

        assert gpos.LookupList.Lookup[1].LookupType == 2  # PairPos
        pairPos = gpos.LookupList.Lookup[1].SubTable[0]
        valueRec1 = pairPos.PairSet[0].PairValueRecord[0].Value1
        assert valueRec1.XAdvDevice
        assert valueRec1.XAdvDevice.DeltaFormat == 0x8000
        assert valueRec1.XAdvance == v2

    @pytest.mark.parametrize(
        "location, expected",
        [
            ({"wght": -1.0, "wdth": -1.0}, (200, -80)),  # -60 - 10, +25 + 5
            ({"wght": -1.0, "wdth": 0.0}, (210, -85)),  # -60, +25
            ({"wght": -1.0, "wdth": 1.0}, (220, -90)),  # -60 + 10, +25 - 5
            ({"wght": 0.0, "wdth": -1.0}, (260, -105)),  # -10, +5
            ({"wght": 0.0, "wdth": 0.0}, (270, -110)),
            ({"wght": 0.0, "wdth": 1.0}, (280, -115)),  # +10, -5
            ({"wght": 1.0, "wdth": -1.0}, (320, -130)),  # +60 - 10, -25 + 5
            ({"wght": 1.0, "wdth": 0.0}, (330, -135)),  # +60, -25
            ({"wght": 1.0, "wdth": 1.0}, (340, -140)),  # +60 + 10, -25 - 5
        ],
    )
    def test_full_instance_GPOS_mark_and_kern(self, varfontGPOS2, location, expected):
        vf = varfontGPOS2
        assert "GDEF" in vf
        assert "GPOS" in vf

        instancer.instantiateOTL(vf, location)

        v1, v2 = expected
        gdef = vf["GDEF"].table
        gpos = vf["GPOS"].table
        assert gdef.Version == 0x00010000
        assert not hasattr(gdef, "VarStore")
        assert gdef.GlyphClassDef

        assert gpos.LookupList.Lookup[0].LookupType == 4  # MarkBasePos
        markBasePos = gpos.LookupList.Lookup[0].SubTable[0]
        baseAnchor = markBasePos.BaseArray.BaseRecord[0].BaseAnchor[0]
        assert baseAnchor.Format == 1
        assert not hasattr(baseAnchor, "XDeviceTable")
        assert not hasattr(baseAnchor, "YDeviceTable")
        assert baseAnchor.XCoordinate == v1
        assert baseAnchor.YCoordinate == 450

        assert gpos.LookupList.Lookup[1].LookupType == 2  # PairPos
        pairPos = gpos.LookupList.Lookup[1].SubTable[0]
        valueRec1 = pairPos.PairSet[0].PairValueRecord[0].Value1
        assert not hasattr(valueRec1, "XAdvDevice")
        assert valueRec1.XAdvance == v2


class InstantiateAvarTest(object):
    @pytest.mark.parametrize("location", [{"wght": 0.0}, {"wdth": 0.0}])
    def test_pin_and_drop_axis(self, varfont, location):
        instancer.instantiateAvar(varfont, location)

        assert set(varfont["avar"].segments).isdisjoint(location)

    def test_full_instance(self, varfont):
        instancer.instantiateAvar(varfont, {"wght": 0.0, "wdth": 0.0})

        assert "avar" not in varfont
