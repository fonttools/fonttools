from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.ttLib.tables import _f_v_a_r
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.varLib import instancer
from fontTools.varLib.mvar import MVAR_ENTRIES
from fontTools.varLib import builder
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
                        (0, 1000),
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
                        (0, 1000),
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
                        (0, 1000),
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
            (0, 1000),
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


class InstantiateMvarTest(object):
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

        instancer.instantiateMvar(varfont, location)

        for mvar_tag, expected_value in expected.items():
            table_tag, item_name = MVAR_ENTRIES[mvar_tag]
            assert getattr(varfont[table_tag], item_name) == expected_value

        # check that the pinned axis does not influence any of the remaining regions
        # in MVAR VarStore
        pinned_axes = location.keys()
        fvar = varfont["fvar"]
        assert all(
            peak == 0
            for region in mvar.VarStore.VarRegionList.Region
            for axis, (start, peak, end) in region.get_support(fvar.axes).items()
            if axis in pinned_axes
        )

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
        instancer.instantiateMvar(varfont, location)

        for mvar_tag, expected_value in expected.items():
            table_tag, item_name = MVAR_ENTRIES[mvar_tag]
            assert getattr(varfont[table_tag], item_name) == expected_value

        assert "MVAR" not in varfont


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
        defaultDeltas, _ = instancer.instantiateItemVariationStore(
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
            reg.get_support(fvarAxes)
            for reg in itemVarStore2.VarRegionList.Region
        ] == regions

        assert itemVarStore2.VarDataCount == 2
        assert itemVarStore2.VarData[0].VarRegionIndex == [0, 1, 2, 4, 5, 6]
        assert itemVarStore2.VarData[0].Item == [
            [10, -20, 30, -40, 50, -60],
            [70, -80, 90, -100, 110, -120],
        ]
        assert itemVarStore2.VarData[1].VarRegionIndex == [3, 4, 5, 6]
        assert itemVarStore2.VarData[1].Item == [[5, -15, 25, -35], [45, -55, 65, -75]]
