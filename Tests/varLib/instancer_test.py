from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools import ttLib
from fontTools.ttLib.tables import _f_v_a_r
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


def _get_coordinates(varfont, glyphname):
    # converts GlyphCoordinates to a list of (x, y) tuples, so that pytest's
    # assert will give us a nicer diff
    return list(varfont["glyf"].getCoordinates(glyphname, varfont))


class InstantiateGvarTest(object):
    @pytest.mark.parametrize("glyph_name", ["hyphen"])
    @pytest.mark.parametrize(
        "optimize",
        [pytest.param(True, id="optimize"), pytest.param(False, id="no-optimize")],
    )
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
                        (33.5, 229),
                        (33.5, 308.5),
                        (264.5, 308.5),
                        (264.5, 229),
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

    def test_full_instance(self, varfont):
        instancer.instantiateGvar(varfont, {"wght": 0.0, "wdth": -0.5})

        assert _get_coordinates(varfont, "hyphen") == [
            (33.5, 229),
            (33.5, 308.5),
            (264.5, 308.5),
            (264.5, 229),
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
                {"wght": 1.0}, {"strs": 100, "undo": -200, "unds": 150}, id="wght=1.0"
            ),
            pytest.param(
                {"wght": 0.5}, {"strs": 75, "undo": -150, "unds": 100}, id="wght=0.5"
            ),
            pytest.param(
                {"wght": 0.0}, {"strs": 50, "undo": -100, "unds": 50}, id="wght=0.0"
            ),
            pytest.param(
                {"wdth": -1.0}, {"strs": 20, "undo": -100, "unds": 50}, id="wdth=-1.0"
            ),
            pytest.param(
                {"wdth": -0.5}, {"strs": 35, "undo": -100, "unds": 50}, id="wdth=-0.5"
            ),
            pytest.param(
                {"wdth": 0.0}, {"strs": 50, "undo": -100, "unds": 50}, id="wdth=0.0"
            ),
        ],
    )
    def test_pin_and_drop_axis(self, varfont, location, expected):
        mvar = varfont["MVAR"].table
        # initially we have a single VarData with deltas associated with 3 regions:
        # 1 with only wght, 1 with only wdth, and 1 with both wght and wdth.
        assert len(mvar.VarStore.VarData) == 1
        assert mvar.VarStore.VarRegionList.RegionCount == 3
        assert mvar.VarStore.VarData[0].VarRegionCount == 3
        assert all(len(item) == 3 for item in mvar.VarStore.VarData[0].Item)

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
    def test_getVarRegionAxes(self):
        axisOrder = ["wght", "wdth", "opsz"]
        regionAxes = {"wdth": (-1.0, -1.0, 0.0), "wght": (0.0, 1.0, 1.0)}
        region = builder.buildVarRegion(regionAxes, axisOrder)
        fvarAxes = [SimpleNamespace(axisTag=tag) for tag in axisOrder]

        result = instancer._getVarRegionAxes(region, fvarAxes)

        assert {
            axisTag: (axis.StartCoord, axis.PeakCoord, axis.EndCoord)
            for axisTag, axis in result.items()
        } == regionAxes

    @pytest.mark.parametrize(
        "location, regionAxes, expected",
        [
            ({"wght": 0.5}, {"wght": (0.0, 1.0, 1.0)}, 0.5),
            ({"wght": 0.5}, {"wght": (0.0, 1.0, 1.0), "wdth": (-1.0, -1.0, 0.0)}, 0.5),
            (
                {"wght": 0.5, "wdth": -0.5},
                {"wght": (0.0, 1.0, 1.0), "wdth": (-1.0, -1.0, 0.0)},
                0.25,
            ),
            ({"wght": 0.5, "wdth": -0.5}, {"wght": (0.0, 1.0, 1.0)}, 0.5),
            ({"wght": 0.5}, {"wdth": (-1.0, -1.0, 1.0)}, 1.0),
        ],
    )
    def test_getVarRegionScalar(self, location, regionAxes, expected):
        varRegionAxes = {
            axisTag: builder.buildVarRegionAxis(support)
            for axisTag, support in regionAxes.items()
        }

        assert instancer._getVarRegionScalar(location, varRegionAxes) == expected

    def test_scaleVarDataDeltas(self):
        regionScalars = [0.0, 0.5, 1.0]
        varData = builder.buildVarData(
            [1, 0], [[100, 200], [-100, -200]], optimize=False
        )

        instancer._scaleVarDataDeltas(varData, regionScalars)

        assert varData.Item == [[50, 0], [-50, 0]]

    def test_getVarDataDeltasForRegions(self):
        varData = builder.buildVarData(
            [1, 0], [[33.5, 67.9], [-100, -200]], optimize=False
        )

        assert instancer._getVarDataDeltasForRegions(varData, {1}) == [[33.5], [-100]]
        assert instancer._getVarDataDeltasForRegions(varData, {0}) == [[67.9], [-200]]
        assert instancer._getVarDataDeltasForRegions(varData, set()) == [[], []]
        assert instancer._getVarDataDeltasForRegions(varData, {1}, rounded=True) == [
            [34],
            [-100],
        ]

    def test_subsetVarStoreRegions(self):
        regionList = builder.buildVarRegionList(
            [
                {"wght": (0, 0.5, 1)},
                {"wght": (0.5, 1, 1)},
                {"wdth": (-1, -1, 0)},
                {"wght": (0, 0.5, 1), "wdth": (-1, -1, 0)},
                {"wght": (0.5, 1, 1), "wdth": (-1, -1, 0)},
            ],
            ["wght", "wdth"],
        )
        varData1 = builder.buildVarData([0, 1, 2, 4], [[0, 1, 2, 3], [4, 5, 6, 7]])
        varData2 = builder.buildVarData([2, 3, 1], [[8, 9, 10], [11, 12, 13]])
        varStore = builder.buildVarStore(regionList, [varData1, varData2])

        instancer._subsetVarStoreRegions(varStore, {0, 4})

        assert (
            varStore.VarRegionList.RegionCount
            == len(varStore.VarRegionList.Region)
            == 2
        )
        axis00 = varStore.VarRegionList.Region[0].VarRegionAxis[0]
        assert (axis00.StartCoord, axis00.PeakCoord, axis00.EndCoord) == (0, 0.5, 1)
        axis01 = varStore.VarRegionList.Region[0].VarRegionAxis[1]
        assert (axis01.StartCoord, axis01.PeakCoord, axis01.EndCoord) == (0, 0, 0)
        axis10 = varStore.VarRegionList.Region[1].VarRegionAxis[0]
        assert (axis10.StartCoord, axis10.PeakCoord, axis10.EndCoord) == (0.5, 1, 1)
        axis11 = varStore.VarRegionList.Region[1].VarRegionAxis[1]
        assert (axis11.StartCoord, axis11.PeakCoord, axis11.EndCoord) == (-1, -1, 0)

        assert varStore.VarDataCount == len(varStore.VarData) == 1
        assert varStore.VarData[0].VarRegionCount == 2
        assert varStore.VarData[0].VarRegionIndex == [0, 1]
        assert varStore.VarData[0].Item == [[0, 3], [4, 7]]
        assert varStore.VarData[0].NumShorts == 0

    @pytest.fixture
    def fvarAxes(self):
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
        "location, expected_deltas, num_regions, num_vardatas",
        [
            ({"wght": 0}, [[[0, 0, 0], [0, 0, 0]], [[], []]], 1, 1),
            ({"wght": 0.25}, [[[0, 50, 0], [0, 50, 0]], [[], []]], 2, 1),
            ({"wdth": 0}, [[[], []], [[0], [0]]], 3, 1),
            ({"wdth": -0.75}, [[[], []], [[75], [75]]], 6, 2),
            (
                {"wght": 0, "wdth": 0},
                [[[0, 0, 0], [0, 0, 0]], [[0, 0, 0, 0], [0, 0, 0, 0]]],
                0,
                0,
            ),
            (
                {"wght": 0.25, "wdth": 0},
                [[[0, 50, 0], [0, 50, 0]], [[0, 0, 0, 0], [0, 0, 0, 0]]],
                0,
                0,
            ),
            (
                {"wght": 0, "wdth": -0.75},
                [[[0, 0, 0], [0, 0, 0]], [[75, 0, 0, 0], [75, 0, 0, 0]]],
                0,
                0,
            ),
        ],
    )
    def test_instantiate_default_deltas(
        self, varStore, fvarAxes, location, expected_deltas, num_regions, num_vardatas
    ):
        defaultDeltas = instancer.instantiateItemVariationStore(
            varStore, fvarAxes, location
        )

        # from fontTools.misc.testTools import getXML
        # print("\n".join(getXML(varStore.toXML, ttFont=None)))

        assert defaultDeltas == expected_deltas
        assert varStore.VarRegionList.RegionCount == num_regions
        assert varStore.VarDataCount == num_vardatas
